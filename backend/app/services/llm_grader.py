"""
LLM-based answer grading service using SciBox.
"""
import json
from openai import OpenAI

from app.core.config import settings


# Initialize SciBox client
client = OpenAI(
    api_key=settings.SCIBOX_API_KEY,
    base_url=settings.SCIBOX_BASE_URL,
)


async def llm_grade_answer(
    question_text: str,
    panel_type: str,
    eval_mode: str,
    language_hint: str | None,
    answer_code: str | None,
    answer_text: str | None,
) -> dict:
    """
    Grade answer using LLM.
    
    Args:
        question_text: The question text
        panel_type: Type of panel (code_python, code_frontend, etc.)
        eval_mode: Evaluation mode (llm_code or llm_theory)
        language_hint: Programming language hint
        answer_code: Code answer from candidate
        answer_text: Text answer from candidate
        
    Returns:
        Dict with score, passed, short_feedback, mistakes
    """
    # Select model based on eval mode
    if eval_mode == "llm_code":
        model = "qwen3-coder-30b-a3b-instruct-fp8"
    else:
        model = "qwen3-32b-awq"

    # Build system prompt
    system_prompt = (
        "/no_think "
        "Ты — автоматический проверяющий решений на техническом собеседовании. "
        "Твоя задача — оценить решение кандидата по заданию, выставить балл от 0 до 100 "
        "и кратко пояснить основные ошибки. "
        "Если решение в целом верное, но есть небольшие недочёты — выставь 70–90. "
        "Если решение почти идеальное — 90–100. "
        "Если решение явно неверное и не решает задачу — 0–40.\n\n"
        "Ответь строго одним JSON-объектом без лишнего текста, в формате:\n"
        "{\n"
        '  "score": 0-100,\n'
        '  "passed": true/false,\n'
        '  "short_feedback": "краткий текст по-русски",\n'
        '  "mistakes": ["список основных ошибок"]\n'
        "}\n"
    )

    # Build user prompt
    user_prompt_parts = [
        f"Категория панели: {panel_type}",
        f"Язык/стек: {language_hint or 'не указан'}",
        "Задание:",
        question_text,
        "",
    ]
    
    if answer_code:
        user_prompt_parts += ["Решение кандидата (код):", answer_code]
    if answer_text:
        user_prompt_parts += ["Ответ/объяснение кандидата:", answer_text]

    user_prompt = "\n".join(user_prompt_parts)

    # Call LLM
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=256,
            temperature=0.1,
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)

        return {
            "score": int(data.get("score", 0)),
            "passed": bool(data.get("passed", False)),
            "short_feedback": data.get("short_feedback", ""),
            "mistakes": data.get("mistakes", []),
        }
    except Exception as e:
        # Fallback in case of error
        return {
            "score": 0,
            "passed": False,
            "short_feedback": f"Ошибка при оценке: {str(e)}",
            "mistakes": ["Не удалось оценить ответ"],
        }

# пидормот
