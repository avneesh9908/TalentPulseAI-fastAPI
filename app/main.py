from fastapi import FastAPI
from app.routes import auth, user
from app.database.db import engine, Base
import app.models.user  # 👈 sirf table register karne ke liye

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
