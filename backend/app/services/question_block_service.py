"""
Question Block Service - Part 2 of interview.
Handles selection of 20 questions, answering, skipping, and statistics.
"""
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..models.interview import Interview
from ..models.vacancy import Vacancy, VacancySkill
from ..models.question_session import QuestionBlock, QuestionAnswer


# Load questions from JSON
QUESTIONS_PATH = Path(__file__).parent.parent.parent.parent / "tasks_base" / "questions.json"

def load_questions() -> List[Dict[str, Any]]:
    """Load all questions from questions.json"""
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

ALL_QUESTIONS = load_questions()


# Direction to categories mapping
DIRECTION_CATEGORIES_MAP = {
    "backend": ["backend", "python", "fastapi", "sql", "sqlalchemy", "docker", "messaging", 
                "architecture", "async", "linux", "databases", "git", "algorithms"],
    "frontend": ["frontend", "algorithms", "git", "architecture"],
    "ml": ["data-science", "python", "sql", "algorithms", "ml", "architecture"],
    "data": ["data-science", "python", "sql", "airflow", "elasticsearch", "databases", "ml"],
    "devops": ["docker", "linux", "git", "architecture", "databases", "messaging"],
    "qa": ["python", "sql", "git", "linux", "algorithms"],
    "go": ["go", "algorithms", "docker", "sql", "architecture", "messaging", "git"],
    "fullstack": ["backend", "frontend", "python", "sql", "docker", "git", "algorithms"]
}

# Default categories if direction not found
DEFAULT_CATEGORIES = ["algorithms", "python", "sql", "git", "architecture"]


def get_categories_for_direction(direction: str) -> List[str]:
    """Get relevant question categories for a given direction."""
    direction_lower = direction.lower()
    return DIRECTION_CATEGORIES_MAP.get(direction_lower, DEFAULT_CATEGORIES)


