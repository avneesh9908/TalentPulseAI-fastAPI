from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token

def signup_user(data, db: Session):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        return {"error": "User already exists"}

    user = User(
        email=data.email,
        password=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered"}

def login_user(data, db: Session):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"error": "Invalid credentials"}

    if not verify_password(data.password, user.password):
        return {"error": "Invalid credentials"}

    token = create_access_token({"sub": user.email})

    return {"access_token": token}














































# from app.core.security import hash_password, verify_password
# from app.core.jwt import create_access_token

# fake_db = []

# def signup_user(data):
#     hashed = hash_password(data.password)
#     fake_db.append({
#         "email": data.email,
#         "password": hashed
#     })
#     return {"message": "User registered"}

# def login_user(data):
#     user = next((u for u in fake_db if u["email"] == data.email), None)
#     if not user:
#         return {"error": "User not found"}

#     if not verify_password(data.password, user["password"]):
#         return {"error": "Invalid password"}

#     token = create_access_token({"sub": user["email"]})
#     return {"access_token": token}
