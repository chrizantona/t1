"""
Interview Flow Service - управление новым flow собеседования
Этап 1: 3 задачи (easy → medium → hard)
Этап 2: Теоретические вопросы (10-25, адаптивно)
"""
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.interview import Interview, Task, TheoryAnswer, Submission
from ..prompts.task_selector import TASK_SELECTOR_SYSTEM, TASK_SELECTOR_USER
from ..prompts.solution_questions import (
    SOLUTION_QUESTIONS_SYSTEM, SOLUTION_QUESTIONS_USER,
    SOLUTION_ANSWER_EVALUATOR_SYSTEM, SOLUTION_ANSWER_EVALUATOR_USER
)
from ..prompts.theory_evaluator import (
    THEORY_SELECTOR_SYSTEM, THEORY_SELECTOR_USER,
    THEORY_ANSWER_EVALUATOR_SYSTEM, THEORY_ANSWER_EVALUATOR_USER,
    INTERVIEW_SCORER_SYSTEM, INTERVIEW_SCORER_USER
)
from .scibox_client import scibox_client

logger = logging.getLogger(__name__)

# Category mapping for directions
DIRECTION_CATEGORIES = {
    "backend": ["backend", "python", "fastapi", "sql", "sqlalchemy", "docker", "architecture", "async", "algorithms"],
    "frontend": ["frontend", "algorithms"],
    "fullstack": ["backend", "frontend", "sql", "docker", "algorithms"],
    "ml": ["data-science", "python", "sql", "algorithms"],
    "data-science": ["data-science", "python", "sql", "algorithms"],
    "data-engineer": ["sql", "python", "docker", "airflow", "architecture"],
    "devops": ["docker", "linux", "architecture"],
    "algorithms": ["algorithms"],
    "mobile": ["frontend", "algorithms"],
    "go": ["go", "architecture", "sql", "docker", "algorithms"]
}


def load_questions_db() -> List[Dict[str, Any]]:
    """Load questions from JSON file."""
    import os
    questions_path = os.path.join(
        os.path.dirname(__file__), 
        "../../../tasks_base/questions.json"
    )
    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_questions_for_direction(questions: List[Dict], direction: str) -> List[Dict]:
    """Filter questions relevant to the candidate's direction."""
    categories = DIRECTION_CATEGORIES.get(direction, ["algorithms"])
    return [q for q in questions if q.get("category") in categories]


