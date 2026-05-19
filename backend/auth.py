import os
import json
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Header, HTTPException

_initialized = False


def _init_firebase():
    global _initialized
    if _initialized or firebase_admin._apps:
        _initialized = True
        return
    sa = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not sa:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env var not set")
    cred = credentials.Certificate(json.loads(sa))
    firebase_admin.initialize_app(cred)
    _initialized = True


async def verify_token(authorization: str = Header(...)):
    _init_firebase()
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[7:]
    try:
        return firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
