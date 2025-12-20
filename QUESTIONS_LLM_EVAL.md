# Интеграция `questions.json` + LLM-проверка ответов

Этот README — ТЗ для Cursor: как подключить базу вопросов `questions.json` к платформе **VibeCode** и как сделать так, чтобы **ответы проверяла LLM**, а не ручные тест-кейсы.

Ключевые моменты:

- Вопросы берём из `questions.json` (категории: algorithms / frontend / backend / data-science).
- Для каждого вопроса выбираем **тип панели** на фронте (какой редактор показать).
- Кандидат отвечает (кодом или текстом).
- Backend отправляет вопрос + ответ в **SciBox LLM**, та возвращает `score` и `feedback` в формате JSON.
- Эти баллы идут в нашу общую систему грейдов (`theory_score` / `coding_score`).

---

## 1. Структура `questions.json`

Файл уже есть (путь: `questions.json` в корне / в папке `data`). Пример элемента:

```json
{
  "id": 1,
  "category": "algorithms",
  "difficulty": "easy",
  "question": "Дан массив целых чисел nums и целое число target..."
}
```

Поля:

- `id: number` — уникальный ID вопроса.
- `category: "algorithms" | "frontend" | "backend" | "data-science"`.
- `difficulty: "easy" | "medium" | "hard"`.
- `question: string` — текст вопроса (может быть формулировкой задачи, теоретическим вопросом и т.д.).

Мы **не** добавляем прямо в JSON решения или тесты — оценкой занимается модель.

---

## 2. Схема таблицы в PostgreSQL

Создаём таблицу `tech_questions`, которая расширяет JSON-структуру метаданными:

```sql
CREATE TYPE question_category AS ENUM (
  'algorithms',
  'frontend',
  'backend',
  'data-science'
);

CREATE TYPE question_difficulty AS ENUM (
  'easy',
  'medium',
  'hard'
);

-- тип панели / редактора на фронте
CREATE TYPE question_panel_type AS ENUM (
  'code_python',   -- классический алгоритмический Python
  'code_frontend', -- React/TS, HTML/CSS
  'code_backend',  -- backend-логика (Python, SQL, архитектура)
  'code_ds',       -- Python + DS-контекст
  'text_only'      -- чисто текстовый ответ (теория)
);

-- способ проверки (все через LLM, но разные роли)
CREATE TYPE question_eval_mode AS ENUM (
  'llm_code',      -- LLM оценивает код-решение
  'llm_theory'     -- LLM оценивает текстовый ответ
);

CREATE TABLE tech_questions (
  id                integer primary key,              -- берем из JSON
  category          question_category not null,
  difficulty        question_difficulty not null,
  question_text     text not null,

  panel_type        question_panel_type not null,
  eval_mode         question_eval_mode not null,

  language_hint     text,                             -- 'python', 'typescript', 'sql', ...

  tags              text[] default '{}',
  created_at        timestamptz default now()
);
```

### 2.1. Маппинг category → panel_type + eval_mode

**Правило по умолчанию (MVP):**

```text
algorithms   → panel_type=code_python   , eval_mode=llm_code   , language_hint='python'
frontend     → panel_type=code_frontend , eval_mode=llm_code   , language_hint='typescript-react'
backend      → panel_type=code_backend  , eval_mode=llm_code   , language_hint='python/sql'
data-science → panel_type=code_ds       , eval_mode=llm_code   , language_hint='python-ds'
```

Если отдельные вопросы окажутся чисто теоретическими (без кода), можно руками обновить им:

```sql
UPDATE tech_questions
SET panel_type = 'text_only', eval_mode = 'llm_theory'
WHERE id IN (...);
```

---

## 3. Импорт `questions.json` в БД

### 3.1. Pydantic‑модель для импорта

```python
# backend/app/models/questions.py

from pydantic import BaseModel
from enum import Enum

class QuestionCategory(str, Enum):
    algorithms = "algorithms"
    frontend = "frontend"
    backend = "backend"
    data_science = "data-science"

class QuestionDifficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class QuestionImport(BaseModel):
    id: int
    category: QuestionCategory
    difficulty: QuestionDifficulty
    question: str
```

### 3.2. Определение panel_type / eval_mode по категории

```python
# backend/app/services/questions_importer.py

from .models.questions import QuestionImport, QuestionCategory
from enum import Enum

class PanelType(str, Enum):
    code_python = "code_python"
    code_frontend = "code_frontend"
    code_backend = "code_backend"
    code_ds = "code_ds"
    text_only = "text_only"

class EvalMode(str, Enum):
    llm_code = "llm_code"
    llm_theory = "llm_theory"

def detect_panel_and_eval(raw: QuestionImport) -> tuple[PanelType, EvalMode, str | None]:
    if raw.category == QuestionCategory.algorithms:
        return PanelType.code_python, EvalMode.llm_code, "python"
    if raw.category == QuestionCategory.frontend:
        return PanelType.code_frontend, EvalMode.llm_code, "typescript-react"
    if raw.category == QuestionCategory.backend:
        return PanelType.code_backend, EvalMode.llm_code, "python/sql"
    if raw.category == QuestionCategory.data_science:
        return PanelType.code_ds, EvalMode.llm_code, "python-ds"
    return PanelType.text_only, EvalMode.llm_theory, None
```

