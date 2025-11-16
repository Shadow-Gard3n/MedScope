# import os
# import logging
# import json
# from fastapi import APIRouter, HTTPException, Depends
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from service.firebase_service import get_current_user
# from schemas.model import ChatInput
# # Import your internal tools
# from routes.ml_models import internal_predict, internal_alternatives

# import google.generativeai as genai

# load_dotenv()
# router = APIRouter()
# logging.basicConfig(level=logging.INFO)

# # --- Gemini Setup ---
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     logging.error("GEMINI_API_KEY not found in .env file")

# genai.configure(api_key=GEMINI_API_KEY)

# # Use a fast, capable model like Gemini 1.5 Flash
# model = genai.GenerativeModel('gemini-2.5-flash')

# # Define tools for Gemini (It's smarter, so we can be more direct)
# TOOLS_PROMPT = """
# You have access to these tools. If the user's request requires one, reply ONLY with the JSON for that tool call.
# 1. `predict_side_effects(drug_name: str)`: For questions about side effects, risks, or safety of a specific drug.
#    Output JSON: {"tool": "predict_side_effects", "arg": "drug_name"}
# 2. `find_alternatives(query: str)`: For questions about alternative medicines for a drug or condition.
#    Output JSON: {"tool": "find_alternatives", "arg": "query"}

# Example: User: "Alternatives to Advil" -> You reply: {"tool": "find_alternatives", "arg": "Advil"}
# If no tool is needed, just answer normally as a helpful medical assistant. Keep it concise.
# """

# @router.post("/chat")
# async def chat_with_bot(data: ChatInput, current_user: str = Depends(get_current_user)):
#     user_msg = data.message.strip()
    
#     # Combine system prompt with user message
#     full_prompt = f"System: You are MediAware Bot, a helpful medical assistant. Always advise consulting a doctor. {TOOLS_PROMPT}\nUser: {user_msg}"

#     try:
#         # Call Gemini API
#         response = model.generate_content(full_prompt)
#         bot_text = response.text.strip()
        
#         # --- SAME JSON PARSING LOGIC AS BEFORE ---
#         try:
#             # Try to find JSON in the response
#             if "{" in bot_text and "}" in bot_text:
#                 json_str = bot_text[bot_text.find("{"):bot_text.rfind("}")+1]
#                 tool_call = json.loads(json_str)
                
#                 if tool_call.get("tool") == "predict_side_effects":
#                     drug_name = tool_call.get("arg")
#                     logging.info(f"Gemini requested predict for: {drug_name}")
#                     return {"response": internal_predict(drug_name)}
                
#                 elif tool_call.get("tool") == "find_alternatives":
#                     query = tool_call.get("arg")
#                     logging.info(f"Gemini requested alternatives for: {query}")
#                     return {"response": internal_alternatives(query)}

#         except json.JSONDecodeError:
#             pass # Not JSON, just normal text

#         return {"response": bot_text}

#     except Exception as e:
#         logging.error(f"Gemini API error: {e}")
#         # More detailed error logging for debugging
#         import traceback
#         traceback.print_exc()
#         return {"response": "I'm having trouble thinking right now. Please try again later."}


# routes/chat.py

import os
import logging
import json
import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from service.firebase_service import get_current_user
from routes.ml_models import internal_predict, internal_alternatives
import google.generativeai as genai
from schemas.model import ChatInput

load_dotenv()
router = APIRouter()
logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=GEMINI_API_KEY)
# Use the model that worked for you in testing
model = genai.GenerativeModel('gemini-2.5-flash') 

TOOLS_PROMPT = """
You are MediAware Bot, a medical assistant.

TOOLS:
1. predict_side_effects(drug_name: str) — for questions about side effects, risks, or safety of a specific drug.
2. find_alternatives(query: str) — for questions asking for alternative medicines or medicines for a condition.

RULES:
- If the user asks about a condition, symptom, or what medicine to take, ALWAYS call {"tool": "find_alternatives", "arg": "<condition>"}.
- If the user asks about side effects, safety, or risks of a drug, ALWAYS call {"tool": "predict_side_effects", "arg": "<drug_name>"}.
- If the user asks questions not related to the tools {"response":"<your_answer_here>"}
- DO NOT answer directly in text when a tool is needed.
- When no tool is needed (e.g. greetings or general advice), reply normally.
- The entire response must be ONLY the JSON object, nothing else.
"""



@router.post("/chat")
async def chat_with_bot(data: ChatInput, current_user: str = Depends(get_current_user)):
    user_msg = data.message.strip()
    
    try:
        # Step 1: Ask Gemini if it needs a tool
        response1 = model.generate_content(f"System: {TOOLS_PROMPT}\nUser: {user_msg}")
        text1 = response1.text.strip()
        logging.info(f"Gemini Raw Response 1: {text1}")

        # Step 2: Try to parse as JSON
        tool_data = None
        try:
            start_idx = text1.find("{")
            end_idx = text1.rfind("}")
            if start_idx != -1 and end_idx != -1:
                 json_str = text1[start_idx : end_idx + 1]
                 tool_data = json.loads(json_str)
        except json.JSONDecodeError:
            pass 

        # Step 3: If tool WAS called, run it and get Gemini to rewrite the result
        if tool_data and "tool" in tool_data and "arg" in tool_data:
            tool_name = tool_data["tool"]
            arg = tool_data["arg"]
            raw_data = ""
            
            if tool_name == "predict_side_effects":
                drug_name = arg
                if not drug_name:
                    raw_data = "Error: You asked for side effects but didn't specify a drug."
                else:
                    logging.info(f"Running tool: predict for {arg}")
                    raw_data = internal_predict(arg)
            elif tool_name == "find_alternatives" or tool_name == "alternatives":
                logging.info(f"Running tool: alternatives for {arg}")
                raw_data = internal_alternatives(arg)
            
            # --- IMPROVED REWRITE PROMPT ---
            final_prompt = (
                f"System: You are MediAware Bot. The user asked: '{user_msg}'.\n"
                f"You retrieved this raw data from the database: '{raw_data}'.\n\n"
                "Task: Write a helpful, natural-sounding response to the user based ONLY on this data.\n"
                "Guidelines:\n"
                "- Use a conversational tone (e.g., 'According to our database...', 'Some options might be...').\n"
                "- Use HTML formatting (<b>bold</b> for drug names, <ul><li> for lists) to make it easy to read.\n"
            )
            
            response2 = model.generate_content(final_prompt)
            print(response2.text)
            return {"response": response2.text.strip()}

        print(text1)
        normal_data = json.loads(text1)
        return {"response": normal_data['response']}

    except Exception as e:
        traceback.print_exc()
        logging.error(f"Chat error: {e}")
        return {"response": "I'm having a little trouble right now. Please try again."}



