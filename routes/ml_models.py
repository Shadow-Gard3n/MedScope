import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from schemas.model import PredictionInput
from service.firebase_service import db, get_current_user
from firebase_admin import firestore
import logging

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