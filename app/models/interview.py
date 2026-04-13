from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.db import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    setup_id = Column(Integer, default=0, nullable=False)

    role = Column(String, nullable=False)
    profile_option = Column(String, nullable=False)
    profile_id = Column(String, nullable=True)
    experience = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    skills = Column(JSON, nullable=False, default=list)

    status = Column(String, nullable=False, default="initialized")
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
