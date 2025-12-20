# VibeCode Jam

AI-платформа для проведения технических собеседований. Разработана в рамках хакатона T1 для автоматизации процесса оценки технических навыков кандидатов с использованием искусственного интеллекта.

---

## Установка и запуск

### Требования

- Docker
- Docker Compose
- Git

### Запуск через Docker (рекомендуется)

1. Клонировать репозиторий

```bash
git clone https://github.com/chrizantona/t1.git
cd t1
```

2. Создать файл окружения

```bash
cp .env.example .env
```

3. Указать API-ключ в файле `.env`

```
SCIBOX_API_KEY=ваш_ключ
```

4. Запустить контейнеры

```bash
cd deploy
docker-compose up --build
```

5. Открыть в браузере

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

### Запуск без Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### База данных

Требуется запущенный PostgreSQL. Параметры подключения указываются в `.env`.

### Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| SCIBOX_API_KEY | API-ключ SciBox LLM | - |
| SCIBOX_BASE_URL | URL SciBox API | https://llm.t1v.scibox.tech/v1 |
| POSTGRES_USER | Пользователь БД | vibecode |
| POSTGRES_PASSWORD | Пароль БД | vibecode |
| POSTGRES_DB | Имя БД | vibecode |

---

## Основной функционал

- **Адаптивные задачи** — автоматический подбор сложности задач под уровень кандидата
- **Браузерная IDE** — встроенный редактор кода с подсветкой синтаксиса на базе Monaco Editor
- **AI-интервьюер** — диалоговый интерфейс для общения с кандидатом и ревью решений
- **Система подсказок** — возможность запроса подсказок с влиянием на итоговый балл
- **Анализ резюме** — автоматическое определение уровня кандидата по загруженному резюме
- **Грейд-прогресс** — визуализация прогресса прохождения собеседования
- **Skill Radar** — карта навыков кандидата по различным направлениям
- **Trust Score** — детекция AI-генерации кода и оценка честности прохождения
- **Отчет для компании** — итоговый отчет с оценкой и рекомендациями

---

## Технологии и инструменты

### Frontend

![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat&logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?style=flat&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=flat&logo=vite&logoColor=white)
![Monaco Editor](https://img.shields.io/badge/Monaco_Editor-4.6-007ACC?style=flat&logo=visualstudiocode&logoColor=white)

### Backend

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.5-E92063?style=flat&logo=pydantic&logoColor=white)

### База данных

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)

### LLM

![SciBox](https://img.shields.io/badge/SciBox-qwen3--32b-FF6F00?style=flat&logo=openai&logoColor=white)

### DevOps

![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?style=flat&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-3.8-2496ED?style=flat&logo=docker&logoColor=white)

---

## Команда проекта

| Участник | Роль | GitHub |
|----------|------|--------|
| Ананьев Даниил | Разработчик | [rougenn](https://github.com/rougenn) |
| Аракелян Артур | Разработчик | [sratov](https://github.com/sratov) |
| Халибеков Алан | Разработчик | [chrizantona](https://github.com/chrizantona) |
| Хамидуллин Тимур | Разработчик | [timurqq73](https://github.com/timurqq73) |

Группа: **БИВТ-24-9**

---

## Архитектура и структура проекта

### Структура директорий

```
vibecode/
|-- backend/                 # FastAPI backend
|   |-- app/
|   |   |-- api/            # API endpoints
|   |   |-- models/         # SQLAlchemy models
|   |   |-- schemas/        # Pydantic schemas
|   |   |-- services/       # Business logic
|   |   |-- prompts/        # LLM prompts
|   |   |-- grading/        # Grading system
|   |   |-- adaptive/       # Adaptive engine
|   |   |-- core/           # Config and DB
|   |-- Dockerfile
|   |-- requirements.txt
|-- frontend/                # React frontend
|   |-- src/
|   |   |-- pages/          # Page components
|   |   |-- components/     # UI components
|   |   |-- api/            # API client
|   |   |-- styles/         # CSS styles
|   |   |-- types/          # TypeScript types
|   |-- Dockerfile
|   |-- package.json
|-- deploy/                  # Docker Compose
|   |-- docker-compose.yml
|-- tasks_base/              # Questions database
    |-- questions.json
    |-- ml_questions.json
```

### Архитектура системы

```
+-------------------------------------------------------------------+
|                         Frontend (React)                           |
|                    http://localhost:5173                           |
+--------------------------------+----------------------------------+
                                 |
                                 | HTTP/REST
                                 v
+-------------------------------------------------------------------+
|                      Backend (FastAPI)                             |
|                    http://localhost:8000                           |
|                                                                    |
|  +------------+  +------------+  +------------+  +---------------+ |
|  | Interview  |  | Questions  |  | Anti-Cheat |  | Resume        | |
|  | API        |  | API        |  | API        |  | Analysis API  | |
|  +-----+------+  +-----+------+  +-----+------+  +-------+-------+ |
|        |               |               |                 |         |
|        +---------------+-------+-------+-----------------+         |
|                                |                                   |
|                        +-------v-------+                           |
|                        | LLM Service   | ------> SciBox API        |
|                        +---------------+                           |
+--------------------------------+----------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------+
|                     PostgreSQL Database                            |
|                    localhost:5433                                  |
+-------------------------------------------------------------------+
```

---

## Демонстрация работы

### Видео-демонстрация

[Смотреть демонстрацию на Google Drive](https://drive.google.com/file/d/1EWLe-K-H8e8acFcUAJhsk0oo_SG0Dwr-/view?usp=sharing)

### Презентация проекта

Презентация доступна в файле [YSL MISIS.pdf](./YSL%20MISIS.pdf)

---

## Заключение

VibeCode Jam решает проблему автоматизации технических собеседований, которая актуальна для IT-компаний любого масштаба. Платформа позволяет:

- Сократить время HR-специалистов на первичный отбор кандидатов
- Обеспечить объективную оценку технических навыков
- Получить детальный отчет о компетенциях кандидата
- Выявить потенциальное использование AI при решении задач

### Отличия от аналогов

- Адаптивная система подбора задач под уровень кандидата
- Встроенная система детекции AI-генерации кода
- Диалоговый AI-интервьюер для уточняющих вопросов
- Визуализация навыков через Skill Radar

### Возможные улучшения

- Интеграция с популярными ATS-системами
- Расширение базы задач для других технологий
- Добавление live-coding сессий с видеосвязью
- Мобильное приложение для кандидатов

---

## Лицензия

Проект распространяется под лицензией MIT License. Подробности в файле [LICENSE](./LICENSE).

```
MIT License

Copyright (c) 2024 VibeCode Jam Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

<!-- пидормот -->
