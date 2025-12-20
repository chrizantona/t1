# VibeCode Anti-Cheat — дизайн и реализация

Этот документ описывает, **как мы анализируем читинг** и считаем `trust_score` (0–100) для результата интервью.

Цель: не «ловить преступников», а давать честную **оценку доверия** к результату.

---

## 1. Общая идея

- На фронте мы собираем телеметрию:
  - ввод/копипаст кода,
  - переключение вкладок,
  - (опционально) открытие DevTools.
- На бэкенде:
  - агрегируем события,
  - считаем **сигналы**,
  - по ним вычисляем `trust_score` (0–100).
- В отчёте показываем:
  - числовой `trust_score`,
  - статус (`ok / suspicious / high_risk`),
  - краткое объяснение, **почему**.

---

## 2. События на фронте

### 2.1. Типы событий

Во фронтовой IDE (React) логируем события такого вида:

```ts
type AntiCheatEventType =
  | "keydown"
  | "paste"
  | "copy"
  | "cut"
  | "focus"
  | "blur"
  | "visibility_change"
  | "devtools";

interface AntiCheatEvent {
  type: AntiCheatEventType;
  taskId: string;
  timestamp: number;        // ms с начала epoch (Date.now())
  meta?: Record<string, unknown>;
}
```

Примеры `meta`:

- для `paste`:
  ```ts
  {
    length: number;         // длина вставленного текста
    fromEmpty: boolean;     // было ли поле кода пустым до вставки
  }
  ```

- для `keydown`:
  ```ts
  { chars: number }         // сколько симов изменено (обычно 1)
  ```

- для `visibility_change`:
  ```ts
  { visible: boolean }      // true/false
  ```

- для `devtools` (если детектим):
  ```ts
  { opened: boolean }
  ```

### 2.2. Отправка на backend

- События буферизуем на фронте.
- Отправляем:
  - либо каждые N секунд,
  - либо при сабмите задачи,
  - либо при завершении интервью.

API, например:

```http
POST /api/anti-cheat/events
{
  "interviewId": "...",
  "candidateId": "...",
  "events": AntiCheatEvent[]
}
```

---

## 3. Агрегация и сигналы на backend

На backend (FastAPI) события кладём в БД и агрегируем в **сигналы**.

### 3.1. Схема таблицы (пример)

```sql
CREATE TABLE anti_cheat_events (
  id           bigserial primary key,
  interview_id uuid      not null,
  candidate_id uuid      not null,
  task_id      text      not null,
  event_type   text      not null,
  timestamp_ms bigint    not null,
  meta         jsonb     not null
);
```

### 3.2. Сигналы, которые считаем

Считаем по всему интервью (или по каждой задаче, а потом агрегируем):

```python
class AntiCheatSignals(BaseModel):
    big_pastes_count: int              # количество больших вставок
    pastes_after_long_blur: int        # вставок после долгого ухода с вкладки
    suspiciously_fast_solutions: int   # очень быстрые идеальные решения
    devtools_opened: bool              # было ли событие devtools=true
    ai_likeness_score: float | None    # оценка "похожести на LLM"
```

#### Big paste (большие вставки кода)

Критерий:

- `type == "paste"`,
- `meta.length >= BIG_PASTE_THRESHOLD` (например, 150–200 символов),
- особенно если `meta.fromEmpty == true` и до этого было мало `keydown`.

#### Pastes after long blur

Паттерн:

- был `blur` / `visibility_change: visible=false`,
- прошло `> LONG_BLUR_MS` (например, 60 000–120 000 мс),
- сразу после возвращения (`focus`/`visibility_change: visible=true`) → `paste`.

Сигнал:

```python
pastes_after_long_blur >= 1
```

#### suspiciously_fast_solutions

Для каждой задачи у нас есть:

- время `task_opened_at`,
- время `first_successful_submit_at`, когда решение прошло почти все тесты.

Если:

- `task.difficulty in ("middle", "hard")`,
- `first_successful_submit_at - task_opened_at < FAST_THRESHOLD_SEC`
  (например, 30–60 сек),
- и при этом покрытие тестов высокое → считаем как `suspiciously_fast_solutions += 1`.

#### devtools_opened

Если приходило событие:

```json
{
  "type": "devtools",
  "meta": { "opened": true }
}
```

→ `devtools_opened = True`.

#### ai_likeness_score

Параллельно можно дернуть LLM:

- модель `qwen3-coder-30b-a3b-instruct-fp8`;
- промпт из `PROMPTS_VibeCode.md` для оценки «насколько код похож на LLM».

Получаем:

```json
{
  "ai_likeness_score": 0-100,
  "comment": "краткое объяснение"
}
```

---

## 4. Формула trust_score (0–100)

### 4.1. Общий принцип

- Стартуем с `100`.
- За каждый подозрительный паттерн вычитаем штраф.
- Результат обрезаем в диапазон `[0, 100]`.

