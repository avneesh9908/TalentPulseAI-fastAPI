from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    # Relationships
    profile     = relationship("Profile", back_populates="user", uselist=False)
    education   = relationship("Education", back_populates="user")
    skills      = relationship("Skill", back_populates="user")
    documents   = relationship("Document", back_populates="user")
    preferences = relationship("CareerPreferences", back_populates="user", uselist=False)
    interviews  = relationship("Interview")