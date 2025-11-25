"""
Adaptive task generation service.
Generates tasks based on candidate level and performance.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from ..models.interview import Task
from .scibox_client import scibox_client


def generate_first_task(interview_id: int, level: str, direction: str, db: Session) -> Task:
    """
    Generate first task for interview using LLM.
    
    Args:
        interview_id: Interview ID
        level: Candidate level (junior/middle/senior)
        direction: Interview direction (backend/frontend/algorithms)
        db: Database session
    
    Returns:
        Created Task object
    """
    # Difficulty mapping
    difficulty_map = {
        "junior": "easy",
        "middle": "medium",
        "middle+": "medium",
        "senior": "hard"
    }
    difficulty = difficulty_map.get(level, "medium")
    
    # Prompt for task generation
    system_prompt = f"""Ты генератор задач для технических собеседований.
Создай задачу уровня {difficulty} по направлению {direction}.

Верни JSON с полями:
- title: название задачи
- description: детальное описание (что нужно сделать)
- visible_tests: список из 3 тестовых кейсов [{{input, expected_output, description}}]
- hidden_tests: список из 2 скрытых тестов
- category: категория (algorithms/data_structures/system_design)

Отвечай ТОЛЬКО валидным JSON."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Создай задачу для {level} разработчика"}
    ]
    
    response = scibox_client.code_completion(messages, temperature=0.7, max_tokens=1024)
    
    # Parse response
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        task_data = json.loads(response.strip())
    except json.JSONDecodeError:
        # Fallback task
        task_data = {
            "title": "Two Sum",
            "description": "Дан массив целых чисел и целевое значение. Верните индексы двух чисел, сумма которых равна целевому значению.",
            "visible_tests": [
                {"input": "[2,7,11,15], target=9", "expected_output": "[0,1]", "description": "Базовый случай"},
                {"input": "[3,2,4], target=6", "expected_output": "[1,2]", "description": "Другие индексы"},
                {"input": "[3,3], target=6", "expected_output": "[0,1]", "description": "Дубликаты"}
            ],
            "hidden_tests": [
                {"input": "[-1,-2,-3,-4,-5], target=-8", "expected_output": "[2,4]", "description": "Отрицательные числа"},
                {"input": "[1,2,3,4,5], target=10", "expected_output": "None", "description": "Нет решения"}
            ],
            "category": "algorithms"
        }
    
    # Create task
    task = Task(
        interview_id=interview_id,
        title=task_data.get("title", "Coding Task"),
        description=task_data.get("description", ""),
        difficulty=difficulty,
        category=task_data.get("category", "algorithms"),
        visible_tests=task_data.get("visible_tests", []),
        hidden_tests=task_data.get("hidden_tests", []),
        max_score=100.0,
        status="active"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


def generate_next_task(
    interview_id: int,
    previous_performance: float,
    current_level: str,
    direction: str,
    db: Session
) -> Task:
    """
    Generate next task based on previous performance.
    Adaptive difficulty adjustment.
    
    Args:
        interview_id: Interview ID
        previous_performance: Score from previous task (0-100)
        current_level: Current assessed level
        direction: Interview direction
        db: Database session
    
    Returns:
        Created Task object
    """
    # Adjust difficulty based on performance
    if previous_performance >= 85:
        # Increase difficulty
        difficulty = "hard" if current_level != "senior" else "hard"
    elif previous_performance >= 60:
        # Keep difficulty
        difficulty = "medium"
    else:
        # Decrease difficulty
        difficulty = "easy"
    
    return generate_first_task(interview_id, current_level, direction, db)


def calculate_task_score(
    passed_visible: int,
    total_visible: int,
    passed_hidden: int,
    total_hidden: int,
    execution_time_ms: float = None,
    max_score: float = 100.0
) -> float:
    """
    Calculate score for a task submission.
    
    Args:
        passed_visible: Number of visible tests passed
        total_visible: Total visible tests
        passed_hidden: Number of hidden tests passed
        total_hidden: Total hidden tests
        execution_time_ms: Execution time in milliseconds
        max_score: Maximum possible score (after hints penalty)
    
    Returns:
        Score (0-max_score)
    """
    if total_visible == 0 and total_hidden == 0:
        return 0.0
    
    # Visible tests worth 60%, hidden tests worth 40%
    visible_score = (passed_visible / total_visible) * 0.6 if total_visible > 0 else 0
    hidden_score = (passed_hidden / total_hidden) * 0.4 if total_hidden > 0 else 0
    
    total_score = (visible_score + hidden_score) * max_score
    
    return round(total_score, 2)

