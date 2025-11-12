import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from schemas.model import PredictionInput, AvoidAlternativesInput, SearchAlternativesInput
import json
from service.firebase_service import db, get_current_user
from firebase_admin import firestore
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

ALTERNATIVES_FILE_PATH = "models/alternative_medicine.json"
drug_lookup = {}
alternatives_data = {}

try:
    with open(ALTERNATIVES_FILE_PATH, 'r') as f:
        alternatives_data = json.load(f)
    logging.info(f"--- Alternatives data loaded from {ALTERNATIVES_FILE_PATH} ---")
    
    # (Drug -> Indication/Effects)
    logging.info("--- Building in-memory drug lookup table... ---")
    for indication, drugs in alternatives_data.items():
        for drug in drugs:
            drug_name_key = drug['name'].strip().lower()
            if drug_name_key not in drug_lookup:
                drug_lookup[drug_name_key] = {
                    "name": drug['name'],
                    "effects": drug['effects'],
                    "indications": set()
                }
            drug_lookup[drug_name_key]["indications"].add(indication)
    
    # Convert sets to lists for JSON serialization
    for drug_key in drug_lookup:
        drug_lookup[drug_key]["indications"] = list(drug_lookup[drug_key]["indications"])
    logging.info(f"--- Built lookup for {len(drug_lookup)} drugs. ---")

except FileNotFoundError:
    logging.error(f"--- ERROR: {ALTERNATIVES_FILE_PATH} not found. ---")


# --- API Endpoints ---

@router.post("/predict")
async def predict_all(data: PredictionInput, current_user: str = Depends(get_current_user)):
    if not all([risk_model, reactions_model, risk_binarizer, reactions_binarizer]):
         raise HTTPException(status_code=500, detail="Models are not loaded.")
    
    try:
        sample_df = pd.DataFrame([data.dict()])
        risk_pred_encoded = risk_model.predict(sample_df)
        risk_labels = risk_binarizer.inverse_transform(risk_pred_encoded)
        reaction_pred_encoded = reactions_model.predict(sample_df)
        reaction_labels = reactions_binarizer.inverse_transform(reaction_pred_encoded)
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Error making prediction.")

    if current_user:
        try:
            search_term = data.drug_profile_joined.split('_ROLE_')[0]
            if search_term and search_term != "UNKNOWN":
                db.collection("users").document(current_user).collection("search_history").add({
                    "search_term": search_term,
                    "timestamp": firestore.SERVER_TIMESTAMP  
                })
        except Exception as e:
            logging.warning(f"Failed to save history: {e}")

    return {
        "risk_profile": risk_labels[0],
        "side_effects": reaction_labels[0]
    }

@router.post("/alternatives/avoid")
async def get_alternatives_avoid(data: AvoidAlternativesInput, current_user: str = Depends(get_current_user)):
    if not alternatives_data:
         raise HTTPException(status_code=500, detail="Data not loaded.")

    indication_key = data.indication.strip().lower()
    original_drug_key = data.original_drug_name.strip().lower()
    avoid_effects_set = {e.strip().lower() for e in data.avoid_side_effects}

    potential_drugs = alternatives_data.get(indication_key, [])
    good_alternatives = []
    for drug in potential_drugs:
        if original_drug_key and original_drug_key in drug['name'].lower():
            continue
        
        found_bad = False
        for avoid in avoid_effects_set:
            if not avoid: continue
            for effect in drug['effects']:
                 if avoid in effect:
                     found_bad = True
                     break
            if found_bad: break
        
        if not found_bad:
            good_alternatives.append(drug['name'])

    return {
        "indication": data.indication,
        "alternatives": list(set(good_alternatives))
    }

@router.post("/alternatives/search")
async def get_alternatives_search(data: SearchAlternativesInput, current_user: str = Depends(get_current_user)):
    if not alternatives_data:
         raise HTTPException(status_code=500, detail="Data not loaded.")

    results = {
        "search_type": "",
        "query": "",
        "primary_drug": None,
        "alternatives": []
    }

    if data.drug_name:
        results["search_type"] = "drug"
        results["query"] = data.drug_name
        drug_key = data.drug_name.strip().lower()
        
        drug_info = drug_lookup.get(drug_key)
        if drug_info:
            results["primary_drug"] = drug_info
            if drug_info["indications"]:
                primary_indication = drug_info["indications"][0]
                all_alts = alternatives_data.get(primary_indication, [])
                results["alternatives"] = [d for d in all_alts if d['name'].lower() != drug_key]
                results["primary_drug"]["primary_indication"] = primary_indication

    elif data.indication:
        results["search_type"] = "indication"
        results["query"] = data.indication
        ind_key = data.indication.strip().lower()
        results["alternatives"] = alternatives_data.get(ind_key, [])

    return results






# --- INTERNAL HELPER FUNCTIONS FOR CHATBOT ---
# def internal_predict(drug_name: str) -> str:
#     """
#     Predicts risks and side effects for a given drug name using default patient values.
#     """
#     # Clean up the input name
#     drug_clean = drug_name.strip().upper()
    
#     # Create a dummy input with 'average' defaults
#     dummy_input = {
#         "age_grp": "Adult",
#         "sex": "UNK",
#         "reporter_country": "US",
#         "occr_country": "US",
#         "is_hcp": False,
#         "drug_profile_joined": f"{drug_clean}_ROLE_PS_ROUTE_Oral_IND_Unknown_DECHAL_Unknown"
#     }

