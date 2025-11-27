"""
Theory Service - Handle theory block of interview.

Flow:
1. Select questions based on vacancy/direction
2. Ask question
3. Evaluate answer
4. Generate follow-up if needed
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .theory_pool import (
    get_question_by_id,
    select_theory_questions,
    get_all_questions
)
from .llm_protocol import (
    ask_question,
    evaluate_answer,
    Stage,
    Intent
)
from ..models.interview import Interview, TheoryAnswer


async def prepare_theory_block(
    interview_id: int,
    direction: str,
    difficulty: str,
    db: Session,
    question_count: int = 3
) -> List[Dict[str, Any]]:
    """
    Prepare theory questions for interview.
    Creates TheoryAnswer records in pending state.
    
    Returns:
        List of prepared questions with their IDs
    """
    # Get already asked questions
    existing = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id
    ).all()
    exclude_ids = [a.question_id for a in existing if a.question_id]
    
    # Select new questions
    questions = select_theory_questions(
        direction=direction,
        difficulty=difficulty,
        count=question_count,
        exclude_ids=exclude_ids
    )
    
    prepared = []
    order_start = len(existing) + 1
    
    for i, q in enumerate(questions):
        # Create TheoryAnswer record
        theory_answer = TheoryAnswer(
            interview_id=interview_id,
            question_id=q["id"],
            question_type="theory",
            question_text=q["question_text"],
            reference_answer=q["canonical_answer"],
            question_order=order_start + i,
            status="pending"
        )
        db.add(theory_answer)
        
        prepared.append({
            "id": q["id"],
            "question_text": q["question_text"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "order": order_start + i
        })
    
    db.commit()
    return prepared


async def get_next_theory_question(
    interview_id: int,
    db: Session
) -> Optional[Dict[str, Any]]:
    """
    Get next pending theory question for the interview.
    
    Returns:
        Question dict or None if all answered
    """
    pending = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id,
        TheoryAnswer.status == "pending"
    ).order_by(TheoryAnswer.question_order).first()
    
    if not pending:
        return None
    
    return {
        "theory_answer_id": pending.id,
        "question_id": pending.question_id,
        "question_text": pending.question_text,
        "question_order": pending.question_order,
        "total_questions": db.query(TheoryAnswer).filter(
            TheoryAnswer.interview_id == interview_id
        ).count()
    }


async def evaluate_theory_answer(
    theory_answer_id: int,
    candidate_answer: str,
    db: Session
) -> Dict[str, Any]:
    """
    Evaluate candidate's answer to theory question.
    Uses LLM for evaluation and updates TheoryAnswer record.
    
    Returns:
        Evaluation result with score and feedback
    """
    theory_answer = db.query(TheoryAnswer).filter(
        TheoryAnswer.id == theory_answer_id
    ).first()
    
    if not theory_answer:
        return {"error": "Theory answer not found"}
    
    interview = db.query(Interview).filter(
        Interview.id == theory_answer.interview_id
    ).first()
    
    # Get full question data for key_points
    question_data = get_question_by_id(theory_answer.question_id)
    key_points = question_data.get("key_points", []) if question_data else []
    
    # Evaluate via LLM
    evaluation = await evaluate_answer(
        stage=Stage.THEORY,
        direction=interview.direction if interview else "any",
        difficulty=interview.selected_level if interview else "junior",
        question_text=theory_answer.question_text,
        candidate_answer=candidate_answer,
        canonical_answer=theory_answer.reference_answer,
        key_points=key_points
    )
    
    # Convert LLM score (0-3) to 0-100
    llm_score = evaluation.get("score", 1)
    score = (llm_score / 3) * 100
    
    # Update TheoryAnswer record
    from datetime import datetime
    theory_answer.candidate_answer = candidate_answer
    theory_answer.score = score
    theory_answer.evaluation_details = evaluation
    theory_answer.status = "answered"
    theory_answer.answered_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "theory_answer_id": theory_answer_id,
        "score": score,
        "feedback": evaluation.get("short_feedback_for_candidate", ""),
        "extra_topics": evaluation.get("extra_topics", []),
        "evaluation": evaluation
    }


async def generate_follow_up_question(
    interview_id: int,
    original_question_id: str,
    candidate_answer: str,
    extra_topic: str,
    db: Session
) -> Dict[str, Any]:
    """
    Generate a follow-up question based on candidate's answer.
    This is for probing deeper into a topic they mentioned.
    
    Args:
        interview_id: Interview ID
        original_question_id: ID of the original question
        candidate_answer: What the candidate answered
        extra_topic: Topic to probe deeper
        db: Database session
        
    Returns:
        Generated follow-up question
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    # Generate follow-up using LLM
    result = await ask_question(
        stage=Stage.THEORY,
        direction=interview.direction if interview else "any",
        difficulty=interview.selected_level if interview else "junior",
        question_type="follow_up",
        topic=extra_topic
    )
    
    if "error" in result:
        return {
            "question_text": f"Расскажите подробнее о {extra_topic}.",
            "is_follow_up": True
        }
    
    # Create TheoryAnswer record for follow-up
    existing_count = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id
    ).count()
    
    follow_up = TheoryAnswer(
        interview_id=interview_id,
        question_type="follow_up",
        question_text=result.get("question_text", f"Расскажите подробнее о {extra_topic}"),
        question_order=existing_count + 1,
        status="pending"
    )
    db.add(follow_up)
    db.commit()
    
    return {
        "theory_answer_id": follow_up.id,
        "question_text": follow_up.question_text,
        "is_follow_up": True,
        "original_topic": extra_topic
    }


async def get_theory_summary(interview_id: int, db: Session) -> Dict[str, Any]:
    """
    Get summary of theory block for the interview.
    
    Returns:
        Summary with total score and breakdown
    """
    answers = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id
    ).all()
    
    if not answers:
        return {
            "total_questions": 0,
            "answered_questions": 0,
            "average_score": 0,
            "breakdown": []
        }
    
    answered = [a for a in answers if a.status == "answered" and a.score is not None]
    
    return {
        "total_questions": len(answers),
        "answered_questions": len(answered),
        "average_score": sum(a.score for a in answered) / len(answered) if answered else 0,
        "breakdown": [
            {
                "question_id": a.question_id,
                "question_text": a.question_text[:100] + "..." if len(a.question_text) > 100 else a.question_text,
                "score": a.score,
                "status": a.status
            }
            for a in answers
        ]
    }


