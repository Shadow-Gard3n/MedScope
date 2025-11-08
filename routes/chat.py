# routes/chat.py (Gemini Version)

import os
import logging
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from service.firebase_service import get_current_user
from schemas.model import ChatInput
# Import your internal tools
from routes.ml_models import internal_predict, internal_alternatives

import google.generativeai as genai

load_dotenv()
router = APIRouter()
logging.basicConfig(level=logging.INFO)

# --- Gemini Setup ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Use a fast, capable model like Gemini 1.5 Flash
model = genai.GenerativeModel('gemini-2.5-flash')

# Define tools for Gemini (It's smarter, so we can be more direct)
TOOLS_PROMPT = """
You have access to these tools. If the user's request requires one, reply ONLY with the JSON for that tool call.
1. `predict_side_effects(drug_name: str)`: For questions about side effects, risks, or safety of a specific drug.
   Output JSON: {"tool": "predict_side_effects", "arg": "drug_name"}
2. `find_alternatives(query: str)`: For questions about alternative medicines for a drug or condition.
   Output JSON: {"tool": "find_alternatives", "arg": "query"}

Example: User: "Alternatives to Advil" -> You reply: {"tool": "find_alternatives", "arg": "Advil"}
If no tool is needed, just answer normally as a helpful medical assistant. Keep it concise.
"""

@router.post("/chat")
async def chat_with_bot(data: ChatInput, current_user: str = Depends(get_current_user)):
    user_msg = data.message.strip()
    
    # Combine system prompt with user message
    full_prompt = f"System: You are MediAware Bot, a helpful medical assistant. Always advise consulting a doctor. {TOOLS_PROMPT}\nUser: {user_msg}"

    try:
        # Call Gemini API
        response = model.generate_content(full_prompt)
        bot_text = response.text.strip()
        
        # --- SAME JSON PARSING LOGIC AS BEFORE ---
        try:
            # Try to find JSON in the response
            if "{" in bot_text and "}" in bot_text:
                json_str = bot_text[bot_text.find("{"):bot_text.rfind("}")+1]
                tool_call = json.loads(json_str)
                
                if tool_call.get("tool") == "predict_side_effects":
                    drug_name = tool_call.get("arg")
                    logging.info(f"Gemini requested predict for: {drug_name}")
                    return {"response": internal_predict(drug_name)}
                
                elif tool_call.get("tool") == "find_alternatives":
                    query = tool_call.get("arg")
                    logging.info(f"Gemini requested alternatives for: {query}")
                    return {"response": internal_alternatives(query)}

        except json.JSONDecodeError:
            pass # Not JSON, just normal text

        return {"response": bot_text}

    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        # More detailed error logging for debugging
        import traceback
        traceback.print_exc()
        return {"response": "I'm having trouble thinking right now. Please try again later."}