```python
def calc_trust_score(signals: AntiCheatSignals) -> int:
    score = 100

    # 1. Большие вставки
    if signals.big_pastes_count >= 1:
        score -= 10 * min(signals.big_pastes_count, 3)  # максимум -30

    # 2. Вставки после долгого ухода с вкладки
    if signals.pastes_after_long_blur > 0:
        score -= 15

    # 3. Очень быстрые идеальные решения
    if signals.suspiciously_fast_solutions > 0:
        score -= 15 * min(signals.suspiciously_fast_solutions, 2)  # максимум -30

    # 4. DevTools
    if signals.devtools_opened:
        score -= 10

    # 5. AI-likeness
    if signals.ai_likeness_score is not None:
        ai = signals.ai_likeness_score
        if ai >= 80:
            score -= 25
        elif ai >= 60:
            score -= 10

    score = max(0, min(100, score))
    return score
```

### 4.2. Интерпретация trust_score

Условная шкала:

- `80–100` → **OK**
  - поведение выглядит естественным;
  - явных признаков внешней помощи нет.

- `50–79` → **Suspicious**
  - есть признаки копипаста/внешних подсказчиков;
  - рекомендуем ручной просмотр кода и логов.

- `0–49` → **High risk**
  - сильные признаки того, что решение получено не самостоятельно;
  - результат стоит использовать с осторожностью.

---

## 5. Объяснение в отчёте

Для каждой метрики желательно формировать человекочитаемый список триггеров.

```python
def build_trust_explanation(signals: AntiCheatSignals, trust_score: int) -> list[str]:
    reasons = []

    if signals.big_pastes_count > 0:
        reasons.append(f"обнаружено {signals.big_pastes_count} больших вставок кода")

    if signals.pastes_after_long_blur > 0:
        reasons.append(
            "фиксировались вставки кода сразу после длительного отсутствия во вкладке"
        )

    if signals.suspiciously_fast_solutions > 0:
        reasons.append(
            f"{signals.suspiciously_fast_solutions} задач решены подозрительно быстро при высоком покрытии тестов"
        )

    if signals.devtools_opened:
        reasons.append("во время решения задачи было открыто окно разработчика (DevTools)")

    if signals.ai_likeness_score is not None:
        if signals.ai_likeness_score >= 80:
            reasons.append(
                f"код сильно похож на LLM-генерированный (AI-likeness ~{signals.ai_likeness_score}%)"
            )
        elif signals.ai_likeness_score >= 60:
            reasons.append(
                f"код частично похож на LLM-генерированный (AI-likeness ~{signals.ai_likeness_score}%)"
            )

    if not reasons:
        reasons.append("аномалий в поведении не обнаружено")

    return reasons
```

В отчёт для компании отдаём, например:

```json
{
  "trust_score": 62,
  "trust_status": "suspicious",
  "trust_reasons": [
    "обнаружено 2 больших вставок кода",
    "фиксировались вставки кода сразу после длительного отсутствия во вкладке"
  ]
}
```

---

## 6. Интеграция в общий пайплайн

### 6.1. В момент завершения интервью

1. Собираем все события по `interviewId`:
   - из таблицы `anti_cheat_events`,
   - из данных по задачам (время выдачи/решения),
   - `ai_likeness_score` по финальным решениям.

2. На основе этого строим `AntiCheatSignals`.

3. Вызываем `calc_trust_score(signals)` и `build_trust_explanation(...)`.

4. Сохраняем в таблицу `interview_results`:

```sql
ALTER TABLE interview_results ADD COLUMN trust_score int;
ALTER TABLE interview_results ADD COLUMN trust_status text;
ALTER TABLE interview_results ADD COLUMN trust_reasons jsonb;
```

### 6.2. Использование в UI и отчёте

- В UI компании:
  - бейдж / индикатор `trust_score`;
  - цвет (зелёный/жёлтый/красный);
  - список причин (tooltip / collapsible panel).

- В PDF/HTML-отчёте:
  - отдельный блок «Доверие к результату (Anti-cheat)»:
    - `trust_score`,
    - статус,
    - причины.

---

## 7. Что нужно реализовать (конкретные шаги)

1. **Frontend**
   - Обёртка вокруг редактора кода:
     - логирование `paste/copy/cut/keydown`.
   - Листенеры окна:
     - `focus/blur`,
     - `visibilitychange`.
   - (Опционально) DevTools detection.
   - Кью событий и `POST /api/anti-cheat/events`.

2. **Backend**
   - Pydantic-модель `AntiCheatEvent` и `AntiCheatSignals`.
   - Endpoint `/api/anti-cheat/events` (bulk ingest).
   - Сервис `anti_cheat_service`:
     - `build_signals(interview_id) -> AntiCheatSignals`,
     - `calc_trust_score(signals) -> int`,
     - `build_trust_explanation(signals, score) -> list[str]`.

3. **Reporting**
   - Добавить `trust_score`, `trust_status`, `trust_reasons` в итоговый JSON отчёта.
   - (Опционально) использовать LLM только для красивой текстовой формулировки,
     но НЕ для расчёта самого `trust_score`.

Этот файл можно положить в репу как `ANTICHEAT.md` и использовать как спецификацию для реализации.
