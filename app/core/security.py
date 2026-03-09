from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)



    # DATABASE_URL = postgresql://postgres:admin123@localhost:5432/talentPulseAI
# DATABASE_URL = postgresql://postgres:admin123@localhost:5432/talentpulseAI



# SECRET_KEY = "mysecretkey123"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
