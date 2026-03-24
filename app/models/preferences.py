from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class CareerPreferences(Base):
    __tablename__ = "career_preferences"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    preferred_role = Column(String(100), nullable=True)
    location       = Column(String(100), nullable=True)
    job_type       = Column(String(50),  nullable=True)   # full-time | intern | contract
    work_mode      = Column(String(50),  nullable=True)   # remote | hybrid | onsite
    salary_min     = Column(Integer,     nullable=True)
    salary_max     = Column(Integer,     nullable=True)
    notice_period  = Column(Integer,     nullable=True)   # in days
    open_to_work   = Column(Boolean,     default=True)
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")