# Frontend для системы LLM-оценки вопросов

## ✅ Реализовано

### Компоненты

#### Панели для разных типов вопросов
- **PythonCodePanel** - для алгоритмических задач на Python
- **FrontendCodePanel** - для React/TypeScript задач
- **BackendCodePanel** - для backend задач (Python/SQL)
- **DataSciencePanel** - для DS задач (pandas/numpy/sklearn)
- **TextAnswerPanel** - для теоретических вопросов

#### Основные компоненты
- **QuestionWorkspace** - главный компонент, выбирает нужную панель по типу вопроса
- **EvaluationResult** - отображение результата оценки с баллами и фидбеком

#### Страницы
- **QuestionsTestPage** - тестовая страница для проверки системы

### API клиент

**`src/api/questions.ts`**
- `getNextQuestion(category, difficulty)` - получить случайный вопрос
- `submitQuestionAnswer(questionId, code, text)` - отправить ответ на оценку

### Типы TypeScript

**`src/types/questions.ts`**
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

### Стили

**`src/styles/questions.css`**
- Стили для всех панелей вопросов
- Стили для результата оценки
- Адаптивный дизайн
- Анимации и переходы

## Использование

### 1. Запуск фронтенда

```bash
cd t1/frontend
npm install
npm run dev
```

### 2. Тестовая страница

Откройте в браузере: `http://localhost:5173/questions-test`

### 3. Использование компонентов

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

## Интеграция с существующей системой

### Добавление в InterviewPage

Можно интегрировать QuestionWorkspace в существующую страницу интервью:

```tsx
// В InterviewPage.tsx
import { QuestionWorkspace } from '../components/questions'

// В зависимости от типа задания показывать либо TaskView, либо QuestionWorkspace
{currentTask.type === 'llm_question' ? (
  <QuestionWorkspace 
    question={currentTask.question}
    onComplete={handleQuestionComplete}
  />
) : (
  <TaskView task={currentTask} />
)}
```

### Связь с адаптивной системой

```tsx
// Получение вопроса на основе адаптивного движка
const getAdaptiveQuestion = async (interviewId: string) => {
  // Адаптивный движок определяет категорию и сложность
  const { category, difficulty } = await getNextAdaptiveParams(interviewId)
  
  // Получаем вопрос
  const question = await getNextQuestion(category, difficulty)
  
  return question
}
```

## Структура файлов

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

## Особенности реализации

### Автоматический выбор панели
QuestionWorkspace автоматически выбирает нужную панель на основе `panel_type`:
- `code_python` → PythonCodePanel
- `code_frontend` → FrontendCodePanel
- `code_backend` → BackendCodePanel
- `code_ds` → DataSciencePanel
- `text_only` → TextAnswerPanel

### Обработка результатов
После отправки ответа:
1. Показывается индикатор загрузки
2. Ответ отправляется на backend для LLM-оценки
3. Результат отображается с цветовой индикацией:
   - 80-100: зеленый (отлично)
   - 50-79: оранжевый (требует доработки)
   - 0-49: красный (неверно)

### Обработка ошибок
Компоненты обрабатывают ошибки сети и показывают понятные сообщения пользователю.

## Следующие шаги

- [ ] Добавить Monaco Editor для лучшего редактирования кода
- [ ] Добавить подсветку синтаксиса
- [ ] Добавить автосохранение ответов
- [ ] Интегрировать с системой анти-чита
- [ ] Добавить таймер для вопросов
- [ ] Добавить историю ответов
