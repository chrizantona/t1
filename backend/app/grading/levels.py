"""
Grade level calculations.
Deterministic mapping between experience, scores, and grades.
"""
from typing import Literal

# Grade to index mapping
# intern(0) -> junior(1) -> middle(2) -> senior(3)
GRADE_TO_INDEX = {
    "intern": 0,
    "junior": 1,
    "middle": 2,
    "senior": 3,
}

INDEX_TO_GRADE = {v: k for k, v in GRADE_TO_INDEX.items()}

GradeLevel = Literal["intern", "junior", "middle", "senior"]


def experience_to_grade_index(years: float) -> int:
    """
    Convert years of experience to grade index.
    
    Rules:
    - 0 years (no exp) → intern (0)
    - < 1.5 years → junior (1)
    - 1.5-3.5 years → middle (2)
    - >= 3.5 years → senior (3)
    """
    if years < 0.5:
        return 0  # intern
    if years < 1.5:
        return 1  # junior
    if years < 3.5:
        return 2  # middle
    return 3  # senior


def score_to_grade_index(score: float) -> int:
    """
    Convert overall score (0-100) to grade index.
    
    Rules:
    - < 30 → intern (0)
    - 30-50 → junior (1)
    - 50-75 → middle (2)
    - >= 75 → senior (3)
    """
    if score < 30:
        return 0  # intern
    if score < 50:
        return 1  # junior
    if score < 75:
        return 2  # middle
    return 3  # senior


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
    
    Returns index 0-3.
    """
    if resume_index is None:
        resume_index = self_index
    
    grade_index = round(
        0.5 * exp_index +
        0.3 * self_index +
        0.2 * resume_index
    )
    
    return max(0, min(3, grade_index))


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
    
    Returns index 0-3.
    """
    idx = round(
        0.6 * perf_index +
        0.25 * exp_index +
        0.15 * self_index
    )
    
    return max(0, min(3, idx))


def grade_to_index(grade: str) -> int:
    """Convert grade string to index."""
    # Handle legacy grades
    grade_lower = grade.lower().replace("-", "_").replace(" ", "_")
    if grade_lower in ["junior_plus", "middle_minus"]:
        return 1  # junior
    if grade_lower in ["middle_plus", "senior_minus"]:
        return 2  # middle
    return GRADE_TO_INDEX.get(grade_lower, 2)  # default to middle


def index_to_grade(index: int) -> GradeLevel:
    """Convert index to grade string."""
    index = max(0, min(3, index))
    return INDEX_TO_GRADE[index]

# пидормот
