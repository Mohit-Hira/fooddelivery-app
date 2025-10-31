from fastapi import Depends, HTTPException, status, Request
import firebase_admin
from firebase_admin import auth, credentials
import os

FIREBASE_CRED = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not firebase_admin._apps:
    cred = credentials.Certificate("./firebase_crede.json")
    firebase_admin.initialize_app(cred)


def verify_firebase_token(request: Request):
    # Read token from cookie
    id_token = request.cookies.get("token")
    if not id_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")

    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token verification failed: {e}")


def get_current_user_optional(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    try:
        return verify_firebase_token(request)
    except:
        return None
