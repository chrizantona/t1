"""
SciBox LLM API Client - ASYNC VERSION
Wrapper for interacting with SciBox models using OpenAI-compatible API.
Fixed: Uses async/await to prevent blocking FastAPI event loop
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import asyncio
import time
import json

from ..core.config import settings


class SciBoxClient:
    """Client for SciBox LLM API with async rate limiting support."""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.SCIBOX_API_KEY,
            base_url=settings.SCIBOX_BASE_URL
        )
        self.chat_model = settings.CHAT_MODEL
        self.coder_model = settings.CODER_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        
        # Rate limiting with locks
        self._chat_lock = asyncio.Lock()
        self._coder_lock = asyncio.Lock()
        self._embedding_lock = asyncio.Lock()
        
        self._last_chat_request = 0
        self._last_coder_request = 0
        self._last_embedding_request = 0
        self._chat_interval = 1.0 / settings.CHAT_MODEL_RPS
        self._coder_interval = 1.0 / settings.CODER_MODEL_RPS
        self._embedding_interval = 1.0 / settings.EMBEDDING_MODEL_RPS
    
    async def _rate_limit(self, last_request_time: float, interval: float) -> None:
        """Async rate limiting - wait if needed without blocking."""
        elapsed = time.time() - last_request_time
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        model: Optional[str] = None
    ) -> str:
        """Send chat completion request (async)."""
        async with self._chat_lock:
            await self._rate_limit(self._last_chat_request, self._chat_interval)
            self._last_chat_request = time.time()
            
            response = await self.client.chat.completions.create(
                model=model or self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
    
    async def code_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        """Send code completion request (async)."""
        async with self._coder_lock:
            await self._rate_limit(self._last_coder_request, self._coder_interval)
            self._last_coder_request = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.coder_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
    
    def _parse_json_response(self, response: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to parse JSON from LLM response."""
        try:
            response = response.strip()
            # Remove <think> tags if present
            import re
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            
            # Remove markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif response.startswith("```"):
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1].strip()
                    if response.startswith("json"):
                        response = response[4:].strip()
            
            parsed = json.loads(response)
            print(f"✅ Successfully parsed JSON response")
            return parsed
        except Exception as e:
            print(f"⚠️ Failed to parse JSON response: {e}")
            print(f"Raw response: {response[:200]}")
            return fallback
    
    # ========== PROMPT METHODS (ALL ASYNC) ==========
    
    async def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """1. CV-based Level Suggestion"""
        system_prompt = """/no_think
Ты — ИИ-ассистент платформы технических собеседований VibeCode.
Твоя задача — анализировать резюме разработчиков и рекомендовать:
- предполагаемый грейд (junior, middle, middle+, senior),
- релевантные направления (backend, frontend, fullstack, data, devops, mobile и т.д.),
- краткие аргументы.

Требования к ответу:
- Ответь строго в формате ОДНОГО JSON-объекта.
- Без поясняющего текста, без комментариев, без Markdown.
- Все ключи JSON — на английском, строки — на русском.

Структура JSON:
{
  "recommended_grade": "junior|middle|middle+|senior",
  "confidence": 0-100,
  "tracks": ["backend", "frontend", "fullstack", ...],
  "years_of_experience": number,
  "key_technologies": ["Python", "React", ...],
  "justification": "краткое текстовое объяснение (до 500 символов)",
  "risk_factors": ["мало коммерческого опыта", "..."]
}"""
        
        user_prompt = f"""Вот текст резюме кандидата (может быть на русском или английском).
Определи его предполагаемый грейд и направления.

Резюме:
{resume_text}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=512)
        
        return self._parse_json_response(response, {
            "recommended_grade": "middle",
            "confidence": 50,
            "tracks": ["backend"],
            "years_of_experience": 2,
            "key_technologies": [],
            "justification": "Не удалось распарсить ответ LLM",
            "risk_factors": []
        })
    
    async def generate_task(
        self,
        level: str,
        track: str,
        history_summary: str = ""
    ) -> Dict[str, Any]:
        """2. Generate adaptive task"""
        system_prompt = """/no_think
Ты — технический интервьюер платформы VibeCode.
Твоя задача — генерировать ОДНУ задачу по программированию для онлайн-собеседования.

Требования к задаче:
- Решаемость за 15–20 минут.
- Никаких чрезмерно сложных олимпиадных задач.
- Чёткое описание входных и выходных данных.
- Примеры входа/выхода.
- Текст задачи по-русски.

Формат ответа:
- Строго ОДИН JSON-объект.
- Без дополнительных комментариев и Markdown.

Структура JSON:
{
  "title": "краткое название задачи",
  "description": "подробное условие задачи (до 1200 символов)",
  "input_format": "описание формата входных данных",
  "output_format": "описание формата выходных данных",
  "examples": [
    {
      "input": "строка с примером ввода",
      "output": "ожидаемый вывод",
      "explanation": "краткое объяснение"
    }
  ],
  "constraints": "ограничения по N, ограничения по времени и памяти",
  "difficulty_level": "junior|middle|senior",
  "topic_tags": ["arrays", "strings", "greedy", ...]
}"""
        
        user_prompt = f"""Нужно сгенерировать задачу для кандидата.

