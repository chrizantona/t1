"""
Grade level calculations.
Deterministic mapping between experience, scores, and grades.
"""
from typing import Literal

# Grade to index mapping
GRADE_TO_INDEX = {
    "junior": 0,
    "junior_plus": 1,
    "middle": 2,
    "middle_plus": 3,
    "senior": 4,
}

INDEX_TO_GRADE = {v: k for k, v in GRADE_TO_INDEX.items()}

GradeLevel = Literal["junior", "junior_plus", "middle", "middle_plus", "senior"]


def experience_to_grade_index(years: float) -> int:
    """
    Convert years of experience to grade index.
    
    Rules:
    - < 0.5 years → junior (0)
    - 0.5-1.5 → junior_plus (1)
    - 1.5-3.5 → middle (2)
    - 3.5-6 → middle_plus (3)
    - >= 6 → senior (4)
    """
    if years < 0.5:
        return 0
    if years < 1.5:
        return 1
    if years < 3.5:
        return 2
    if years < 6:
        return 3
    return 4


def score_to_grade_index(score: float) -> int:
    """
    Convert overall score (0-100) to grade index.
    
    Rules:
    - < 40 → junior (0)
    - 40-55 → junior_plus (1)
    - 55-70 → middle (2)
    - 70-85 → middle_plus (3)
    - >= 85 → senior (4)
    """
    if score < 40:
        return 0
    if score < 55:
        return 1
    if score < 70:
        return 2
    if score < 85:
        return 3
    return 4


def calc_start_grade_index(
    exp_index: int,
    self_index: int,
    resume_index: int | None = None
) -> int:
    """
    Calculate starting grade index based on:
    - Experience (50% weight)
    - Self-assessment (30% weight)
    - Resume grade (20% weight)
    
    Returns index 0-4.
    """
    if resume_index is None:
        resume_index = self_index
    
    grade_index = round(
        0.5 * exp_index +
        0.3 * self_index +
        0.2 * resume_index
    )
    
    return max(0, min(4, grade_index))


def calc_final_grade_index(
    exp_index: int,
    self_index: int,
    perf_index: int
) -> int:
    """
    Calculate final grade index based on:
    - Performance (60% weight) - most important
    - Experience (25% weight)
    - Self-assessment (15% weight)
    
    Returns index 0-4.
    """
    idx = round(
        0.6 * perf_index +
        0.25 * exp_index +
        0.15 * self_index
    )
    
    return max(0, min(4, idx))


def grade_to_index(grade: str) -> int:
    """Convert grade string to index."""
    return GRADE_TO_INDEX.get(grade, 2)  # default to middle


def index_to_grade(index: int) -> GradeLevel:
    """Convert index to grade string."""
    index = max(0, min(4, index))
    return INDEX_TO_GRADE[index]
