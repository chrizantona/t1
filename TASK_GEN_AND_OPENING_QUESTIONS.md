# VibeCode — отображение генерации задач + бот, который задаёт первый вопрос

Этот README — ТЗ для доработки двух фич, которые сильно бустят демонстрацию:

1. **UI «как LLM генерирует задачу»** — не просто магия, а понятный пользователю процесс.
2. **Бот сам начинает диалог по задаче** — сразу задаёт умный первый вопрос (асимптотика, подход, pandas и т.п.).

Стек: **React + TS / FastAPI + Python / Postgres / Claude Opus 4.5 (+ SciBox при желании).**

---

## 1. Отображение того, как LLM генерирует задачу

### 1.1. Что именно хотим показать

Когда система подбирает/генерирует задачу (особенно если она подстраивается под вакансию и резюме), нужно:

- визуально показать, что **идёт работа LLM**;
- показать **ключевые параметры**, на основе которых сформирована задача:
  - трек (backend/ml/...),
  - целевые скиллы (Python, SQL, Docker),
  - уровень сложности (easy/middle/hard),
  - контекст вакансии;
- дать краткое человеческое объяснение:
  - «Эта задача выбрана, чтобы проверить работу с массивами и асимптотику на уровне Middle backend вакансии».

Не нужно раскрывать внутренний chain-of-thought, только **объяснение выбора**.

---

### 1.2. Изменения в модели данных

#### 1.2.1. Таблица `interview_tasks`

Предположим, у нас уже есть таблица, где храним задачи, которые реально дали кандидату:

```sql
CREATE TABLE interview_tasks (
  id                uuid primary key,
  interview_id      uuid not null,
  vacancy_id        uuid not null,
  candidate_id      uuid not null,

  task_payload      jsonb not null,  -- сама задача (описание, примеры, тесты)
  block_type        text not null,   -- "algo" | "practice" | "theory"
  source_type       text not null,   -- "from_pool" | "llm_generated"

  -- НОВОЕ:
  generation_meta   jsonb not null,  -- метаданные о генерации/выборе

  created_at        timestamptz default now()
);
```

Структура `generation_meta`:

```json
{
  "llm_model": "claude-3.5-opus",
  "track": "backend",
  "difficulty": "middle",
  "target_skills": ["python", "sql", "algorithms"],
  "vacancy_id": "uuid-вакансии",
  "vacancy_level": "middle",
  "candidate_initial_grade": "middle_plus",
  "selection_reason": "Кандидат и вакансия — backend middle. Выбрана задача на работу с массивами и асимптотикой, чтобы проверить понимание сложности и аккуратность кода.",
  "generation_timestamp": "2025-11-26T10:15:00Z"
}
```

---

### 1.3. Backend: endpoint генерации/выбора задачи

#### 1.3.1. Endpoint

```http
POST /api/interviews/{interview_id}/tasks/generate
```

Request body (минимум):

```json
{
  "block_type": "algo",
  "track": "backend",
  "target_skills": ["python", "algorithms"],
  "vacancy_id": "uuid",
  "candidate_id": "uuid"
}
```

Ответ:

```json
{
  "task": { ... },               // JSON задачи (как в нашей базе)
  "generation_meta": { ... }     // метаданные, как выше
}
```

#### 1.3.2. Логика внутри

1. На основе:
   - Vacancy (skill_matrix, track, level),
   - CandidateVacancyContext (initial_grade, skill_matrix),
   - переданных `block_type`, `target_skills`,
   - решаем:
     - `difficulty` (easy/middle/hard),
     - берем ли задачу из пула (`from_pool`) или генерируем новой LLM.

2. Если берём из пула:
   - `task_payload` = найденная запись из нашей базы задач,
   - `generation_meta.selection_reason` формируем через **отдельный вызов** Claude.

3. Если генерируем через LLM:
   - вызываем промпт `TASK_GENERATOR` (см. `PROMPTS_CLAUDE_OPUS.md`),
   - получаем JSON задачи,
   - **дополнительно** вызываем `TASK_SELECTION_EXPLAINER` (ниже) для красивого текста.

Сохраняем в `interview_tasks`:

- `task_payload`,
- `generation_meta`.

---

### 1.4. Claude-промпт: `TASK_SELECTION_EXPLAINER`

**System prompt:**

