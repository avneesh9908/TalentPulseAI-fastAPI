from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


ExperienceType = Literal["0-1", "1-3", "3-5", "5-8", "8+"]
DifficultyType = Literal["easy", "medium", "hard"]
RoleType = Literal["frontend", "backend", "fullstack", "ml", "data", "mobile", "devops", "security", "general"]
ProfileOptionType = Literal["existing", "upload"]
InterviewStatusType = Literal["initialized", "in_progress", "completed", "failed", "submitted"]


class InterviewSetupRequest(BaseModel):
    setup_id: int = Field(default=0, ge=0)
    experience: ExperienceType
    difficulty: DifficultyType
    skills: List[str] = Field(min_length=1, max_length=20)
    role: RoleType
    profile_option: ProfileOptionType
    profile_id: Optional[str] = None


class InterviewSetupResponse(BaseModel):
    interview_id: str
    setup_id: int
    user_id: int
    role: str
    experience: str
    difficulty: str
    skills: List[str]
    profile_option: str
    status: InterviewStatusType
    started_at: datetime
    message: str
