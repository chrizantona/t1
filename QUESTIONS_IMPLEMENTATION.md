# Реализация системы LLM-оценки вопросов

## Статус: ✅ Полностью реализовано (Backend + Frontend)

Система LLM-оценки технических вопросов полностью реализована согласно спецификации QUESTIONS_LLM_EVAL.md.

---

## Backend ✅

### Реализованные компоненты

#### 1. Модели данных (`app/models/questions.py`)
- `TechQuestion` - модель вопроса с полями:
  - `id`, `category`, `difficulty`, `question_text`
  - `panel_type` - тип панели для фронтенда
  - `eval_mode` - режим оценки (llm_code/llm_theory)
  - `language_hint` - подсказка языка программирования
  - `tags`, `created_at`

#### 2. Pydantic схемы (`app/schemas/questions.py`)
- `QuestionImport` - для импорта из JSON
- `QuestionOut` - для отдачи вопроса клиенту
- `QuestionAnswerIn` - для приема ответа
- `QuestionAnswerEval` - для результата оценки

#### 3. Сервисы

**`app/services/questions_importer.py`**
- `detect_panel_and_eval()` - определяет тип панели и режим оценки по категории:
  - algorithms → code_python + llm_code + python
  - frontend → code_frontend + llm_code + typescript-react
  - backend → code_backend + llm_code + python/sql
  - data-science → code_ds + llm_code + python-ds

**`app/services/llm_grader.py`**
- `llm_grade_answer()` - оценка ответа через SciBox LLM:
  - Использует `qwen3-coder-30b-a3b-instruct-fp8` для кода
  - Использует `qwen3-32b-awq` для теории
  - Возвращает: score (0-100), passed, short_feedback, mistakes

#### 4. API endpoints (`app/api/questions.py`)
- `GET /api/questions/next` - получить случайный вопрос по категории и сложности
- `POST /api/questions/{id}/answer` - отправить ответ на оценку

#### 5. Скрипт импорта (`app/scripts/import_questions.py`)
- Импортирует вопросы из `tasks_base/questions.json` в БД
- Автоматически определяет panel_type и eval_mode
- Пропускает уже существующие вопросы

### База данных

**Таблица `tech_questions`**
```sql
CREATE TABLE tech_questions (
  id INTEGER PRIMARY KEY,
  category VARCHAR (algorithms|frontend|backend|data-science),
  difficulty VARCHAR (easy|medium|hard),
  question_text TEXT,
  panel_type VARCHAR (code_python|code_frontend|code_backend|code_ds|text_only),
  eval_mode VARCHAR (llm_code|llm_theory),
  language_hint VARCHAR(100),
  tags TEXT[],
  created_at TIMESTAMP
);
```

**Импортированные данные:** ✅ 60 вопросов успешно импортированы

---

## Frontend ✅

### Реализованные компоненты

#### Панели для разных типов вопросов
- **PythonCodePanel** (`components/questions/PythonCodePanel.tsx`) - для алгоритмических задач
- **FrontendCodePanel** (`components/questions/FrontendCodePanel.tsx`) - для React/TypeScript
- **BackendCodePanel** (`components/questions/BackendCodePanel.tsx`) - для backend задач
- **DataSciencePanel** (`components/questions/DataSciencePanel.tsx`) - для DS задач
- **TextAnswerPanel** (`components/questions/TextAnswerPanel.tsx`) - для теории

#### Основные компоненты
- **QuestionWorkspace** (`components/questions/QuestionWorkspace.tsx`) - главный компонент
- **EvaluationResult** (`components/questions/EvaluationResult.tsx`) - результат оценки

#### Страницы
- **QuestionsTestPage** (`pages/QuestionsTestPage.tsx`) - тестовая страница

### API клиент (`api/questions.ts`)
```typescript
getNextQuestion(category, difficulty): Promise<Question>
submitQuestionAnswer(questionId, code?, text?): Promise<QuestionAnswerEval>
```

### Типы TypeScript (`types/questions.ts`)
```typescript
type PanelType = "code_python" | "code_frontend" | "code_backend" | "code_ds" | "text_only"

interface Question {
  id: number
  category: string
  difficulty: string
  question_text: string
  panel_type: PanelType
  language_hint?: string
}

interface QuestionAnswerEval {
  score: number        // 0-100
  passed: boolean
  short_feedback: string
  mistakes: string[]
}
```

### Стили (`styles/questions.css`)
- Стили для всех панелей
- Результат оценки с цветовой индикацией
- Адаптивный дизайн

---

## Использование

### Backend

**1. Запуск базы данных:**
```bash
cd t1/deploy
docker-compose up -d postgres
```

**2. Импорт вопросов:**
```bash
cd t1/backend
python -m app.scripts.import_questions
```

**3. Запуск API:**
```bash
cd t1/backend
uvicorn app.main:app --reload
```

### Frontend

**1. Установка зависимостей:**
```bash
cd t1/frontend
npm install
```

**2. Запуск dev сервера:**
```bash
npm run dev
```

