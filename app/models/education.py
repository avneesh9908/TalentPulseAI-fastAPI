from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class Education(Base):
    __tablename__ = "education"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    degree      = Column(String(150), nullable=False)
    university  = Column(String(150), nullable=False)
    field       = Column(String(100), nullable=True)
    start_year  = Column(Integer,     nullable=False)
    end_year    = Column(Integer,     nullable=True)   # null = currently studying
    grade       = Column(String(50),  nullable=True)
    description = Column(Text,         nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="education")