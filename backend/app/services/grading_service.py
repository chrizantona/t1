"""
Grading service integrating new deterministic logic.
"""
from sqlalchemy.orm import Session
from typing import Optional

from ..models.interview import Interview, Task, Submission, Hint
from ..grading.levels import (
    experience_to_grade_index,
    grade_to_index,
    calc_start_grade_index,
    index_to_grade
)
from ..grading.tracks import determine_track
from ..grading.aggregate import FinalGradeCalculation
from ..adaptive.engine import TaskResult, update_level_after_task, DifficultyLevel
from ..theory.engine import TheoryAnswer


def calculate_start_grade(
    years_of_experience: float,
    self_claimed_grade: str,
    resume_grade: Optional[str] = None
) -> dict:
    """
    Calculate starting grade for interview.
    
    Returns:
        {
            "start_grade": "middle",
            "start_grade_index": 2,
            "exp_index": 1,
            "self_index": 2,
            "resume_index": 2
        }
    """
    exp_index = experience_to_grade_index(years_of_experience)
    self_index = grade_to_index(self_claimed_grade)
    resume_index = grade_to_index(resume_grade) if resume_grade else None
    
    start_index = calc_start_grade_index(exp_index, self_index, resume_index)
    start_grade = index_to_grade(start_index)
    
    return {
        "start_grade": start_grade,
        "start_grade_index": start_index,
        "exp_index": exp_index,
        "self_index": self_index,
        "resume_index": resume_index or self_index
    }


def get_task_result_from_db(task: Task) -> TaskResult:
    """
    Convert database Task to TaskResult for grading.
    """
    # Count hints
    hints_soft = sum(1 for h in task.hints if h.hint_level == "soft")
    hints_medium = sum(1 for h in task.hints if h.hint_level == "medium")
    hints_hard = sum(1 for h in task.hints if h.hint_level == "hard")
    
    # Get test results from last submission
    visible_passed = 0
    visible_total = 0
    hidden_passed = 0
    hidden_total = 0
    
    if task.submissions:
        last_submission = task.submissions[-1]
        # Parse test results
        if hasattr(last_submission, 'test_results') and last_submission.test_results:
            results = last_submission.test_results
            visible_passed = results.get('visible_passed', 0)
            visible_total = results.get('visible_total', 0)
            hidden_passed = results.get('hidden_passed', 0)
            hidden_total = results.get('hidden_total', 0)
    
    # Fallback to task's visible/hidden tests
    if visible_total == 0 and task.visible_tests:
        visible_total = len(task.visible_tests)
    if hidden_total == 0 and task.hidden_tests:
        hidden_total = len(task.hidden_tests)
    
    # Normalize difficulty (medium -> middle)
    normalized_difficulty = task.difficulty
    if normalized_difficulty == "medium":
        normalized_difficulty = "middle"
    elif normalized_difficulty not in ["easy", "middle", "hard"]:
        normalized_difficulty = "middle"  # Default fallback
    
    return TaskResult(
        difficulty=normalized_difficulty,
        visible_passed=visible_passed,
        visible_total=visible_total,
        hidden_passed=hidden_passed,
        hidden_total=hidden_total,
        hints_soft=hints_soft,
        hints_medium=hints_medium,
        hints_hard=hints_hard,
        time_sec=0.0  # TODO: calculate from timestamps
    )


def calculate_next_difficulty(
    current_difficulty: DifficultyLevel,
    task: Task,
    user_clicked_next: bool = False
) -> DifficultyLevel:
    """
    Calculate next task difficulty based on current task result.
    """
    result = get_task_result_from_db(task)
    return update_level_after_task(current_difficulty, result, user_clicked_next)


def calculate_final_grade_for_interview(
    interview_id: int,
    db: Session
) -> dict:
    """
    Calculate final grade for completed interview.
    
    Returns complete grade calculation with all metrics.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise ValueError(f"Interview {interview_id} not found")
    
    # Get all task results
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    task_results = [get_task_result_from_db(task) for task in tasks]
    
    # Get theory answers (if implemented)
    theory_answers = []  # TODO: implement theory questions
    
    # Calculate final grade
    calc = FinalGradeCalculation(
        years_of_experience=interview.years_of_experience or 2.0,
        self_claimed_grade=interview.selected_level,
        task_results=task_results,
        theory_answers=theory_answers
    )
    
    # Update interview with results
    interview.overall_score = calc.overall_score
    interview.overall_grade = calc.final_grade
    db.commit()
    
    return {
        **calc.to_dict(),
        "grade_progress": calc.get_grade_progress(),
        "task_breakdown": [
            {
                "difficulty": r.difficulty,
                "visible_rate": r.visible_passed / max(1, r.visible_total),
                "total_rate": (r.visible_passed + r.hidden_passed) / max(1, r.visible_total + r.hidden_total),
                "hints_used": r.hints_soft + r.hints_medium + r.hints_hard
            }
            for r in task_results
        ]
    }
