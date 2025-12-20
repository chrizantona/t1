"""
Question Block API - Part 2 of interview.
Endpoints for starting block, getting questions, submitting answers, skipping.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from ..core.db import get_db
from ..services.question_block_service import (
    start_question_block,
    get_current_question,
    submit_answer,
    skip_question,
    retry_answer,
    get_block_status,
    get_block_statistics
)
from ..services.llm_protocol import evaluate_answer, Stage


router = APIRouter()


# Pydantic schemas
class StartBlockRequest(BaseModel):
    interview_id: int
    question_count: int = 20


class SubmitAnswerRequest(BaseModel):
    answer_id: int
    candidate_answer: str


class SkipQuestionRequest(BaseModel):
    answer_id: int


class RetryQuestionRequest(BaseModel):
    answer_id: int


class BlockStatusResponse(BaseModel):
    block_id: int
    status: str
    total_questions: int
    current_index: int
    total_answered: int
    total_skipped: int
    total_correct: Optional[int] = None
    average_score: Optional[float] = None
    average_response_time: Optional[float] = None
    category_scores: Optional[dict] = None
    difficulty_scores: Optional[dict] = None


class QuestionResponse(BaseModel):
    answer_id: int
    question_order: int
    total_questions: int
    question_text: str
    category: str
    difficulty: str
    question_type: str
    status: str
    shown_at: Optional[str] = None


class AnswerResultResponse(BaseModel):
    answer_id: int
    status: str
    score: Optional[float] = None
    is_correct: Optional[bool] = None
    response_time_seconds: Optional[float] = None
    feedback: Optional[str] = None
    block_completed: bool
    next_question_index: Optional[int] = None


# Endpoints

@router.post("/start")
async def start_block(
    request: StartBlockRequest,
    db: Session = Depends(get_db)
):
    """
    Start the question block for an interview.
    Selects 20 random questions based on vacancy requirements.
    """
    result = await start_question_block(
        interview_id=request.interview_id,
        db=db,
        question_count=request.question_count
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/{block_id}/current")
async def get_current(
    block_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the current question for the block.
    Updates shown_at timestamp on first view.
    """
    result = await get_current_question(block_id, db)
    
    if not result:
        raise HTTPException(status_code=404, detail="Question not found or block completed")
    
    if "status" in result and result["status"] == "completed":
        return result
    
    return result


@router.post("/answer")
async def answer_question(
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Submit an answer to the current question.
    Evaluates the answer using LLM and updates statistics.
    """
    from ..models.question_session import QuestionAnswer, QuestionBlock
    from ..models.interview import Interview
    
    # Get answer and block info for LLM evaluation
    answer = db.query(QuestionAnswer).filter(QuestionAnswer.id == request.answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    block = answer.question_block
    interview = db.query(Interview).filter(Interview.id == block.interview_id).first()
    
    # Evaluate answer using LLM
    evaluation_score = None
    feedback = None
    
    try:
        evaluation = await evaluate_answer(
            stage=Stage.THEORY,
            direction=interview.direction if interview else "any",
            difficulty=answer.difficulty,
            question_text=answer.question_text,
            candidate_answer=request.candidate_answer,
            canonical_answer=answer.reference_answer,
            key_points=[]
        )
        
        # Convert LLM score (0-3) to 0-100
        llm_score = evaluation.get("score", 1)
        evaluation_score = (llm_score / 3) * 100
        feedback = evaluation.get("short_feedback_for_candidate", "")
        
        # Store evaluation details
        answer.evaluation_details = evaluation
        answer.feedback = feedback
        db.commit()
        
    except Exception as e:
        print(f"LLM evaluation error: {e}")
        # Continue without score if LLM fails
    
    # Submit the answer
    result = await submit_answer(
        answer_id=request.answer_id,
        candidate_answer=request.candidate_answer,
        db=db,
        evaluation_score=evaluation_score
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    result["feedback"] = feedback
    return result


@router.post("/skip")
async def skip(
    request: SkipQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Skip the current question. Cannot go back.
    """
    result = await skip_question(
        answer_id=request.answer_id,
        db=db
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/retry")
async def retry(
    request: RetryQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Retry an answered question.
    Each retry halves the maximum possible score.
    """
    result = await retry_answer(
        answer_id=request.answer_id,
        db=db
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/{block_id}/status")
async def get_status(
    block_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current status of the question block.
    """
    result = await get_block_status(block_id, db)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/interview/{interview_id}/statistics")
async def get_statistics(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for the question block.
    Used for the final report.
    """
    result = await get_block_statistics(interview_id, db)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/interview/{interview_id}/block")
async def get_block_by_interview(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get question block for an interview.
    """
    from ..models.question_session import QuestionBlock
    
    block = db.query(QuestionBlock).filter(
        QuestionBlock.interview_id == interview_id
    ).first()
    
    if not block:
        raise HTTPException(status_code=404, detail="Question block not found")
    
    return await get_block_status(block.id, db)


# пидормот
