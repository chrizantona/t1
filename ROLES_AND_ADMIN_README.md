# VibeCode — роли пользователя: Кандидат (Worker) и Администратор (Recruiter)

Этот README — ТЗ для реализации **двух режимов входа** в систему и разделения функционала:

- **Кандидат (Worker)** — приходит решать задачи по конкретной вакансии.
- **Администратор / Рекрутер (Admin/Recruiter)** — заводит вакансии, настраивает скилл-матрицу, задачи, смотрит отчёты.

Стек: React + TypeScript / FastAPI + Python / PostgreSQL / Claude Opus 4.5 (+ SciBox при нужде).

Опираемся на предыдущие спеки:

- `VACANCY_FLOW_README.md` — вакансия как центр вселенной.
- `PROMPTS_CLAUDE_OPUS.md` — промпты для резюме/вакансий/отчётов.
- `TASK_GEN_AND_OPENING_QUESTIONS.md` — генерация задач + первый вопрос бота.

---

## 0. Концепция ролей

- **Кандидат** — минимальный friction:
  - выбор вакансии,
  - загрузка резюме,
  - прохождение кастомного собеса,
  - просмотр своего результата.
- **Администратор (рекрутер)**:
  - создаёт и настраивает вакансии (JD → skill-матрица → блоки задач),
  - смотрит pipeline кандидатов по каждой вакансии,
  - открывает финальные отчёты «кандидат vs вакансия».

---

## 1. Модель пользователей и ролей

### 1.1. Таблица `users`

```sql
CREATE TYPE user_role AS ENUM ('candidate', 'admin');

CREATE TABLE users (
  id            uuid primary key,
  email         text unique not null,
  password_hash text not null,
  full_name     text,
  role          user_role not null,     -- 'candidate' или 'admin'

  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);
```

> Для хакатона можно упростить хранение пароля, но поле `role` должно быть.

### 1.2. Профили (если нужно расширять)

```sql
CREATE TABLE candidate_profiles (
  user_id       uuid primary key references users(id),
  resume_last_uploaded_at timestamptz,
  tg_handle     text,
  extra_data    jsonb
);

CREATE TABLE admin_profiles (
  user_id       uuid primary key references users(id),
  company_name  text,
  position      text,
  extra_data    jsonb
);
```

---

## 2. Авторизация и роутинг по ролям

### 2.1. Логин/регистрация

Фронт: одна страница `/login` с переключателем:

- кнопки:
  - «Войти как кандидат»
  - «Войти как рекрутер»
- для демо — быстрый вход (заготовленные аккаунты).

Backend:

- `POST /api/auth/login` — email + пароль → выдаём JWT с `user_id` и `role`.
- `POST /api/auth/register` (опционально).

### 2.2. Разделение роутов

После успешного логина:

- если `role = candidate` → `/app/candidate`.
- если `role = admin` → `/app/admin`.

Пример на React:

```tsx
<Route path="/app/candidate/*" element={<CandidateLayout />} />
<Route path="/app/admin/*" element={<AdminLayout />} />
```

---

## 3. Функционал кандидата (Worker)

Здесь мы используем уже спроектированный кандидатский flow, просто завязываем его на роль.

### 3.1. Экран выбора вакансии

- Route: `/app/candidate/vacancies`
- API: `GET /api/vacancies/public`
- UI:
  - карточки вакансий,
  - «Пройти собеседование по этой вакансии».

### 3.2. Загрузка резюме для выбранной вакансии

- Route: `/app/candidate/vacancies/:id/upload-resume`
- API:
  - `POST /api/candidate/vacancies/:id/resume` (PDF или текст)
- Backend:
  - парсит PDF,
  - вызывает `RESUME_ANALYZER`,
  - создаёт `candidate_vacancy_context`.

UI после обработки:

- краткое summary резюме,
- предполагаемый грейд,
- предварительное соответствие вакансии (match-preview).

### 3.3. Прохождение собеса

- Route: `/app/candidate/interviews/:interviewId`
- Блоки:
  - Алгоритмы,
  - Практическая задача,
  - Теория/кейсы.

Используем спецификации:

- задачи привязаны к вакансии (`VACANCY_FLOW_README.md`),
- показываем `generation_meta` (почему именно эта задача),
- чат-ассистент:
  - первый вопрос от бота (`TASK_OPENING_QUESTIONS`),
  - подсказки,
  - live-чат.

### 3.4. Личный результат

- Route: `/app/candidate/interviews/:interviewId/result`
- API: `GET /api/candidate/interviews/:id/result`
- UI:
  - краткое описание:
    - рекомендованный грейд,
    - сильные/слабые стороны,
    - рекомендации по развитию.

---

## 4. Функционал администратора (Recruiter)

Тут весь vacancy-first бизнес-план.

### 4.1. Дэшборд администратора

- Route: `/app/admin`
- API: `GET /api/admin/vacancies/overview`

Показываем:

- список вакансий:
  - название,
  - трек,
  - уровень,
  - количество кандидатов (in progress / completed),
- кнопка: «Создать вакансию».

### 4.2. Управление вакансиями

