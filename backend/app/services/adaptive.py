"""
Adaptive task generation service.
Uses predefined task pool for reliability.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..models.interview import Task
from .task_pool import get_task_sequence, get_task_by_difficulty


async def generate_first_task(interview_id: int, level: str, direction: str, db: Session) -> Task:
    """
    Generate first task from predefined pool.
    
    Args:
        interview_id: Interview ID
        level: Candidate level (intern/junior/middle/senior)
        direction: Interview direction
        db: Database session
    
    Returns:
        Created Task object
    """
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
    db: Session
) -> Task:
    """
    Generate next task from pool.
    
    Args:
        interview_id: Interview ID
        previous_performance: Score from previous task (0-100)
        current_level: Current assessed level
        direction: Interview direction
        db: Database session
    
    Returns:
        Created Task object
    """
    # Get count of existing tasks
    existing_tasks = db.query(Task).filter(Task.interview_id == interview_id).count()
    
    # Get full sequence for the level
    all_tasks = get_task_sequence(current_level, count=5)
    
    # Get next task from sequence
    if existing_tasks < len(all_tasks):
        task_data = all_tasks[existing_tasks]
    else:
        # If completed all tasks in sequence, repeat with harder difficulty
        task_data = get_task_by_difficulty("hard")
    
    difficulty = task_data["difficulty"]
    
    # Create task from pool
    task = Task(
        interview_id=interview_id,
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