#     try:
#         sample_df = pd.DataFrame([dummy_input])
        
#         # Run predictions
#         risk_pred = risk_model.predict(sample_df)
#         risk_labels = risk_binarizer.inverse_transform(risk_pred)[0]
        
#         reaction_pred = reactions_model.predict(sample_df)
#         reaction_labels = reactions_binarizer.inverse_transform(reaction_pred)[0]

#         # Format the output for the chat
#         risk_str = ", ".join(risk_labels) if risk_labels else "None predicted"
#         effects_str = ", ".join(reaction_labels) if reaction_labels else "None common predicted"
        
#         return f"For {drug_clean} (assuming typical adult use): Predicted Risks: {risk_str}. Potential Side Effects: {effects_str}."

#     except Exception as e:
#         logging.error(f"Internal predict error for {drug_name}: {e}")
#         return f"Sorry, I couldn't run the prediction model for '{drug_name}'. Please try the full form on the home page."



# In routes/ml_models.py

def internal_predict(drug_name: str, age_grp: str = "Adult", sex: str = "UNK", country: str = "COUNTRY NOT SPECIFIED", route: str = "Unknown", indication: str = "Unknown") -> str:
    """
    Predicts risks and side effects using ML, AND looks up reported effects from the database.
    """
    drug_clean = drug_name.strip().upper()
    drug_key = drug_name.strip().lower()
    
    # --- 1. ML PREDICTION ---
    sex_clean = sex.upper() if sex.upper() in ['M', 'F'] else 'UNK'
    age_clean = age_grp.capitalize() if age_grp.capitalize() in ['Neonate', 'Infant', 'Child', 'Adolescent', 'Adult', 'Elderly'] else 'Adult'
    route_clean = route.strip() if route else "Unknown"
    ind_clean = indication.strip() if indication else "Unknown"

    input_data = {
        "age_grp": age_clean,
        "sex": sex_clean,
        "reporter_country": country.upper(),
        "occr_country": country.upper(),
        "is_hcp": False,
        "drug_profile_joined": f"{drug_clean}_ROLE_PS_ROUTE_{route_clean}_IND_{ind_clean}_DECHAL_Unknown"
    }
    
    ml_output = ""
    try:
        sample_df = pd.DataFrame([input_data])
        risk_pred = risk_model.predict(sample_df)
        
        risk_labels = risk_binarizer.inverse_transform(risk_pred)[0]
        
        reaction_pred = reactions_model.predict(sample_df)
        reaction_labels = reactions_binarizer.inverse_transform(reaction_pred)[0]

        risk_str = ", ".join(risk_labels) if len(risk_labels) > 0 else "None specifically predicted"
        effects_str = ", ".join(reaction_labels) if len(reaction_labels) > 0 else "None specifically predicted"
        
        ml_output = (f"<li><b>AI Predicted Risks (for this profile):</b> {risk_str}</li>"
                     f"<li><b>AI Predicted Side Effects (for this profile):</b> {effects_str}</li>")

    except Exception as e:
        logging.error(f"Internal predict ML error for {drug_name}: {e}")
        ml_output = "<li><b>AI Prediction:</b> Could not run for this specific profile.</li>"

    # --- 2. DATABASE LOOKUP ---
    db_output = ""
    drug_info = drug_lookup.get(drug_key)
    if drug_info and drug_info.get('effects'):
        db_effects = drug_info['effects'][:10]
        db_effects_str = ", ".join(db_effects)
        remaining = len(drug_info['effects']) - 10
        if remaining > 0:
            db_effects_str += f", and {remaining} more..."
            
        db_output = f"<li><b>General Reported Side Effects (from Database):</b> {db_effects_str}</li>"
    else:
        db_output = f"<li><b>Database:</b> No general side effects found for '{drug_clean}'.</li>"

    # --- 3. COMBINE OUTPUTS ---
    return (f"For <b>{drug_clean}</b> (Profile: {age_clean}, {sex_clean}, {country.upper()}):\n"
            f"<ul>"
            f"{ml_output}"
            f"{db_output}"
            f"</ul>")


def internal_alternatives(query: str) -> str:
    """
    Finds alternatives for a drug or indication.
    """
    query_lower = query.strip().lower()
    
    # 1. Try as a DRUG name first
    drug_info = drug_lookup.get(query_lower)
    if drug_info:
        # It's a drug! Find its primary indication.
        if drug_info["indications"]:
            indication = drug_info["indications"][0]
            # Find other drugs for this indication
            alts = alternatives_data.get(indication, [])
            # Filter out the original drug and take top 3
            alt_names = [d['name'] for d in alts if d['name'].lower() != query_lower][:3]
            
            if alt_names:
                return f"'{query}' is often used for {indication}. Some possible alternatives are: {', '.join(alt_names)}."
            return f"'{query}' is used for {indication}, but I don't have other alternatives listed for that."
        return f"I found '{query}' in my database, but I don't have a clear indication listed to find alternatives."

    alts = alternatives_data.get(query_lower)
    if alts:
        alt_names = [d['name'] for d in alts][:3]
        return f"Common medicines for '{query}': {', '.join(alt_names)}."

    return f"I couldn't find any information for '{query}' as either a drug or a medical condition."