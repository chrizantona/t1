"""
Aggregate scoring and final grade calculation.
"""
from typing import Optional
from ..adaptive.engine import TaskResult, calculate_coding_score
from ..theory.engine import TheoryAnswer, calculate_theory_score
from .levels import (
    experience_to_grade_index,
    score_to_grade_index,
    grade_to_index,
    calc_final_grade_index,
    index_to_grade,
    GradeLevel
)


class FinalGradeCalculation:
    """Complete grade calculation with all components."""
    
    def __init__(
        self,
        years_of_experience: float,
        self_claimed_grade: str,
        task_results: list[TaskResult],
        theory_answers: list[TheoryAnswer]
    ):
        self.years_of_experience = years_of_experience
        self.self_claimed_grade = self_claimed_grade
        self.task_results = task_results
        self.theory_answers = theory_answers
        
        # Calculate components
        self.exp_index = experience_to_grade_index(years_of_experience)
        self.self_index = grade_to_index(self_claimed_grade)
        
        self.coding_score = calculate_coding_score(task_results)
        self.theory_score = calculate_theory_score(theory_answers)
        
        # Overall score: 70% coding + 30% theory
        self.overall_score = 0.7 * self.coding_score + 0.3 * self.theory_score
        
        # Performance grade index
        self.perf_index = score_to_grade_index(self.overall_score)
        
        # Final grade index
        self.final_grade_index = calc_final_grade_index(
            self.exp_index,
            self.self_index,
            self.perf_index
        )
        
        # Final grade string
        self.final_grade = index_to_grade(self.final_grade_index)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "years_of_experience": self.years_of_experience,
            "self_claimed_grade": self.self_claimed_grade,
            "exp_index": self.exp_index,
            "self_index": self.self_index,
            "coding_score": round(self.coding_score, 2),
            "theory_score": round(self.theory_score, 2),
            "overall_score": round(self.overall_score, 2),
            "perf_index": self.perf_index,
            "final_grade_index": self.final_grade_index,
            "final_grade": self.final_grade,
            "grade_breakdown": {
                "experience_contribution": f"{self.exp_index} (25% weight)",
                "self_assessment_contribution": f"{self.self_index} (15% weight)",
                "performance_contribution": f"{self.perf_index} (60% weight)",
            }
        }
    
    def get_grade_progress(self) -> dict:
        """Get progress towards next grade."""
        current_idx = self.final_grade_index
        next_idx = min(3, current_idx + 1)
        
        # Score thresholds: intern(0-30), junior(30-50), middle(50-75), senior(75+)
        score_thresholds = [0, 30, 50, 75, 100]
        current_threshold = score_thresholds[current_idx]
        next_threshold = score_thresholds[next_idx]
        
        if current_idx == 3:  # Already senior
            progress = 100.0
            points_to_next = 0
        else:
            range_size = next_threshold - current_threshold
            progress = ((self.overall_score - current_threshold) / range_size) * 100
            progress = max(0, min(100, progress))
            points_to_next = max(0, next_threshold - self.overall_score)
        
        return {
            "current_grade": self.final_grade,
            "next_grade": index_to_grade(next_idx) if current_idx < 3 else "senior",
            "progress_percent": round(progress, 1),
            "points_to_next_grade": round(points_to_next, 1),
            "current_score": round(self.overall_score, 2)
        }
