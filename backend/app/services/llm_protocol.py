"""
LLM Protocol - Structured Intent-Based Communication with SciBox LLM.

According to ТЗ (CR7M3NTAL1TY.MD):
- Every request is structured with intent, stage, direction, etc.
- System prompt tells model it's an INTERVIEWER, not a helpful assistant
- Model should NEVER give full working code during active task
"""
import json
import re
from typing import Optional, Dict, Any, Literal
from enum import Enum

from .scibox_client import scibox_client
from ..core.config import settings


class Intent(str, Enum):
    """LLM request intents."""
    ASK_QUESTION = "ASK_QUESTION"
    EVALUATE_ANSWER = "EVALUATE_ANSWER"
    GIVE_HINT = "GIVE_HINT"
    ANALYZE_BUG = "ANALYZE_BUG"
    EXPLAIN_SOLUTION = "EXPLAIN_SOLUTION"
    SMALL_TALK = "SMALL_TALK"
    CLASSIFY_AI_LIKE = "CLASSIFY_AI_LIKE"
    PARSE_RESUME = "PARSE_RESUME"
    PARSE_VACANCY = "PARSE_VACANCY"


class Stage(str, Enum):
    """Interview stages."""
    ALGO = "ALGO"
    PRACTICE = "PRACTICE"
    THEORY = "THEORY"
    META = "META"


# System prompt for qwen3-32b-awq (universal chat model)
INTERVIEWER_SYSTEM_PROMPT = """/no_think
Ты ИИ-интервьюер платформы технических собеседований VibeCode.
Ты НЕ обычный чат-бот и НЕ должен просто решать задачи за кандидата.

Каждый запрос к тебе приходит в виде JSON в последнем сообщении пользователя.
Твои правила:

1. Сначала распарсь JSON.
2. Посмотри поле "intent" и "stage".
3. Выполни строго то, что требуется для этого intent.
4. Отвечай ТОЛЬКО одним JSON-объектом без лишнего текста.

intent:
- "ASK_QUESTION": сгенерировать формулировку вопроса для кандидата.
- "EVALUATE_ANSWER": оценить ответ кандидата относительно canonical_answer и key_points.
- "GIVE_HINT": дать подсказку по задаче (без полного решения и рабочего кода).
- "ANALYZE_BUG": объяснить, почему решение кандидата не проходит скрытые тесты, и дать направление исправления.
- "EXPLAIN_SOLUTION": после завершения вопроса объяснить правильный подход (опционально с упрощённым примером).
- "SMALL_TALK": поддержать лёгкий диалог без раскрытия ответов или решений задач.
- "CLASSIFY_AI_LIKE": по куску кода оценить, насколько он похож на AI-сгенерированный (0..1).
- "PARSE_RESUME": извлечь скиллы и примерный грейд из текста резюме.
- "PARSE_VACANCY": извлечь скиллы и требования из описания вакансии.

Особо важно:
- В intent "ASK_QUESTION", "GIVE_HINT", "ANALYZE_BUG" и "SMALL_TALK" НИКОГДА не выдавай полный рабочий код решения задачи.
- Полные решения можно описывать только в intent "EXPLAIN_SOLUTION" И ТОЛЬКО если в контексте указано, что задача уже завершена.

Формат ответов:
- ASK_QUESTION: {"question_text": "...", "short_intro": "..."}
- EVALUATE_ANSWER: {"score": 0..3, "comment_for_interviewer": "...", "short_feedback_for_candidate": "...", "extra_topics": ["..."] }
- GIVE_HINT: {"hint_level": "light|medium|heavy", "hint_text": "..."}
- ANALYZE_BUG: {"analysis": "...", "suggested_focus": "..."}
- EXPLAIN_SOLUTION: {"explanation": "..."}
- SMALL_TALK: {"reply": "..."}
- CLASSIFY_AI_LIKE: {"ai_style_score": 0.0..1.0, "signals": ["..."]}
- PARSE_RESUME: {"proposed_grade": "...", "years_of_experience": number, "skills": [{"id": "...", "name": "...", "level": 0..3}], "tech_stack": ["..."], "summary": "..."}
- PARSE_VACANCY: {"skills": [...], "critical_skills": [...], "weights": {...}}
"""

