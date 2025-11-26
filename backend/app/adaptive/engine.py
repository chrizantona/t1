"""
Adaptive difficulty engine.
Determines when to increase/decrease task difficulty.
"""
from typing import Literal
from pydantic import BaseModel

DifficultyLevel = Literal["easy", "medium", "middle", "hard"]


class TaskResult(BaseModel):
    """Result of a single task attempt."""
    difficulty: DifficultyLevel
    visible_passed: int
    visible_total: int
    hidden_passed: int
    hidden_total: int
    hints_soft: int = 0
    hints_medium: int = 0
    hints_hard: int = 0
    time_sec: float = 0.0


def is_strong_pass(result: TaskResult) -> bool:
    """
    Check if result is a strong pass (candidate did very well).
    
    Rules:
    - For easy/middle:
      - All visible tests passed (100%)
      - Total pass rate >= 90%
      - No hard hints, max 1 medium hint
    
    - For hard:
      - All visible tests passed (100%)
      - Total pass rate >= 75%
    """
    visible_rate = result.visible_passed / max(1, result.visible_total)
    total_rate = (result.visible_passed + result.hidden_passed) / max(
        1, result.visible_total + result.hidden_total
    )
    
    if result.difficulty in ("easy", "middle"):
        return (
            visible_rate == 1.0 and
            total_rate >= 0.9 and
            result.hints_hard == 0 and
            result.hints_medium <= 1
        )
    else:  # hard
        return visible_rate == 1.0 and total_rate >= 0.75


def is_fail(result: TaskResult) -> bool:
    """
    Check if result is a fail (candidate struggled).
    
    Rules:
    - Visible pass rate < 60% OR
    - Total pass rate < 50%
    """
    visible_rate = result.visible_passed / max(1, result.visible_total)
    total_rate = (result.visible_passed + result.hidden_passed) / max(
        1, result.visible_total + result.hidden_total
    )
    
    return visible_rate < 0.6 or total_rate < 0.5


def level_up(level: DifficultyLevel) -> DifficultyLevel:
    """Increase difficulty level."""
    if level == "easy":
        return "middle"
    if level == "middle":
        return "hard"
    return "hard"


def level_down(level: DifficultyLevel) -> DifficultyLevel:
    """Decrease difficulty level."""
    if level == "hard":
        return "middle"
    if level == "middle":
        return "easy"
    return "easy"


def update_level_after_task(
    current_level: DifficultyLevel,
    result: TaskResult,
    user_clicked_next: bool
) -> DifficultyLevel:
    """
    Update difficulty level after task completion.
    
    Rules:
    - Strong pass → level up
    - Fail + user clicked next → level down
    - Otherwise → stay same
    """
    if is_strong_pass(result):
        return level_up(current_level)
    
    if is_fail(result) and user_clicked_next:
        return level_down(current_level)
    
    return current_level


def calculate_task_score(result: TaskResult) -> float:
    """
    Calculate weighted score for a single task.
    
    Returns score in "conditional units" (0.0 to difficulty_weight).
    """
    # Difficulty weights
    difficulty_weight = {
        "easy": 1.0,
        "middle": 2.0,
        "hard": 3.0,
    }[result.difficulty]
    
    # Pass rates
    visible_rate = result.visible_passed / max(1, result.visible_total)
    hidden_rate = result.hidden_passed / max(1, result.hidden_total)
    total_rate = (result.visible_passed + result.hidden_passed) / max(
        1, result.visible_total + result.hidden_total
    )
    
    # Hint penalties
    hint_penalty = (
        0.10 * result.hints_soft +
        0.20 * result.hints_medium +
        0.35 * result.hints_hard
    )
    hint_penalty = min(hint_penalty, 0.7)  # Max 70% penalty
    
    # Effective rate after penalties
    effective_rate = max(0.0, total_rate * (1.0 - hint_penalty))
    
    # Weighted score
    task_score_unit = effective_rate * difficulty_weight
    
    return task_score_unit


def calculate_coding_score(results: list[TaskResult]) -> float:
    """
    Calculate overall coding score (0-100) from all task results.
    
    Formula:
    coding_score = (sum of weighted scores) / (sum of weights) * 100
    """
    if not results:
        return 0.0
    
    total_score = sum(calculate_task_score(r) for r in results)
    total_weight = sum({
        "easy": 1.0,
        "middle": 2.0,
        "hard": 3.0,
    }[r.difficulty] for r in results)
    
    coding_score = (total_score / max(1, total_weight)) * 100.0
    
    return min(100.0, max(0.0, coding_score))
