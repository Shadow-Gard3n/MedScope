from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from service.firebase_service import create_user, login_user
from fastapi.responses import RedirectResponse
from firebase_admin import auth
from fastapi import APIRouter, HTTPException
from firebase_admin import firestore
from service.firebase_service import verify_google_token
from fastapi.responses import JSONResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = firestore.client()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    error = request.query_params.get("error", "")
    status = request.query_params.get("status", "")

    return templates.TemplateResponse("login.html", {"request": request, "error": error, "status": status})

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    error = request.query_params.get("error", "")
    return templates.TemplateResponse("signup.html", {"request": request, "error": error})

@router.post("/signup/save")
async def signup(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    result = create_user(email, password, name)
    
    if "error" in result:
        error_message = result["error"]
        if "INVALID_EMAIL" in error_message:
            error_message = "Invalid email address. Please try with valid email."
        elif "Invalid password string" in error_message:
            error_message = "Invalid password. Password must be a string at least 6 characters long."
        elif "EMAIL_EXISTS" in error_message:
            error_message = "The email is already registered. Try logging in."
        else:
            error_message = result["error"]
    
        return RedirectResponse(url=f"/signup?error={error_message}", status_code=303)
    return RedirectResponse(url="/login?status=Your account has been created successfully. Please verify your email to get started", status_code=303)

@router.post("/login/save")
async def login(email: str = Form(...), password: str = Form(...)):
    result = await login_user(email, password)
    
    if "error" in result:
        error_message = result["error"]
        if "INVALID_LOGIN_CREDENTIALS" in error_message:
            error_message = "Invalid email or password. Please try again."
        else:
            error_message = result["error"]
            
        return RedirectResponse(url=f"/login?error={error_message}", status_code=303)

    user_id = result.get("userId")
    session_token = result.get("idToken", "") 

    if not session_token:
        return RedirectResponse(url="/login?error=InvalidSession", status_code=303)  # handle missing session token

    response = RedirectResponse(url=f"/home/{user_id}", status_code=303)
    response.set_cookie(key="session", value=session_token, httponly=True, max_age=604800)  # store session securely
    return response

@router.post("/login/google")
async def google_login(id_token: str = Form(...)):
    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name", "")

        if not name:
            user_record = auth.get_user(user_id)
            name = user_record.display_name if user_record.display_name else "Unknown User"

        # Check if user exists in Firestore, if not, create a new entry
        user_ref = db.collection("users").document(user_id)
        user_data = user_ref.get()

        if not user_data.exists:
            user_ref.set({
                "user_id": user_id,
                "email": email,
                "name": name
            })

        response = JSONResponse(content={"user_id": user_id})
        response.set_cookie(key="session", value=id_token, httponly=True, max_age=604800, secure=True)
        return response

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("session")  # Remove session cookie
    return response
