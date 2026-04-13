from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from app.routes import auth, user, interview
from app.database.db import engine, Base
import app.models

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",     
        "http://localhost:3000",      
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],             
    allow_headers=["*"],             
)


Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(interview.router, prefix="/interview", tags=["Interview"])