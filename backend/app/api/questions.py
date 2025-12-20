"""
API endpoints for tech questions and ML theory questions.
"""
import json
import random
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.core.db import get_db
from app.models.questions import TechQuestion
from app.schemas.questions import QuestionOut, QuestionAnswerIn, QuestionAnswerEval
from app.services.llm_grader import llm_grade_answer
from app.services.scibox_client import scibox_client


router = APIRouter()


# Load ML questions from JSON file
def load_ml_questions() -> List[dict]:
    """Load ML theory questions from JSON file."""
    # Try multiple possible paths
    possible_paths = [
        Path("/tasks_base/ml_questions.json"),  # Docker mount
        Path(__file__).parent.parent.parent.parent / "tasks_base" / "ml_questions.json",  # Local dev
        Path("tasks_base/ml_questions.json"),  # Relative
    ]
    
    for questions_path in possible_paths:
        if questions_path.exists():
            try:
                with open(questions_path, "r", encoding="utf-8") as f:
                    questions = json.load(f)
                    print(f"✅ Loaded {len(questions)} ML questions from {questions_path}")
                    return questions
            except Exception as e:
                print(f"⚠️ Failed to load ML questions from {questions_path}: {e}")
    
    print("⚠️ ML questions file not found")
    return []


ML_QUESTIONS = load_ml_questions()


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


# ============== ML THEORY QUESTIONS ==============

@router.get("/ml/random")
async def get_random_ml_question(
    difficulty: Optional[str] = Query(None, description="easy|medium|hard"),
    topic: Optional[str] = Query(None, description="linear_models|classification|trees|ensembles|neural_networks|cnn|bias_variance|metrics|practical"),
    count: int = Query(1, ge=1, le=10, description="Number of questions to return"),
):
    """
    Get random ML theory question(s).
    
    Args:
        difficulty: Filter by difficulty (optional)
        topic: Filter by topic (optional)
        count: Number of questions to return (1-10)
        
    Returns:
        Random ML question(s) with id, question, topic, difficulty
    """
    if not ML_QUESTIONS:
        raise HTTPException(status_code=404, detail="ML questions not loaded")
    
    # Filter questions
    filtered = ML_QUESTIONS
    
    if difficulty:
        filtered = [q for q in filtered if q.get("difficulty") == difficulty]
    
    if topic:
        filtered = [q for q in filtered if q.get("topic") == topic]
    
    if not filtered:
        raise HTTPException(status_code=404, detail="No questions found matching criteria")
    
    # Select random questions
    selected = random.sample(filtered, min(count, len(filtered)))
    
    # Return without answer (to hide from frontend)
    return [
        {
            "id": q["id"],
            "question": q["question"],
            "topic": q.get("topic", "general"),
            "difficulty": q.get("difficulty", "medium"),
            "category": q.get("category", "ml-theory")
        }
        for q in selected
    ]


@router.get("/ml/topics")
async def get_ml_topics():
    """
    Get list of available ML topics with question counts.
    """
    if not ML_QUESTIONS:
        return {"topics": [], "total": 0}
    
    topic_counts = {}
    for q in ML_QUESTIONS:
        topic = q.get("topic", "general")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    return {
        "topics": [
            {"name": topic, "count": count}
            for topic, count in sorted(topic_counts.items())
        ],
        "total": len(ML_QUESTIONS)
    }


@router.post("/ml/{question_id}/evaluate")
async def evaluate_ml_answer(
    question_id: int,
    user_answer: str = Query(..., description="User's answer to the question"),
):
    """
    Evaluate user's answer to ML theory question.
    Uses LLM to compare with reference answer and return score.
    
    Args:
        question_id: ML question ID
        user_answer: User's answer text
        
    Returns:
        Score (0-100) and detailed feedback
    """
    # Find question by ID
    question = next((q for q in ML_QUESTIONS if q["id"] == question_id), None)
    
    if not question:
        raise HTTPException(status_code=404, detail="ML question not found")
    
    if not user_answer or not user_answer.strip():
        return {
            "score": 0,
            "correct_points": [],
            "missing_points": ["Ответ не предоставлен"],
            "errors": [],
            "feedback": "Пожалуйста, предоставьте ответ на вопрос.",
            "question": question["question"],
            "reference_answer": question["answer"]
        }
    
    # Evaluate using LLM
    try:
        result = await scibox_client.evaluate_theory_answer(
            question=question["question"],
            reference_answer=question["answer"],
            user_answer=user_answer
        )
        
        # Add question info to result
        result["question"] = question["question"]
        result["reference_answer"] = question["answer"]
        result["topic"] = question.get("topic", "general")
        result["difficulty"] = question.get("difficulty", "medium")
        
        return result
        
    except Exception as e:
        # Fallback if LLM fails
        return {
            "score": 0,
            "correct_points": [],
            "missing_points": [],
            "errors": [f"Ошибка оценки: {str(e)}"],
            "feedback": "Не удалось оценить ответ автоматически. Попробуйте позже.",
            "question": question["question"],
            "reference_answer": question["answer"]
        }


@router.get("/ml/{question_id}")
async def get_ml_question_by_id(question_id: int):
    """
    Get specific ML question by ID (without answer for quiz mode).
    """
    question = next((q for q in ML_QUESTIONS if q["id"] == question_id), None)
    
    if not question:
        raise HTTPException(status_code=404, detail="ML question not found")
    
    return {
        "id": question["id"],
        "question": question["question"],
        "topic": question.get("topic", "general"),
        "difficulty": question.get("difficulty", "medium"),
        "category": question.get("category", "ml-theory")
    }


@router.get("/ml/{question_id}/with-answer")
async def get_ml_question_with_answer(question_id: int):
    """
    Get ML question with reference answer (for review/learning mode).
    """
    question = next((q for q in ML_QUESTIONS if q["id"] == question_id), None)
    
    if not question:
        raise HTTPException(status_code=404, detail="ML question not found")
    
    return question

# пидормот
