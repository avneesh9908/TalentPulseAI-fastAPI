from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class Skill(Base):
    __tablename__ = "skills"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    name       = Column(String(100), nullable=False)
    level      = Column(Integer,     nullable=False)   # 1–5
    years      = Column(Integer,     nullable=True)
    category   = Column(String(20),  default="primary")  # primary | secondary
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="skills")