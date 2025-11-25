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
    
    # Task variety categories
    categories = [
        "algorithms",
        "data_structures", 
        "system_design",
        "backend_api",
        "frontend_components",
        "database_queries",
        "optimization",
        "debugging"
    ]
    
    # Select appropriate category based on direction
    if direction == "backend":
        category_options = ["algorithms", "backend_api", "database_queries", "system_design"]
    elif direction == "frontend":
        category_options = ["algorithms", "frontend_components", "data_structures"]
    else:
        category_options = ["algorithms", "data_structures", "optimization"]
    
    import random
    selected_category = random.choice(category_options)
    
    # Prompt for task generation
    system_prompt = f"""Ты генератор задач для технических собеседований.
Создай РАЗНООБРАЗНУЮ задачу уровня {difficulty} по направлению {direction} в категории {selected_category}.

ВАЖНО: Задачи должны быть РАЗНЫМИ каждый раз! Не повторяй одни и те же задачи.

Примеры типов задач:
- Алгоритмические: поиск, сортировка, работа с деревьями
- Backend: REST API, аутентификация, кеширование  
- Frontend: компоненты, обработка событий, state management
- SQL: сложные запросы, join'ы, индексы
- Оптимизация: сложность, память, производительность

Верни JSON с полями:
- title: название задачи (на русском)
- description: детальное описание задачи (200-300 слов), что нужно реализовать
- visible_tests: массив из 3-4 тестовых кейсов [{{input, expected_output, description}}]
- hidden_tests: массив из 2-3 скрытых тестов [{{input, expected_output, description}}]
- category: категория задачи
- hints: массив с 3 подсказками разного уровня (light, medium, heavy)

Отвечай ТОЛЬКО валидным JSON."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Создай новую уникальную задачу для {level} разработчика по направлению {direction}. Сделай её интересной и практичной!"}
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
    Adaptive difficulty adjustment with VARIETY.
    
    Args:
        interview_id: Interview ID
        previous_performance: Score from previous task (0-100)
        current_level: Current assessed level
        direction: Interview direction
        db: Database session
    
    Returns:
        Created Task object
    """
    import random
    
    # Get existing tasks to avoid repetition
    existing_tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    used_categories = [t.category for t in existing_tasks]
    
    # Adjust difficulty based on performance
    if previous_performance >= 85:
        difficulty = "hard"
        adjusted_level = "senior"
    elif previous_performance >= 70:
        difficulty = "medium"
        adjusted_level = "middle+"
    elif previous_performance >= 50:
        difficulty = "medium"
        adjusted_level = current_level
    else:
        difficulty = "easy"
        adjusted_level = "junior"
    
    # Select category ensuring VARIETY
    if direction == "backend":
        all_categories = ["algorithms", "backend_api", "database_queries", "system_design", "caching", "security"]
    elif direction == "frontend":
        all_categories = ["algorithms", "frontend_components", "state_management", "performance", "accessibility"]
    else:
        all_categories = ["algorithms", "data_structures", "optimization", "sorting", "trees", "graphs"]
    
    # Prefer categories not used yet
    unused_categories = [c for c in all_categories if c not in used_categories]
    selected_category = random.choice(unused_categories if unused_categories else all_categories)
    
    # Create enhanced prompt for task generation
    difficulty_map = {
        "junior": "easy",
        "middle": "medium",
        "middle+": "medium",
        "senior": "hard"
    }
    task_difficulty = difficulty_map.get(adjusted_level, difficulty)
    
    # Generate task with specific category
    system_prompt = f"""Ты генератор задач для технических собеседований.
Создай УНИКАЛЬНУЮ задачу уровня {task_difficulty} по направлению {direction} в категории {selected_category}.

КРИТИЧЕСКИ ВАЖНО:
1. Задача ДОЛЖНА быть РАЗНОЙ каждый раз - используй разные алгоритмы, паттерны, API
2. Категория {selected_category} - сделай задачу именно по этой теме
3. Уже использованные категории: {', '.join(used_categories) if used_categories else 'нет'}

Типы задач по категориям:
- algorithms: Two Sum, Binary Search, Sliding Window, Kadane's Algorithm
- data_structures: Stack, Queue, LinkedList, Tree operations
- backend_api: REST endpoint with validation, Auth middleware, Rate limiter
- database_queries: Complex JOIN, Window functions, Indexing optimization
- frontend_components: Form validation, Infinite scroll, Drag-n-drop
- state_management: Redux-like store, Observer pattern
- caching: LRU Cache, Redis patterns, Memoization
- security: SQL injection prevention, XSS protection, JWT validation
- system_design: Rate limiter, URL shortener, Load balancer logic
- performance: Code optimization, Big O improvement, Memory usage
- trees: BST operations, Tree traversals, Lowest Common Ancestor
- graphs: DFS, BFS, Shortest path, Cycle detection

Верни JSON с полями:
- title: название задачи (на русском) - ДОЛЖНО быть уникальным!
- description: детальное описание (200-400 слов), что нужно реализовать
- visible_tests: массив из 3-4 тестов [{{input, expected_output, description}}]
- hidden_tests: массив из 3-4 скрытых тестов [{{input, expected_output, description}}]
- category: "{selected_category}"
- difficulty: "{task_difficulty}"

ВАЖНО: Тесты должны быть с РЕАЛЬНЫМИ данными, проверяемые кодом!

Отвечай ТОЛЬКО валидным JSON, без дополнительного текста."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Создай НОВУЮ задачу категории '{selected_category}' для {adjusted_level} разработчика. Прошлая производительность: {previous_performance}%. Будь креативным!"}
    ]
    
    response = scibox_client.code_completion(messages, temperature=0.8, max_tokens=1536)
    
    # Parse response
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        task_data = json.loads(response.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}")
        print(f"Response was: {response[:500]}")
        # Fallback with variety based on category
        fallback_tasks = {
            "algorithms": {
                "title": "Longest Substring Without Repeating Characters",
                "description": "Дана строка s, найдите длину самой длинной подстроки без повторяющихся символов. Используйте sliding window технику.",
                "visible_tests": [
                    {"input": "abcabcbb", "expected_output": "3", "description": "abc"},
                    {"input": "bbbbb", "expected_output": "1", "description": "b"},
                    {"input": "pwwkew", "expected_output": "3", "description": "wke"}
                ],
                "hidden_tests": [
                    {"input": "", "expected_output": "0", "description": "empty"},
                    {"input": "dvdf", "expected_output": "3", "description": "vdf"}
                ]
            },
            "backend_api": {
                "title": "Rate Limiter Implementation",
                "description": "Реализуйте rate limiter, который ограничивает количество запросов: максимум N запросов за M секунд. Используйте словарь для хранения временных меток.",
                "visible_tests": [
                    {"input": "{'n': 3, 'm': 10, 'requests': [1, 2, 3]}", "expected_output": "[True, True, True]", "description": "Within limit"},
                    {"input": "{'n': 2, 'm': 10, 'requests': [1, 2, 11]}", "expected_output": "[True, True, True]", "description": "After window"}
                ],
                "hidden_tests": [
                    {"input": "{'n': 2, 'm': 10, 'requests': [1, 2, 3]}", "expected_output": "[True, True, False]", "description": "Exceed limit"}
                ]
            },
            "database_queries": {
                "title": "SQL Query Builder",
                "description": "Создайте функцию, которая генерирует SQL-запрос с JOIN на основе входных параметров. Поддержка INNER JOIN, LEFT JOIN.",
                "visible_tests": [
                    {"input": "{'table1': 'users', 'table2': 'orders', 'join_type': 'INNER', 'on': 'user_id'}", "expected_output": "SELECT * FROM users INNER JOIN orders ON users.user_id = orders.user_id", "description": "Basic join"}
                ],
                "hidden_tests": [
                    {"input": "{'table1': 'products', 'table2': 'categories', 'join_type': 'LEFT', 'on': 'category_id'}", "expected_output": "SELECT * FROM products LEFT JOIN categories ON products.category_id = categories.category_id", "description": "Left join"}
                ]
            }
        }
        task_data = fallback_tasks.get(selected_category, fallback_tasks["algorithms"])
        task_data["category"] = selected_category
    
    # Create task
    task = Task(
        interview_id=interview_id,
        title=task_data.get("title", "Coding Task"),
        description=task_data.get("description", "Solve the coding problem"),
        difficulty=task_difficulty,
        category=task_data.get("category", selected_category),
        visible_tests=task_data.get("visible_tests", []),
        hidden_tests=task_data.get("hidden_tests", []),
        max_score=100.0,
        status="active"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


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

