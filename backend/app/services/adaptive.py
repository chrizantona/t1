"""
Adaptive task generation service.
Uses predefined task pool for reliability.

ADAPTIVITY LOGIC (from ТЗ):
- If candidate scores > 70 and ai_style_score < 0.5 -> level UP
- junior -> middle, middle -> senior
- This affects task selection for next task
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, Tuple

from ..models.interview import Task, Interview
from .task_pool import get_task_sequence, get_task_by_difficulty

# Level progression map
LEVEL_UP_MAP = {
    "intern": "junior",
    "junior": "junior+",
    "junior+": "middle",
    "middle": "middle+",
    "middle+": "senior",
    "senior": "senior"  # Can't go higher
}

LEVEL_DOWN_MAP = {
    "senior": "middle+",
    "middle+": "middle",
    "middle": "junior+",
    "junior+": "junior",
    "junior": "intern",
    "intern": "intern"  # Can't go lower
}

# Thresholds for level adjustment
LEVEL_UP_THRESHOLD = 70  # Score >= 70 to level up
LEVEL_DOWN_THRESHOLD = 30  # Score <= 30 to level down
AI_STYLE_MAX_FOR_LEVEL_UP = 0.5  # Must have low AI suspicion to level up


def should_level_up(score: float, ai_style_score: float = 0.0) -> bool:
    """Check if candidate should be leveled up based on performance."""
    return score >= LEVEL_UP_THRESHOLD and ai_style_score < AI_STYLE_MAX_FOR_LEVEL_UP


def should_level_down(score: float) -> bool:
    """Check if candidate should be leveled down based on performance."""
    return score <= LEVEL_DOWN_THRESHOLD


def adjust_level(current_level: str, score: float, ai_style_score: float = 0.0) -> Tuple[str, str]:
    """
    Adjust level based on performance.
    
    Returns:
        Tuple of (new_level, change_description)
    """
    if should_level_up(score, ai_style_score):
        new_level = LEVEL_UP_MAP.get(current_level, current_level)
        if new_level != current_level:
            return new_level, f"Уровень повышен: {current_level} → {new_level}"
    elif should_level_down(score):
        new_level = LEVEL_DOWN_MAP.get(current_level, current_level)
        if new_level != current_level:
            return new_level, f"Уровень понижен: {current_level} → {new_level}"
    
    return current_level, None


async def generate_first_task(interview_id: int, level: str, direction: str, db: Session) -> Task:
    """
    Generate first task from predefined pool.
    Also sets initial effective_level on Interview.
    
    Args:
        interview_id: Interview ID
        level: Candidate level (intern/junior/middle/senior)
        direction: Interview direction
        db: Database session
    
    Returns:
        Created Task object
    """
    # Set initial effective level
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview:
        interview.effective_level = level
    
    # Get first task from pool
    tasks_sequence = get_task_sequence(level, count=1)
    
    if not tasks_sequence:
        # Fallback - should never happen
        from .task_pool import TASK_POOL
        task_data = TASK_POOL["two_sum"]
    else:
        task_data = tasks_sequence[0]
    
    difficulty = task_data["difficulty"]
    
    # Create task from pool
    task = Task(
        interview_id=interview_id,
        task_order=1,
        title=task_data["title"],
        description=task_data["description"],
        difficulty=difficulty,
        category=task_data["category"],
        visible_tests=task_data["visible_tests"],
        hidden_tests=task_data["hidden_tests"],
        max_score=100.0,
        status="active"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


async def generate_next_task(
    interview_id: int,
    previous_performance: float,
    current_level: str,
    direction: str,
    db: Session,
    ai_style_score: float = 0.0
) -> Task:
    """
    Generate next task from pool with ADAPTIVE level adjustment.
    
    According to ТЗ:
    - If score > 70 and ai_style_score < 0.5 -> level UP
    - Use new level for task selection
    
    Args:
        interview_id: Interview ID
        previous_performance: Score from previous task (0-100)
        current_level: Current assessed level
        direction: Interview direction
        db: Database session
        ai_style_score: AI similarity score (0-1)
    
    Returns:
        Created Task object with level adjustment info
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    # Get effective level (may have been adjusted)
    effective_level = interview.effective_level if interview and interview.effective_level else current_level
    
    # Check for level adjustment based on previous performance
    new_level, change_message = adjust_level(effective_level, previous_performance, ai_style_score)
    
    # Update effective level on interview
    if interview and new_level != effective_level:
        interview.effective_level = new_level
        # Store level change in stage_results
        if interview.stage_results is None:
            interview.stage_results = []
        interview.stage_results.append({
            "type": "level_change",
            "from": effective_level,
            "to": new_level,
            "reason": change_message,
            "triggered_by_score": previous_performance
        })
    
    # Get count of existing tasks
    existing_tasks = db.query(Task).filter(Task.interview_id == interview_id).count()
    
    # Get full sequence for the NEW level
    all_tasks = get_task_sequence(new_level, count=5)
    
    # Get next task from sequence
    if existing_tasks < len(all_tasks):
        task_data = all_tasks[existing_tasks]
    else:
        # If completed all tasks in sequence, get harder task
        task_data = get_task_by_difficulty("hard" if new_level in ["middle+", "senior"] else "medium")
    
    difficulty = task_data["difficulty"]
    
    # Create task from pool
    task = Task(
        interview_id=interview_id,
        task_order=existing_tasks + 1,
        title=task_data["title"],
        description=task_data["description"],
        difficulty=difficulty,
        category=task_data["category"],
        visible_tests=task_data["visible_tests"],
        hidden_tests=task_data["hidden_tests"],
        max_score=100.0,
        status="active"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Attach level change info to task (for frontend notification)
    task._level_changed = new_level != effective_level
    task._level_change_message = change_message
    task._new_level = new_level
    
    return task


def calculate_task_score(
    passed_visible: int = 0,
    total_visible: int = 1,
    passed_hidden: int = 0,
    total_hidden: int = 1,
    execution_time_ms: int = None,
    max_score: float = 100.0,
    task: "Task" = None
) -> float:
    """
    Calculate score for a task based on test results.
    
    Args:
        passed_visible: Number of visible tests passed
        total_visible: Total visible tests
        passed_hidden: Number of hidden tests passed
        total_hidden: Total hidden tests
        execution_time_ms: Execution time (unused for now)
        max_score: Maximum possible score
        task: Optional Task object (legacy support)
    
    Returns:
        Calculated score (0 to max_score)
    """
    # If Task object provided, extract data from it
    if task is not None:
        visible_passed = 0
        hidden_passed = 0
        
        for sub in task.submissions:
            if hasattr(sub, 'passed_visible') and sub.passed_visible:
                visible_passed = max(visible_passed, sub.passed_visible)
            if hasattr(sub, 'passed_hidden') and sub.passed_hidden:
                hidden_passed = max(hidden_passed, sub.passed_hidden)
        
        total_visible = len(task.visible_tests) if task.visible_tests else 1
        total_hidden = len(task.hidden_tests) if task.hidden_tests else 1
        passed_visible = visible_passed
        passed_hidden = hidden_passed
        max_score = task.max_score if task.max_score else 100.0
    
    # Avoid division by zero
    total_visible = max(total_visible, 1)
    total_hidden = max(total_hidden, 1)
    
    # 60% for visible tests, 40% for hidden tests
    visible_score = (passed_visible / total_visible) * 0.6
    hidden_score = (passed_hidden / total_hidden) * 0.4
    
    return (visible_score + hidden_score) * max_score
