from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth_db import (
    init_db,
    create_user,
    verify_user,
    create_session,
    get_user_by_session,
    delete_session,
    add_history,
    get_history,
    clear_history,
    add_favorite,
    get_favorites,
    delete_favorite,
    add_emergency_contact,
    get_emergency_contacts,
    delete_emergency_contact,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# MODELS
# ============================================================

class RegisterRequest(BaseModel):

    name: str
    email: str
    password: str


class LoginRequest(BaseModel):

    email: str
    password: str


class HistoryRequest(BaseModel):

    source: str
    message: str


class FavoriteRequest(BaseModel):

    message: str


class EmergencyContactRequest(BaseModel):

    name: str
    phone: str


# ============================================================
# AUTH HELPER
# ============================================================

def get_current_user(
    authorization: Optional[str]
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    token = authorization.replace(
        "Bearer ",
        "",
        1
    ).strip()

    user = get_user_by_session(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    return user


# ============================================================
# REGISTER
# ============================================================

@router.post("/api/auth/register")
def register(data: RegisterRequest):

    name = data.name.strip()
    email = data.email.lower().strip()
    password = data.password

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Name is too short"
        )

    if "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email"
        )

    if len(password) < 4:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 4 characters"
        )

    user = create_user(
        name,
        email,
        password
    )

    if not user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    token = create_session(user["id"])

    return {
        "success": True,
        "message": "Registration successful",
        "token": token,
        "user": user
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/api/auth/login")
def login(data: LoginRequest):

    user = verify_user(
        data.email,
        data.password
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_session(user["id"])

    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get("/api/auth/me")
def me(
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post("/api/auth/logout")
def logout(
    authorization: Optional[str] = Header(None)
):

    if authorization and authorization.startswith("Bearer "):

        token = authorization.replace(
            "Bearer ",
            "",
            1
        ).strip()

        delete_session(token)

    return {
        "success": True,
        "message": "Logged out successfully"
    }


# ============================================================
# HISTORY - GET
# ============================================================

@router.get("/api/user/history")
def user_history(
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    return {
        "success": True,
        "history": get_history(user["id"])
    }


# ============================================================
# HISTORY - ADD
# ============================================================

@router.post("/api/user/history")
def save_history(
    data: HistoryRequest,
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    add_history(
        user["id"],
        data.source,
        data.message
    )

    return {
        "success": True,
        "message": "History saved"
    }


# ============================================================
# HISTORY - CLEAR
# ============================================================

@router.delete("/api/user/history")
def remove_history(
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    clear_history(user["id"])

    return {
        "success": True,
        "message": "History cleared"
    }


# ============================================================
# FAVORITES - GET
# ============================================================

@router.get("/api/user/favorites")
def user_favorites(
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    return {
        "success": True,
        "favorites": get_favorites(user["id"])
    }


# ============================================================
# FAVORITES - ADD
# ============================================================

@router.post("/api/user/favorites")
def save_favorite(
    data: FavoriteRequest,
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    message = data.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Favorite message is empty"
        )

    add_favorite(
        user["id"],
        message
    )

    return {
        "success": True,
        "message": "Favorite saved"
    }


# ============================================================
# FAVORITES - DELETE
# ============================================================

@router.delete("/api/user/favorites/{message}")
def remove_favorite(
    message: str,
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    delete_favorite(
        user["id"],
        message
    )

    return {
        "success": True,
        "message": "Favorite removed"
    }


# ============================================================
# EMERGENCY CONTACTS - GET
# ============================================================

@router.get("/api/user/emergency-contacts")
def user_emergency_contacts(
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    return {
        "success": True,
        "contacts": get_emergency_contacts(user["id"])
    }


# ============================================================
# EMERGENCY CONTACT - ADD
# ============================================================

@router.post("/api/user/emergency-contacts")
def save_emergency_contact(
    data: EmergencyContactRequest,
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    name = data.name.strip()
    phone = data.phone.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Contact name is required"
        )

    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number is required"
        )

    add_emergency_contact(
        user["id"],
        name,
        phone
    )

    return {
        "success": True,
        "message": "Emergency contact saved"
    }


# ============================================================
# EMERGENCY CONTACT - DELETE
# ============================================================

@router.delete("/api/user/emergency-contacts/{phone}")
def remove_emergency_contact(
    phone: str,
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    delete_emergency_contact(
        user["id"],
        phone
    )

    return {
        "success": True,
        "message": "Emergency contact removed"
    }