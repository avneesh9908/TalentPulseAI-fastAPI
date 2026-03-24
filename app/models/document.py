from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class Document(Base):
    __tablename__ = "documents"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    name        = Column(String(255), nullable=False)
    type        = Column(String(50),  nullable=False)   # resume | certificate | other
    file_url    = Column(String(500), nullable=False)   # S3 URL
    file_key    = Column(String(500), nullable=False)   # S3 key (needed for deletion)
    size_kb     = Column(Integer,     nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="documents")