from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class Profile(Base):
    __tablename__ = "profiles"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name       = Column(String(100), nullable=True)
    headline        = Column(String(200), nullable=True)
    phone           = Column(String(20),  nullable=True)
    location        = Column(String(100), nullable=True)
    dob             = Column(Date,         nullable=True)
    nationality     = Column(String(50),  nullable=True)
    experience_yrs  = Column(Integer,     nullable=True)
    bio             = Column(Text,         nullable=True)
    linkedin_url    = Column(String(255), nullable=True)
    github_url      = Column(String(255), nullable=True)
    portfolio_url   = Column(String(255), nullable=True)
    photo_url       = Column(String(500), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")