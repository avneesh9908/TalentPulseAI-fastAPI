"""
Interview routes - handles interview setup, progress tracking, and submission
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.deps import get_db
from app.dependencies.auth import get_current_user
from app.models.interview import Interview
from app.models.user import User
from app.schemas.resume_rag_schema import (
    ContextRetrieveRequest,
    ContextRetrieveResponse,
    ResumeIndexRequest,
    ResumeIndexResponse,
)
from app.services.resume_rag_service import ResumeRAGService
from datetime import datetime
from app.schemas.interview_schema import InterviewSetupRequest, InterviewSetupResponse

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/setup", response_model=InterviewSetupResponse)
def setup_interview(
    payload: InterviewSetupRequest,
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
        "role": "frontend",             # Role: frontend, backend, fullstack, ml, data, mobile, devops, security, general
        "profile_option": "existing",   # Profile type: existing or upload
        "profile_id": null              # Optional: existing profile ID if using existing
    }
    
    Response returns interview session ID with setup_id=0
    """
    try:
        interview_id = f"interview_{current_user.id}_{int(datetime.utcnow().timestamp())}"

        record = Interview(
            interview_id=interview_id,
            user_id=current_user.id,
            setup_id=payload.setup_id,
            role=payload.role,
            profile_option=payload.profile_option,
            profile_id=payload.profile_id,
            experience=payload.experience,
            difficulty=payload.difficulty,
            skills=payload.skills,
            status="initialized",
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        response = {
            "interview_id": interview_id,
            "setup_id": record.setup_id,
            "user_id": current_user.id,
            "role": record.role,
            "experience": record.experience,
            "difficulty": record.difficulty,
            "skills": record.skills,
            "profile_option": record.profile_option,
            "status": record.status,
            "started_at": record.started_at,
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


@router.post("/resume/index", response_model=ResumeIndexResponse)
def index_resume_for_rag(
    payload: ResumeIndexRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Parse resume text/PDF and run chunking + embedding + vector indexing.
    """
    try:
        service = ResumeRAGService()
        resume_doc, chunk_count = service.index_resume(
            db=db,
            user_id=current_user.id,
            payload=payload,
        )

        return {
            "interview_id": payload.interview_id,
            "resume_id": resume_doc.id,
            "chunks_indexed": chunk_count,
            "vector_collection": service.collection_name,
            "status": "indexed",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume indexing failed: {str(e)}",
        )


@router.post("/context/retrieve", response_model=ContextRetrieveResponse)
def retrieve_context_for_question_generation(
    payload: ContextRetrieveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve top-k context chunks for question generation using setup payload fields.
    """
    try:
        service = ResumeRAGService()
        context_pack = service.retrieve_context(
            db=db,
            user_id=current_user.id,
            payload=payload,
        )

        return {
            "interview_id": payload.interview_id,
            "retrieved_count": len(context_pack),
            "context_pack": context_pack,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context retrieval failed: {str(e)}",
        )


@router.get("/{interview_id}")
def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get interview details by ID"""
    try:
        interview = (
            db.query(Interview)
            .filter(
                Interview.interview_id == interview_id,
                Interview.user_id == current_user.id,
            )
            .first()
        )

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )

        return {
            "interview_id": interview.interview_id,
            "user_id": current_user.id,
            "setup_id": interview.setup_id,
            "role": interview.role,
            "experience": interview.experience,
            "difficulty": interview.difficulty,
            "skills": interview.skills,
            "profile_option": interview.profile_option,
            "status": interview.status,
            "started_at": interview.started_at,
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