```text
Ты — Claude Opus 4.5, модуль, который объясняет человеку, ПОЧЕМУ была выбрана или сгенерирована именно такая задача.

Твоя задача:
- кратко и понятным языком описать логику выбора задачи:
  - под какую вакансию/трек она подобрана,
  - какие скиллы и на каком уровне проверяет,
  - почему такой уровень сложности,
  - почему она релевантна опыту кандидата.

НЕ раскрывай все внутренние шаги рассуждений, не пиши chain-of-thought.
Дай только итоговое объяснение, максимум 3–5 предложений.

Ответь строго в формате JSON.
```

**User prompt:**

```text
=== VACANCY_INFO ===
{{vacancy_parsed_json_or_brief}}
=== END_VACANCY_INFO ===

=== CANDIDATE_INFO ===
{{candidate_skill_matrix_or_brief}}
=== END_CANDIDATE_INFO ===

=== TASK_META ===
{
  "block_type": "{{block_type}}",        // algo | practice | theory
  "track": "{{track}}",                  // backend | ml | ...
  "difficulty": "{{difficulty}}",
  "target_skills": {{json_target_skills_array}}
}
=== END_TASK_META ===

=== TASK_PAYLOAD ===
{{task_payload_json}}
=== END_TASK_PAYLOAD ===

Верни JSON:

{
  "selection_reason": "краткое объяснение для человека (3–5 предложений на русском)"
}
```

Ответ вставляем в `generation_meta.selection_reason`.

---

### 1.5. Frontend: как это красиво показать

#### 1.5.1. Экран «Подбор задачи»

Когда кандидат нажимает «Начать блок» или «Следующая задача»:

1. Фронт дергает `POST /tasks/generate`.
2. Пока ждём ответ:
   - показываем шаги (skeleton):

     - «1. Анализ вакансии и резюме»
     - «2. Выбор трека и сложности»
     - «3. Подбор задачи под твой уровень»

3. После ответа:

   - показываем саму задачу;
   - рядом/сверху блок:

     ```text
     Как была выбрана задача:

     Трек: Backend · Уровень: Middle
     Цель: проверить Python + алгоритмическое мышление на уровне middle вакансии.
     Почему именно она: {{generation_meta.selection_reason}}
     ```

4. Дополнительно можно дать маленький бейдж:
   - «Задача подобрана LLM под эту вакансию»  
     или  
   - «LLM-ассистент составил задачу на основе вакансии и резюме».

Это полностью закрывает требование: **отображать процесс работы LLM над задачей**.

---

## 2. Бот, который первым задаёт вопрос по задаче

Сейчас: бот отвечает **только когда кандидат пишет**.  
Нужно: как только выдали задачу — бот сам первым задаёт умный вопрос, контекстный для типа задачи.

Примеры:

- Алгоритмы:
  - «Какую асимптотическую сложность, по твоему мнению, должно иметь оптимальное решение?»
- ML:
  - «Какие шаги предобработки данных ты бы сделал в первую очередь?»
  - или «Расскажи, как ты обычно работаешь с pandas при такой задаче».
- Backend:
  - «Какие граничные кейсы нужно учесть в этом API?»
- Data/SQL:
  - «Как бы ты проверил корректность результатов запросов?»

---

### 2.1. Общий flow

1. Backend сгенерировал/выбрал задачу и создал запись в `interview_tasks`.
2. После этого **сразу**:
   - дергаем LLM с промптом `TASK_OPENING_QUESTION`,
   - сохраняем её как первое сообщение в `interview_chat_messages`.
3. Фронт:
   - получает задачу + список сообщений;
   - сразу видит в чате вопрос от бота.

---

### 2.2. Таблица сообщений чата

Если её ещё нет:

```sql
CREATE TABLE interview_chat_messages (
  id             uuid primary key,
  interview_id   uuid not null,
  task_id        uuid,           -- может быть null для общих сообщений
  sender_type    text not null,  -- "bot" | "candidate"
  sender_name    text not null,  -- "VibeCode AI" | "Candidate"
  message_text   text not null,
  created_at     timestamptz default now()
);
```

---

### 2.3. Claude-промпт: `TASK_OPENING_QUESTION`

**System prompt:**

