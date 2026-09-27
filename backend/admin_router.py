import hashlib, secrets, os, sqlite3
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router=APIRouter()
BASE=Path(__file__).resolve().parent
DB=BASE/"data"/"users.db"
ADMIN_EMAIL=os.getenv("ACA_ADMIN_EMAIL","admin@aca.local").lower()
ADMIN_PASSWORD=os.getenv("ACA_ADMIN_PASSWORD","Admin@12345")
_admin_tokens=set()

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def require_admin(auth):
    if not auth or not auth.startswith("Bearer ") or auth.replace("Bearer ","",1).strip() not in _admin_tokens:
        raise HTTPException(401,"Admin authentication required")
    return True

class AdminLogin(BaseModel): email:str; password:str

@router.post("/api/admin/login")
def admin_login(data:AdminLogin):
    if data.email.lower().strip()!=ADMIN_EMAIL or data.password!=ADMIN_PASSWORD:
        raise HTTPException(401,"Invalid admin credentials")
    token=secrets.token_urlsafe(32); _admin_tokens.add(token)
    return {"success":True,"token":token,"admin":{"email":ADMIN_EMAIL,"role":"admin","name":"System Administrator"}}

@router.get("/api/admin/me")
def admin_me(authorization:str|None=Header(None)):
    require_admin(authorization); return {"success":True,"admin":{"email":ADMIN_EMAIL,"role":"admin","name":"System Administrator"}}

@router.post("/api/admin/logout")
def admin_logout(authorization:str|None=Header(None)):
    if authorization and authorization.startswith("Bearer "): _admin_tokens.discard(authorization.replace("Bearer ","",1).strip())
    return {"success":True}

@router.get("/api/admin/stats")
def stats(authorization:str|None=Header(None)):
    require_admin(authorization); c=conn()
    result={}
    for key,table in [("users","users"),("history","communication_history"),("favorites","favorites"),("emergency_contacts","emergency_contacts")]:
        result[key]=c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    c.close(); return result

@router.get("/api/admin/users")
def users(authorization:str|None=Header(None)):
    require_admin(authorization); c=conn(); rows=c.execute("SELECT id,name,email,created_at FROM users ORDER BY id DESC").fetchall(); c.close(); return {"users":[dict(r) for r in rows]}

@router.delete("/api/admin/users/{user_id}")
def delete_user(user_id:int,authorization:str|None=Header(None)):
    require_admin(authorization); c=conn();
    c.execute("DELETE FROM sessions WHERE user_id=?",(user_id,)); c.execute("DELETE FROM communication_history WHERE user_id=?",(user_id,)); c.execute("DELETE FROM favorites WHERE user_id=?",(user_id,)); c.execute("DELETE FROM emergency_contacts WHERE user_id=?",(user_id,)); c.execute("DELETE FROM users WHERE id=?",(user_id,)); c.commit(); c.close(); return {"success":True}

@router.get("/api/admin/history")
def history(authorization:str|None=Header(None)):
    require_admin(authorization); c=conn(); rows=c.execute("SELECT id,user_id,source,message,created_at FROM communication_history ORDER BY id DESC").fetchall(); c.close(); return {"history":[dict(r) for r in rows]}

@router.delete("/api/admin/history/{history_id}")
def delete_history(history_id:int,authorization:str|None=Header(None)):
    require_admin(authorization); c=conn(); c.execute("DELETE FROM communication_history WHERE id=?",(history_id,)); c.commit(); c.close(); return {"success":True}

@router.get("/api/admin/emergency-contacts")
def emergency_contacts(authorization:str|None=Header(None)):
    require_admin(authorization); c=conn(); rows=c.execute("SELECT id,user_id,name,phone,created_at FROM emergency_contacts ORDER BY id DESC").fetchall(); c.close(); return {"contacts":[dict(r) for r in rows]}