# System prompt for qwen3-coder (code assistant) - used for bug analysis and AI detection
CODER_SYSTEM_PROMPT = """/no_think
Ты код-ассистент платформы технических собеседований VibeCode.
Анализируй код, находи баги, оценивай качество.
НЕ выдавай полный рабочий код решения - только анализ и направления.
Отвечай ТОЛЬКО JSON без лишнего текста.
"""


def _clean_response(response: str) -> str:
    """Remove <think> tags and extract JSON from response."""
    # Remove think tags
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    response = response.strip()
    
    # Try to extract JSON
    if response.startswith('{'):
        return response
    
    # Find JSON in response
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if json_match:
        return json_match.group()
    
    return response


def _parse_json_response(response: str) -> Dict[str, Any]:
    """Parse JSON from LLM response."""
    cleaned = _clean_response(response)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object
        start = cleaned.find('{')
        end = cleaned.rfind('}') + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except:
                pass
        return {"error": "Failed to parse response", "raw": response[:500]}


async def call_llm_with_intent(
    intent: Intent,
    stage: Stage,
    direction: str,
    difficulty: str,
    context: Dict[str, Any],
    language: str = "ru",
    use_coder_model: bool = False
) -> Dict[str, Any]:
    """
    Call LLM with structured intent-based request.
    
    Args:
        intent: What we want the LLM to do
        stage: Current interview stage (ALGO, PRACTICE, THEORY, META)
        direction: Interview direction (backend, frontend, ml, etc.)
        difficulty: Current difficulty level (junior, middle, senior)
        context: Additional context depending on intent
        language: Response language (ru/en)
        use_coder_model: Use code assistant model instead of chat model
        
    Returns:
        Parsed JSON response from LLM
    """
    # Build the request payload
    payload = {
        "intent": intent.value,
        "stage": stage.value,
        "direction": direction,
        "difficulty": difficulty,
        "language": language,
        "context": context
    }
    
    # Choose system prompt and model
    system_prompt = CODER_SYSTEM_PROMPT if use_coder_model else INTERVIEWER_SYSTEM_PROMPT
    model = settings.CODER_MODEL if use_coder_model else settings.CHAT_MODEL
    
    # Make request
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    ]
    
    response = await scibox_client.chat_completion(
        messages=messages,
        model=model,
        temperature=0.3 if intent in [Intent.EVALUATE_ANSWER, Intent.CLASSIFY_AI_LIKE] else 0.7,
        max_tokens=1024
    )
    
    return _parse_json_response(response)


# ============ Convenience Functions ============