```text
Ты — Claude Opus 4.5, AI-интервьюер в платформе VibeCode.

Твоя задача — САМЫМ ПЕРВЫМ задать умный и короткий вопрос по только что выданной задаче, чтобы:
- включить кандидата в диалог,
- подсветить, на что важно обратить внимание,
- НЕ подсказать готовое решение.

Примеры:
- Для алгоритмической задачи: спросить про ожидаемую асимптотическую сложность, структуру данных, граничные случаи.
- Для ML-задачи: про набор данных, предобработку, метрики качества, работу с pandas.
- Для backend-задачи: про контракт API, ошибки, транзакции, индексы.
- Для data/SQL: про схему таблиц, join'ы, проверку корректности запросов.

Правила:
- Один конкретный вопрос, 1–3 предложения максимум.
- Никаких решений и подсказок с готовым кодом.
- Вопрос должен быть адаптирован к уровню кандидата (junior/middle/senior) и сложности задачи (easy/middle/hard).

Ответ — ОДНА строка с вопросом, без JSON и без пояснений.
```

**User prompt:**

```text
=== TASK ===
{{task_description}}
=== END_TASK ===

Тип блока: {{block_type}}            // algo | practice | theory
Трек: {{track}}                      // backend | ml | data | frontend | devops
Уровень кандидата: {{candidate_grade}}     // junior | middle | senior
Сложность задачи: {{difficulty}}           // easy | middle | hard

Сформулируй один открытый вопрос кандидату по этой задаче, чтобы начать диалог.
```

---

### 2.4. Backend-функция

```python
async def create_task_and_opening_question(
    interview_id: UUID,
    vacancy_id: UUID,
    candidate_id: UUID,
    block_type: str,
    track: str,
    target_skills: list[str],
    ...
):
    # 1. генерируем/выбираем задачу
    task, generation_meta = await generate_task_with_meta(...)

    # 2. сохраняем interview_tasks
    task_id = await save_interview_task(
        interview_id=interview_id,
        vacancy_id=vacancy_id,
        candidate_id=candidate_id,
        task_payload=task,
        block_type=block_type,
        source_type="from_pool_or_llm",
        generation_meta=generation_meta,
    )

    # 3. вызываем Claude для opening question
    opening_question = await call_claude_task_opening_question(
        task_description=task["description"],
        block_type=block_type,
        track=track,
        candidate_grade=...,   # наш текущий грейд
        difficulty=task["difficulty"],
    )

    # 4. сохраняем сообщение бота
    await save_chat_message(
        interview_id=interview_id,
        task_id=task_id,
        sender_type="bot",
        sender_name="VibeCode AI",
        message_text=opening_question,
    )

    return task_id
```

---

### 2.5. Frontend: как это выглядит

1. После нажатия «Начать задачу» фронт делает запрос:

   ```ts
   const res = await fetch(`/api/interviews/${interviewId}/tasks/start`, {
     method: "POST",
     body: JSON.stringify({ block_type, track, target_skills }),
   });
   ```

   Ответ:

   ```json
   {
     "task": { ... },
     "generation_meta": { ... },
     "initial_messages": [
       {
         "sender_type": "bot",
         "sender_name": "VibeCode AI",
         "message_text": "Первый вопрос по задаче..."
       }
     ]
   }
   ```

2. UI:

   - слева — текст задачи,
   - справа/снизу — чат, где **уже есть** первое сообщение от бота:
     - «Какую асимптотическую сложность ты планируешь достичь в своём решении?»  
     или  
     - «С чего бы ты начал работу с данными в этой задаче?»

3. Кандидат отвечает в чат, и live-ассистент (уже через `LIVE_INTERVIEW_ASSISTANT`) продолжает диалог.

---

## 3. Что можно рассказать на чекпоинте

Про генерацию:

> «При выдаче задачи мы не просто подкидываем рандомную задачку.  
>  LLM учитывает вакансию, скилл-матрицу и уровень кандидата, генерирует или подбирает задачу и сразу объясняет, почему именно она: какие скиллы проверяет, под какой грейд вакансии таргетится.  
>  Это видно в UI — кандидат и рекрутер видят, как задача “родилась”.»

Про первый вопрос бота:

> «Как только задача показана, AI-интервьюер сам начинает диалог — задаёт первый контекстный вопрос по задаче: про асимптотику, pandas, дизайн API и т.д.  
>  Это очень похоже на живое собеседование: не просто задачка на экране, а реальный диалог с умным интервьюером.»

Этот README можно сохранить в репе как  
`TASK_GEN_AND_OPENING_QUESTIONS.md` и использовать как ТЗ на доработку.
