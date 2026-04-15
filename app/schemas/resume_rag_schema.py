from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.interview_schema import (
    DifficultyType,
    ExperienceType,
    ProfileOptionType,
    RoleType,
)


class ResumePayload(BaseModel):
    source: Literal["upload", "existing", "text"] = "upload"
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    text: Optional[str] = None
    base64_pdf: Optional[str] = None


class ChunkingConfig(BaseModel):
    chunk_size: int = Field(default=700, ge=200, le=2000)
    chunk_overlap: int = Field(default=120, ge=0, le=500)


class EmbeddingConfig(BaseModel):
    provider: Literal["cursor"] = "cursor"
    model: str = "text-embedding-3-small"


class ResumeIndexRequest(BaseModel):
    interview_id: str
    setup_id: int = Field(default=0, ge=0)
    role: RoleType
    experience: ExperienceType
    difficulty: DifficultyType
    skills: List[str] = Field(min_length=1, max_length=20)
    profile_option: ProfileOptionType
    resume: ResumePayload
    chunking: ChunkingConfig = ChunkingConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()


class ResumeIndexResponse(BaseModel):
    interview_id: str
    resume_id: int
    chunks_indexed: int
    vector_collection: str
    status: str


class ContextRetrieveRequest(BaseModel):
    interview_id: str
    setup_id: int = 0
    role: RoleType
    experience: ExperienceType
    difficulty: DifficultyType
    skills: List[str] = Field(min_length=1, max_length=20)
    profile_option: ProfileOptionType
    query: str = Field(min_length=3)
    top_k: int = Field(default=6, ge=1, le=20)
    min_score: Optional[float] = None


class RetrievedContextChunk(BaseModel):
    chunk_id: int
    section: Optional[str]
    score: float
    text: str
    metadata: Dict[str, Any]


class ContextRetrieveResponse(BaseModel):
    interview_id: str
    retrieved_count: int
    context_pack: List[RetrievedContextChunk]
