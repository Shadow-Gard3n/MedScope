# import os
# import logging
# from fastapi import APIRouter, HTTPException, Request
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse
# from pydantic import BaseModel
# from dotenv import load_dotenv

# from service.llm import llm1, llm2 

# # --- CONFIGURATION ---
# logging.basicConfig(level=logging.INFO)

# # Load .env file from the root directory
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     logging.error("OPENAI_API_KEY not found in .env file")
    
# router = APIRouter()

# # We define our own templates object, pointing to the project's 'templates' dir
# templates = Jinja2Templates(directory="templates")

# # --- PYDANTIC MODELS ---
# class ConversationHistory(BaseModel):
#     history: str

# class AnalysisResult(BaseModel):
#     diagnosis: str
#     questions: str

# # --- ROUTES ---

# @router.get("/assistant/{uid}", response_class=HTMLResponse)
# async def get_assistant_page(request: Request, uid: str):
#     """
#     Serves the assistant.html page for the user.
#     This route matches the link in your HTML nav bar.
#     """
#     # Mock user object to satisfy the {{ user.uid }} in the template
#     user_context = {"uid": uid}
#     return templates.TemplateResponse(
#         "assistant.html", 
#         {"request": request, "user": user_context}
#     )

# @router.post("/get-analysis", response_model=AnalysisResult)
# async def get_analysis(body: ConversationHistory):
#     """
#     API Endpoint: Receives the full transcript from the browser,
#     processes it with llm1 and llm2, and returns the analysis.
#     """
#     if not OPENAI_API_KEY:
#         raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set on the server")

#     try:
#         logging.info("Processing /get-analysis request...")
        
#         # Call your LLM functions from hacurate/llm.py
#         diagnosis_result = llm2(OPENAI_API_KEY, body.history)
#         questions_result = llm1(OPENAI_API_KEY, body.history)
        
#         return AnalysisResult(
#             diagnosis=diagnosis_result,
#             questions=questions_result
#         )
#     except Exception as e:
#         logging.error(f"Error during LLM analysis: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


import os
import logging
import asyncio # Import asyncio for parallel execution
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Import your LLM functions. 
# Ensure your service/llm.py uses 'await' and '.ainvoke' as discussed previously!
from service.llm import llm1, llm2 

logging.basicConfig(level=logging.INFO)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/assistant/{uid}", response_class=HTMLResponse)
async def get_assistant_page(request: Request, uid: str):
    user_context = {"uid": uid}
    return templates.TemplateResponse("assistant.html", {"request": request, "user": user_context})

# --- THE NEW WEBSOCKET ENDPOINT ---
@router.websocket("/ws/analysis/{uid}")
async def websocket_endpoint(websocket: WebSocket, uid: str):
    """
    Real-time, bi-directional connection.
    Replaces the slow HTTP POST requests.
    """
    await websocket.accept()
    logging.info(f"WebSocket connected for user {uid}")

    try:
        while True:
            # 1. Wait for text from the frontend
            data = await websocket.receive_json()
            history = data.get("history")

            if history:
                # 2. Run LLMs in PARALLEL (Like your threads)
                # This runs both functions at the exact same time
                task_diagnosis = asyncio.create_task(llm2(OPENAI_API_KEY, history))
                task_questions = asyncio.create_task(llm1(OPENAI_API_KEY, history))

                # 3. Wait for both to finish (should take only as long as the slowest one)
                diagnosis_result, questions_result = await asyncio.gather(task_diagnosis, task_questions)

                # 4. Send back immediately
                await websocket.send_json({
                    "diagnosis": diagnosis_result,
                    "questions": questions_result
                })

    except WebSocketDisconnect:
        logging.info(f"User {uid} disconnected")
    except Exception as e:
        logging.error(f"WebSocket Error: {e}")
        try:
            await websocket.close()
        except:
            pass