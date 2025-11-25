# VibeCode — логика грейдов, адаптивности и отчётов

Этот README описывает бизнес- и математику-логику для платформы **VibeCode**.  
По нему можно реализовать backend-логику в FastAPI и использовать её на фронте.

Сюда входят:

1. Определение **трека (сферы)** и **стартового грейда** по резюме и самооценке.
2. **Адаптивное** управление сложностью задач (easy / middle / hard).
3. Правило, что **крайние (edge) кейсы** есть только в hard-задачах.
4. Решение по **базе задач** (pre-generated, не генерим на лету).
5. Контекстный **ассистент** по ходу решения задач.
6. Логика **теоретических вопросов**.
7. **Формула оценки** и перевода в финальный грейд с разными весами задач.

---

## 1. Определение трека и стартового грейда

### 1.1. Входные данные

На старте интервью собираем:

- `self_claimed_grade: str`  
  Одно из:
  - `"junior" | "junior_plus" | "middle" | "middle_plus" | "senior"`.

- `self_claimed_track: str`  
  Одно из:
  - `"backend" | "frontend" | "fullstack" | "data" | "devops" | "mobile" | "other"`.

- `resume_text: str`  
  Сырые данные резюме.

- (опционально) `years_of_experience_input: float`  
  Если кандидат сам указал стаж.

### 1.2. Парсинг резюме LLM’ом (вспомогательно)

LLM используется как **парсер**, а НЕ как окончательный автор грейда.

Пример ожидаемого JSON от LLM:

```json
{
  "years_of_experience": 2.7,
  "resume_tracks": ["backend", "fullstack"],
  "key_technologies": ["Python", "FastAPI", "PostgreSQL"],
  "self_grade_from_resume": "middle",   // если явно написано в резюме
  "notes": "краткое резюме по опыту"
}
```

Эти данные передаём в наш **детерминированный модуль правил**.

### 1.3. Маппинг грейдов в числовой индекс

Внутри системы оперируем числовыми индексами:

- `0` — `junior`
- `1` — `junior_plus`
- `2` — `middle`
- `3` — `middle_plus`
- `4` — `senior`

```python
GRADE_TO_INDEX = {
    "junior": 0,
    "junior_plus": 1,
    "middle": 2,
    "middle_plus": 3,
    "senior": 4,
}

INDEX_TO_GRADE = {v: k for k, v in GRADE_TO_INDEX.items()}
```

### 1.4. Грейд по опыту (experience grade)

На основе `years_of_experience` задаём **жёсткие пороги**:

- `< 0.5 года` → 0 (`junior`)
- `0.5–1.5` → 1 (`junior_plus`)
- `1.5–3.5` → 2 (`middle`)
- `3.5–6` → 3 (`middle_plus`)
- `>= 6` → 4 (`senior`)

```python
def experience_to_grade_index(years: float) -> int:
    if years < 0.5:
        return 0
    if years < 1.5:
        return 1
    if years < 3.5:
        return 2
    if years < 6:
        return 3
    return 4
```

### 1.5. Грейд по самооценке

Берём грейд из формы:

```python
self_index = GRADE_TO_INDEX[self_claimed_grade]
```

Если из резюме LLM вытащил явный грейд (`self_grade_from_resume`), можно взять максимум:

```python
if resume_self_grade is not None:
    resume_index = GRADE_TO_INDEX[resume_self_grade]
    self_index = max(self_index, resume_index)
```

### 1.6. Определение трека (сферы)

Трек должен определяться **уверенно**:

1. Если `self_claimed_track` указан → используем его.
2. Иначе — на основании `resume_tracks` и ключевых слов в `resume_text`:
   - backend → python, java, spring, fastapi, rest, api, sql, postgres и т.п.;
   - frontend → javascript, typescript, react, vue, angular, css, html и т.п.;
   - и т.д.

Если явно написано `backend`, `frontend` и т.д. — просто берём это, без сомнений.

### 1.7. Стартовый грейд (start_grade_index)

Используем взвешенную комбинацию:

- опыт (`exp_index`),
- самооценка (`self_index`),
- грейд из резюме (если есть, иначе = self).

```python
def calc_start_grade_index(exp_index: int, self_index: int, resume_index: int | None) -> int:
    if resume_index is None:
        resume_index = self_index

    grade_index = round(
        0.5 * exp_index +   # опыт даёт половину влияния
        0.3 * self_index +  # самооценка
        0.2 * resume_index  # грейд в резюме
    )
    return max(0, min(4, grade_index))
```

Пример:  
человек пишет `middle`, но опыта 0.3 года → `exp_index` = 0, итоговый стартовый индекс будет смещён в сторону junior.

---

## 2. Адаптивное управление сложностью задач

### 2.1. Уровни сложности

Три категории задач:

- `easy`
- `middle`
- `hard`

### 2.2. Начало интервью

Всегда **начинаем с easy** задачи:

```python
state.level = "easy"
```

### 2.3. Результат по задаче (TaskResult)

Для каждой задачи сохраняем:

