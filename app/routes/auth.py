from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate, UserLogin
from app.services.auth_service import signup_user, login_user
from app.database.deps import get_db

router = APIRouter()

@router.post("/signup")
def signup(data: UserCreate, db: Session = Depends(get_db)):
    return signup_user(data, db)

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    return login_user(data, db)
