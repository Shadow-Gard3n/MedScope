import os
import firebase_admin
from firebase_admin import auth, credentials, firestore
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi import Request
from google.oauth2 import id_token
import firebase_admin
from firebase_admin import auth
import requests


load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate("D:\\Coding\\web with python\\FastApi\\project\\serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
FIREBASE_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"



async def get_current_user(request: Request):
    session_token = request.cookies.get("session")  # check if session exists
    if not session_token:
        return None  # redirect if not logged in
    
    try:
        decoded_token = auth.verify_id_token(session_token)
        user_id = decoded_token.get("uid")
        return user_id  # return authenticated user's ID
    except Exception:
        return None


# async def create_user(email: str, password: str, name: str):
#     try:
#         user = auth.create_user(email=email, password=password, display_name=name)

#         return {"status": "User created successfully. Please verify your email.", "user_id": user.uid}
#     except Exception as e:
#         return {"error": str(e)}

async def create_user(email: str, password: str, name: str):
    try:
        user = auth.create_user(email=email, password=password, display_name=name)

        # this is required for sending a verification email
        signin_request = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        signin_response = requests.post(FIREBASE_SIGNIN_URL, json=signin_request).json()

        id_token = signin_response.get("idToken")  # extract the id token
        if not id_token:
            return {"error": "Failed to get ID token for email verification."}

        firebase_email_api = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        email_request = {
            "requestType": "VERIFY_EMAIL",
            "idToken": id_token  
        }
        email_response = requests.post(firebase_email_api, json=email_request)

        # print("Firebase Sign-in Response:", signin_response)  
        # print("Firebase Email Response:", email_response.json())

        
        if email_response.status_code == 200:
            return {"status": "User created successfully. Verification email sent."}
        else:
            return {"error": f"Failed to send verification email: {email_response.json()}"}

    except Exception as e:
        return {"error": str(e)}

# async def login_user(email: str, password: str):
#     try:
#         payload = {
#             "email": email,
#             "password": password,
#             "returnSecureToken": True
#         }
#         response = requests.post(FIREBASE_SIGNIN_URL, json=payload)
#         if response.status_code == 200:
#             data = response.json()

#             user = auth.get_user_by_email(email)
            
#             return {
#                 "message": "Login successful",
#                 "idToken": data["idToken"],      
#                 "refreshToken": data["refreshToken"], 
#                 "userId": data["localId"]
#             }
#         else:
#             return {"error": response.json().get("error", {}).get("message", "Login failed")}
#     except Exception as e:
#         return {"error": str(e)}

async def login_user(email: str, password: str):
    try:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(FIREBASE_SIGNIN_URL, json=payload)

        if response.status_code == 200:
            data = response.json()
            user = auth.get_user_by_email(email)

            if not user.email_verified:
                return {"error": "Please verify your email before logging in."}

            return {
                "message": "Login successful",
                "idToken": data["idToken"],      
                "refreshToken": data["refreshToken"], 
                "userId": data["localId"]
            }
        else:
            return {"error": response.json().get("error", {}).get("message", "Login failed")}
    except Exception as e:
        return {"error": str(e)}

    
async def verify_google_token(token: str):
    """ Verify a Firebase authentication token. """
    try:
        decoded_token = auth.verify_id_token(token) 
        return {
            "user_id": decoded_token["uid"],  
            "email": decoded_token["email"],
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture")
        }
    except Exception as e:
        return {"error": str(e)}
    