```python
class TaskResult(BaseModel):
    difficulty: Literal["easy", "middle", "hard"]
    visible_passed: int
    visible_total: int
    hidden_passed: int
    hidden_total: int
    hints_soft: int
    hints_medium: int
    hints_hard: int
    time_sec: float
```

Считаем:

```python
visible_rate = visible_passed / max(1, visible_total)
hidden_rate = hidden_passed / max(1, hidden_total)
total_rate = (visible_passed + hidden_passed) / max(1, visible_total + hidden_total)
```

### 2.4. Пороги (strong pass / fail)

**Strong pass** (очень уверенное решение):

- для `easy` и `middle`:
  - `visible_rate == 1.0`
  - `total_rate >= 0.9`
  - `hints_hard == 0` и `hints_medium <= 1`

- для `hard`:
  - `visible_rate == 1.0`
  - `total_rate >= 0.75`

**Fail / слабое решение**:

- `visible_rate < 0.6` **или**
- `total_rate < 0.5`.

```python
def is_strong_pass(r: TaskResult) -> bool:
    visible_rate = r.visible_passed / max(1, r.visible_total)
    total_rate = (r.visible_passed + r.hidden_passed) / max(1, r.visible_total + r.hidden_total)

    if r.difficulty in ("easy", "middle"):
        if visible_rate == 1.0 and total_rate >= 0.9 and r.hints_hard == 0 and r.hints_medium <= 1:
            return True
    else:  # hard
        if visible_rate == 1.0 and total_rate >= 0.75:
            return True
    return False


def is_fail(r: TaskResult) -> bool:
    visible_rate = r.visible_passed / max(1, r.visible_total)
    total_rate = (r.visible_passed + r.hidden_passed) / max(1, r.visible_total + r.hidden_total)
    return visible_rate < 0.6 or total_rate < 0.5
```

### 2.5. Изменение уровня сложности

Функции перехода:

```python
def level_up(level: str) -> str:
    if level == "easy":
        return "middle"
    if level == "middle":
        return "hard"
    return "hard"


def level_down(level: str) -> str:
    if level == "hard":
        return "middle"
    if level == "middle":
        return "easy"
    return "easy"
```

Алгоритм после задачи:

- Если `strong pass` → уровень повышается.
- Если `fail` и кандидат нажал «перейти к следующей задаче» → уровень понижается.
- Иначе уровень остаётся прежним.

```python
def update_level_after_task(state_level: str, result: TaskResult, user_clicked_next: bool) -> str:
    if is_strong_pass(result):
        return level_up(state_level)

    if is_fail(result) and user_clicked_next:
        return level_down(state_level)

    return state_level
```

---

## 3. Крайние случаи (edge-cases) только в hard-задачах

Политика по тестам:

- У тестов в базе может быть флаг `is_extreme: bool`.
- **Easy**:
  - нет `is_extreme == True` в hidden-тестах.
- **Middle**:
  - минимум edge-кейсов, без жёстких ограничений по N/сложности.
- **Hard**:
  - все тяжёлые граничные кейсы лежат здесь (`is_extreme == True`).

Это соответствует требованию: **крайние случаи только в hard**, на то они и hard.

---

## 4. База задач: не генерим на лету

Для хакатона выбираем вариант:

> **Предварительная база задач (по ~20 на уровень/трек)**  
> а не генерация задач в реальном времени.

Реализация:

- Задачи лежат в БД (`tasks`), либо в миграциях/JSON, но используются как **фиксированный пул**.
- LLM:
  - не генерирует задачи в рантайме,
  - используется для:
    - подсказок,
    - Bug Hunter (доп. тесты),
    - отчётов и skill radar,
    - анализа резюме.

---

## 5. Ассистент во время решения (понимание контекста)

Во время решения кандидат может задать вопрос ассистенту.  
Ассистент всегда должен видеть контекст задачи и состояния.

### 5.1. Контекст, который передаём в LLM

```json
{
  "task": {
    "id": "...",
    "track": "backend",
    "difficulty": "middle",
    "title": "...",
    "description": "...",
    "input_format": "...",
    "output_format": "..."
  },
  "code": "текущий код кандидата",
  "test_results": {
    "visible_passed": 3,
    "visible_total": 5,
    "hidden_passed": 0,
    "hidden_total": 2
  },
  "hints_used": {
    "soft": 1,
    "medium": 0,
    "hard": 0
  }
}
```

### 5.2. Правила для ассистента

В system-промпте:

- ассистент — **технический интервьюер**;
- видит:
  - условие задачи,
  - текущий код,
  - результаты тестов;
- отвечает:
  - по-русски,
  - **в рамках текущей задачи**,
  - не выдаёт полный рабочий код, только объяснения, уточнения, примеры.

User-промпт:  
вставляем контекст (сжатый) + текст вопроса кандидата.

---

## 6. Теоретические вопросы в процессе интервью

### 6.1. Когда задаём теорию

Логика:

- Если кандидат **успешно проходит задачу** (strong pass):
  - после этой задачи задаём 1–3 теоретических вопроса.
- Теоретические вопросы привязаны к:
  - треку (`track`),
  - уровню (`easy/middle/hard` или грейду).

