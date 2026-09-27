from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth_db import *

router = APIRouter()
init_db()

class RegisterRequest(BaseModel): name: str; email: str; password: str
class LoginRequest(BaseModel): email: str; password: str
class HistoryRequest(BaseModel): source: str = "TEXT"; message: str; type: str | None = None; value: str | None = None
class FavoriteRequest(BaseModel): message: str = ""
class EmergencyContactRequest(BaseModel): name: str = "Emergency"; phone: str = ""; contact: str = ""

def get_current_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    user=get_user_by_session(authorization.replace("Bearer ","",1).strip())
    if not user: raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user

@router.post("/api/auth/register")
def register(data:RegisterRequest):
    name=data.name.strip(); email=data.email.lower().strip(); password=data.password
    if len(name)<2: raise HTTPException(400,"Name is too short")
    if "@" not in email: raise HTTPException(400,"Invalid email")
    if len(password)<4: raise HTTPException(400,"Password must contain at least 4 characters")
    user=create_user(name,email,password)
    if not user: raise HTTPException(409,"Email already registered")
    return {"success":True,"message":"Registration successful","token":create_session(user["id"]),"user":user}

@router.post("/api/auth/login")
def login(data:LoginRequest):
    user=verify_user(data.email,data.password)
    if not user: raise HTTPException(401,"Invalid email or password")
    return {"success":True,"message":"Login successful","token":create_session(user["id"]),"user":{"id":user["id"],"name":user["name"],"email":user["email"]}}

@router.get("/api/auth/me")
def me(authorization:Optional[str]=Header(None)):
    u=get_current_user(authorization); return {"success":True,"user":{"id":u["id"],"name":u["name"],"email":u["email"]}}

@router.post("/api/auth/logout")
def logout(authorization:Optional[str]=Header(None)):
    if authorization and authorization.startswith("Bearer "): delete_session(authorization.replace("Bearer ","",1).strip())
    return {"success":True}

@router.get("/api/user/history")
def user_history(authorization:Optional[str]=Header(None)):
    h=get_history(get_current_user(authorization)["id"]); return {"success":True,"history":h,"items":h}

@router.post("/api/user/history")
def save_history(data:HistoryRequest,authorization:Optional[str]=Header(None)):
    u=get_current_user(authorization); add_history(u["id"], data.source or data.type or "TEXT", data.message or data.value or ""); return {"success":True}

@router.delete("/api/user/history")
def remove_history(authorization:Optional[str]=Header(None)):
    clear_history(get_current_user(authorization)["id"]); return {"success":True}

@router.get("/api/user/favorites")
def user_favorites(authorization:Optional[str]=Header(None)):
    rows=get_favorites(get_current_user(authorization)["id"]); values=[r["message"] for r in rows]; return {"success":True,"favorites":values,"items":values,"details":rows}

@router.post("/api/user/favorites")
def save_favorite(data:FavoriteRequest,authorization:Optional[str]=Header(None)):
    message=data.message.strip();
    if not message: raise HTTPException(400,"Favorite message is empty")
    add_favorite(get_current_user(authorization)["id"],message); return {"success":True}

@router.delete("/api/user/favorites/{message}")
def remove_favorite(message:str,authorization:Optional[str]=Header(None)):
    delete_favorite(get_current_user(authorization)["id"],message); return {"success":True}

@router.get("/api/user/emergency-contacts")
def user_emergency_contacts(authorization:Optional[str]=Header(None)):
    c=get_emergency_contacts(get_current_user(authorization)["id"]); return {"success":True,"contacts":c,"items":c}

@router.post("/api/user/emergency-contacts")
def save_emergency_contact(data:EmergencyContactRequest,authorization:Optional[str]=Header(None)):
    u=get_current_user(authorization); name=(data.name or "Emergency").strip(); phone=(data.phone or data.contact).strip()
    if not name or not phone: raise HTTPException(400,"Contact name and phone are required")
    add_emergency_contact(u["id"],name,phone); return {"success":True}

@router.delete("/api/user/emergency-contacts/{phone}")
def remove_emergency_contact(phone:str,authorization:Optional[str]=Header(None)):
    delete_emergency_contact(get_current_user(authorization)["id"],phone); return {"success":True}
