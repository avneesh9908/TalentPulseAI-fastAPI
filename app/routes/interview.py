"""
Interview routes - handles interview setup, progress tracking, and submission
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.deps import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from datetime import datetime
from typing import Optional, List

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# TYPES (temporary - move to schemas later)
# ─────────────────────────────────────────────────────────────────────────────

class InterviewSetupRequest:
    """Unified request for interview setup (combining 3 steps into 1)"""
    def __init__(
        self,
        experience: str,
        difficulty: str,
        skills: List[str],
        role: str,
        profile_option: str,  # "existing" or "upload"
        setup_id: int = 0,
        profile_id: Optional[str] = None,
    ):
        self.setup_id = setup_id
        self.experience = experience
        self.difficulty = difficulty
        self.skills = skills
        self.role = role
        self.profile_option = profile_option
        self.profile_id = profile_id


class InterviewSetupResponse:
    """Interview session created"""
    def __init__(self, interview_id: str, setup_id: int, status: str):
        self.interview_id = interview_id
        self.setup_id = setup_id
        self.status = status
        self.started_at = datetime.utcnow().isoformat()
        self.message = "Interview session initialized successfully"


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/setup")
def setup_interview(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initialize interview with unified setup payload (all 3 steps combined)
    
    Payload structure:
    {
        "setup_id": 0,
        "experience": "1-3",           # Experience level: 0-1, 1-3, 3-5, 5-8, 8+
        "difficulty": "medium",         # Interview difficulty: easy, medium, hard
        "skills": ["React", "TypeScript", "JavaScript"],  # Selected skills
        "role": "frontend",             # Role: frontend, backend, fullstack, ml, data, mobile, devops
        "profile_option": "existing",   # Profile type: existing or upload
        "profile_id": null              # Optional: existing profile ID if using existing
    }
    
    Response returns interview session ID with setup_id=0
    """
    try:
        # Extract payload fields
        setup_id = payload.get("setup_id", 0)
        experience = payload.get("experience")
        difficulty = payload.get("difficulty")
        skills = payload.get("skills", [])
        role = payload.get("role")
        profile_option = payload.get("profile_option")
        profile_id = payload.get("profile_id")

        # Validation
        if not all([experience, difficulty, role, profile_option]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: experience, difficulty, role, profile_option"
            )

        VALID_EXPERIENCE = ["0-1", "1-3", "3-5", "5-8", "8+"]
        VALID_DIFFICULTY = ["easy", "medium", "hard"]
        VALID_ROLES = ["frontend", "backend", "fullstack", "ml", "data", "mobile", "devops", "general"]
        VALID_PROFILE_OPTIONS = ["existing", "upload"]

        if experience not in VALID_EXPERIENCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid experience level. Must be one of: {VALID_EXPERIENCE}"
            )

        if difficulty not in VALID_DIFFICULTY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty. Must be one of: {VALID_DIFFICULTY}"
            )

        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {VALID_ROLES}"
            )

        if profile_option not in VALID_PROFILE_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profile_option. Must be one of: {VALID_PROFILE_OPTIONS}"
            )

        # TODO: Store interview session in database
        # For now, just create a mock interview_id
        interview_id = f"interview_{current_user.id}_{int(datetime.utcnow().timestamp())}"

        # Create response
        response = {
            "interview_id": interview_id,
            "setup_id": setup_id,
            "user_id": current_user.id,
            "role": role,
            "experience": experience,
            "difficulty": difficulty,
            "skills": skills,
            "profile_option": profile_option,
            "status": "initialized",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Interview session initialized successfully"
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup interview: {str(e)}"
        )


@router.get("/{interview_id}")
def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get interview details by ID"""
    try:
        # TODO: Fetch from database
        return {
            "interview_id": interview_id,
            "user_id": current_user.id,
            "status": "initialized",
            "message": "Interview details retrieved"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interview: {str(e)}"
        )


@router.put("/{interview_id}/progress")
def save_progress(
    interview_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save interview progress (auto-save during interview)"""
    try:
        # TODO: Update interview progress in database
        step = payload.get("step")
        data = payload.get("data", {})

        return {
            "interview_id": interview_id,
            "step": step,
            "status": "progress_saved",
            "message": "Interview progress saved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save progress: {str(e)}"
        )


@router.post("/{interview_id}/submit")
def submit_interview(
    interview_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit completed interview"""
    try:
        answers = payload.get("answers", {})
        completed_at = payload.get("completed_at")

        # TODO: Store results, calculate score, update status
        return {
            "interview_id": interview_id,
            "status": "submitted",
            "score": 0,  # TODO: Calculate actual score
            "message": "Interview submitted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit interview: {str(e)}"
        )
