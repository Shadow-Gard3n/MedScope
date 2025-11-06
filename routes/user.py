from fastapi import APIRouter, Request, Form, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from service.firebase_service import create_user, login_user, get_current_user
from fastapi.responses import RedirectResponse
from firebase_admin import auth, firestore
from fastapi import APIRouter, HTTPException
from service.firebase_service import db
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/user/me")
async def get_user(request: Request, current_user: str = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user = auth.get_user(current_user) 
        return {"display_name": user.display_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/home/{user_id}", response_class=HTMLResponse)
async def get_user_home(request: Request, user_id: str, current_user: str = Depends(get_current_user)):
    if current_user is None or current_user != user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user = auth.get_user(current_user)
        return templates.TemplateResponse("home.html", {"request": request, "user": user})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.get("/profile/{user_id}", response_class=HTMLResponse)
async def get_user_profile(request: Request, user_id: str, current_user: str = Depends(get_current_user)):
    if current_user is None or current_user != user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user = auth.get_user(current_user)
        
        creation_timestamp = None
        if user.user_metadata and user.user_metadata.creation_timestamp:
            creation_timestamp = datetime.fromtimestamp(user.user_metadata.creation_timestamp / 1000)
        
        user_data = {
            "uid": user.uid,
            "display_name": user.display_name,
            "email": user.email,
            "photo_url": user.photo_url,
            "creation_timestamp": creation_timestamp
        }
        
        history_ref = db.collection("users").document(current_user).collection("search_history")
        
        history_query = history_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20)
        history_docs = history_query.stream()
        
        search_history = []
        unique_searches = set()
        
        for doc in history_docs:
            term = doc.to_dict().get("search_term")
            if term and term not in unique_searches:
                search_history.append(term)
                unique_searches.add(term)
                if len(search_history) >= 10:
                    break
                    
        user_data["search_history"] = search_history
        
        return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))