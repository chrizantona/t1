"""
Complexity Checker - Ask about time/space complexity after solving a task.

According to ТЗ:
1. After task is solved, AI asks about complexity
2. Candidate answers
3. We evaluate via EVALUATE_ANSWER
4. Coder model analyzes code and estimates actual complexity
5. We compare candidate's understanding with reality
"""
import json
import re
from typing import Dict, Any, Optional

from .scibox_client import scibox_client
from .llm_protocol import (
    ask_question,
    evaluate_answer,
    Stage,
    Intent
)
from ..core.config import settings


async def generate_complexity_question(
    task_title: str,
    task_description: str,
    candidate_code: str,
    difficulty: str = "junior"
) -> Dict[str, Any]:
    """
    Generate a question asking about time and space complexity.
    
    Returns:
        {
            "question_text": "Расскажи, как работает твой алгоритм...",
            "short_intro": "Отлично, задача решена!"
        }
    """
    result = await ask_question(
        stage=Stage.ALGO,
        direction="algorithms",
        difficulty=difficulty,
        question_type="time_space_complexity",
        task_description=task_description,
        candidate_code=candidate_code
    )
    
    # If LLM failed, use default question
    if "error" in result:
        return {
            "question_text": f"Отлично! Ты решил задачу '{task_title}'. Расскажи, как работает твой алгоритм и какова его временная и пространственная сложность (Big O)?",
            "short_intro": "Теперь давай обсудим твоё решение."
        }
    
    return result


async def analyze_code_complexity(code: str) -> Dict[str, Any]:
    """
    Use coder model to analyze actual complexity of the code.
    
    Returns:
        {
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "explanation": "...",
            "algorithm_type": "two_pointers"
        }
    """
    system_prompt = """/no_think
Ты эксперт по анализу алгоритмов. Проанализируй код и определи:
1. Временную сложность (Big O)
2. Пространственную сложность (Big O)
3. Тип используемого алгоритма

Отвечай ТОЛЬКО JSON:
{
    "time_complexity": "O(...)",
    "space_complexity": "O(...)",
    "algorithm_type": "название подхода",
    "explanation": "краткое объяснение"
}
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Проанализируй сложность этого кода:\n\n```python\n{code}\n```"}
    ]
    
    try:
        response = await scibox_client.chat_completion(
            messages=messages,
            model=settings.CODER_MODEL,
            temperature=0.1,
            max_tokens=512
        )
        
        # Clean response
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        # Try to parse JSON
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        
        return {
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "algorithm_type": "Unknown",
            "explanation": "Не удалось проанализировать"
        }
        
    except Exception as e:
        return {
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "algorithm_type": "Unknown",
            "explanation": f"Error: {str(e)}"
        }


async def evaluate_complexity_answer(
    candidate_answer: str,
    actual_complexity: Dict[str, Any],
    task_description: str,
    difficulty: str = "junior"
) -> Dict[str, Any]:
    """
    Evaluate candidate's understanding of complexity.
    Compare with actual complexity analysis.
    
    Returns:
        {
            "score": 0..3,
            "time_correct": bool,
            "space_correct": bool,
            "understanding_level": "full|partial|wrong",
            "feedback": "...",
            "comment_for_interviewer": "..."
        }
    """
    # Build canonical answer from analysis
    canonical_answer = f"""
Временная сложность: {actual_complexity.get('time_complexity', 'O(?)')}
Пространственная сложность: {actual_complexity.get('space_complexity', 'O(?)')}
Алгоритм: {actual_complexity.get('algorithm_type', '?')}
"""
    
    key_points = [
        f"Временная сложность: {actual_complexity.get('time_complexity', 'O(?)')}",
        f"Пространственная сложность: {actual_complexity.get('space_complexity', 'O(?)')}",
        "Понимание, почему такая сложность"
    ]
    
    result = await evaluate_answer(
        stage=Stage.ALGO,
        direction="algorithms",
        difficulty=difficulty,
        question_text="Какова временная и пространственная сложность твоего решения?",
        candidate_answer=candidate_answer,
        canonical_answer=canonical_answer,
        key_points=key_points
    )
    
    # Check if time/space are correct
    answer_lower = candidate_answer.lower()
    time_comp = actual_complexity.get('time_complexity', '').lower()
    space_comp = actual_complexity.get('space_complexity', '').lower()
    
    time_correct = time_comp in answer_lower if time_comp else False
    space_correct = space_comp in answer_lower if space_comp else False
    
    # Determine understanding level
    if time_correct and space_correct:
        understanding_level = "full"
    elif time_correct or space_correct:
        understanding_level = "partial"
    else:
        understanding_level = "wrong"
    
    result["time_correct"] = time_correct
    result["space_correct"] = space_correct
    result["understanding_level"] = understanding_level
    result["actual_time_complexity"] = actual_complexity.get('time_complexity')
    result["actual_space_complexity"] = actual_complexity.get('space_complexity')
    
    return result


async def full_complexity_check(
    task_title: str,
    task_description: str,
    candidate_code: str,
    candidate_answer: str,
    difficulty: str = "junior"
) -> Dict[str, Any]:
    """
    Full complexity check flow:
    1. Analyze actual complexity
    2. Evaluate candidate's answer
    3. Return combined result
    
    Returns complete evaluation with score and feedback.
    """
    # Step 1: Analyze actual complexity
    actual_complexity = await analyze_code_complexity(candidate_code)
    
    # Step 2: Evaluate candidate's answer
    evaluation = await evaluate_complexity_answer(
        candidate_answer=candidate_answer,
        actual_complexity=actual_complexity,
        task_description=task_description,
        difficulty=difficulty
    )
    
    return {
        "actual_complexity": actual_complexity,
        "evaluation": evaluation,
        "candidate_understands": evaluation.get("understanding_level") in ["full", "partial"],
        "complexity_score": evaluation.get("score", 0) / 3 * 100  # Convert to 0-100
    }


