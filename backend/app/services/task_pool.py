"""
Task pool service.
Manages pre-generated tasks from database.
According to VibeCode_logic: we use pre-generated task pool, not runtime generation.
"""
from sqlalchemy.orm import Session
from typing import Optional
import random

from ..models.interview import Task, Interview
from ..adaptive.engine import DifficultyLevel


def get_next_task_from_pool(
    interview_id: int,
    difficulty: DifficultyLevel,
    track: str,
    db: Session
) -> Optional[Task]:
    """
    Get next task from pre-generated pool.
    
    Rules:
    - Select from tasks matching difficulty and track
    - Avoid tasks already used in this interview
    - Randomize to avoid repetition
    
    Args:
        interview_id: Current interview ID
        difficulty: Task difficulty (easy/middle/hard)
        track: Interview track (backend/frontend/etc)
        db: Database session
    
    Returns:
        Task object or None if no suitable tasks found
    """
    # Get already used task IDs
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return None
    
    used_task_ids = [t.id for t in interview.tasks]
    
    # Query available tasks
    query = db.query(Task).filter(
        Task.difficulty == difficulty,
        Task.category == track,
        Task.id.notin_(used_task_ids) if used_task_ids else True
    )
    
    available_tasks = query.all()
    
    if not available_tasks:
        # Fallback: try without track filter
        query = db.query(Task).filter(
            Task.difficulty == difficulty,
            Task.id.notin_(used_task_ids) if used_task_ids else True
        )
        available_tasks = query.all()
    
    if not available_tasks:
        return None
    
    # Randomly select one
    selected_task = random.choice(available_tasks)
    
    # Create a copy for this interview
    new_task = Task(
        interview_id=interview_id,
        title=selected_task.title,
        description=selected_task.description,
        difficulty=difficulty,
        category=track,
        visible_tests=selected_task.visible_tests,
        hidden_tests=selected_task.hidden_tests,
        max_score=100,
        actual_score=None,
        status="pending"
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return new_task


async def generate_or_select_task(
    interview_id: int,
    difficulty: DifficultyLevel,
    track: str,
    db: Session
) -> Task:
    """
    Get task from pool or generate if pool is empty.
    
    Priority:
    1. Try to get from pre-generated pool
    2. If pool empty, generate using LLM (fallback)
    """
    # Try pool first
    task = get_next_task_from_pool(interview_id, difficulty, track, db)
    
    if task:
        return task
    
    # Fallback: generate using LLM
    from .adaptive import generate_first_task
    
    # Map difficulty to grade level for LLM
    difficulty_to_level = {
        "easy": "junior",
        "middle": "middle",
        "hard": "senior"
    }
    level = difficulty_to_level.get(difficulty, "middle")
    
    return await generate_first_task(interview_id, level, track, db)