Уровень кандидата: {level} (junior|middle|senior).
Направление: {track} (например, backend, frontend, algorithms).

Краткая история предыдущих задач и результатов (может быть пустой):
{history_summary}

Сгенерируй следующую задачу так, чтобы:
- если кандидат уверенно решает текущий уровень, новая задача была чуть сложнее;
- если кандидат проваливает задачи, новая задача была немного проще или другого типа."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.4, max_tokens=1024)
        
        return self._parse_json_response(response, {
            "title": "Сумма двух чисел",
            "description": "Напишите функцию, которая принимает два числа и возвращает их сумму.",
            "input_format": "Два целых числа a и b",
            "output_format": "Одно целое число - сумма a и b",
            "examples": [{"input": "2 3", "output": "5", "explanation": "2 + 3 = 5"}],
            "constraints": "1 <= a, b <= 1000",
            "difficulty_level": level,
            "topic_tags": ["math", "basic"]
        })
    
    async def generate_hint(
        self,
        task_text: str,
        user_code: str,
        test_results: str,
        hint_level: str
    ) -> Dict[str, Any]:
        """3. Hint Economy"""
        system_prompt = """/no_think
Ты — ИИ-помощник на техническом собеседовании платформы VibeCode.
Твоя задача — давать подсказки по задаче так, чтобы кандидат мог продвинуться,
но при этом не получать готовое решение.

Типы подсказок:
- "soft" — мягкая подсказка, один наводящий вопрос или направление мысли;
- "medium" — идея алгоритма в общих словах;
- "hard" — почти готовый алгоритм или псевдокод, но без полноценного кода.

Формат ответа: ОДИН JSON-объект:
{
  "hint_level": "soft|medium|hard",
  "hint_text": "текст подсказки по-русски",
  "warning": "краткое предупреждение, как это снизит максимальный балл (до 200 символов)"
}"""
        
        user_prompt = f"""Текущая задача:
{task_text}

Текущий код кандидата (может быть пустым):
{user_code}

Уже известные результаты тестов:
{test_results}

Тип подсказки: {hint_level} (soft|medium|hard).

Дай подсказку указанного уровня. Не раскрывай полностью финальное решение."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=512)
        
        return self._parse_json_response(response, {
            "hint_level": hint_level,
            "hint_text": "Подумайте о базовых структурах данных для этой задачи.",
            "warning": "Использование подсказки снизит максимальный балл на 10%"
        })
    
    async def generate_bug_hunter_tests(
        self,
        task_text: str,
        user_code: str,
        known_tests: str
    ) -> Dict[str, Any]:
        """4. AI Bug Hunter"""
        system_prompt = """/no_think
Ты — модуль "AI Bug Hunter" платформы VibeCode.
Твоя задача — по условию задачи и решению кандидата придумать входные данные,
на которых это решение с высокой вероятностью сломается или покажет неверный результат.

Формат ответа: ОДИН JSON-объект:
{
  "generated_tests": [
    { "input": "пример входа", "description": "почему этот кейс сложный" }
  ]
}

Требования:
- от 2 до 5 тестов;
- входные данные должны быть совместимы с форматом задачи;
- делай упор на граничные случаи, большие объёмы данных, повторяющиеся элементы, пустые коллекции."""
        
        user_prompt = f"""Условие задачи:
{task_text}

Решение кандидата:
{user_code}

Уже существующие тесты (для понимания, что уже покрыто):
{known_tests}

Сгенерируй дополнительные тесты, которые с высокой вероятностью найдут баги в этом решении."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.code_completion(messages, temperature=0.3, max_tokens=512)
        
        return self._parse_json_response(response, {"generated_tests": []})
    
    async def generate_final_report(
        self,
        raw_metrics_json: str
    ) -> Dict[str, Any]:
        """5. Skill Radar + final report"""
        system_prompt = """/no_think
Ты — модуль итоговой оценки кандидата платформы VibeCode.
Ты получаешь сырые метрики интервью и должен:
- оценить грейд кандидата,
- заполнить карту навыков (skill radar),
- дать короткие рекомендации, что подтянуть до следующего грейда.

Формат ответа: ОДИН JSON-объект:
{
  "overall_grade": "junior|middle|middle+|senior",
  "overall_score": 0-100,
  "skills": {
    "algorithms":   { "score": 0-100, "comment": "..." },
    "architecture": { "score": 0-100, "comment": "..." },
    "clean_code":   { "score": 0-100, "comment": "..." },
    "debugging":    { "score": 0-100, "comment": "..." },
    "communication":{ "score": 0-100, "comment": "..." }
  },
  "next_grade_tips": [
    "краткий совет 1",
    "краткий совет 2"
  ],
  "summary_text": "краткое резюме по кандидату (до 600 символов)"
}

Все тексты — по-русски."""
        
        user_prompt = f"""Вот данные по интервью в JSON:
{raw_metrics_json}

На основе этих данных оцени кандидата и заполни структуру JSON."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=1024)
        
        return self._parse_json_response(response, {
            "overall_grade": "middle",
            "overall_score": 70,
            "skills": {
                "algorithms": {"score": 70, "comment": "Хорошо"},
                "architecture": {"score": 65, "comment": "Средне"},
                "clean_code": {"score": 75, "comment": "Хорошо"},
                "debugging": {"score": 60, "comment": "Требует улучшения"},
                "communication": {"score": 70, "comment": "Хорошо"}
            },
            "next_grade_tips": ["Практиковать алгоритмы", "Улучшить архитектуру"],
            "summary_text": "Кандидат показал средний уровень"
        })
    
    async def check_explanation(
        self,
        task_text: str,
        user_code: str,
        user_explanation: str
    ) -> Dict[str, Any]:
        """6. Explanation Check"""
        system_prompt = """/no_think
