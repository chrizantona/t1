# Реализация Claude Opus промптов для VibeCode

## Статус: ✅ Полностью реализовано

Все 8 модулей промптов из PROMPTS_CLAUDE_OPUS.md реализованы и интегрированы в backend.

---

## Реализованные модули

### 1. Resume Analyzer (`/api/claude/resume/analyze`)
**Назначение:** Парсинг PDF резюме → структурированные данные

**Входные данные:**
```json
{
  "resume_text": "текст резюме"
}
```

**Выходные данные:**
```json
{
  "years_of_experience": 3.5,
  "tracks": ["backend", "fullstack"],
  "resume_self_grade": "middle",
  "tech_stack": ["Python", "Django", "PostgreSQL"],
  "domains": ["fintech", "e-commerce"],
  "summary": "Опытный backend-разработчик..."
}
```

---

### 2. Vacancy Analyzer (`/api/claude/vacancy/analyze`)
**Назначение:** Разбор вакансии → структурированные требования

**Входные данные:**
```json
{
  "vacancy_text": "текст вакансии"
}
```

**Выходные данные:**
```json
{
  "role_title": "Senior Backend Developer",
  "expected_grade": "senior",
  "tracks": ["backend"],
  "must_have_skills": ["Python", "PostgreSQL", "Kubernetes"],
  "nice_to_have_skills": ["AWS", "Kafka"],
  "domains": ["fintech"],
  "soft_requirements": ["коммуникация с бизнесом"],
  "focus_areas": ["производительность", "дизайн API"]
}
```

---

### 3. Resume-Vacancy Matcher (`/api/claude/match`)
**Назначение:** Матчинг кандидата и вакансии

**Входные данные:**
```json
{
  "resume_parsed": {...},
  "vacancy_parsed": {...},
  "interview_summary": "optional"
}
```

**Выходные данные:**
```json
{
  "match_score": 75,
  "match_summary": "Кандидат хорошо подходит по backend-навыкам...",
  "strong_fit": ["Python", "PostgreSQL"],
  "gaps": ["нет опыта с Kubernetes"],
  "recommended_topics_for_tasks": ["дизайн REST API"],
  "recommended_difficulty": "middle"
}
```

---

### 4. Task Generator (`/api/claude/task/generate`)
**Назначение:** Генерация задач и автотестов (оффлайн)

**Входные данные:**
```json
{
  "track": "backend",
  "difficulty": "middle",
  "mode": "coding",
  "target_skills": ["REST API", "PostgreSQL"],
  "vacancy_summary": "optional"
}
```

**Выходные данные:**
```json
{
  "task_type": "coding",
  "track": "backend",
  "difficulty": "middle",
  "title": "REST API для задач",
  "description": "Реализуйте CRUD API...",
  "input_format": "...",
  "output_format": "...",
  "constraints": "...",
  "visible_examples": [...],
  "hidden_tests": [...],
  "llm_rubric": {...}
}
```

---

### 5. Hint Generator (`/api/claude/hints/generate`)
**Назначение:** Генерация подсказок по задаче (3 уровня)

**Входные данные:**
```json
{
  "task_description": "условие задачи",
  "candidate_code": "текущий код",
  "test_results": "{}",
  "grade": "middle",
  "difficulty": "middle"
}
```

**Выходные данные:**
```json
{
  "soft_hint": "Подумайте о структуре данных...",
  "medium_hint": "Используйте хеш-таблицу для...",
  "hard_hint": "Создайте словарь, где ключ - значение..."
}
```

---

### 6. Live Interview Assistant (`/api/claude/chat/respond`)
**Назначение:** Live-чат интервьюера (reactive/proactive)

**Входные данные:**
```json
{
  "mode": "reactive",
  "task_description": "условие задачи",
  "candidate_code": "текущий код",
  "test_results": "{}",
  "user_message": "Не понимаю, как начать",
  "grade": "junior",
  "difficulty": "easy"
}
```

**Выходные данные:**
```json
{
  "message": "Давайте разберём задачу по шагам..."
}
```

---

### 7. Solution Reviewer (`/api/claude/solution/review`)
**Назначение:** Усиленная проверка решений поверх тестов

**Входные данные:**
```json
{
  "task_description": "условие задачи",
  "candidate_code": "код решения",
  "test_results": "{}",
  "grade": "middle",
  "difficulty": "middle"
}
```

**Выходные данные:**
```json
{
  "correctness_score": 85,
  "robustness_score": 70,
  "code_quality_score": 80,
  "algo_complexity_level": "medium",
  "short_verdict": "Решение корректное, но есть проблемы с edge-cases",
  "strengths": ["чистый код", "хорошая структура"],
  "weaknesses": ["не обработаны пустые входные данные"],
  "suggested_improvements": ["добавить валидацию входных данных"]
}
```

---

### 8. AI Code Detector (`/api/claude/ai/detect`)
**Назначение:** Детекция AI-сгенерированного кода

