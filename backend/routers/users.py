from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, RoleEnum
from auth import hash_password, decode_token, is_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[RoleEnum] = RoleEnum.member

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: RoleEnum

    class Config:
        from_attributes = True

def get_current_user(token: str, db: Session) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Ungültiger Token")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
    return user

@router.post("/", response_model=UserOut)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=list[UserOut])
def get_all_users(token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    return db.query(User).all()

@router.delete("/{user_id}")
def delete_user(user_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    db.delete(user)
    db.commit()
    return {"detail": "Benutzer gelöscht"}