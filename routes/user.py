from fastapi import APIRouter, Request, Form, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from service.firebase_service import create_user, login_user, get_current_user
from fastapi.responses import RedirectResponse
from firebase_admin import auth
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
        user = auth.get_user(current_user)  # Fetch user using session's user ID
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

# @router.get("/profile/{user_id}", response_class=HTMLResponse)
# async def get_user_profile(request: Request, user_id: str, current_user: str = Depends(get_current_user)):
#     if current_user is None or current_user != user_id:
#         raise HTTPException(status_code=401, detail="Not authenticated")

#     try:
#         user = auth.get_user(current_user)
        
#         user_data = {
#             "uid": user.uid,
#             "display_name": user.display_name,
#             "email": user.email,
#             "photo_url": user.photo_url,
#             "creation_timestamp": user.user_metadata.creation_timestamp if user.user_metadata else None
#         }
        
#         return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

    
@router.get("/profile/{user_id}", response_class=HTMLResponse)
async def get_user_profile(request: Request, user_id: str, current_user: str = Depends(get_current_user)):
    if current_user is None or current_user != user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user = auth.get_user(current_user)
        
        creation_timestamp = None
        if user.user_metadata and user.user_metadata.creation_timestamp:
            # Convert timestamp (in milliseconds) to datetime object
            creation_timestamp = datetime.fromtimestamp(user.user_metadata.creation_timestamp / 1000)
        user_data = {
            "uid": user.uid,
            "display_name": user.display_name,
            "email": user.email,
            "photo_url": user.photo_url,
            "creation_timestamp": creation_timestamp
        }
        
        return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



