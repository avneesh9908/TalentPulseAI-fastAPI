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
import re
from app.schemas.interview_schema import InterviewSetupRequest, InterviewSetupResponse

router = APIRouter()


def _answer_words(answer: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", answer.lower()))


def _score_single_answer(answer: str, skills: list[str]) -> dict:
    text = (answer or "").strip()
    if not text:
        return {
            "score": 0,
            "feedback": "No answer captured. Add a clear response with an example.",
        }

    words = _answer_words(text)
    structure_markers = ["because", "for example", "tradeoff", "challenge", "result", "impact"]
    technical_markers = [s.lower() for s in skills[:8] if s]
    structure_hits = sum(1 for marker in structure_markers if marker in text.lower())
    technical_hits = sum(1 for marker in technical_markers if marker and marker in text.lower())

    depth_score = min(1.0, words / 90.0)
    structure_score = min(1.0, structure_hits / 3.0)
    technical_score = min(1.0, technical_hits / 2.0) if technical_markers else 0.6

    total = int(round((depth_score * 0.5 + structure_score * 0.25 + technical_score * 0.25) * 100))
    if total >= 80:
        feedback = "Strong response with solid depth and good technical clarity."
    elif total >= 60:
        feedback = "Good baseline. Add one concrete metric/result to strengthen impact."
    else:
        feedback = "Too brief or generic. Use STAR format and include technical specifics."

    return {"score": total, "feedback": feedback}


def _build_interview_feedback(answers: dict, skills: list[str]) -> dict:
    answer_items = list(answers.items())
    per_question = []
    for key, value in answer_items:
        raw = " ".join(value) if isinstance(value, list) else str(value or "")
        scored = _score_single_answer(raw, skills)
        per_question.append(
            {
                "question_id": key,
                "score": scored["score"],
                "feedback": scored["feedback"],
                "word_count": _answer_words(raw),
            }
        )

    if not per_question:
        return {
            "score": 0,
            "strengths": [],
            "improvements": ["No answers were submitted. Try the interview again with full responses."],
            "overall_feedback": "No responses were captured.",
            "question_feedback": [],
            "next_steps": [
                "Practice answering with STAR format.",
                "Speak 60-120 seconds per question.",
            ],
        }

    avg_score = int(round(sum(item["score"] for item in per_question) / len(per_question)))
    avg_words = int(round(sum(item["word_count"] for item in per_question) / len(per_question)))
    answered_with_depth = sum(1 for item in per_question if item["word_count"] >= 45)

    strengths = []
    improvements = []
    if avg_score >= 75:
        strengths.append("Responses show strong technical depth and clear communication.")
    if answered_with_depth >= max(1, len(per_question) // 2):
        strengths.append("Most answers include enough detail to evaluate your experience.")
    if skills:
        strengths.append(f"Relevant skills were covered: {', '.join(skills[:4])}.")

    if avg_words < 45:
        improvements.append("Increase answer depth: target 60-120 words per question.")
    if any(item["score"] < 60 for item in per_question):
        improvements.append("Strengthen weaker answers using a Situation-Task-Action-Result structure.")
    improvements.append("Add measurable outcomes (latency, scale, revenue, accuracy) to improve credibility.")

    level = "excellent" if avg_score >= 80 else "good" if avg_score >= 65 else "developing"
    overall_feedback = (
        f"Overall performance is {level}. You scored {avg_score}/100. "
        f"Average answer length was {avg_words} words."
    )

    return {
        "score": avg_score,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "overall_feedback": overall_feedback,
        "question_feedback": per_question,
        "next_steps": [
            "Do one timed mock round focusing on weaker questions.",
            "Prepare concise project stories with metrics and trade-offs.",
            "Review top role-specific concepts before your next interview.",
        ],
    }


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
        resume_doc, chunk_count, vector_indexed = service.index_resume(
            db=db,
            user_id=current_user.id,
            payload=payload,
        )

        return {
            "interview_id": payload.interview_id,
            "resume_id": resume_doc.id,
            "chunks_indexed": chunk_count,
            "vector_collection": service.collection_name,
            "status": "indexed" if vector_indexed else "indexed_without_vectors",
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

        feedback = _build_interview_feedback(answers, interview.skills or [])
        interview.status = "submitted"
        db.commit()

        return {
            "interview_id": interview_id,
            "status": "submitted",
            "score": feedback["score"],
            "completed_at": completed_at or datetime.utcnow().isoformat(),
            "message": "Interview submitted successfully",
            "feedback": feedback,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit interview: {str(e)}"
        )