### 3.3. Скрипт импорта

```python
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .models.questions import QuestionImport
from .services.questions_importer import detect_panel_and_eval

QUESTIONS_PATH = Path(__file__).parent / "data" / "questions.json"

async def import_questions(session: AsyncSession) -> None:
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    for item in data:
        raw = QuestionImport(**item)
        panel_type, eval_mode, lang_hint = detect_panel_and_eval(raw)

        await session.execute(
            text("""
                INSERT INTO tech_questions
                  (id, category, difficulty, question_text, panel_type, eval_mode, language_hint)
                VALUES
                  (:id, :category, :difficulty, :question_text, :panel_type, :eval_mode, :language_hint)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": raw.id,
                "category": raw.category.value,
                "difficulty": raw.difficulty.value,
                "question_text": raw.question,
                "panel_type": panel_type.value,
                "eval_mode": eval_mode.value,
                "language_hint": lang_hint,
            }
        )
    await session.commit()
```

---

## 4. Backend API: выдача вопросов и приём ответов

### 4.1. Схема ответа с вопросом

```python
# backend/app/api/schemas/questions.py

from pydantic import BaseModel
from enum import Enum

class PanelType(str, Enum):
    code_python = "code_python"
    code_frontend = "code_frontend"
    code_backend = "code_backend"
    code_ds = "code_ds"
    text_only = "text_only"

class QuestionOut(BaseModel):
    id: int
    category: str
    difficulty: str
    question_text: str
    panel_type: PanelType
    language_hint: str | None = None
```

### 4.2. Получить вопрос (адаптивный блок / теория)

```python
# backend/app/api/routes/questions.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.questions import QuestionOut
from ...db import get_async_session

router = APIRouter(prefix="/questions", tags=["questions"])

@router.get("/next", response_model=QuestionOut)
async def get_next_question(
    category: str = Query(..., description="algorithms|frontend|backend|data-science"),
    difficulty: str = Query(..., description="easy|medium|hard"),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        """
        SELECT id, category, difficulty, question_text, panel_type, language_hint
        FROM tech_questions
        WHERE category = :category AND difficulty = :difficulty
        ORDER BY random()
        LIMIT 1
        """,
        {"category": category, "difficulty": difficulty},
    )
    row = result.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No question found")

    return QuestionOut(
        id=row.id,
        category=row.category,
        difficulty=row.difficulty,
        question_text=row.question_text,
        panel_type=row.panel_type,
        language_hint=row.language_hint,
    )
```

### 4.3. Приём ответа кандидата

```python
# backend/app/api/schemas/answers.py

from pydantic import BaseModel

class QuestionAnswerIn(BaseModel):
    question_id: int
    answer_code: str | None = None   # для кодовых панелей
    answer_text: str | None = None   # для текстового/объяснений

class QuestionAnswerEval(BaseModel):
    score: int          # 0-100
    passed: bool
    short_feedback: str
    mistakes: list[str] = []
```

Эндпоинт:

```python
@router.post("/{question_id}/answer", response_model=QuestionAnswerEval)
async def submit_answer(
    question_id: int,
    payload: QuestionAnswerIn,
    session: AsyncSession = Depends(get_async_session),
):
    # 1. достаём метаданные вопроса
    qrow = await session.execute(
        """
        SELECT id, category, difficulty, question_text, panel_type, eval_mode, language_hint
        FROM tech_questions
        WHERE id = :id
        """,
        {"id": question_id},
    )
    q = qrow.fetchone()
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")

    # 2. вызываем LLM-оценку
    eval_result = await llm_grade_answer(
        question_text=q.question_text,
        panel_type=q.panel_type,
        eval_mode=q.eval_mode,
        language_hint=q.language_hint,
        answer_code=payload.answer_code,
        answer_text=payload.answer_text,
    )

    # 3. сохраняем результат в БД (таблица interview_question_results)
    # ... (опционально)

    return eval_result
```

---

## 5. LLM‑проверка ответов (без ручных тестов)

### 5.1. Общий подход

Мы **не** пишем для каждого вопроса набор тестов/ожидаемых ответов.  
Вместо этого:

- Передаём в LLM:
  - текст вопроса,
  - ответ кандидата (код/текст),
  - категорию/сложность/язык (для контекста).
- Модель **сама думает**, насколько ответ корректен, и возвращает:
  - `score` (0–100),
  - `passed` (true/false),
  - `short_feedback` и список ошибок.

### 5.2. Модели SciBox

- `qwen3-coder-30b-a3b-instruct-fp8` — для всех кодовых вопросов (`eval_mode=llm_code`).
- `qwen3-32b-awq` — для чисто теоретических (`eval_mode=llm_theory`, если появятся).