Ты — модуль проверки понимания решения платформы VibeCode.
Ты получаешь: условие задачи, код кандидата и его текстовое объяснение.

Твоя задача — оценить:
- насколько кандидат понимает свой алгоритм,
- умеет ли объяснить сложность,
- видит ли граничные случаи.

Формат ответа:
{
  "communication_score": 0-100,
  "understanding_level": "low|medium|high",
  "comment": "краткий комментарий (до 400 символов)"
}"""
        
        user_prompt = f"""Условие задачи:
{task_text}

Код кандидата:
{user_code}

Объяснение кандидата:
{user_explanation}

Оцени понимание кандидатом своего решения."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=512)
        
        return self._parse_json_response(response, {
            "communication_score": 70,
            "understanding_level": "medium",
            "comment": "Кандидат демонстрирует базовое понимание решения"
        })
    
    async def check_ai_likeness(
        self,
        user_code: str
    ) -> Dict[str, Any]:
        """7. AI-Likeness"""
        system_prompt = """/no_think
Ты — модуль оценки "AI-подобности" кода платформы VibeCode.
Твоя задача — по стилю, структуре и шаблонам кода оценить,
насколько он похож на типичный код, сгенерированный LLM.

Формат ответа:
{
  "ai_likeness_score": 0-100,
  "comment": "краткое объяснение, почему такой балл (до 400 символов)"
}"""
        
        user_prompt = f"""Вот решение кандидата:
{user_code}

Оцени, насколько оно похоже на типичное LLM-решение по стилю и структуре."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.code_completion(messages, temperature=0.2, max_tokens=256)
        
        return self._parse_json_response(response, {
            "ai_likeness_score": 30,
            "comment": "Код выглядит естественно написанным человеком"
        })
    
    async def chat_with_interviewer(
        self,
        task_text: str,
        level: str,
        user_code_or_description: str,
        user_message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """8. AI Interviewer Chat"""
        system_prompt = """/no_think
Ты — технический интервьюер платформы VibeCode.
Ты ведёшь собеседование с разработчиком.

Правила:
- Отвечай кратко и по делу.
- Задавай уточняющие вопросы по алгоритму, структурам данных и граничным случаям.
- Не пиши полный код решения.
- По умолчанию общайся по-русски.
- Подстраивайся под текущий уровень кандидата (junior/middle/senior)."""
        
        user_prompt = f"""Контекст текущей задачи:
{task_text}

Уровень кандидата: {level}.

Текущий код или описание подхода:
{user_code_or_description}

Сообщение кандидата:
{user_message}

Ответь как технический интервьюер: уточни подход, задай вопрос или направь размышления, не раскрывая полного решения."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            messages.extend(chat_history)
        
        messages.append({"role": "user", "content": user_prompt})
        
        response = await self.chat_completion(messages, temperature=0.7, max_tokens=512)
        return response
    
    async def generate_boss_fight_task(
        self,
        interview_weaknesses_json: str
    ) -> Dict[str, Any]:
        """9. Boss Fight"""
        system_prompt = """/no_think
Ты — модуль генерации финальной "boss fight" задачи платформы VibeCode.
Твоя задача — по истории интервью и слабым местам кандидата
сгенерировать одну персонализированную финальную задачу.

Формат такой же, как у обычной задачи:
{
  "title": "...",
  "description": "...",
  "input_format": "...",
  "output_format": "...",
  "examples": [...],
  "constraints": "...",
  "difficulty_level": "junior|middle|senior",
  "topic_tags": [...]
}"""
        
        user_prompt = f"""Вот краткий JSON с результатами интервью и выявленными слабыми местами:
{interview_weaknesses_json}

Сгенерируй ОДНУ финальную задачу-босса, которая целенаправленно проверит эти слабые места.
Условие на русском языке."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.4, max_tokens=1024)
        
        return self._parse_json_response(response, {
            "title": "Финальная задача",
            "description": "Решите сложную задачу",
            "input_format": "Входные данные",
            "output_format": "Выходные данные",
            "examples": [],
            "constraints": "Стандартные ограничения",
            "difficulty_level": "middle",
            "topic_tags": ["algorithms"]
        })


# Global client instance
scibox_client = SciBoxClient()