**3. Тестовая страница:**
Откройте: `http://localhost:5173/questions-test`

---

## Примеры использования

### Backend API

**Получить вопрос:**
```bash
GET /api/questions/next?category=algorithms&difficulty=easy
```

Ответ:
```json
{
  "id": 1,
  "category": "algorithms",
  "difficulty": "easy",
  "question_text": "Дан массив целых чисел nums...",
  "panel_type": "code_python",
  "language_hint": "python"
}
```

**Отправить ответ:**
```bash
POST /api/questions/1/answer
{
  "question_id": 1,
  "answer_code": "def two_sum(nums, target):\n    ..."
}
```

Ответ:
```json
{
  "score": 85,
  "passed": true,
  "short_feedback": "Решение корректное, но можно оптимизировать",
  "mistakes": ["Не используется хеш-таблица для O(n)"]
}
```

### Frontend компоненты

```tsx
import { QuestionWorkspace } from './components/questions'
import { getNextQuestion } from './api/questions'

function MyComponent() {
  const [question, setQuestion] = useState<Question | null>(null)

  useEffect(() => {
    getNextQuestion('algorithms', 'easy').then(setQuestion)
  }, [])

  const handleComplete = (result: QuestionAnswerEval) => {
    console.log('Score:', result.score)
    console.log('Feedback:', result.short_feedback)
  }

  return question ? (
    <QuestionWorkspace 
      question={question} 
      onComplete={handleComplete} 
    />
  ) : (
    <div>Loading...</div>
  )
}
```

---

## Интеграция с существующей системой

### Связь с адаптивным движком

Результаты LLM-оценки (`score`, `passed`) интегрируются с:
- Адаптивным движком для выбора следующего вопроса
- Системой грейдинга (`theory_score` / `coding_score`)
- Финальным отчетом о сильных/слабых сторонах кандидата

### Добавление в InterviewPage

```tsx
// В InterviewPage.tsx
import { QuestionWorkspace } from '../components/questions'

// Показывать QuestionWorkspace для LLM-вопросов
{currentTask.type === 'llm_question' ? (
  <QuestionWorkspace 
    question={currentTask.question}
    onComplete={handleQuestionComplete}
  />
) : (
  <TaskView task={currentTask} />
)}
```

---

## Структура файлов

### Backend
```
backend/app/
├── api/
│   └── questions.py              # API endpoints
├── models/
│   └── questions.py              # SQLAlchemy модели
├── schemas/
│   └── questions.py              # Pydantic схемы
├── services/
│   ├── questions_importer.py    # Импорт вопросов
│   └── llm_grader.py            # LLM оценка
└── scripts/
    └── import_questions.py       # Скрипт импорта
```

### Frontend
```
frontend/src/
├── api/
│   └── questions.ts              # API клиент
├── components/
│   └── questions/
│       ├── QuestionWorkspace.tsx # Главный компонент
│       ├── PythonCodePanel.tsx   # Python панель
│       ├── FrontendCodePanel.tsx # Frontend панель
│       ├── BackendCodePanel.tsx  # Backend панель
│       ├── DataSciencePanel.tsx  # DS панель
│       ├── TextAnswerPanel.tsx   # Текстовая панель
│       ├── EvaluationResult.tsx  # Результат оценки
│       └── index.ts              # Экспорты
├── pages/
│   └── QuestionsTestPage.tsx     # Тестовая страница
├── styles/
│   └── questions.css             # Стили
└── types/
    └── questions.ts              # TypeScript типы
```

---

## Чек-лист реализации

### Backend ✅
- [x] Создать модели и схемы
- [x] Реализовать API endpoints
- [x] Реализовать LLM-оценку
- [x] Создать скрипт импорта
- [x] Импортировать 60 вопросов
- [x] Протестировать API

### Frontend ✅
- [x] Создать типы TypeScript
- [x] Реализовать QuestionWorkspace
- [x] Реализовать панели для разных типов вопросов
- [x] Интегрировать с API
- [x] Показывать результаты оценки
- [x] Создать тестовую страницу
- [x] Добавить стили

### Интеграция (следующие шаги)
- [ ] Связать с адаптивным движком
- [ ] Добавить в систему грейдинга
- [ ] Включить в финальный отчет
- [ ] Добавить Monaco Editor для лучшего редактирования
- [ ] Интегрировать с системой анти-чита
- [ ] Добавить таймер для вопросов

---

## Особенности реализации

### Автоматический выбор панели
QuestionWorkspace автоматически выбирает нужную панель на основе `panel_type`

### Цветовая индикация результатов
- 80-100: зеленый (отлично)
- 50-79: оранжевый (требует доработки)
- 0-49: красный (неверно)

### Обработка ошибок
Все компоненты обрабатывают ошибки сети и показывают понятные сообщения

---

## Документация

- **Backend:** См. комментарии в коде
- **Frontend:** `frontend/QUESTIONS_FRONTEND.md`
- **Спецификация:** `QUESTIONS_LLM_EVAL.md`
