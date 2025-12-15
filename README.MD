# VibeCode

AI-платформа для технических собеседований ML/DS специалистов. Кандидат решает задачи в браузерной IDE, общается с AI-интервьюером голосом или текстом, получает оценку грейда и карту навыков.

## Какую бизнес-задачу решает

VibeCode помогает ускорять и стандартизировать технический найм. Платформа автоматизирует часть работы интервьюера (задачи, тесты, первичная оценка), делает результаты кандидатов сопоставимыми между собой и даёт понятную обратную связь. Для HR и нанимающей команды это означает быстрее принимать решения на основе прозрачных метрик, а для кандидата — понятный процесс и понимание своего уровня и зон роста.

## Быстрый запуск (Docker)

### Требования

* Docker + Docker Compose
* Свободные порты: 5173, 8000, 5433

### 1. Клонировать репозиторий

```bash
git clone https://github.com/chrizantona/t1.git
cd t1
```

### 2. Запустить

```bash
cd deploy
docker-compose up --build
```

### 3. Открыть в браузере

* Frontend: [http://localhost:5173](http://localhost:5173)
* Backend API: [http://localhost:8000](http://localhost:8000)
* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Основные возможности

### Интервью

* Адаптивные задачи: сложность подстраивается под уровень кандидата
* Браузерная IDE: Monaco Editor с подсветкой Python
* AI-интервьюер: диалог, ревью решений, follow-up вопросы
* Голосовой ввод: распознавание речи через Whisper API
* Система подсказок: 3 уровня подсказок с влиянием на балл

### Оценка

* Автоматическое тестирование: видимые и скрытые тесты
* LLM-оценка теории: AI оценивает ответы на вопросы
* Trust Score: детекция переключения вкладок
* Skill Radar: карта навыков по 5 осям ML/DS

### Результаты

* Грейд: Junior/Middle/Senior с процентом уверенности
* Детальный отчёт: сильные/слабые стороны, рекомендации
* Экспорт: отчёт для HR/компании

## Технологии

### Frontend

* React 18 + TypeScript
* Vite
* Monaco Editor
* Chart.js (Skill Radar)

### Backend

* FastAPI (Python 3.11)
* SQLAlchemy + PostgreSQL
* Pydantic

### AI/ML (Cloud.ru API)

* Qwen3-235B-A22B-Instruct — основной чат (генерация задач, оценка, диалог)
* Qwen3-Coder-480B-A35B — код-ассистент (анализ кода, подсказки)
* openai/whisper-large-v3 — голосовой ввод
* BAAI/bge-m3 — эмбеддинги (пока не используется активно)
  Всё через Cloud.ru API с одним ключом.

### Инфраструктура

* Docker + Docker Compose
* PostgreSQL 15
* FFmpeg (конвертация аудио)

## Структура проекта

```
t1/
├── backend/
│   ├── app/
│   │   ├── api/          # Endpoints (interview, resume, voice, admin)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # LLM, code execution, scoring
│   │   └── core/         # Config, database
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        # Landing, Interview, Questions, Result
│   │   ├── components/   # UI components
│   │   ├── api/          # API client
│   │   └── styles/       # CSS
│   └── Dockerfile
├── deploy/
│   └── docker-compose.yml
├── tasks_base/           # База ML вопросов (JSON)
└── SETUP.md              # Детальная инструкция
```

## Разработка (без Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### PostgreSQL

Нужен запущенный PostgreSQL на порту 5433 (или изменить в config.py).

## API Endpoints

### Interview

* POST /api/interview/start — начать интервью
* GET /api/interview/{id}/tasks — получить задачи
* POST /api/interview/submit — отправить решение
* POST /api/interview/chat — чат с AI
* POST /api/interview/hint — запросить подсказку
* POST /api/interview/{id}/generate-task — сгенерировать следующую задачу
* GET /api/interview/{id}/report — финальный отчёт

### Questions (теория)

* GET /api/questions/{interview_id} — получить вопросы
* POST /api/questions/{id}/answer — ответить на вопрос

### Voice

* POST /api/voice/transcribe — распознать речь (Whisper)

### Resume

* POST /api/resume/analyze — анализ резюме

## Troubleshooting

### Порт занят

```bash
netstat -ano | findstr :5173
```

### Логи

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Пересборка

```bash
docker-compose down
docker-compose up --build
```