### 5.3. Пример функции `llm_grade_answer`

```python
from openai import OpenAI
import json

client = OpenAI(
    api_key=SCIBOX_API_KEY,
    base_url="https://llm.t1v.scibox.tech/v1",
)

async def llm_grade_answer(
    question_text: str,
    panel_type: str,
    eval_mode: str,
    language_hint: str | None,
    answer_code: str | None,
    answer_text: str | None,
) -> dict:
    if eval_mode == "llm_code":
        model = "qwen3-coder-30b-a3b-instruct-fp8"
    else:
        model = "qwen3-32b-awq"

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
        "  \"score\": 0-100,\n"
        "  \"passed\": true/false,\n"
        "  \"short_feedback\": \"краткий текст по-русски\",\n"
        "  \"mistakes\": [\"список основных ошибок\"]\n"
        "}\n"
    )

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
```

> Для этой базы вопросов мы **опираемся на LLM-оценку**,  
> а не на заранее прописанные тест-кейсы.

---

## 6. Фронтенд: выбор панели и отправка ответа

### 6.1. Типы на фронте

```ts
// frontend/src/types/questions.ts

export type PanelType =
  | "code_python"
  | "code_frontend"
  | "code_backend"
  | "code_ds"
  | "text_only";

export interface Question {
  id: number;
  category: string;
  difficulty: string;
  question_text: string;
  panel_type: PanelType;
  language_hint?: string | null;
}

export interface QuestionAnswerEval {
  score: number;         // 0-100
  passed: boolean;
  short_feedback: string;
  mistakes: string[];
}
```

### 6.2. Рендер панели по `panel_type`

```tsx
// frontend/src/components/question/QuestionWorkspace.tsx

import { Question } from "@/types/questions";
import { PythonCodePanel } from "./panels/PythonCodePanel";
import { FrontendCodePanel } from "./panels/FrontendCodePanel";
import { BackendCodePanel } from "./panels/BackendCodePanel";
import { DataSciencePanel } from "./panels/DataSciencePanel";
import { TextAnswerPanel } from "./panels/TextAnswerPanel";

type Props = {
  question: Question;
};

export const QuestionWorkspace: React.FC<Props> = ({ question }) => {
  switch (question.panel_type) {
    case "code_python":
      return <PythonCodePanel question={question} />;
    case "code_frontend":
      return <FrontendCodePanel question={question} />;
    case "code_backend":
      return <BackendCodePanel question={question} />;
    case "code_ds":
      return <DataSciencePanel question={question} />;
    case "text_only":
    default:
      return <TextAnswerPanel question={question} />;
  }
};
```

### 6.3. Вызов API проверки

```ts
// frontend/src/api/questions.ts

import { QuestionAnswerEval } from "@/types/questions";

export async function submitQuestionAnswer(params: {
  questionId: number;
  answerCode?: string;
  answerText?: string;
}): Promise<QuestionAnswerEval> {
  const res = await fetch(`/api/questions/${params.questionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question_id: params.questionId,
      answer_code: params.answerCode ?? null,
      answer_text: params.answerText ?? null,
    }),
  });

  if (!res.ok) {
    throw new Error("Failed to submit answer");
  }
  return res.json();
}
```

---

## 7. Связка с адаптивностью и отчётами

- Адаптивный движок (`Adaptive Engine`) подмешивает вопросы из `tech_questions`:
  - по `category` = трек (backend/frontend/algorithms/data-science),
  - по `difficulty` = уровень (easy/medium/hard).
- Результаты LLM‑оценки (`score`, `passed`) по этим вопросам:
  - идут в `theory_score` / `coding_score` как часть общей формулы грейда,
  - используются в финальном отчёте (какие темы даются тяжело, где сильные ответы).

---

## 8. To‑Do для Cursor (шорт-лист)

**Backend:**

- [ ] Создать ENUM’ы `question_category`, `question_difficulty`, `question_panel_type`, `question_eval_mode`.
- [ ] Создать таблицу `tech_questions`.
- [ ] Написать скрипт импорта `questions.json` → `tech_questions`.
- [ ] Реализовать `GET /questions/next`.
- [ ] Реализовать `POST /questions/{id}/answer` + `llm_grade_answer` с использованием SciBox LLM.

**Frontend:**

- [ ] Добавить типы `Question`, `PanelType`, `QuestionAnswerEval`.
- [ ] Реализовать компонент `QuestionWorkspace` и панели:
  - `PythonCodePanel`,
  - `FrontendCodePanel`,
  - `BackendCodePanel`,
  - `DataSciencePanel`,
  - `TextAnswerPanel`.
- [ ] Реализовать вызов API проверки и показ `score` + `short_feedback`.

Этого достаточно, чтобы платформа задавала вопросы из `questions.json`, давала кандидату правильный редактор под тип вопроса и в реальном времени получала оценку от модели.
