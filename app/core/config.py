from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    VECTOR_DB_URL: str = ""
    # Backward-compatible alias (legacy key); prefer VECTOR_DB_URL.
    VECTOR_DATABASE_URL: str = ""
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    CURSOR_API_KEY: str = ""
    CURSOR_API_BASE_URL: str = "https://api.cursor.sh/v1"
    CURSOR_EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_COLLECTION: str = "talentpulse_resume_chunks"

    class Config:
        env_file = ".env"

settings = Settings()