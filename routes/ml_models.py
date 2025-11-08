import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from schemas.model import PredictionInput
from schemas.model import AlternativesInput, SearchAlternativesInput
import json
from service.firebase_service import db, get_current_user
from firebase_admin import firestore
import logging
from collections import defaultdict

router = APIRouter()
logging.basicConfig(level=logging.INFO)

MODEL_PATH = "models/"
try:
    risk_model = joblib.load(f'{MODEL_PATH}risk_model_3.joblib')
    reactions_model = joblib.load(f'{MODEL_PATH}reactions_model_3.joblib')
    risk_binarizer = joblib.load(f'{MODEL_PATH}risk_binarizer_3.joblib')
    reactions_binarizer = joblib.load(f'{MODEL_PATH}reactions_binarizer_3.joblib')
    logging.info("--- All 4 ML models loaded successfully! ---")

except FileNotFoundError:
    logging.error("--- ERROR: Model files not found. ---")
    risk_model, reactions_model, risk_binarizer, reactions_binarizer = None, None, None, None


@router.post("/predict")
async def predict_all(data: PredictionInput, current_user: str = Depends(get_current_user)):
    
    if not all([risk_model, reactions_model, risk_binarizer, reactions_binarizer]):
         raise HTTPException(status_code=500, detail="Models are not loaded.")
    
    try:
        sample_df = pd.DataFrame([data.dict()])
    except Exception as e:
        logging.error(f"Error creating DataFrame: {e}")
        raise HTTPException(status_code=400, detail="Error processing input data.")

    try:
        risk_pred_encoded = risk_model.predict(sample_df)
        risk_labels = risk_binarizer.inverse_transform(risk_pred_encoded)
        
        reaction_pred_encoded = reactions_model.predict(sample_df)
        reaction_labels = reactions_binarizer.inverse_transform(reaction_pred_encoded)
    
    except Exception as e:
        logging.error(f"Error during model prediction: {e}")
        raise HTTPException(status_code=500, detail="Error making prediction.")

    if current_user:
        try:
            search_term = data.drug_profile_joined.split('_ROLE_')[0]
            
            if search_term and search_term != "UNKNOWN":
                history_ref = db.collection("users").document(current_user).collection("search_history")
                history_ref.add({
                    "search_term": search_term,
                    "timestamp": firestore.SERVER_TIMESTAMP  
                })
        except Exception as e:
            logging.warning(f"Failed to save search history for user {current_user}: {e}")

    return {
        "risk_profile": risk_labels[0],
        "side_effects": reaction_labels[0]
    }



ALTERNATIVES_FILE_PATH = "models/alternative_medicine.json" # Make sure this path is correct
try:
    with open(ALTERNATIVES_FILE_PATH, 'r') as f:
        alternatives_data = json.load(f)
    logging.info(f"--- Alternatives lookup file loaded successfully! ({ALTERNATIVES_FILE_PATH}) ---")
except FileNotFoundError:
    logging.error(f"--- ERROR: {ALTERNATIVES_FILE_PATH} not found. Alternatives will not work. ---")
    alternatives_data = {}

@router.post("/alternatives")
async def get_alternatives(data: AlternativesInput, current_user: str = Depends(get_current_user)):
    """
    Finds alternative drugs for a given indication that do NOT have
    the specified side effects, using fuzzy matching.
    """
    if not alternatives_data:
         raise HTTPException(status_code=500, detail="Alternatives data is not loaded.")

    indication_key = data.indication.strip().lower()
    
    original_drug_key = data.original_drug_name.strip().lower()

    avoid_effects_set = {effect.strip().lower() for effect in data.avoid_side_effects}

    # 2. Find all drugs for the indication
    potential_drugs = alternatives_data.get(indication_key, [])
    
    if not potential_drugs:
        return {"indication": data.indication, "alternatives": []}

    # 3. Filter the list with new "fuzzy" logic
    good_alternatives = []
    for drug in potential_drugs:
        drug_name = drug['name']
        drug_name_lower = drug_name.lower()
        drug_effects_list = drug['effects'] # This is already lowercase from your notebook

        # --- NEW FILTER 1: Check if it's just the same drug ---
        # If the original drug name is *in* this drug's name, skip it.
        # e.g., if original is "augmentin", skip "augmentin 1000 duo tablet"
        if original_drug_key and original_drug_key in drug_name_lower:
            continue  # Skip this, it's not a true alternative

        # --- NEW FILTER 2: Fuzzy Side Effect Check ---
        found_bad_effect = False
        for avoid_effect in avoid_effects_set: # e.g., "pain"
            if not avoid_effect:
                continue

            # Check if our simple "bad" effect (e.g., "pain")
            # is *contained within* any of the complex effect strings
            # e.g., "pain" IN "injection site reactions (pain, swelling, redness)"
            for complex_effect in drug_effects_list:
                if avoid_effect in complex_effect:
                    found_bad_effect = True
                    break # Found a bad effect, stop checking this drug's effects
            
            if found_bad_effect:
                break # Stop checking this drug, move to the next one

        # If, after all checks, we found no bad effects, add it to the list
        if not found_bad_effect:
            good_alternatives.append(drug_name)

    # Return the list of safe alternatives (remove duplicates)
    return {
        "indication": data.indication,
        "alternatives": list(set(good_alternatives))
    }


