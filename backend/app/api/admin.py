"""
Admin API endpoints.
For company dashboard and interview management.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..core.db import get_db
from ..models.interview import Interview
from ..schemas.interview import InterviewResponse

router = APIRouter()


@router.get("/interviews", response_model=List[InterviewResponse])
async def list_all_interviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all interviews for admin dashboard."""
    interviews = db.query(Interview).offset(skip).limit(limit).all()
    return interviews


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get platform statistics."""
    total_interviews = db.query(Interview).count()
    completed_interviews = db.query(Interview).filter(Interview.status == "completed").count()
    
    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_interviews,
        "in_progress": total_interviews - completed_interviews
    }


# пидормот
