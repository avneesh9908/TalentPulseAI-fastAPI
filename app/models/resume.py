from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base


class ResumeDocument(Base):
    __tablename__ = "resume_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interview_id = Column(String, nullable=False, index=True)
    setup_id = Column(Integer, nullable=False, default=0)

    role = Column(String, nullable=False)
    experience = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    skills = Column(JSON, nullable=False, default=list)
    profile_option = Column(String, nullable=False)

    source = Column(String, nullable=False, default="upload")
    file_name = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)

    raw_text = Column(Text, nullable=False)
    parsed_sections = Column(JSON, nullable=False, default=dict)
    parsed_summary = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
    chunks = relationship(
        "ResumeChunk", back_populates="resume_document", cascade="all, delete-orphan"
    )


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id = Column(Integer, primary_key=True, index=True)
    resume_document_id = Column(
        Integer, ForeignKey("resume_documents.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    section = Column(String, nullable=True)
    chunk_text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    resume_document = relationship("ResumeDocument", back_populates="chunks")