**Входные данные:**
```json
{
  "candidate_code": "код для анализа"
}
```

**Выходные данные:**
```json
{
  "ai_likeness_score": 45,
  "explanation": "Код имеет некоторые признаки AI-генерации...",
  "suspicious_signals": ["шаблонные комментарии", "учебные названия переменных"]
}
```

---

### 9. Final Report Generator (`/api/claude/report/generate`)
**Назначение:** Финальный отчёт по кандидату

**Входные данные:**
```json
{
  "resume_parsed": {...},
  "vacancy_parsed": {...},
  "match_result": {...},
  "interview_metrics": {...},
  "trust_and_ai": {...},
  "solution_review_summary": {...}
}
```

**Выходные данные:**
```json
{
  "final_grade": "middle",
  "final_track": "backend",
  "hire_recommendation": "yes",
  "hire_comment": "Кандидат показал хорошие навыки...",
  "report_markdown": "# Отчёт по кандидату\n\n## Профиль...",
  "key_strengths": ["Python", "SQL"],
  "key_risks": ["мало опыта с highload"],
  "suggested_next_steps": ["пригласить на интервью с тимлидом"]
}
```

---

## Структура файлов

```
backend/app/
├── prompts/
│   ├── __init__.py              # Экспорт всех промптов
│   ├── resume_analyzer.py       # Промпт 1
│   ├── vacancy_analyzer.py      # Промпт 2
│   ├── resume_vacancy_matcher.py # Промпт 2.3
│   ├── task_generator.py        # Промпт 3
│   ├── hint_generator.py        # Промпт 4
│   ├── live_assistant.py        # Промпт 5
│   ├── solution_reviewer.py     # Промпт 6
│   ├── ai_detector.py           # Промпт 7
│   └── final_report.py          # Промпт 8
├── services/
│   └── claude_service.py        # Сервис для вызова LLM
├── schemas/
│   └── claude.py                # Pydantic схемы
└── api/
    └── claude.py                # API endpoints
```

---

## Использование

### Запуск API

```bash
cd t1/backend
uvicorn app.main:app --reload
```

### Документация API

Откройте: `http://localhost:8000/docs`

Все endpoints доступны в разделе "Claude LLM".

---

## Бизнес-цепочка end-to-end

1. **HR загружает вакансию** → `POST /api/claude/vacancy/analyze`
2. **Кандидат загружает PDF резюме** → `POST /api/claude/resume/analyze`
3. **Система делает матчинг** → `POST /api/claude/match`
4. **Генерация задач** (оффлайн) → `POST /api/claude/task/generate`
5. **Во время решения:**
   - Подсказки → `POST /api/claude/hints/generate`
   - Live-чат → `POST /api/claude/chat/respond`
6. **После каждой задачи:**
   - Проверка решения → `POST /api/claude/solution/review`
   - AI-детекция → `POST /api/claude/ai/detect`
7. **В конце:**
   - Финальный отчёт → `POST /api/claude/report/generate`

---

## Особенности реализации

### Формат ответов
- Все промпты возвращают JSON (кроме live_assistant)
- Используется префикс `/no_think` для стабильного JSON-вывода
- Автоматический парсинг JSON из ответа LLM

### Обработка ошибок
- Все endpoints возвращают HTTP 500 при ошибках LLM
- Детальное сообщение об ошибке в response

### Модели SciBox
- `qwen3-32b-awq` - основная модель для всех промптов
- `qwen3-coder-30b-a3b-instruct-fp8` - для кодовых задач (в llm_grader)

---

## Интеграция с существующей системой

### Anti-Cheat
AI-детектор (`ai_likeness_score`) интегрируется с системой анти-чита:
```python
# В anti_cheat_advanced.py
ai_result = await detect_ai_code(candidate_code)
signals.ai_likeness = ai_result["ai_likeness_score"]
```

### Grading
Solution Reviewer интегрируется с системой грейдинга:
```python
# В grading_service.py
review = await review_solution(task, code, tests, grade, difficulty)
coding_score = (review["correctness_score"] + review["code_quality_score"]) / 2
```

### Reporting
Final Report Generator использует все метрики:
```python
# В reporting.py
report = await generate_final_report(
    resume_parsed, vacancy_parsed, match_result,
    interview_metrics, trust_and_ai, solution_review_summary
)
```

---

## Чек-лист реализации

- [x] Промпт 1: Resume Analyzer
- [x] Промпт 2: Vacancy Analyzer
- [x] Промпт 2.3: Resume-Vacancy Matcher
- [x] Промпт 3: Task Generator
- [x] Промпт 4: Hint Generator
- [x] Промпт 5: Live Interview Assistant
- [x] Промпт 6: Solution Reviewer
- [x] Промпт 7: AI Code Detector
- [x] Промпт 8: Final Report Generator
- [x] API endpoints для всех модулей
- [x] Pydantic схемы для валидации
- [x] Интеграция с main.py
- [x] Документация
