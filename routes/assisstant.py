import os
import logging
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from service.firebase_service import get_current_user
import google.generativeai as genai
import asyncio
from fastapi.responses import StreamingResponse

router = APIRouter()

load_dotenv()
router = APIRouter()
logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')

class ConversationHistory(BaseModel):
    history: str

class AnalysisResult(BaseModel):
    diagnosis: str
    questions: str


async def gemini_llm_stream(history: str):
    """
    Calls Gemini API to get a streaming conversational reply.
    """
    prompt = f"""
    You are an empathetic medical assistant AI. Your role is to have a natural,
    conversational dialogue with a patient to understand their symptoms.
    
    Based on the following conversation history, provide a *conversational reply only*.
    - DO NOT provide a diagnosis.
    - DO NOT list questions.
    - Just continue the conversation naturally.

    History:
    {history}
    
    Assistant: 
    """
    
    try:
        response = await model.generate_content_async(
            prompt,
            stream=True,
            # safety_settings=safety_settings
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        logging.error(f"Error during Gemini stream: {e}")
        yield "I'm sorry, I encountered an error and can't respond right now."

async def gemini_llm_analysis(history: str) -> AnalysisResult:
    """
    Calls Gemini API to get a structured JSON analysis.
    """
    # Get the JSON schema from our Pydantic model
    json_schema = AnalysisResult.model_json_schema()
    
    prompt = f"""
    You are a medical analysis engine. Analyze the following consultation history
    and provide:
    1. A list of potential diagnoses (as a string).
    2. A list of suggested follow-up questions (as a string, separated by newlines).

    Respond with *only* a valid JSON object that adheres to the following schema.
    Do not include markdown (```json ... ```) or any other text.
    
    Schema:
    {json_schema}
    
    Consultation History:
    {history}
    """
    
    # Configure the model to output JSON
    json_config = genai.types.GenerationConfig(response_mime_type="application/json")
    
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=json_config,
            # safety_settings=safety_settings
        )
        
        # Check for prompt feedback or other issues
        if not response.parts:
            logging.error(f"Gemini analysis returned no parts. Feedback: {response.prompt_feedback}")
            raise HTTPException(status_code=500, detail="Analysis returned no content.")
            
        # Parse the JSON response
        data = json.loads(response.text)
        return AnalysisResult(**data)
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from Gemini: {e}")
        logging.error(f"Raw Gemini response: {response.text}")
        return AnalysisResult(
            diagnosis="Error: Could not parse analysis.",
            questions="Error: Invalid analysis format received."
        )
    except Exception as e:
        logging.error(f"Error in Gemini analysis call: {e}")
        if 'response' in locals() and response.prompt_feedback:
             logging.error(f"Prompt Feedback: {response.prompt_feedback}")
        return AnalysisResult(
            diagnosis="Error: Analysis failed.",
            questions="Error: Could not connect to analysis engine."
        )

# --- API Endpoints ---

@router.post("/stream-reply")
async def stream_reply(body: ConversationHistory, user: dict = Depends(get_current_user)):
    """
    Endpoint 1: Streams back ONLY the conversational reply.
    """
    return StreamingResponse(
        gemini_llm_stream(body.history),
        media_type="text/plain"
    )

@router.post("/get-analysis", response_model=AnalysisResult)
async def get_analysis(body: ConversationHistory, user: dict = Depends(get_current_user)):
    """
    Endpoint 2: Returns ONLY the final structured JSON analysis.
    """
    return await gemini_llm_analysis(body.history)