from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ✅ Add this import
from app.routes import auth, user
from app.database.db import engine, Base
import app.models.user 

app = FastAPI()

# ✅ ✅ ✅ ADD CORS MIDDLEWARE HERE - Right after app creation ✅ ✅ ✅
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Vite
        "http://localhost:3000",      # React
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)

# Database tables create
Base.metadata.create_all(bind=engine)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])