### 6.2. База теоретических вопросов

Отдельная таблица, без LLM-генерации в рантайме:

```sql
theory_questions(
  id              serial primary key,
  track           text,      -- backend | frontend | ...
  level           text,      -- easy | middle | hard / grade-level
  question_text   text,
  answer_type     text,      -- "open" | "multi"
  correct_keywords text[],   -- для open
  options         jsonb      -- для multi-choice
)
```

### 6.3. Оценка ответов (theory_score)

Вариант 1 (MVP): keyword-based:

```python
def grade_theory_answer(answer: str, keywords: list[str]) -> float:
    ans = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in ans)
    if hits == 0:
        return 0.0
    if hits == len(keywords):
        return 1.0
    return 0.5
```

Итоговый теоретический скор:

```python
if M > 0:
    theory_score = sum(q.score for q in theory_answers) / M * 100.0
else:
    theory_score = 0.0
```

(Можно заменить на LLM-оценку, но формула сверху достаточно понятна.)

---

## 7. Формула итоговой оценки и грейда

### 7.1. Веса задач по сложности

Условные веса:

- `easy` → `w_easy = 1`
- `middle` → `w_middle = 2`
- `hard` → `w_hard = 3`

### 7.2. Скор за одну задачу

Для каждой задачи `result: TaskResult`:

```python
difficulty_weight = {
    "easy": 1,
    "middle": 2,
    "hard": 3,
}[result.difficulty]

visible_rate = result.visible_passed / max(1, result.visible_total)
hidden_rate = result.hidden_passed / max(1, result.hidden_total)
total_rate = (result.visible_passed + result.hidden_passed) / max(1, result.visible_total + result.hidden_total)

# штрафы за подсказки
hint_penalty = (
    0.10 * result.hints_soft +
    0.20 * result.hints_medium +
    0.35 * result.hints_hard
)
hint_penalty = min(hint_penalty, 0.7)  # штраф не более 70%

effective_rate = max(0.0, total_rate * (1.0 - hint_penalty))

task_score_unit = effective_rate * difficulty_weight  # в "условных единицах"
```

### 7.3. Кодинговый скор (coding_score)

Пусть:

- `W = sum(difficulty_weight_i)` — сумма весов задач,
- `S = sum(task_score_unit_i)` — сумма взвешенных результатов.

Тогда:

```python
coding_score = S / max(1, W) * 100.0   # [0,100]
```

### 7.4. Теоретический скор (theory_score)

Как выше (§6.3):

```python
if M > 0:
    theory_score = sum(q.score for q in theory_answers) / M * 100.0
else:
    theory_score = 0.0
```

### 7.5. Общий скор (overall_score)

Например:

- 70% веса — код,
- 30% веса — теория.

```python
overall_score = 0.7 * coding_score + 0.3 * theory_score   # [0,100]
```

### 7.6. Перевод overall_score в performance grade

Маппинг:

- `< 40` → `0` (`junior`)
- `40–55` → `1` (`junior_plus`)
- `55–70` → `2` (`middle`)
- `70–85` → `3` (`middle_plus`)
- `>= 85` → `4` (`senior`)

```python
def score_to_grade_index(score: float) -> int:
    if score < 40:
        return 0
    if score < 55:
        return 1
    if score < 70:
        return 2
    if score < 85:
        return 3
    return 4
```

### 7.7. Финальный грейд (final_grade_index)

Собираем всё:

- `exp_index` — по опыту (§1.4),
- `self_index` — по самооценке (§1.5),
- `perf_index` — по результатам интервью (§7.6).

Финальный грейд:

```python
def calc_final_grade_index(exp_index: int, self_index: int, perf_index: int) -> int:
    idx = round(
        0.6 * perf_index +   # главное — реальный perf
        0.25 * exp_index +   # чуть учитываем опыт
        0.15 * self_index    # и самооценку
    )
    return max(0, min(4, idx))
```

Итоговый грейд:

```python
final_grade = INDEX_TO_GRADE[final_grade_index]
```

---

## 8. Что реализовать в коде (для Cursor)

Рекомендуемые модули:

- `grading/levels.py`  
  - `experience_to_grade_index(years)`,
  - `score_to_grade_index(score)`,
  - `calc_start_grade_index(exp_index, self_index, resume_index)`,
  - `calc_final_grade_index(exp_index, self_index, perf_index)`.

- `grading/tracks.py`  
  - определение трека по `self_claimed_track` + ключевым словам резюме.

- `adaptive/engine.py`  
  - `TaskResult` модель,
  - `is_strong_pass(result)`,
  - `is_fail(result)`,
  - `update_level_after_task(state_level, result, user_clicked_next)`.

- `theory/engine.py`  
  - выбор вопросов по `track/level`,
  - подсчёт `theory_score`.

- `reporting/aggregate.py`  
  - подсчёт `coding_score`, `theory_score`, `overall_score`,
  - расчёт `perf_index` и `final_grade_index`,
  - подготовка JSON для LLM-отчёта.

Этот файл — чистая спецификация логики.  
По нему можно спокойно писать реализацию в Cursor Pro.