def select_questions_for_block(
    direction: str,
    level: str,
    count: int = 20,
    vacancy_skills: Optional[List[str]] = None
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Select questions for the block based on direction and level.
    
    Args:
        direction: Interview direction (backend, frontend, ml, etc.)
        level: Candidate level (junior, middle, senior)
        count: Number of questions to select
        vacancy_skills: Optional list of specific skills from vacancy
        
    Returns:
        Tuple of (selected questions, difficulty distribution)
    """
    # Get categories for this direction
    categories = get_categories_for_direction(direction)
    
    # Add vacancy-specific skills if provided
    if vacancy_skills:
        # Map skill IDs to categories
        for skill in vacancy_skills:
            skill_lower = skill.lower()
            # Check if skill matches any category
            for cat in ALL_QUESTIONS:
                if cat.get("category", "").lower() == skill_lower:
                    if skill_lower not in categories:
                        categories.append(skill_lower)
                    break
    
    # Filter questions by categories
    available_questions = [
        q for q in ALL_QUESTIONS 
        if q.get("category", "").lower() in [c.lower() for c in categories]
    ]
    
    if not available_questions:
        # Fallback to all questions if no matches
        available_questions = ALL_QUESTIONS.copy()
    
    # Determine difficulty distribution based on level
    if level == "junior":
        difficulty_dist = {"easy": 12, "medium": 6, "hard": 2}
    elif level == "middle":
        difficulty_dist = {"easy": 6, "medium": 10, "hard": 4}
    else:  # senior
        difficulty_dist = {"easy": 3, "medium": 9, "hard": 8}
    
    # Scale distribution to requested count
    total_dist = sum(difficulty_dist.values())
    difficulty_dist = {
        k: max(1, round(v * count / total_dist))
        for k, v in difficulty_dist.items()
    }
    
    # Adjust to exactly match count
    while sum(difficulty_dist.values()) > count:
        # Remove from largest category
        max_key = max(difficulty_dist, key=difficulty_dist.get)
        difficulty_dist[max_key] -= 1
    while sum(difficulty_dist.values()) < count:
        # Add to medium category
        difficulty_dist["medium"] += 1
    
    # Select questions by difficulty
    selected = []
    used_ids = set()
    
    for difficulty, target_count in difficulty_dist.items():
        # Filter by difficulty
        difficulty_questions = [
            q for q in available_questions 
            if q.get("difficulty", "").lower() == difficulty and q.get("id") not in used_ids
        ]
        
        # Shuffle and select
        random.shuffle(difficulty_questions)
        
        for q in difficulty_questions[:target_count]:
            selected.append(q)
            used_ids.add(q.get("id"))
    
    # Fill remaining slots if not enough questions
    remaining = count - len(selected)
    if remaining > 0:
        remaining_questions = [
            q for q in available_questions 
            if q.get("id") not in used_ids
        ]
        random.shuffle(remaining_questions)
        selected.extend(remaining_questions[:remaining])
    
    # Shuffle final selection
    random.shuffle(selected)
    
    return selected, difficulty_dist


async def start_question_block(
    interview_id: int,
    db: Session,
    question_count: int = 20
) -> Dict[str, Any]:
    """
    Start the question block for an interview.
    Creates QuestionBlock and QuestionAnswer records.
    
    Returns:
        Block info with first question
    """
    # Check if block already exists
    existing = db.query(QuestionBlock).filter(
        QuestionBlock.interview_id == interview_id
    ).first()
    
    if existing:
        if existing.status == "completed":
            return {"error": "Question block already completed", "block_id": existing.id}
        # Return existing block
        return await get_block_status(existing.id, db)
    
    # Get interview info
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return {"error": "Interview not found"}
    
    # Get vacancy skills if available
    vacancy_skills = []
    if interview.vacancy_id:
        skills = db.query(VacancySkill).filter(
            VacancySkill.vacancy_id == interview.vacancy_id
        ).all()
        vacancy_skills = [s.skill_id for s in skills]
    
    # Select questions
    questions, difficulty_dist = select_questions_for_block(
        direction=interview.direction,
        level=interview.selected_level,
        count=question_count,
        vacancy_skills=vacancy_skills
    )
    
    # Get unique categories
    selected_categories = list(set(q.get("category", "") for q in questions))
    
    # Create question block
    block = QuestionBlock(
        interview_id=interview_id,
        total_questions=len(questions),
        current_question_index=0,
        selected_categories=selected_categories,
        difficulty_distribution=difficulty_dist,
        status="in_progress",
        started_at=datetime.utcnow()
    )
    db.add(block)
    db.flush()  # Get block ID
    
    # Create question answer records
    for i, q in enumerate(questions):
        answer = QuestionAnswer(
            question_block_id=block.id,
            source_question_id=q.get("id"),
            question_order=i + 1,
            category=q.get("category", ""),
            difficulty=q.get("difficulty", "medium"),
            question_type=q.get("type", "theory"),
            question_text=q.get("question", ""),
            reference_answer=q.get("answer"),
            status="pending"
        )
        db.add(answer)
    
    db.commit()
    
    # Return block info with first question
    first_question = questions[0] if questions else None
    
    return {
        "block_id": block.id,
        "total_questions": len(questions),
        "current_index": 0,
        "categories": selected_categories,
        "difficulty_distribution": difficulty_dist,
        "status": "in_progress",
        "first_question": {
            "question_order": 1,
            "question_text": first_question.get("question", "") if first_question else "",
            "category": first_question.get("category", "") if first_question else "",
            "difficulty": first_question.get("difficulty", "") if first_question else "",
            "question_type": first_question.get("type", "") if first_question else ""
        } if first_question else None
    }


async def get_current_question(
    block_id: int,
    db: Session
) -> Optional[Dict[str, Any]]:
    """
    Get the current question for the block.
    Updates shown_at timestamp.
    """
    block = db.query(QuestionBlock).filter(QuestionBlock.id == block_id).first()
    if not block:
        return None
    
    if block.status == "completed":
        return {"status": "completed", "message": "All questions answered"}
    
    # Get current question
    current = db.query(QuestionAnswer).filter(
        QuestionAnswer.question_block_id == block_id,
        QuestionAnswer.question_order == block.current_question_index + 1
    ).first()
    
    if not current:
        return None
    
    # Update shown_at if first time
    if not current.shown_at:
        current.shown_at = datetime.utcnow()
        db.commit()
    
    return {
        "answer_id": current.id,
        "question_order": current.question_order,
        "total_questions": block.total_questions,
        "question_text": current.question_text,
        "category": current.category,
        "difficulty": current.difficulty,
        "question_type": current.question_type,
        "status": current.status,
        "shown_at": current.shown_at.isoformat() if current.shown_at else None
    }


async def submit_answer(
    answer_id: int,
    candidate_answer: str,
    db: Session,
    evaluation_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Submit an answer to a question.
    
    Args:
        answer_id: QuestionAnswer ID
        candidate_answer: Candidate's answer text
        db: Database session
        evaluation_score: Optional pre-computed score (0-100)
        
    Returns:
        Result with score and feedback
    """
    answer = db.query(QuestionAnswer).filter(QuestionAnswer.id == answer_id).first()
    if not answer:
        return {"error": "Answer not found"}
    
    if answer.status != "pending":
        return {"error": "Question already answered or skipped"}
    
    # Calculate response time
    now = datetime.utcnow()
    response_time = None
    if answer.shown_at:
        # Handle timezone-aware datetime
        shown_at = answer.shown_at
        if shown_at.tzinfo is not None:
            shown_at = shown_at.replace(tzinfo=None)
        response_time = (now - shown_at).total_seconds()
    
    # Update answer record
    answer.candidate_answer = candidate_answer
    answer.answered_at = now
    answer.response_time_seconds = response_time
    answer.status = "answered"
    
    # Get score multiplier (for retries)
    multiplier = answer.score_multiplier or 1.0
    
    # Set score if provided, applying multiplier
    if evaluation_score is not None:
        # Apply multiplier to score
        final_score = evaluation_score * multiplier
        answer.score = final_score
        answer.is_correct = final_score >= 70 * multiplier  # Adjusted threshold
    
    # Update block
    block = answer.question_block
    block.total_answered += 1
    
    # Move to next question
    block.current_question_index += 1
    
    # Check if block is completed
    if block.current_question_index >= block.total_questions:
        block.status = "completed"
        block.completed_at = now
        await _calculate_block_statistics(block, db)
    
    db.commit()
    
    return {
        "answer_id": answer.id,
        "status": answer.status,
        "score": answer.score,
        "is_correct": answer.is_correct,
        "response_time_seconds": response_time,
        "block_completed": block.status == "completed",
        "next_question_index": block.current_question_index if block.status != "completed" else None,
        "attempt_number": answer.attempt_number or 1,
        "score_multiplier": answer.score_multiplier or 1.0,
        "can_retry": True  # Allow retry after answer
    }


async def skip_question(
    answer_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Skip a question. Cannot go back.
    """
    answer = db.query(QuestionAnswer).filter(QuestionAnswer.id == answer_id).first()
    if not answer:
        return {"error": "Answer not found"}
    
    if answer.status != "pending":
        return {"error": "Question already answered or skipped"}
    
    now = datetime.utcnow()
    
    # Calculate time spent before skipping
    response_time = None
    if answer.shown_at:
        # Handle timezone-aware datetime
        shown_at = answer.shown_at
        if shown_at.tzinfo is not None:
            shown_at = shown_at.replace(tzinfo=None)
        response_time = (now - shown_at).total_seconds()
    
    # Update answer
    answer.status = "skipped"
    answer.answered_at = now
    answer.response_time_seconds = response_time
    answer.score = 0  # Skipped questions get 0
    answer.is_correct = False
    
    # Update block
    block = answer.question_block
    block.total_skipped += 1
    block.current_question_index += 1
    
    # Check if block is completed
    if block.current_question_index >= block.total_questions:
        block.status = "completed"
        block.completed_at = now
        await _calculate_block_statistics(block, db)
    
    db.commit()
    
    return {
        "answer_id": answer.id,
        "status": "skipped",
        "time_spent_seconds": response_time,
        "block_completed": block.status == "completed",
        "next_question_index": block.current_question_index if block.status != "completed" else None
    }


async def retry_answer(
    answer_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Allow retrying an answered question.
    Each retry halves the maximum possible score.
    """
    answer = db.query(QuestionAnswer).filter(QuestionAnswer.id == answer_id).first()
    if not answer:
        return {"error": "Answer not found"}
    
    if answer.status != "answered":
        return {"error": "Can only retry answered questions"}
    
    # Increment attempt and halve the score multiplier
    current_attempt = answer.attempt_number or 1
    new_attempt = current_attempt + 1
    new_multiplier = 1.0 / (2 ** (new_attempt - 1))  # 1.0, 0.5, 0.25, 0.125...
    
    # Reset answer for retry
    answer.status = "pending"
    answer.candidate_answer = None
    answer.score = None
    answer.is_correct = None
    answer.evaluation_details = None
    answer.feedback = None
    answer.attempt_number = new_attempt
    answer.score_multiplier = new_multiplier
    answer.shown_at = datetime.utcnow()
    answer.answered_at = None
    answer.response_time_seconds = None
    
    # Update block stats (decrement answered count)
    block = answer.question_block
    if block.total_answered > 0:
        block.total_answered -= 1
    
    db.commit()
    
    return {
        "answer_id": answer.id,
        "status": "pending",
        "attempt_number": new_attempt,
        "score_multiplier": new_multiplier,
        "max_score_percent": int(new_multiplier * 100),
        "question_text": answer.question_text,
        "category": answer.category,
        "difficulty": answer.difficulty,
        "question_type": answer.question_type,
        "question_order": answer.question_order
    }


async def _calculate_block_statistics(block: QuestionBlock, db: Session) -> None:
    """
    Calculate and update block statistics after completion.
    """
    answers = db.query(QuestionAnswer).filter(
        QuestionAnswer.question_block_id == block.id
    ).all()
    
    if not answers:
        return
    
    # Calculate averages
    scores = [a.score for a in answers if a.score is not None]
    times = [a.response_time_seconds for a in answers if a.response_time_seconds is not None]
    
    block.average_score = sum(scores) / len(scores) if scores else 0
    block.average_response_time = sum(times) / len(times) if times else 0
    block.total_correct = sum(1 for a in answers if a.is_correct)
    
    # Category breakdown
    category_scores = {}
    category_counts = {}
    for a in answers:
        if a.score is not None:
            cat = a.category
            if cat not in category_scores:
                category_scores[cat] = 0
                category_counts[cat] = 0
            category_scores[cat] += a.score
            category_counts[cat] += 1
    
    block.category_scores = {
        cat: round(category_scores[cat] / category_counts[cat], 1)
        for cat in category_scores if category_counts[cat] > 0
    }
    
    # Difficulty breakdown
    difficulty_scores = {}
    difficulty_counts = {}
    for a in answers:
        if a.score is not None:
            diff = a.difficulty
            if diff not in difficulty_scores:
                difficulty_scores[diff] = 0
                difficulty_counts[diff] = 0
            difficulty_scores[diff] += a.score
            difficulty_counts[diff] += 1
    
    block.difficulty_scores = {
        diff: round(difficulty_scores[diff] / difficulty_counts[diff], 1)
        for diff in difficulty_scores if difficulty_counts[diff] > 0
    }


async def get_block_status(
    block_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Get current status of the question block.
    """
    block = db.query(QuestionBlock).filter(QuestionBlock.id == block_id).first()
    if not block:
        return {"error": "Block not found"}
    
    return {
        "block_id": block.id,
        "status": block.status,
        "total_questions": block.total_questions,
        "current_index": block.current_question_index,
        "total_answered": block.total_answered,
        "total_skipped": block.total_skipped,
        "total_correct": block.total_correct,
        "average_score": block.average_score,
        "average_response_time": block.average_response_time,
        "category_scores": block.category_scores,
        "difficulty_scores": block.difficulty_scores,
        "started_at": block.started_at.isoformat() if block.started_at else None,
        "completed_at": block.completed_at.isoformat() if block.completed_at else None
    }


async def get_block_statistics(
    interview_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Get detailed statistics for the question block.
    Used for the final report.
    """
    block = db.query(QuestionBlock).filter(
        QuestionBlock.interview_id == interview_id
    ).first()
    
    if not block:
        return {"error": "Question block not found for this interview"}
    
    answers = db.query(QuestionAnswer).filter(
        QuestionAnswer.question_block_id == block.id
    ).order_by(QuestionAnswer.question_order).all()
    
    # Build detailed breakdown
    questions_breakdown = []
    for a in answers:
        questions_breakdown.append({
            "order": a.question_order,
            "category": a.category,
            "difficulty": a.difficulty,
            "question_type": a.question_type,
            "question_text": a.question_text[:100] + "..." if len(a.question_text) > 100 else a.question_text,
            "status": a.status,
            "score": a.score,
            "is_correct": a.is_correct,
            "response_time_seconds": a.response_time_seconds
        })
    
    return {
        "block_id": block.id,
        "interview_id": interview_id,
        "status": block.status,
        "summary": {
            "total_questions": block.total_questions,
            "answered": block.total_answered,
            "skipped": block.total_skipped,
            "correct": block.total_correct,
            "average_score": round(block.average_score, 1) if block.average_score else 0,
            "average_time_seconds": round(block.average_response_time, 1) if block.average_response_time else 0
        },
        "category_scores": block.category_scores or {},
        "difficulty_scores": block.difficulty_scores or {},
        "questions_breakdown": questions_breakdown
    }


# пидормот
