from fastapi import FastAPI
from app.routes import auth, user
from app.database.db import engine, Base
from app.models import user

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
