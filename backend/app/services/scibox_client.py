"""
SciBox LLM API Client - ASYNC VERSION with KILLER PROMPTS
Wrapper for interacting with SciBox models using OpenAI-compatible API.
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import asyncio
import time
import json
import re

from ..core.config import settings
from .prompts import (
    RESUME_ANALYSIS_SYSTEM, RESUME_ANALYSIS_USER,
    INTERVIEWER_CHAT_SYSTEM, INTERVIEWER_CHAT_USER,
    HINT_SYSTEM, HINT_USER,
    BUG_ANALYSIS_SYSTEM, BUG_ANALYSIS_USER,
    EVALUATE_ANSWER_SYSTEM, EVALUATE_ANSWER_USER,
    COMPLEXITY_QUESTION_SYSTEM, COMPLEXITY_QUESTION_USER,
    AI_DETECTION_SYSTEM, AI_DETECTION_USER,
    FINAL_REPORT_SYSTEM, FINAL_REPORT_USER
)
from ..prompts.task_selection_explainer import (
    TASK_SELECTION_EXPLAINER_SYSTEM, TASK_SELECTION_EXPLAINER_USER,
    TASK_OPENING_QUESTION_SYSTEM, TASK_OPENING_QUESTION_USER,
    SOLUTION_FOLLOWUP_SYSTEM, SOLUTION_FOLLOWUP_USER,
    SOLUTION_ANSWER_EVAL_SYSTEM, SOLUTION_ANSWER_EVAL_USER
)


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
    
    def _clean_think_tags(self, text: str) -> str:
        """Remove <think> tags and ALL internal reasoning from response."""
        if not text:
            return text
        # Remove <think>...</think> blocks (greedy and non-greedy)
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.DOTALL).strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        # Remove partial or malformed tags
        text = re.sub(r'</?think[^>]*>', '', text).strip()
        # Remove any remaining <think> without closing
        text = re.sub(r'<think>[\s\S]*$', '', text, flags=re.DOTALL).strip()
        return text
    
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
        """Send chat completion request (async). Auto-cleans <think> tags."""
        async with self._chat_lock:
            await self._rate_limit(self._last_chat_request, self._chat_interval)
            self._last_chat_request = time.time()
            
            try:
                response = await self.client.chat.completions.create(
                    model=model or self.chat_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content or ""
                # ALWAYS clean think tags from ALL responses
                content = self._clean_think_tags(content)
                return content
            except Exception as e:
                print(f"⚠️ Chat completion error: {e}")
                return ""
    
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
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.coder_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"⚠️ Code completion error: {e}")
                return ""
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using bge-m3 model (async)."""
        async with self._embedding_lock:
            await self._rate_limit(self._last_embedding_request, self._embedding_interval)
            self._last_embedding_request = time.time()
            
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"⚠️ Embedding error: {e}")
                return []
    
    def _parse_json_response(self, response: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to parse JSON from LLM response with robust handling."""
        if not response:
            print("⚠️ Empty response from LLM")
            return fallback
            
        try:
            response = response.strip()
            
            # Remove <think> tags if present (qwen3 thinking mode)
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            
            # Remove markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                parts = response.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        response = part[4:].strip()
                        break
                    elif part.startswith("{"):
                        response = part
                        break
            
            # Try to find JSON object in response
            if not response.startswith("{"):
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    response = json_match.group()
            
            parsed = json.loads(response)
            print(f"✅ Successfully parsed JSON response")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"Raw response (first 500 chars): {response[:500]}")
            return fallback
        except Exception as e:
            print(f"⚠️ Unexpected error parsing response: {e}")
            return fallback
    
    # ========== KILLER PROMPT METHODS ==========
    
    async def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        🎯 CV Analysis - Senior Tech Recruiter level analysis
        Returns comprehensive candidate assessment with grade, tracks, strengths, weaknesses
        """
        user_prompt = RESUME_ANALYSIS_USER.format(resume_text=resume_text)
        
        messages = [
            {"role": "system", "content": RESUME_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=1024)
        
        return self._parse_json_response(response, {
            "recommended_grade": "middle",
            "confidence": 50,
            "tracks": ["backend"],
            "years_of_experience": 2,
            "key_technologies": [],
            "strengths": ["Есть опыт разработки"],
            "weaknesses": ["Требуется дополнительная информация"],
            "justification": "Недостаточно данных для точной оценки",
            "risk_factors": [],
            "interview_focus": ["Уточнить опыт на собеседовании"]
        })
    
    async def chat_with_interviewer(
        self,
        task_text: str,
        level: str,
        direction: str,
        task_title: str,
        user_code: str,
        user_message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        💬 AI Interviewer - Friendly but professional technical interviewer
        Never gives solutions, asks clarifying questions, supports candidate
        """
        user_prompt = INTERVIEWER_CHAT_USER.format(
            level=level,
            direction=direction,
            task_title=task_title,
            task_description=task_text,
            user_code=user_code or "# Кандидат еще не написал код",
            user_message=user_message
        )
        
        messages = [{"role": "system", "content": INTERVIEWER_CHAT_SYSTEM}]
        
        if chat_history:
            # Add last 10 messages for context
            messages.extend(chat_history[-10:])
        
        messages.append({"role": "user", "content": user_prompt})
        
        response = await self.chat_completion(messages, temperature=0.7, max_tokens=512)
        
        # Return plain text, not JSON
        return response if response else "Хороший вопрос! Давай разберёмся вместе."
    
    async def generate_hint(
        self,
        task_text: str,
        user_code: str,
        test_results: str,
        hint_level: str
    ) -> Dict[str, Any]:
        """
        💡 Hint Generation - Progressive hints without giving away solution
        Levels: light (-10 pts), medium (-25 pts), heavy (-40 pts)
        """
        user_prompt = HINT_USER.format(
            task_text=task_text,
            user_code=user_code or "# Код пока не написан",
            test_results=test_results or "Тесты еще не запускались",
            hint_level=hint_level
        )
        
        messages = [
            {"role": "system", "content": HINT_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.4, max_tokens=512)
        
        return self._parse_json_response(response, {
            "hint_level": hint_level,
            "hint_text": "Попробуй начать с самого простого случая. Как бы ты решил задачу для минимального входа?",
            "encouragement": "Ты на верном пути, продолжай!",
            "next_step": "Определи базовый случай и постепенно усложняй"
        })
    
    async def generate_auto_hint_on_failure(
        self,
        task_title: str,
        task_description: str,
        visible_tests: List[Dict],
        user_code: str,
        error_message: str = ""
    ) -> Dict[str, Any]:
        """
        🔄 Auto-hint on submission failure
        Gives helpful hint about input format, common mistakes, etc.
        Penalty: -15 points from max_score
        """
        # Format visible tests for context
        tests_info = ""
        for i, test in enumerate(visible_tests[:2], 1):
            tests_info += f"Тест {i}: вход={test.get('input')}, выход={test.get('expected_output')}\n"
        
        system_prompt = """/no_think
Ты помощник на техническом собеседовании. Кандидат отправил неправильное решение.
Твоя задача — дать КРАТКУЮ подсказку (2-3 предложения), которая поможет понять:
1. Как правильно читать входные данные
2. Какой тип данных ожидается на выходе
3. Частые ошибки в подобных задачах

НЕ давай готовое решение! Только направь в нужную сторону.

Ответь в формате JSON:
{
    "hint_text": "краткая подсказка",
    "input_format_tip": "как читать данные",
    "common_mistake": "частая ошибка"
}"""

        user_prompt = f"""Задача: {task_title}
Описание: {task_description}

Примеры тестов:
{tests_info}

Код кандидата:
```python
{user_code[:500] if user_code else '# пусто'}
```

{f'Ошибка: {error_message}' if error_message else 'Тесты не прошли'}

Дай краткую подсказку."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.4, max_tokens=300)
        
        return self._parse_json_response(response, {
            "hint_text": "Проверь формат входных данных и тип возвращаемого значения.",
            "input_format_tip": "Убедись, что правильно читаешь входные данные.",
            "common_mistake": "Часто забывают про граничные случаи."
        })

    async def analyze_bug(
        self,
        task_description: str,
        user_code: str,
        test_results: str,
        error_message: str = ""
    ) -> Dict[str, Any]:
        """
        🐛 Bug Analysis - Code reviewer explaining why code fails
        Shows failing example, explains bug, hints direction without giving fix
        """
        user_prompt = BUG_ANALYSIS_USER.format(
            task_description=task_description,
            user_code=user_code,
            test_results=test_results,
            error_message=error_message or "Нет явной ошибки, тесты просто не проходят"
        )
        
        messages = [
            {"role": "system", "content": BUG_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=768)
        
        return self._parse_json_response(response, {
            "bug_type": "logic",
            "analysis": "В коде есть логическая ошибка. Проверь внимательно условия и граничные случаи.",
            "failing_example": "Попробуй запустить код на крайних значениях входных данных",
            "expected_vs_actual": "Результат отличается от ожидаемого",
            "hint_direction": "Подумай, что происходит на границах входных данных",
            "severity": "major"
        })
    
    async def evaluate_theory_answer(
        self,
        question: str,
        canonical_answer: str,
        key_points: List[str],
        candidate_answer: str,
        difficulty: str = "middle"
    ) -> Dict[str, Any]:
        """
        📝 Theory Answer Evaluation - Expert examiner scoring 0-3
        Checks correctness, completeness, understanding depth
        """
        user_prompt = EVALUATE_ANSWER_USER.format(
            question=question,
            canonical_answer=canonical_answer,
            key_points="\n".join(f"- {p}" for p in key_points) if key_points else "Нет ключевых пунктов",
            candidate_answer=candidate_answer,
            difficulty=difficulty
        )
        
        messages = [
            {"role": "system", "content": EVALUATE_ANSWER_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.2, max_tokens=768)
        
        return self._parse_json_response(response, {
            "score": 1,
            "correctness": "Ответ частично корректен",
            "missing": "Требуется более детальный анализ",
            "errors": [],
            "feedback_for_candidate": "Ответ засчитан, но можно было раскрыть тему глубже.",
            "extra_topics": [],
            "interviewer_note": "Требует дополнительной проверки на follow-up"
        })
    
    async def generate_complexity_question(
        self,
        task_title: str,
        task_description: str,
        candidate_code: str
    ) -> Dict[str, Any]:
        """
        ⏱️ Complexity Question - Ask about time/space complexity
        Generates natural follow-up question about algorithm complexity
        """
        user_prompt = COMPLEXITY_QUESTION_USER.format(
            task_title=task_title,
            task_description=task_description,
            candidate_code=candidate_code
        )
        
        messages = [
            {"role": "system", "content": COMPLEXITY_QUESTION_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.5, max_tokens=384)
        
        return self._parse_json_response(response, {
            "intro": "Отлично, задача решена!",
            "question": "Расскажи, какая временная и пространственная сложность у твоего решения?",
            "follow_up": "А можно ли оптимизировать алгоритм?"
        })
    
    async def check_ai_likeness(self, user_code: str, level: str = "middle") -> Dict[str, Any]:
        """
        🤖 AI Code Detection - Detect AI-generated code patterns
        Returns probability score 0-1 with confidence and signals
        """
        user_prompt = AI_DETECTION_USER.format(
            code=user_code,
            level=level
        )
        
        messages = [
            {"role": "system", "content": AI_DETECTION_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.code_completion(messages, temperature=0.2, max_tokens=512)
        
        return self._parse_json_response(response, {
            "ai_style_score": 0.3,
            "confidence": "low",
            "signals": [],
            "human_signals": ["Естественный стиль кода"],
            "verdict": "likely_human",
            "recommendation": "Спросить про детали реализации"
        })
    
    async def generate_final_report(self, raw_metrics_json: str) -> Dict[str, Any]:
        """
        📊 Final Report Generation - Professional interview summary
        Decision: hire/consider/reject with skills breakdown and recommendations
        """
        user_prompt = FINAL_REPORT_USER.format(interview_data=raw_metrics_json)
        
        messages = [
            {"role": "system", "content": FINAL_REPORT_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=1500)
        
        return self._parse_json_response(response, {
            "overall_grade": "middle",
            "overall_score": 70,
            "decision": "consider",
            "decision_reasoning": "Кандидат показал средний уровень. Рекомендуется дополнительное собеседование.",
            "skills": {
                "algorithms": {"score": 70, "comment": "Базовые алгоритмы знает"},
                "architecture": {"score": 65, "comment": "Средний уровень"},
                "clean_code": {"score": 75, "comment": "Код читаемый"},
                "debugging": {"score": 60, "comment": "Есть потенциал"},
                "communication": {"score": 70, "comment": "Объясняет понятно"}
            },
            "strengths": ["Базовые знания программирования"],
            "areas_to_improve": ["Алгоритмы", "Системный дизайн"],
            "candidate_feedback": "Хорошая работа! Рекомендуем подтянуть алгоритмы и структуры данных.",
            "hiring_manager_notes": "Требуется дополнительная оценка",
            "next_steps": ["Техническое интервью с командой"]
        })
    
    async def generate_task_selection_reason(
        self,
        task_payload: Dict[str, Any],
        track: str,
        difficulty: str,
        target_skills: List[str],
        candidate_level: str,
        direction: str,
        block_type: str = "algo",
        vacancy_info: str = "",
        candidate_additional_info: str = ""
    ) -> str:
        """
        🎯 Task Selection Explainer - Explain WHY this task was selected
        Returns human-readable explanation (3-5 sentences)
        """
        import json as json_module
        
        user_prompt = TASK_SELECTION_EXPLAINER_USER.format(
            vacancy_info=vacancy_info or "Прямое интервью без привязки к вакансии",
            candidate_level=candidate_level,
            direction=direction,
            candidate_additional_info=candidate_additional_info or "Дополнительная информация отсутствует",
            block_type=block_type,
            track=track,
            difficulty=difficulty,
            target_skills=json_module.dumps(target_skills, ensure_ascii=False),
            task_payload=json_module.dumps(task_payload, ensure_ascii=False, indent=2)
        )
        
        messages = [
            {"role": "system", "content": TASK_SELECTION_EXPLAINER_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=512)
        
        result = self._parse_json_response(response, {
            "selection_reason": f"Задача подобрана для проверки навыков {', '.join(target_skills)} на уровне {difficulty} для {direction}-разработчика уровня {candidate_level}."
        })
        
        return result.get("selection_reason", "Задача подобрана автоматически под ваш профиль.")
    
    async def generate_opening_question(
        self,
        task_description: str,
        block_type: str,
        track: str,
        candidate_grade: str,
        difficulty: str
    ) -> str:
        """
        💬 Opening Question - Generate first smart question for the task
        Returns single question to start dialogue with candidate
        """
        user_prompt = TASK_OPENING_QUESTION_USER.format(
            task_description=task_description,
            block_type=block_type,
            track=track,
            candidate_grade=candidate_grade,
            difficulty=difficulty
        )
        
        messages = [
            {"role": "system", "content": TASK_OPENING_QUESTION_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.7, max_tokens=256)
        
        # Clean response
        if response:
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            response = response.strip('"').strip("'")
        
        if not response:
            # Fallback questions based on track
            fallback_questions = {
                "backend": "🤔 Какую асимптотическую сложность ты планируешь достичь в своём решении?",
                "algorithms": "🤔 Какую асимптотическую сложность ты планируешь достичь в своём решении?",
                "ml": "📊 С чего бы ты начал работу с данными в этой задаче?",
                "data-science": "📊 Какие шаги предобработки данных ты бы сделал в первую очередь?",
                "frontend": "🎨 Какие компоненты тебе понадобятся для решения этой задачи?",
                "devops": "🔧 Какие инструменты и подходы ты бы использовал?",
                "data": "📊 Как бы ты проверил корректность результатов?"
            }
            response = fallback_questions.get(track, "🤔 Какой подход ты планируешь использовать для решения этой задачи?")
        
        return response
    
    async def generate_solution_followup_question(
        self,
        task_title: str,
        task_description: str,
        candidate_code: str,
        candidate_level: str,
        difficulty: str
    ) -> str:
        """
        🎯 Solution Follow-up Question - Ask about the solution after task completion
        Returns single question about complexity, algorithm, optimization etc.
        """
        user_prompt = SOLUTION_FOLLOWUP_USER.format(
            task_title=task_title,
            task_description=task_description,
            candidate_code=candidate_code,
            candidate_level=candidate_level,
            difficulty=difficulty
        )
        
        messages = [
            {"role": "system", "content": SOLUTION_FOLLOWUP_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.6, max_tokens=256)
        
        # Clean response - remove any <think> tags
        response = self._clean_think_tags(response)
        
        if not response:
            # Fallback questions
            fallback = [
                f"🤔 Какова временная сложность твоего решения? А пространственная?",
                f"🤔 Можешь объяснить, почему ты выбрал именно такой подход?",
                f"🤔 Можно ли оптимизировать это решение? Как?",
            ]
            import random
            response = random.choice(fallback)
        
        return response
    
    async def evaluate_solution_answer(
        self,
        task_title: str,
        candidate_code: str,
        question: str,
        candidate_answer: str,
        candidate_level: str
    ) -> Dict[str, Any]:
        """
        📝 Evaluate Solution Answer - Score candidate's answer about their solution
        Returns score (0-100) with feedback
        """
        user_prompt = SOLUTION_ANSWER_EVAL_USER.format(
            task_title=task_title,
            candidate_code=candidate_code,
            question=question,
            candidate_answer=candidate_answer,
            candidate_level=candidate_level
        )
        
        messages = [
            {"role": "system", "content": SOLUTION_ANSWER_EVAL_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.2, max_tokens=512)
        
        # Clean response
        response = self._clean_think_tags(response)
        
        return self._parse_json_response(response, {
            "score": 50,
            "correctness": 50,
            "completeness": 50,
            "understanding": 50,
            "feedback": "Ответ учтён в оценке.",
            "correct_answer": None
        })
    
    # ========== LEGACY METHODS (for backward compatibility) ==========
    
    async def generate_task(
        self,
        level: str,
        track: str,
        history_summary: str = ""
    ) -> Dict[str, Any]:
        """Generate adaptive task (legacy - prefer task_pool)"""
        system_prompt = """/no_think
Ты — технический интервьюер. Сгенерируй ОДНУ задачу по программированию.
Уровень: {level}. Направление: {track}.

Формат JSON:
{{
  "title": "название",
  "description": "условие на русском",
  "input_format": "формат входа",
  "output_format": "формат выхода",
  "examples": [{{"input": "...", "output": "...", "explanation": "..."}}],
  "constraints": "ограничения",
  "difficulty_level": "{level}",
  "topic_tags": ["..."]
}}""".format(level=level, track=track)
        
        user_prompt = f"""Сгенерируй задачу для {level} {track}-разработчика.
История: {history_summary or 'Первая задача'}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.4, max_tokens=1024)
        
        return self._parse_json_response(response, {
            "title": "Сумма двух чисел",
            "description": "Напишите функцию, которая возвращает сумму двух чисел.",
            "examples": [{"input": "2, 3", "output": "5", "explanation": "2+3=5"}],
            "difficulty_level": level,
            "topic_tags": ["math"]
        })
    
    async def generate_bug_hunter_tests(
        self,
        task_text: str,
        user_code: str,
        known_tests: str
    ) -> Dict[str, Any]:
        """Generate edge case tests to break candidate's code"""
        system_prompt = """/no_think
Ты — Bug Hunter. Найди слабые места в коде и сгенерируй тесты, которые его сломают.

JSON ответ:
{
  "generated_tests": [
    {"input": "тест", "description": "почему сломает"}
  ]
}"""
        
        user_prompt = f"""Задача: {task_text}
Код: {user_code}
Существующие тесты: {known_tests}

Сгенерируй 3-5 тестов-edge cases."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.code_completion(messages, temperature=0.3, max_tokens=512)
        
        return self._parse_json_response(response, {"generated_tests": []})
    
    async def generate_edge_case_tests_enhanced(
        self,
        task_description: str,
        input_format: str,
        output_format: str,
        examples: str,
        candidate_code: str,
        existing_tests: str
    ) -> Dict[str, Any]:
        """Enhanced Bug Hunter with security checks"""
        from .code_sanitizer import sanitize_code_for_llm, get_security_summary
        
        security_report = get_security_summary(candidate_code)
        
        if security_report["prompt_injection"]["detected"]:
            return {
                "security_blocked": True,
                "security_report": security_report,
                "analysis": {
                    "detected_algorithm": "BLOCKED",
                    "potential_weaknesses": ["Обнаружена попытка манипуляции"],
                    "missing_checks": []
                },
                "edge_case_tests": []
            }
        
        sanitized_code, sanitize_report = sanitize_code_for_llm(candidate_code)
        
        result = await self.generate_bug_hunter_tests(
            task_description, 
            sanitized_code, 
            existing_tests
        )
        
        result["security_report"] = security_report
        result["sanitize_report"] = sanitize_report
        result["security_blocked"] = False
        
        return result
    
    async def check_explanation(
        self,
        task_text: str,
        user_code: str,
        user_explanation: str
    ) -> Dict[str, Any]:
        """Check if candidate understands their solution"""
        system_prompt = """/no_think
Оцени, насколько кандидат понимает своё решение.

JSON:
{
  "communication_score": 0-100,
  "understanding_level": "low|medium|high",
  "comment": "комментарий"
}"""
        
        user_prompt = f"""Задача: {task_text}
Код: {user_code}
Объяснение: {user_explanation}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3, max_tokens=384)
        
        return self._parse_json_response(response, {
            "communication_score": 70,
            "understanding_level": "medium",
            "comment": "Кандидат понимает основы своего решения"
        })
    
    async def generate_boss_fight_task(self, interview_weaknesses_json: str) -> Dict[str, Any]:
        """Generate personalized final challenge based on weaknesses"""
        return await self.generate_task("senior", "algorithms", interview_weaknesses_json)


# Global client instance
scibox_client = SciBoxClient()

# пидормот