async def select_three_tasks(
    direction: str,
    level: str,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Select 3 appropriate tasks for the interview.
    Uses fast deterministic selection (no LLM) for quick start.
    """
    questions = load_questions_db()
    
    # Filter coding questions for the direction
    coding_questions = [
        q for q in questions 
        if q.get("type") == "coding" or q.get("category") == "algorithms"
    ]
    relevant_questions = filter_questions_for_direction(coding_questions, direction)
    
    # If not enough relevant questions, add algorithms
    if len(relevant_questions) < 10:
        algo_questions = [q for q in questions if q.get("category") == "algorithms"]
        relevant_questions.extend([q for q in algo_questions if q not in relevant_questions])
    
    # Use fast deterministic selection (no LLM call)
    return _fallback_task_selection(relevant_questions, level)


def _fallback_task_selection(questions: List[Dict], level: str) -> List[Dict]:
    """Fallback task selection without LLM."""
    # Group by difficulty
    easy = [q for q in questions if q.get("difficulty") == "easy"]
    medium = [q for q in questions if q.get("difficulty") == "medium"]
    hard = [q for q in questions if q.get("difficulty") == "hard"]
    
    # Level-based selection
    level_mapping = {
        "intern": (easy[:1] or medium[:1], easy[1:2] or medium[:1], medium[:1] or hard[:1]),
        "junior": (easy[:1] or medium[:1], medium[:1] or easy[1:2], medium[1:2] or hard[:1]),
        "junior+": (easy[:1], medium[:1], medium[1:2] or hard[:1]),
        "middle": (easy[:1] or medium[:1], medium[:1], hard[:1] or medium[1:2]),
        "middle+": (medium[:1], medium[1:2] or hard[:1], hard[:1] or hard[1:2]),
        "senior": (medium[:1], hard[:1], hard[1:2] or hard[:1])
    }
    
    task1, task2, task3 = level_mapping.get(level, level_mapping["middle"])
    
    selected = []
    for i, task_list in enumerate([task1, task2, task3], 1):
        if task_list:
            q = task_list[0]
            selected.append({
                "question_id": q["id"],
                "order": i,
                "difficulty_label": q.get("difficulty", "medium"),
                "reason": "Автоматический подбор"
            })
    
    return selected


async def generate_adaptive_task(
    interview_id: int,
    direction: str,
    difficulty: str,
    task_order: int,
    db: Session
) -> Task:
    """
    Generate a SINGLE task adaptively based on difficulty.
    Used for real-time task generation after each completion.
    """
    from .task_pool import get_task_by_difficulty
    
    # Get task from pool based on difficulty
    task_data = get_task_by_difficulty(difficulty, task_order)
    
    task = Task(
        interview_id=interview_id,
        task_order=task_order,
        title=task_data["title"],
        description=task_data["description"],
        difficulty=task_data["difficulty"],
        category=task_data.get("category", "algorithms"),
        visible_tests=task_data.get("visible_tests", []),
        hidden_tests=task_data.get("hidden_tests", []),
        max_score=100.0,
        status="active"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    logger.info(f"Generated adaptive task #{task_order} (difficulty={difficulty}) for interview {interview_id}")
    return task


async def create_interview_tasks(
    interview_id: int,
    direction: str,
    level: str,
    db: Session
) -> List[Task]:
    """
    Create 3 tasks for the interview using TASK_POOL for reliable tests.
    """
    from .task_pool import get_task_sequence
    
    # Get 3 tasks from the pool based on level
    pool_tasks = get_task_sequence(level, count=3)
    
    created_tasks = []
    
    for i, task_data in enumerate(pool_tasks, 1):
        task = Task(
            interview_id=interview_id,
            task_order=i,
            title=task_data["title"],
            description=task_data["description"],
            difficulty=task_data["difficulty"],
            category=task_data.get("category", "algorithms"),
            visible_tests=task_data.get("visible_tests", []),
            hidden_tests=task_data.get("hidden_tests", []),
            max_score=100.0,
            status="active" if i == 1 else "pending"
        )
        
        db.add(task)
        created_tasks.append(task)
    
    db.commit()
    for task in created_tasks:
        db.refresh(task)
    
    logger.info(f"Created {len(created_tasks)} tasks for interview {interview_id}")
    return created_tasks


# Predefined tests for common algorithm tasks
TASK_TESTS = {
    1: {  # Two Sum
        "visible": [
            {"input": "[2,7,11,15], 9", "expected_output": "[0, 1]", "description": "Базовый пример"},
            {"input": "[3,2,4], 6", "expected_output": "[1, 2]", "description": "Элементы не в начале"},
            {"input": "[3,3], 6", "expected_output": "[0, 1]", "description": "Одинаковые элементы"}
        ],
        "hidden": [
            {"input": "[1,2,3,4,5], 9", "expected_output": "[3, 4]", "description": "Последние элементы"},
            {"input": "[1], 1", "expected_output": "None", "description": "Один элемент"}
        ]
    },
    2: {  # Palindrome
        "visible": [
            {"input": "A man a plan a canal Panama", "expected_output": "True", "description": "Классический палиндром"},
            {"input": "race a car", "expected_output": "False", "description": "Не палиндром"},
            {"input": " ", "expected_output": "True", "description": "Пустая строка"}
        ],
        "hidden": [
            {"input": "ab_a", "expected_output": "True", "description": "Спецсимволы"},
            {"input": "0P", "expected_output": "False", "description": "Цифры и буквы"}
        ]
    },
    3: {  # Binary Search
        "visible": [
            {"input": "[-1,0,3,5,9,12], 9", "expected_output": "4", "description": "Элемент в середине"},
            {"input": "[-1,0,3,5,9,12], 2", "expected_output": "-1", "description": "Элемент не найден"},
            {"input": "[5], 5", "expected_output": "0", "description": "Один элемент"}
        ],
        "hidden": [
            {"input": "[1,2,3,4,5,6,7,8,9,10], 1", "expected_output": "0", "description": "Первый элемент"},
            {"input": "[1,2,3,4,5,6,7,8,9,10], 10", "expected_output": "9", "description": "Последний элемент"}
        ]
    },
    5: {  # Kadane - Max Subarray Sum
        "visible": [
            {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6", "description": "Подмассив [4,-1,2,1]"},
            {"input": "[1]", "expected_output": "1", "description": "Один элемент"},
            {"input": "[5,4,-1,7,8]", "expected_output": "23", "description": "Весь массив"}
        ],
        "hidden": [
            {"input": "[-1,-2,-3]", "expected_output": "-1", "description": "Все отрицательные"},
            {"input": "[0,0,0]", "expected_output": "0", "description": "Все нули"}
        ]
    },
    6: {  # Longest Subarray with Sum K
        "visible": [
            {"input": "[1,2,3,1,1,1,1], 3", "expected_output": "3", "description": "Подмассив [1,1,1]"},
            {"input": "[1,2,3], 6", "expected_output": "3", "description": "Весь массив"},
            {"input": "[1,-1,5,-2,3], 3", "expected_output": "4", "description": "С отрицательными"}
        ],
        "hidden": [
            {"input": "[1,1,1,1,1], 2", "expected_output": "2", "description": "Много одинаковых"},
            {"input": "[0,0,0,0], 0", "expected_output": "4", "description": "Нули"}
        ]
    }
}


def get_tests_for_question(question_id: int, question: dict) -> tuple:
    """Get tests for a question - predefined or generated defaults."""
    if question_id in TASK_TESTS:
        tests = TASK_TESTS[question_id]
        return tests.get("visible", []), tests.get("hidden", [])
    
    # For theory questions - no tests needed
    if question.get("type") == "theory":
        return [], []
    
    # Default tests for coding questions without predefined tests
    return [
        {"input": "example", "expected_output": "result", "description": "Пример (проверьте вывод вручную)"}
    ], []


async def generate_solution_questions(
    interview_id: int,
    db: Session
) -> List[TheoryAnswer]:
    """
    Generate questions about candidate's solutions (algorithm + complexity).
    For each solved task: 2 questions. For unsolved: skip and score 0.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    tasks = db.query(Task).filter(Task.interview_id == interview_id).order_by(Task.task_order).all()
    
    # Build tasks and solutions summary for LLM
    tasks_and_solutions = []
    for task in tasks:
        # Get best submission
        best_submission = db.query(Submission).filter(
            Submission.task_id == task.id
        ).order_by(Submission.created_at.desc()).first()
        
        is_solved = task.status == "completed" or (
            best_submission and 
            best_submission.passed_visible == best_submission.total_visible and
            best_submission.passed_hidden == best_submission.total_hidden
        )
        
        code = best_submission.code if best_submission else ""
        
        tasks_and_solutions.append({
            "task_id": task.id,
            "task_order": task.task_order,
            "title": task.title,
            "description": task.description,
            "solved": is_solved,
            "code": code if is_solved else ""
        })
        
        # Save final code to task
        if best_submission:
            task.final_code = best_submission.code
            db.commit()
    
    # Format for LLM
    formatted_tasks = "\n\n".join([
        f"Задача {t['task_order']}: {t['title']}\n"
        f"Описание: {t['description']}\n"
        f"Решена: {'Да' if t['solved'] else 'Нет'}\n"
        f"Код решения:\n```\n{t['code']}\n```" if t['solved'] else f"Код: Не решена"
        for t in tasks_and_solutions
    ])
    
    # Call LLM to generate questions
    messages = [
        {"role": "system", "content": SOLUTION_QUESTIONS_SYSTEM},
        {"role": "user", "content": SOLUTION_QUESTIONS_USER.format(
            tasks_and_solutions=formatted_tasks
        )}
    ]
    
    created_questions = []
    question_order = 1
    
    try:
        response = await scibox_client.chat_completion(messages, temperature=0.3, max_tokens=2048)
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            result = json.loads(json_match.group())
            
            for task_q in result.get("task_questions", []):
                task_id = task_q.get("task_id")
                solved = task_q.get("solved", False)
                
                if not solved:
                    # Create skipped questions with 0 score
                    for q_type in ["algorithm", "complexity"]:
                        theory_answer = TheoryAnswer(
                            interview_id=interview_id,
                            question_type=f"solution_{q_type}",
                            question_text=f"Вопрос о {'алгоритме' if q_type == 'algorithm' else 'сложности'} решения задачи",
                            related_task_id=task_id,
                            question_order=question_order,
                            status="skipped",
                            score=0
                        )
                        db.add(theory_answer)
                        created_questions.append(theory_answer)
                        question_order += 1
                else:
                    # Create actual questions for solved tasks
                    for q in task_q.get("questions", []):
                        theory_answer = TheoryAnswer(
                            interview_id=interview_id,
                            question_type=f"solution_{q.get('type', 'algorithm')}",
                            question_text=q.get("question", ""),
                            reference_answer=q.get("reference_answer", ""),
                            evaluation_details={"key_points": q.get("key_points", [])},
                            related_task_id=task_id,
                            question_order=question_order,
                            status="pending"
                        )
                        db.add(theory_answer)
                        created_questions.append(theory_answer)
                        question_order += 1
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to generate solution questions: {e}")
        # Fallback: create generic questions
        for task in tasks:
            is_solved = task.status == "completed"
            
            # Algorithm question
            theory_answer = TheoryAnswer(
                interview_id=interview_id,
                question_type="solution_algorithm",
                question_text=f"Объясните алгоритм вашего решения задачи '{task.title}'",
                related_task_id=task.id,
                question_order=question_order,
                status="skipped" if not is_solved else "pending",
                score=0 if not is_solved else None
            )
            db.add(theory_answer)
            created_questions.append(theory_answer)
            question_order += 1
            
            # Complexity question
            theory_answer = TheoryAnswer(
                interview_id=interview_id,
                question_type="solution_complexity",
                question_text=f"Какова временная и пространственная сложность вашего решения задачи '{task.title}'?",
                related_task_id=task.id,
                question_order=question_order,
                status="skipped" if not is_solved else "pending",
                score=0 if not is_solved else None
            )
            db.add(theory_answer)
            created_questions.append(theory_answer)
            question_order += 1
        
        db.commit()
    
    return created_questions


async def get_next_theory_question(
    interview_id: int,
    db: Session
) -> Optional[Dict[str, Any]]:
    """
    Get next theory question using adaptive selection.
    Returns None if interview should end.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    # Get all answers so far
    all_answers = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id
    ).order_by(TheoryAnswer.question_order).all()
    
    # Count answered questions
    answered = [a for a in all_answers if a.status in ["answered", "skipped"]]
    pending = [a for a in all_answers if a.status == "pending"]
    
    # Check early stop conditions
    min_questions = 10
    max_questions = 25
    
    if len(answered) >= max_questions:
        return None  # Max reached
    
    # First return any pending solution questions
    if pending:
        next_q = pending[0]
        return {
            "id": next_q.id,
            "question_order": next_q.question_order,
            "question_type": next_q.question_type,
            "question_text": next_q.question_text,
            "related_task_id": next_q.related_task_id,
            "total_answered": len(answered),
            "max_questions": max_questions
        }
    
    # All solution questions answered, now select theory questions
    # Calculate current performance
    scored_answers = [a for a in answered if a.score is not None and a.status == "answered"]
    avg_score = sum(a.score for a in scored_answers) / len(scored_answers) if scored_answers else 50
    
    # Check for early stop
    if len(answered) >= min_questions:
        if interview.confidence_score >= 80 and avg_score >= 75:
            # High performer, can stop early
            return None
        if interview.confidence_score >= 70 and avg_score <= 30:
            # Low performer pattern confirmed
            return None
    
    # Get asked question IDs
    asked_ids = [a.question_id for a in all_answers if a.question_id]
    
    # Load theory questions for direction
    questions = load_questions_db()
    theory_questions = [
        q for q in questions 
        if q.get("type") == "theory" and q["id"] not in asked_ids
    ]
    relevant_questions = filter_questions_for_direction(theory_questions, interview.direction)
    
    if not relevant_questions:
        return None  # No more questions
    
    # Use LLM to select next question
    messages = [
        {"role": "system", "content": THEORY_SELECTOR_SYSTEM},
        {"role": "user", "content": THEORY_SELECTOR_USER.format(
            direction=interview.direction,
            level=interview.selected_level,
            confidence=interview.confidence_score,
            avg_score=avg_score,
            question_number=len(answered) + 1,
            max_questions=max_questions,
            asked_question_ids=str(asked_ids),
            available_questions=json.dumps(relevant_questions[:30], ensure_ascii=False)
        )}
    ]
    
    try:
        response = await scibox_client.chat_completion(messages, temperature=0.3, max_tokens=512)
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            result = json.loads(json_match.group())
            
            if not result.get("should_continue", True):
                return None  # LLM decided to stop
            
            question_id = result.get("question_id")
            question = next((q for q in questions if q["id"] == question_id), None)
            
            if question:
                # Create theory answer record
                next_order = max([a.question_order for a in all_answers], default=0) + 1
                theory_answer = TheoryAnswer(
                    interview_id=interview_id,
                    question_id=question_id,
                    question_type="theory",
                    question_text=question["question"],
                    question_order=next_order,
                    status="pending"
                )
                db.add(theory_answer)
                db.commit()
                db.refresh(theory_answer)
                
                return {
                    "id": theory_answer.id,
                    "question_order": theory_answer.question_order,
                    "question_type": "theory",
                    "question_text": question["question"],
                    "category": question.get("category"),
                    "difficulty": question.get("difficulty"),
                    "total_answered": len(answered),
                    "max_questions": max_questions
                }
    
    except Exception as e:
        logger.error(f"Failed to select theory question: {e}")
    
    # Fallback: return first available question
    if relevant_questions:
        q = relevant_questions[0]
        next_order = max([a.question_order for a in all_answers], default=0) + 1
        theory_answer = TheoryAnswer(
            interview_id=interview_id,
            question_id=q["id"],
            question_type="theory",
            question_text=q["question"],
            question_order=next_order,
            status="pending"
        )
        db.add(theory_answer)
        db.commit()
        db.refresh(theory_answer)
        
        return {
            "id": theory_answer.id,
            "question_order": theory_answer.question_order,
            "question_type": "theory",
            "question_text": q["question"],
            "category": q.get("category"),
            "total_answered": len(answered),
            "max_questions": max_questions
        }
    
    return None


async def evaluate_theory_answer(
    answer_id: int,
    candidate_answer: str,
    db: Session
) -> Dict[str, Any]:
    """
    Evaluate candidate's answer to a theory question.
    Updates confidence score based on result.
    """
    theory_answer = db.query(TheoryAnswer).filter(TheoryAnswer.id == answer_id).first()
    if not theory_answer:
        raise ValueError(f"Answer {answer_id} not found")
    
    interview = db.query(Interview).filter(Interview.id == theory_answer.interview_id).first()
    
    # Prepare evaluation prompt
    if theory_answer.question_type.startswith("solution_"):
        # Solution question - use solution evaluator
        key_points = theory_answer.evaluation_details.get("key_points", []) if theory_answer.evaluation_details else []
        
        messages = [
            {"role": "system", "content": SOLUTION_ANSWER_EVALUATOR_SYSTEM},
            {"role": "user", "content": SOLUTION_ANSWER_EVALUATOR_USER.format(
                question=theory_answer.question_text,
                reference_answer=theory_answer.reference_answer or "Нет эталонного ответа",
                key_points=", ".join(key_points),
                candidate_answer=candidate_answer
            )}
        ]
    else:
        # Theory question - use theory evaluator
        messages = [
            {"role": "system", "content": THEORY_ANSWER_EVALUATOR_SYSTEM},
            {"role": "user", "content": THEORY_ANSWER_EVALUATOR_USER.format(
                question=theory_answer.question_text,
                reference_answer=theory_answer.reference_answer or "Нет эталонного ответа - оцени по своим знаниям",
                candidate_answer=candidate_answer,
                level=interview.selected_level
            )}
        ]
    
    evaluation = {"score": 50, "feedback": "Оценка недоступна"}
    
    try:
        response = await scibox_client.chat_completion(messages, temperature=0.2, max_tokens=1024)
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            evaluation = json.loads(json_match.group())
    except Exception as e:
        logger.error(f"Failed to evaluate answer: {e}")
    
    # Update theory answer
    from datetime import datetime
    theory_answer.candidate_answer = candidate_answer
    theory_answer.score = evaluation.get("score", 50)
    theory_answer.correctness = evaluation.get("correctness", 50)
    theory_answer.completeness = evaluation.get("completeness", 50)
    theory_answer.evaluation_details = evaluation
    theory_answer.status = "answered"
    theory_answer.answered_at = datetime.utcnow()
    
    # Update interview confidence score
    _update_confidence_score(interview, evaluation.get("score", 50), db)
    
    db.commit()
    
    return {
        "score": theory_answer.score,
        "feedback": evaluation.get("feedback", ""),
        "evaluation": evaluation
    }


def _update_confidence_score(interview: Interview, new_score: float, db: Session):
    """Update interview confidence score based on answer pattern."""
    # Get all scored answers
    scored_answers = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview.id,
        TheoryAnswer.score.isnot(None),
        TheoryAnswer.status == "answered"
    ).all()
    
    if not scored_answers:
        return
    
    scores = [a.score for a in scored_answers]
    avg_score = sum(scores) / len(scores)
    
    # Level expectation mapping
    level_expectations = {
        "intern": 35,
        "junior": 45,
        "junior+": 55,
        "middle": 65,
        "middle+": 75,
        "senior": 85
    }
    expected = level_expectations.get(interview.selected_level, 60)
    
    # Calculate confidence based on consistency
    variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
    consistency = max(0, 100 - variance)
    
    # How close to expected level
    level_match = max(0, 100 - abs(avg_score - expected) * 2)
    
    # Combined confidence
    interview.confidence_score = (consistency * 0.4 + level_match * 0.6)
    
    db.commit()


async def generate_final_scores(interview_id: int, db: Session) -> Dict[str, Any]:
    """
    Generate final interview scores and assessment.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    answers = db.query(TheoryAnswer).filter(TheoryAnswer.interview_id == interview_id).all()
    
    # Prepare summaries
    tasks_summary = "\n".join([
        f"Задача {t.task_order}: {t.title}\n"
        f"  Сложность: {t.difficulty}\n"
        f"  Статус: {t.status}\n"
        f"  Балл: {t.actual_score or 0}/100"
        for t in tasks
    ])
    
    solution_answers = [a for a in answers if a.question_type.startswith("solution_")]
    theory_answers_list = [a for a in answers if a.question_type == "theory"]
    
    solution_summary = "\n".join([
        f"Вопрос {a.question_order}: {a.question_text[:50]}...\n"
        f"  Ответ: {(a.candidate_answer or 'Пропущен')[:100]}...\n"
        f"  Балл: {a.score or 0}"
        for a in solution_answers if a.status == "answered"
    ])
    
    theory_summary = "\n".join([
        f"Вопрос {a.question_order}: {a.question_text[:50]}...\n"
        f"  Ответ: {(a.candidate_answer or 'Пропущен')[:100]}...\n"
        f"  Балл: {a.score or 0}"
        for a in theory_answers_list if a.status == "answered"
    ])
    
    # Stats
    solved_tasks = len([t for t in tasks if t.status == "completed"])
    total_attempts = sum([
        db.query(Submission).filter(Submission.task_id == t.id).count()
        for t in tasks
    ])
    hints_used = sum([len(t.hints) for t in tasks])
    
    # Call LLM for final assessment
    messages = [
        {"role": "system", "content": INTERVIEW_SCORER_SYSTEM},
        {"role": "user", "content": INTERVIEW_SCORER_USER.format(
            candidate_name=interview.candidate_name or "Кандидат",
            claimed_level=interview.selected_level,
            direction=interview.direction,
            tasks_summary=tasks_summary,
            solution_answers_summary=solution_summary or "Нет ответов",
            theory_answers_summary=theory_summary or "Нет ответов",
            solved_tasks=solved_tasks,
            total_tasks=len(tasks),
            total_attempts=total_attempts,
            hints_used=hints_used,
            avg_task_time="N/A"
        )}
    ]
    
    try:
        response = await scibox_client.chat_completion(messages, temperature=0.2, max_tokens=2048)
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            result = json.loads(json_match.group())
            
            # Update interview with scores
            scores = result.get("scores", {})
            interview.code_quality_score = scores.get("code_quality")
            interview.problem_solving_score = scores.get("problem_solving")
            interview.code_explanation_score = scores.get("code_explanation")
            interview.theory_knowledge_score = scores.get("theory_knowledge")
            interview.overall_score = result.get("overall_score")
            interview.overall_grade = result.get("suggested_grade")
            interview.status = "completed"
            interview.current_stage = "completed"
            
            from datetime import datetime
            interview.completed_at = datetime.utcnow()
            
            db.commit()
            
            return result
    
    except Exception as e:
        logger.error(f"Failed to generate final scores: {e}")
    
    # Fallback scoring
    return {
        "scores": {
            "code_quality": 50,
            "problem_solving": (solved_tasks / len(tasks) * 100) if tasks else 0,
            "code_explanation": 50,
            "theory_knowledge": 50
        },
        "overall_score": 50,
        "suggested_grade": interview.selected_level,
        "summary": "Автоматическая оценка недоступна"
    }