async def ask_question(
    stage: Stage,
    direction: str,
    difficulty: str,
    question_type: str,
    task_description: Optional[str] = None,
    candidate_code: Optional[str] = None,
    topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a question for the candidate.
    
    Args:
        stage: Interview stage
        direction: Interview direction
        difficulty: Difficulty level
        question_type: Type of question (time_space_complexity, algorithm_explanation, theory, etc.)
        task_description: Task description if asking about a task
        candidate_code: Candidate's code if asking about their solution
        topic: Topic for theory questions
        
    Returns:
        {"question_text": "...", "short_intro": "..."}
    """
    context = {
        "question_type": question_type
    }
    if task_description:
        context["task_description"] = task_description
    if candidate_code:
        context["candidate_code"] = candidate_code
    if topic:
        context["topic"] = topic
        
    return await call_llm_with_intent(
        intent=Intent.ASK_QUESTION,
        stage=stage,
        direction=direction,
        difficulty=difficulty,
        context=context
    )


async def evaluate_answer(
    stage: Stage,
    direction: str,
    difficulty: str,
    question_text: str,
    candidate_answer: str,
    canonical_answer: Optional[str] = None,
    key_points: Optional[list] = None
) -> Dict[str, Any]:
    """
    Evaluate candidate's answer.
    
    Returns:
        {
            "score": 0..3,
            "comment_for_interviewer": "...",
            "short_feedback_for_candidate": "...",
            "extra_topics": ["..."]  # Topics candidate mentioned that we can probe deeper
        }
    """
    context = {
        "question_text": question_text,
        "candidate_answer": candidate_answer
    }
    if canonical_answer:
        context["canonical_answer"] = canonical_answer
    if key_points:
        context["key_points"] = key_points
        
    return await call_llm_with_intent(
        intent=Intent.EVALUATE_ANSWER,
        stage=stage,
        direction=direction,
        difficulty=difficulty,
        context=context
    )


async def give_hint(
    stage: Stage,
    direction: str,
    difficulty: str,
    hint_level: Literal["light", "medium", "heavy"],
    task_description: str,
    candidate_code: Optional[str] = None,
    test_results: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a hint for the candidate.
    
    Penalties:
    - light: -10 points
    - medium: -25 points  
    - heavy: -40 points
    
    IMPORTANT: Never give full working code!
    
    Returns:
        {"hint_level": "...", "hint_text": "..."}
    """
    context = {
        "hint_level": hint_level,
        "task_description": task_description
    }
    if candidate_code:
        context["candidate_code"] = candidate_code
    if test_results:
        context["test_results"] = test_results
        
    return await call_llm_with_intent(
        intent=Intent.GIVE_HINT,
        stage=stage,
        direction=direction,
        difficulty=difficulty,
        context=context
    )


async def analyze_bug(
    stage: Stage,
    direction: str,
    difficulty: str,
    task_description: str,
    candidate_code: str,
    test_results: str,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze why candidate's code fails hidden tests.
    Give direction without revealing the solution.
    
    Returns:
        {"analysis": "...", "suggested_focus": "..."}
    """
    context = {
        "task_description": task_description,
        "candidate_code": candidate_code,
        "test_results": test_results
    }
    if error_message:
        context["error_message"] = error_message
        
    return await call_llm_with_intent(
        intent=Intent.ANALYZE_BUG,
        stage=stage,
        direction=direction,
        difficulty=difficulty,
        context=context,
        use_coder_model=True
    )


async def classify_ai_like(code: str) -> Dict[str, Any]:
    """
    Classify if code looks AI-generated.
    
    Returns:
        {"ai_style_score": 0.0..1.0, "signals": ["..."]}
    """
    context = {
        "code": code
    }
    
    return await call_llm_with_intent(
        intent=Intent.CLASSIFY_AI_LIKE,
        stage=Stage.META,
        direction="any",
        difficulty="any",
        context=context,
        use_coder_model=True
    )


async def parse_resume(resume_text: str) -> Dict[str, Any]:
    """
    Parse resume and extract skills, grade, experience.
    
    Returns:
        {
            "proposed_grade": "junior|middle|senior",
            "years_of_experience": number,
            "skills": [{"id": "...", "name": "...", "level": 0..3}],
            "tech_stack": ["Python", "Django", ...],
            "summary": "..."
        }
    """
    context = {
        "resume_text": resume_text
    }
    
    return await call_llm_with_intent(
        intent=Intent.PARSE_RESUME,
        stage=Stage.META,
        direction="any",
        difficulty="any",
        context=context
    )


async def parse_vacancy(vacancy_text: str) -> Dict[str, Any]:
    """
    Parse vacancy and extract skill requirements.
    
    Returns:
        {
            "skills": [...],
            "critical_skills": [...],
            "weights": {...}
        }
    """
    context = {
        "vacancy_text": vacancy_text
    }
    
    return await call_llm_with_intent(
        intent=Intent.PARSE_VACANCY,
        stage=Stage.META,
        direction="any",
        difficulty="any",
        context=context
    )


async def explain_solution(
    task_description: str,
    correct_approach: str,
    task_completed: bool = True
) -> Dict[str, Any]:
    """
    Explain the correct solution after task is completed.
    Only call this when task_completed=True!
    
    Returns:
        {"explanation": "..."}
    """
    if not task_completed:
        return {"error": "Cannot explain solution for active task"}
    
    context = {
        "task_description": task_description,
        "correct_approach": correct_approach,
        "task_completed": True
    }
    
    return await call_llm_with_intent(
        intent=Intent.EXPLAIN_SOLUTION,
        stage=Stage.ALGO,
        direction="any",
        difficulty="any",
        context=context
    )


async def small_talk(
    user_message: str,
    interview_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle small talk without revealing answers.
    
    Returns:
        {"reply": "..."}
    """
    context = {
        "user_message": user_message
    }
    if interview_context:
        context["interview_context"] = interview_context
        
    return await call_llm_with_intent(
        intent=Intent.SMALL_TALK,
        stage=Stage.META,
        direction="any",
        difficulty="any",
        context=context
    )



# пидормот