#### 4.2.1. Список вакансий

- Route: `/app/admin/vacancies`
- API: `GET /api/admin/vacancies`

Таблица:

| Название | Трек | Уровень | Активных кандидатов | Действия |
|----------|------|---------|---------------------|----------|

#### 4.2.2. Создание/редактирование вакансии

- Route: `/app/admin/vacancies/new`, `/app/admin/vacancies/:id`

Шаги (как в `VACANCY_FLOW_README.md`):

1. **Основное:**
   - title, level, track,
   - загрузка JD.
   - Backend вызывает Claude-ролю `VACANCY_ANALYZER` → draft skill-матрица.

2. **Скилл-матрица:**
   - таблица по `skill_matrix.skills`:
     - required_level,
     - importance,
     - weight,
     - check_types,
     - is_critical.

3. **Профили блоков:**
   - какие блоки активны (algo/practice/theory),
   - сколько задач/вопросов,
   - каким скиллам должны соответствовать.

4. **Правила решения:**
   - пороги `strong_yes/yes/hold`,
   - список `critical_skills`,
   - разрешён ли downlevel.

Все изменения через:

- `PUT /api/admin/vacancies/:id/skill_matrix`
- `PUT /api/admin/vacancies/:id/profiles`
- `PUT /api/admin/vacancies/:id/decision_rules`

---

### 4.3. Pipeline кандидатов по вакансии

- Route: `/app/admin/vacancies/:id/pipeline`
- API: `GET /api/admin/vacancies/:id/candidates`

UI:

таблица:

| Кандидат | Статус | Vacancy-fit | Грейд | Trust | Открыть отчёт |
|----------|--------|------------|-------|-------|---------------|

Статусы:

- `not_started`,
- `in_progress`,
- `completed`.

---

### 4.4. Отчёт «Кандидат vs Вакансия»

- Route: `/app/admin/interviews/:id`
- API: `GET /api/admin/interviews/:id/report`

В отчёте используем результат `FINAL_REPORT_GENERATOR`:

Вкладки:

1. **Сводка**
   - Название вакансии,
   - Имя кандидата,
   - vacancy_fit_score,
   - final_grade,
   - hire_recommendation,
   - key_strengths / key_risks.

2. **Скилл-матрица**
   - Таблица:
     - skill,
     - required_level,
     - фактический уровень,
     - комментарий.

3. **Блоки собеса**
   - Алго: задачи, результаты, комментарий,
   - Практика: задача/лабка, метрики,
   - Теория: вопросы, ответы, оценка.

4. **Anti-cheat**
   - trust_score,
   - trust_status,
   - ai_likeness_score,
   - текстовое объяснение.

---

## 5. Ограничение доступа (RBAC)

### 5.1. Backend

Создаём dependency `require_role`:

```python
from fastapi import Depends, HTTPException, status
from .auth import get_current_user

def require_role(*allowed_roles: str):
    async def dependency(user = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
    return dependency
```

Примеры:

```python
@router.get("/admin/vacancies", dependencies=[Depends(require_role("admin"))])
async def list_admin_vacancies():
    ...

@router.get("/candidate/vacancies", dependencies=[Depends(require_role("candidate", "admin"))])
async def list_public_vacancies():
    ...
```

---

## 6. UX-картинка для жюри

**Как кандидат:**

1. Зашёл → выбрал вакансию → загрузил резюме.
2. Система показала:
   - твой грейд,
   - как ты матчишься с вакансией.
3. Начал интервью:
   - задачи подобраны под вакансию и твой уровень,
   - LLM объясняет, зачем именно эта задача,
   - бот сам первым задаёт вопрос по задаче.
4. В конце видит свой результат.

**Как рекрутер:**

1. Зашёл → создал вакансию из JD:
   - LLM распарсил требования,
   - предложил скилл-матрицу и веса.
2. Видит pipeline:
   - кандидаты по этой вакансии,
   - у каждого vacancy-fit, грейд, trust.
3. Открывает отчёт:
   - не просто «он middle»,
   - а конкретный разбор: где соответствует требованиям вакансии, а где нет.

---

## 7. To-Do для реализации (для Cursor)

**Backend:**

- [ ] Добавить таблицу `users` с полем `role` и авторизацию.
- [ ] Реализовать `require_role` и ограничить admin-эндпоинты.
- [ ] Реализовать admin-API:
  - создание/редактирование вакансий,
  - overview/pipeline по вакансиям,
  - выдача финального отчёта.
- [ ] Связать candidate flow с выбранной вакансией и текущим пользователем-кандидатом.

**Frontend:**

- [ ] Страница логина с выбором роли.
- [ ] Layout `/app/candidate/*` с экранами:
  - список вакансий,
  - загрузка резюме,
  - прохождение интервью,
  - просмотр результата.
- [ ] Layout `/app/admin/*` с экранами:
  - список вакансий,
  - создание/редактирование,
  - pipeline по вакансии,
  - просмотр отчётов.

Этот README можно положить в репу как `ROLES_AND_ADMIN_README.md` и скормить Cursor/Claude как ТЗ по ролям и админскому функционалу.
