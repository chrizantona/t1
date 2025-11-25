# VibeCode - Инструкция по запуску

## 🚀 Быстрый старт через Docker

Все сервисы запускаются через Docker Compose одной командой.

### Предварительные требования

- Docker и Docker Compose установлены
- Порты 5173, 8000 и 5433 свободны

### Шаги запуска

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/chrizantona/t1.git
cd t1
```

2. **Создайте файл .env в корне проекта:**
```bash
cp .env.example .env
```

Убедитесь, что в `.env` указан ваш SciBox API ключ:
```env
SCIBOX_API_KEY=sk-5NTsD4a9Rif0Cwk4-p5pZQ
```

3. **Скопируйте .env в папку deploy:**
```bash
cp .env deploy/.env
```

4. **Запустите все сервисы:**
```bash
cd deploy
docker-compose up --build
```

### Доступ к сервисам

После успешного запуска:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Postgres**: localhost:5433

### Проверка работоспособности

```bash
# Проверка backend
curl http://localhost:8000/health

# Проверка frontend
curl http://localhost:5173
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Backend
docker-compose logs -f backend

# Frontend
docker-compose logs -f frontend

# Postgres
docker-compose logs -f postgres
```

### Остановка сервисов

```bash
docker-compose down

# С удалением volumes
docker-compose down -v
```

## 📱 Использование платформы

### 1. Главная страница (LandingPage)
- Загрузите резюме для автоматической рекомендации уровня (CV-based Level Suggestion)
- Или выберите уровень и направление вручную
- Нажмите "Начать интервью"

### 2. Страница интервью (InterviewPage)
- Решайте задачи в браузерной IDE
- Общайтесь с AI интервьюером в чате
- Используйте подсказки (они уменьшают максимальный балл)
- Отправляйте код на проверку

### 3. Страница результатов (ResultPage)
- Финальный грейд и overall score
- Trust Score (анти-чит)
- Skill Radar Chart (карта навыков)
- Рекомендации для роста

### 4. Панель администратора
- Доступна по адресу: http://localhost:5173/admin
- Список всех интервью
- Статистика платформы

## 🎯 Killer Features

### ✅ Реализованные фичи:

1. **CV-based Level Suggestion** - Анализ резюме и автоматическая рекомендация уровня
2. **Adaptive Task Generation** - Генерация задач через SciBox LLM
3. **AI Interviewer Chat** - Диалог с ИИ-интервьюером
4. **Hint Economy** - Подсказки с ценой (уменьшают макс. балл)
5. **Skill Radar Chart** - Карта навыков по 5 осям
6. **Grade Progress Bar** - Визуализация прогресса между грейдами
7. **Trust Score** - Анти-чит система
8. **AI-Likeness Detection** - Определение похожести кода на AI-генерацию
9. **Final Report** - Полный отчёт с рекомендациями

## 🛠️ Технологии

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **LLM**: SciBox API (qwen3-32b-awq, qwen3-coder-30b-a3b-instruct-fp8)
- **Deployment**: Docker + Docker Compose

## 📝 API Endpoints

### Interview
- `POST /api/interview/start` - Начать интервью
- `GET /api/interview/{id}` - Получить интервью
- `GET /api/interview/{id}/tasks` - Получить задачи
- `POST /api/interview/submit` - Отправить решение
- `POST /api/interview/chat` - Чат с AI
- `POST /api/interview/hint` - Запросить подсказку
- `GET /api/interview/{id}/report` - Финальный отчёт
- `POST /api/interview/{id}/complete` - Завершить интервью

### Resume
- `POST /api/resume/analyze` - Анализ резюме

### Admin
- `GET /api/admin/interviews` - Список интервью
- `GET /api/admin/statistics` - Статистика

## 🔧 Разработка

### Backend (без Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (без Docker)

```bash
cd frontend
npm install
npm run dev
```

## 📦 Структура проекта

```
t1/
├── backend/
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── core/        # Config, DB
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/       # React pages
│   │   ├── components/  # React components
│   │   └── api/         # API client
│   ├── package.json
│   └── Dockerfile
├── deploy/
│   └── docker-compose.yml
├── .env                 # Environment variables (НЕ коммитится)
├── .env.example         # Пример .env
└── README.MD            # Описание проекта
```

## ⚠️ Важно

- `.env` файл НЕ КОММИТИТСЯ в git (защита API ключа)
- API ключ SciBox хранится только локально
- Для прода нужно настроить переменные окружения на сервере

## 🐛 Troubleshooting

### Порт 5432 уже занят
В `docker-compose.yml` порт postgres изменён на 5433:
```yaml
ports:
  - "5433:5432"
```

### Backend не запускается
Проверьте логи:
```bash
docker-compose logs backend
```

Убедитесь, что .env файл скопирован в deploy/:
```bash
cp .env deploy/.env
```

### Frontend не загружается
Проверьте, что Vite dev server запущен:
```bash
docker-compose logs frontend
```

## 📞 Поддержка

В случае проблем:
1. Проверьте логи сервисов
2. Убедитесь, что все порты свободны
3. Перезапустите Docker Compose

---

**Разработано для хакатона t1**  
**Платформа VibeCode - AI-собеседования нового поколения**

