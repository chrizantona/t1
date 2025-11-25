"""
Theory questions engine.
Keyword-based scoring for theoretical questions.
"""
from typing import Literal
from pydantic import BaseModel


class TheoryAnswer(BaseModel):
    """Answer to a theory question."""
    question_id: int
    answer_text: str
    score: float = 0.0  # 0.0 to 1.0


def grade_theory_answer(
    answer: str,
    correct_keywords: list[str]
) -> float:
    """
    Grade theory answer based on keyword matching.
    
    Rules:
    - 0 keywords found → 0.0
    - All keywords found → 1.0
    - Partial match → 0.5
    
    Returns score 0.0 to 1.0
    """
    if not correct_keywords:
        return 1.0  # No keywords to check
    
    answer_lower = answer.lower()
    hits = sum(1 for kw in correct_keywords if kw.lower() in answer_lower)
    
    if hits == 0:
        return 0.0
    if hits == len(correct_keywords):
        return 1.0
    return 0.5


def calculate_theory_score(answers: list[TheoryAnswer]) -> float:
    """
    Calculate overall theory score (0-100) from all answers.
    
    Formula:
    theory_score = (sum of scores) / (number of questions) * 100
    """
    if not answers:
        return 0.0
    
    total_score = sum(a.score for a in answers)
    theory_score = (total_score / len(answers)) * 100.0
    
    return min(100.0, max(0.0, theory_score))


def should_ask_theory(
    task_was_strong_pass: bool,
    theory_questions_asked: int,
    max_theory_questions: int = 10
) -> bool:
    """
    Determine if we should ask theory questions after this task.
    
    Rules:
    - Only after strong pass
    - Not more than max_theory_questions total
    """
    return task_was_strong_pass and theory_questions_asked < max_theory_questions
