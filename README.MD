# VibeCode

AI-платформа для технических собеседований. Кандидат решает задачи в браузерной IDE, общается с AI-интервьюером, получает оценку грейда и карту навыков.

## Быстрый запуск (Docker)

### Требования

- Docker
- Docker Compose

### 1. Клонировать репозиторий

```bash
git clone https://github.com/chrizantona/t1.git
cd t1
```

### 2. Создать файл .env

```bash
cp .env.example .env
```

Отредактировать `.env` и указать ваш API-ключ:

```
SCIBOX_API_KEY=ваш_ключ
```

### 3. Запустить

```bash
cd deploy
docker-compose up --build
```

### 4. Открыть в браузере

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| SCIBOX_API_KEY | API-ключ SciBox LLM | - |
| SCIBOX_BASE_URL | URL SciBox API | https://llm.t1v.scibox.tech/v1 |
| POSTGRES_USER | Пользователь БД | vibecode |
| POSTGRES_PASSWORD | Пароль БД | vibecode |
| POSTGRES_DB | Имя БД | vibecode |

## Стек

- Frontend: React + TypeScript + Vite
- Backend: FastAPI (Python 3.11)
- Database: PostgreSQL 15
- LLM: SciBox (qwen3-32b-awq, qwen3-coder-30b)

## Структура проекта

```
t1/
  backend/          # FastAPI backend
  frontend/         # React frontend
  deploy/           # Docker Compose конфигурация
  tasks_base/       # База вопросов и задач
```

## Альтернативный запуск (без Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
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

Требуется запущенный PostgreSQL. Обновить DATABASE_URL в .env соответственно.

## Основные возможности

- Адаптивные задачи по уровню кандидата
- Браузерная IDE с подсветкой синтаксиса
- AI-интервьюер для диалога и ревью решений
- Система подсказок с влиянием на балл
- Анализ резюме для рекомендации уровня
- Грейд-прогресс и карта навыков (Skill Radar)
- Trust Score и детекция AI-генерации кода
- Отчет для компании с итоговой оценкой
