"""
API endpoints for tech questions.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.models.questions import TechQuestion
from app.schemas.questions import QuestionOut, QuestionAnswerIn, QuestionAnswerEval
from app.services.llm_grader import llm_grade_answer


router = APIRouter()


@router.get("/next", response_model=QuestionOut)
async def get_next_question(
    category: str = Query(..., description="algorithms|frontend|backend|data-science"),
    difficulty: str = Query(..., description="easy|medium|hard"),
    db: Session = Depends(get_db),
):
    """
    Get next random question by category and difficulty.
    
    Args:
        category: Question category
        difficulty: Question difficulty
        db: Database session
        
    Returns:
        Random question matching criteria
    """
    question = (
        db.query(TechQuestion)
        .filter(
            TechQuestion.category == category,
            TechQuestion.difficulty == difficulty
        )
        .order_by(func.random())
        .first()
    )
    
    if question is None:
        raise HTTPException(status_code=404, detail="No question found")
    
    return QuestionOut(
        id=question.id,
        category=question.category.value,
        difficulty=question.difficulty.value,
        question_text=question.question_text,
        panel_type=question.panel_type,
        language_hint=question.language_hint,
    )


@router.post("/{question_id}/answer", response_model=QuestionAnswerEval)
async def submit_answer(
    question_id: int,
    payload: QuestionAnswerIn,
    db: Session = Depends(get_db),
):
    """
    Submit answer for evaluation by LLM.
    
    Args:
        question_id: Question ID
        payload: Answer data (code and/or text)
        db: Database session
        
    Returns:
        Evaluation result with score and feedback
    """
    # Get question
    question = db.query(TechQuestion).filter(TechQuestion.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Grade answer using LLM
    eval_result = await llm_grade_answer(
        question_text=question.question_text,
        panel_type=question.panel_type.value,
        eval_mode=question.eval_mode.value,
        language_hint=question.language_hint,
        answer_code=payload.answer_code,
        answer_text=payload.answer_text,
    )
    
    return QuestionAnswerEval(**eval_result)
