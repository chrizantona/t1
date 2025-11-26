```markdown
# VibeCode Jam — README для реализации платформы

Этот README — ТЗ для Cursor / кода: как собрать нашу платформу **AI-собеседований** с поддержкой вакансий, баз задач, метрик, анти-читерства и адаптивности.

Используем **ТОЛЬКО SciBox LLM**:

- `qwen3-32b-awq` — универсальный чат.
- `qwen3-coder-30b-a3b-instruct-fp8` — код-ассистент.
- `bge-m3` — эмбеддинги (поиск задач, матчинги).

---

## 0. Концепт в двух словах

Мы делаем платформу, где:

- **Центр мира — вакансия**, а не просто “рандомное собеседование”.
- Кандидат:
  1. Выбирает вакансию и уровень.
  2. Грузит резюме.
  3. Проходит:
     - алго-задачу,
     - практическую по направлению (pipeline/endpoint/и т.д.),
     - теорию по скиллам из вакансии и резюме.
- **SciBox LLM**:
  - адаптирует сложность,
  - задаёт уточняющие вопросы,
  - объясняет ошибки,
  - оценивает ответы,
  - **НЕ решает задачи за кандидата** (только подсказки и разбор после).
- В конце:
  - считаем **математическую метрику**,
  - выдаём грейд и отчёт “кандидат ↔ конкретная вакансия”.

Фокус на демо-видео: показать **полный цикл** + **адаптивность** + **обратную связь** + **анти-чит** + **финальный отчёт**.

---

## 1. Основные сущности домена

### 1.1. Вакансия (`Vacancy`)

```ts
type SkillType = "algo" | "practice" | "theory" | "system_design";

type VacancySkill = {
  id: string;             // "python", "ml_basics", "docker", ...
  name: string;
  requiredLevel: 0 | 1 | 2 | 3; // 0 - не критично, 3 - высокий уровень
  weight: number;         // важность в итоговой метрике
  type: SkillType;
};

type Vacancy = {
  id: string;
  title: string;          // "ML Engineer Junior"
  direction: "ML" | "Backend" | "Frontend" | "DevOps" | "QA" | "Data";
  gradeRequired: "junior" | "middle" | "senior";

  skills: VacancySkill[];

  // Привязанные слоты задач
  algoSlots: string[];      // id задач easy/med/hard
  practiceSlots: string[];  // id практических задач
  theoryQuestionIds: string[]; // id вопросов по теории

  // Параметры метрики и пороги решения
  scoringWeights: {
    algo: number;
    practice: number;
    theory: number;
    soft: number;
    skillsMatch: number;
  };

  decisionThresholds: {
    hire: number;       // >=
    consider: number;   // >=, но < hire
  };

  criticalSkills: string[]; // id скиллов, без которых auto reject
};
```

---

### 1.2. База задач и вопросов (`Task`, `Question`)

#### 1.2.1. Алго / практические задачи

```ts
type Difficulty = "easy" | "medium" | "hard";

type TestCase = {
  input: string;
  expectedOutput: string;
  hidden: boolean;
  timeoutMs?: number;
};

type Task = {
  id: string;
  source: "internal" | "deepml" | "cf_like" | "frontend_like" | "devops_lab";
  direction: "Algo" | "ML" | "Backend" | "Frontend" | "DevOps" | "QA" | "Data";
  difficulty: Difficulty;
  title: string;
  statementCore: string;        // сухое описание сути
  tags: string[];               // ["array", "two_pointers"]
  skills: string[];             // id VacancySkill, которые эта задача проверяет
  publicTests: TestCase[];
  privateTests: TestCase[];
  maxScore: number;             // обычно 100
};
```

**Откуда брать задачи (примеры источников):**

* Алгоритмы: свои / open-аналоги leetcode/CF (easy/medium/hard).
* ML: Deep-ML — открытая платформа задач по ML, все задачи бесплатны и постоянно обновляются сообществом.([deep-ml.com](https://www.deep-ml.com/?utm_source=chatgpt.com "Deep-ML"))
* Frontend: BFE.dev — “как leetcode, но для фронта”, >600 JS/React/CSS задач.([bigfrontend.dev](https://bigfrontend.dev/?utm_source=chatgpt.com "BFE.dev - prepare for Front-End job interviews."))
* DevOps: идеи тасков по DevOps можно брать из KodeKloud Engineer (реальные задачки в симулированной компании).([KodeKloud Engineer](https://engineer.kodekloud.com/?utm_source=chatgpt.com "KodeKloud Engineer | Real Project Tasks on Real Systems"))
* ML-вопросы: твоя PDF + open репы вроде Machine-Learning-Interviews.([GitHub](https://github.com/alirezadir/Machine-Learning-Interviews?utm_source=chatgpt.com "alirezadir/Machine-Learning-Interviews"))

Формально в коде считаем, что все задачи хранятся у нас в БД, с уже подготовленными тестами.

#### 1.2.2. Теоретические вопросы

```ts
type QuestionType = "theory" | "design" | "debug" | "pipeline";

type Question = {
  id: string;
  direction: "ML" | "Go" | "Python" | "Git" | "Docker" | "Linux" | "HTTP" | "Kafka" | ...;
  topic: string;            // "regularization", "goroutine", ...
  text: string;             // сам вопрос
  difficulty: "junior" | "middle" | "senior";
  type: QuestionType;
  tags: string[];
  hasCanonicalAnswer: boolean;
  canonicalAnswer?: string; // эталонный краткий ответ
  keyPoints?: string[];     // список пунктов, по которым оцениваем
};
```

**ML PDF** → автоматически парсим в `(question, answer)` и размечаем difficulty/topic/type через `qwen3-32b-awq`.

**Go/Python/Git/Docker без ответов** → автогенерируем `canonicalAnswer` + `keyPoints` через LLM  **оффлайн** , сохраняем в БД.

---

### 1.3. Профиль кандидата (`CandidateProfile`)

```ts
type SkillLevel = 0 | 1 | 2 | 3; // 0 - не умеет, 3 - сильный

type CandidateSkillSnapshot = {
  skillId: string;
  levelFromResume?: SkillLevel;
  levelFromPractice?: SkillLevel;
  levelFromTheory?: SkillLevel;
  finalLevel?: number; // float 0..3
};

type CandidateProfile = {
  id: string;
  name: string;
  resumeRaw: string;             // текст из pdf
  direction: string;
  initialGrade: "junior" | "middle" | "senior"; // по резюме
  skills: CandidateSkillSnapshot[];
};
```

Профиль строится из резюме через `qwen3-32b-awq`: вытаскиваем стек, опыт, примерный грейд.

---

### 1.4. Сессия собеседования (`InterviewSession`)

```ts
type InterviewStage = "ALGO" | "PRACTICE" | "THEORY" | "DONE";

type HintLevel = "light" | "medium" | "heavy";

type HintUsage = {
  taskId: string;
  hintLevel: HintLevel;
  penalty: number;  // -10/-25/-40 из 100
};

type CheatSignals = {
  copyPasteCount: number;
  devtoolsOpened: boolean;
  focusLostCount: number;
  aiStyleScore: number;   // 0..1, оценка LLM "похоже на AI-код"
  codeSimilarityScore: number; // 0..1 к нашим эталонным решениям (через embeddings)
};

type StageResult = {
  stage: InterviewStage;
  taskId?: string;
  questionId?: string;
  rawScore: number;        // до штрафов
  finalScore: number;      // после штрафов
  details: any;            // время, попытки, асимптотика и т.п.
};

type InterviewSession = {
  id: string;
  vacancyId: string;
  candidateId: string;
  currentStage: InterviewStage;

  chosenLevel: "junior" | "middle" | "senior"; // что выбрал кандидат при старте
  effectiveLevel: "junior" | "middle" | "senior"; // динамический, может подрасти/упасть

  algoTaskId?: string;
  practiceTaskId?: string;
  theoryQuestionIds: string[];

  hints: HintUsage[];
  cheatSignals: CheatSignals;

  stages: StageResult[];

  finalScore?: number;     // 0..100
  finalGrade?: "junior" | "middle" | "senior";
  decision?: "hire" | "consider" | "reject";
};
```

---

## 2. Поток собеседования end-to-end (для демо и логики)

### 2.1. Старт: вакансия + резюме + уровень

1. Пользователь открывает платформу.
2. Выбирает **вакансию** (из списка).
3. Выбирает  **уровень собеседования** : `Junior / Middle / Senior`.
4. Загружает резюме (PDF/текст).
5. Бэкенд:
   * вытаскивает текст PDF,
   * шлёт в `qwen3-32b-awq` → строит `CandidateProfile`:
     * примерный грейд,
     * базовые скиллы.
6. Создаётся `InterviewSession` c:
   * `vacancyId`,
   * `candidateId`,
   * `chosenLevel`,
   * `effectiveLevel` = min(chosenLevel, vacancy.gradeRequired).

---

### 2.2. Блок 1. Алгоритмы (адаптивность + асимптотика)

**Уровни задач:**

```text
Для chosenLevel = JUNIOR:   первая задача: easy,   повышаем — medium
Для chosenLevel = MIDDLE:   первая задача: medium, повышаем — hard
Для chosenLevel = SENIOR:   первая задача: hard,   дальше hard/дизайн
```

**Демо по ТЗ:**

* демонстрируем:
  * выбор `Junior`,
  * первая задача — easy (Junior),
  * после успешного решения — вторая задача — medium (Middle-level).

**Алгоритм:**

1. Бэкенд выбирает `algoTask`:

   ```ts
   pickAlgoTask(vacancy, effectiveLevel) -> Task
   // например:
   // junior -> easy, middle -> medium, senior -> hard
   ```
2. Показываем задачу в UI:

   * statement генерируем  **real-time** :
     * берём `task.statementCore`,
     * шлём в `qwen3-32b-awq` с `stream: true` и промптом «оформить условие для junior/middle/senior».
   * В IDE (Monaco/CodeMirror) включена подсветка, автодоп, запуск в Docker.
3. Кандидат пишет код, запускает:

   * публичные тесты (видно зелёные галочки),
   * приватные тесты (видно только факт: прошёл/не прошёл).
4. Сохраняем метрики:

   * время до первого успешного запуска,
   * количество запусков,
   * процент прохода скрытых тестов.
5. После первого решения ассистент спрашивает про  **асимптотику** :

   ```json
   // Intent ASK_QUESTION (детально ниже в LLM-протоколе)
   {
     "intent": "ASK_QUESTION",
     "stage": "ALGO",
     "direction": "Algo",
     "difficulty": chosenLevel,
     "language": "ru",
     "context": {
       "questionType": "time_space_complexity",
       "taskId": "..."
     }
   }
   ```

   LLM формирует вопрос, например:

   > "Расскажи, как работает твой алгоритм и какая у него сложность по времени и памяти?"
   >
6. Кандидат отвечает текстом; мы:

   * оцениваем ответ через `qwen3-32b-awq` (`EVALUATE_ANSWER`),
   * параллельно `qwen3-coder` смотрит на код и оценивает ожидаемую сложность,
   * сравниваем:  **совпадает ли понимание кандидата с реальной сложностью** .
7. **AI-generated code detection (черновая логика):**

   * фронт: отслеживаем:
     * большие paste-события,
     * devtools,
     * странные паттерны (копипаста из буфера).
   * бэкенд:
     * сравниваем код с нашими эталонными решениями через `bge-m3` (эмбеддинги),
     * шлём код в `qwen3-coder` с intent `CLASSIFY_AI_LIKE`:
       * модель возвращает `aiStyleScore ∈ [0,1]`.
   * всё это записывается в `session.cheatSignals`.
8. На основе:

   * правильности,
   * времени,
   * асимптотики,
   * количества попыток,
   * подсказок (см. подсказки ниже),

   считаем `algoStageResult`.
9. Адаптивность:

   * если `algoStageResult.finalScore` > порога (например 70) и `cheatSignals.aiStyleScore < 0.5`:
     * повышаем `effectiveLevel` на ступень (`junior -> middle`, `middle -> senior`).
   * это используется для выбора следующей задачи (в демо — второй задачи уровня Middle).

---

### 2.3. Блок 2. Практика по направлению (ML pipeline / BE endpoint / и т.д.)

1. Из `Vacancy.skills` берём must-have навыки с `type = "practice"` (и direction вакансии).
2. Подбираем `Task` с `direction = vacancy.direction` и `difficulty` ~= `effectiveLevel`.
   * Для ML — задача из Deep-ML типа «собрать классификационный pipeline на sklearn» (у нас уже есть публичные и приватные тесты).
   * Для BE — HTTP endpoint с проверкой логики ответа.
   * Для DevOps — консольная команда/скрипт с валидацией состояния контейнера/сервиса.
3. Как и в алго-кейсе:
   * statement оформляем через `qwen3-32b-awq` с `stream: true`, чтобы текст задачи “печатался” в реальном времени.
   * запуск кода — в Docker.
4. Кандидат решает:
   * публичные тесты проходят,
   * скрытые могут падать (по ТЗ это нужно показать).
5. При падении скрытых тестов:
   * шлём код + результаты тестов в `qwen3-coder` с intent `ANALYZE_BUG`,
   * LLM генерит объяснение ошибки (без прямого решения),
   * показываем кандидату, даём шанс исправить.
6. Считаем `practicalStageResult`.

---

### 2.4. Блок 3. Теория по вакансии + “углубление, если кандидат сам поднял тему”

1. Из вакансии берём `Vacancy.skills` с `type = "theory"` и их важность.
2. Из `CandidateProfile.skills` смотрим:

   * какие из этих скиллов он указал в резюме,
   * какие нет.
3. Формируем очередь вопросов:

   * **пересечение** (есть и в резюме, и в вакансии, must-have) → спросить первым,
   * **must-have, которых нет в резюме** → уточнить “чуть-чуть знаешь или совсем нет?”,
   * **nice-to-have** → если остались время/метрики.
4. Каждый вопрос задаём через LLM (intent `ASK_QUESTION` / `THEORY`).
5. Кандидат отвечает, и мы:

   * шлём `EVALUATE_ANSWER` с `canonicalAnswer` + `keyPoints`,
   * получаем:
     * `score 0..3`,
     * `comment_for_interviewer`,
     * `short_feedback_for_candidate`.
6. **Фича: кандидат “уехал” в другой топик, и LLM его “гасит до талого”**
   Реализация:

   * В промпте `EVALUATE_ANSWER` просим LLM дополнительно:
     * выделить **появившиеся темы** из ответа (например, кандидат начал рассуждать про Kafka, хотя вопрос был про HTTP).
   * Если среди этих тем есть скиллы из `Vacancy.skills` с высоким весом:
     * добавляем новый вопрос по этой теме в очередь.
   * В следующем вопросе LLM пишет:
     > "Ты упомянул Kafka. Давай чуть глубже: расскажи, как работают consumer groups."
     >

   Так LLM  **подхватывает то, во что сам влез кандидат** , и докапывается до уровня его реальных знаний.
7. Вся теория суммируется в `theoryStageResult`, плюс обновляются `CandidateSkillSnapshot.levelFromTheory`.

---

## 3. Подсказки по задачам (hint system)

Для каждой задачи (`Task.maxScore = 100`) есть три уровня подсказок:

```ts
HintLevel: 
  "light"  // -10 баллов
  "medium" // -25 баллов
  "heavy"  // -40 баллов
```

### Логика:

* **Light hint (−10)** :
* “подтолкнуть мысль”: назвать подход/структуру данных, но без кода.
* **Medium hint (−25)** :
* описать пошаговый план решения, можно с псевдокодом, но без полного рабочего кода.
* **Heavy hint (−40)** :
* практически раскрывает алгоритм целиком, но:
  * **без финального кода** ,
  * без точных констант/имён — кандидат всё равно должен собраться и написать сам.

**Правило:**

В `ALGO` и `PRACTICE` стадиях  **LLM НИКОГДА не выдаёт полный рабочий код** , пока задача активна.

Он может только:

* дать подсказку (intent `GIVE_HINT`),
* объяснить ошибку (intent `ANALYZE_BUG`),
* задать наводящие вопросы.

Только когда задача закрыта (успешно/по таймауту) — можно вызвать intent `EXPLAIN_SOLUTION`,

и то в демо достаточно текстового объяснения и хайлайта ключевых идей.

Подсказки записываются в `session.hints`, и при подсчёте `finalScore` для задачи мы уменьшаем:

```ts
finalScore = rawScore - Σ(hint.penalty)
finalScore = Math.max(finalScore, 0)
```

---

## 4. Анти-читерство

### 4.1. Фронтенд сигналы

Ловим:

* `copy` / `paste` в редакторе.
* Открытие DevTools (по событиям).
* Потери фокуса окна (`blur/focus`) и их частоту.
* Возможные признаки расширений (эвристика: упираемся в то, что реально успеем).

Всё это → `CheatSignals`:

```ts
cheatSignals = {
  copyPasteCount,
  devtoolsOpened,
  focusLostCount,
  aiStyleScore,
  codeSimilarityScore
}
```

### 4.2. Бэкенд / LLM сигналы

1. **Сходство с эталонными решениями:**
   * для каждой задачи храним `referenceSolutions` (или хотя бы 1).
   * считаем эмбеддинги через `bge-m3`:
     * кандидатский код vs эталон,
   * получаем `codeSimilarityScore ∈ [0,1]`.
2. **AI-style классификация:**
   * шлём код в `qwen3-coder` c intent `CLASSIFY_AI_LIKE`:
     > "Оцени по шкале 0..1, насколько этот код похож на сгенерированный LLM (стиль, имена, структура)."
     >
   * результат → `aiStyleScore`.
3. **Совокупный риск читерства:**
   Где-то в конце считаем:
   ```ts
   const cheatRisk = f(cheatSignals) // 0..1
   const cheatPenaltyFactor = 1 - 0.3 * cheatRisk // до -30% от общего балла
   finalScore = totalScore * cheatPenaltyFactor
   ```

В отчёте показываем:

* не “ты списал”, а:
  * “Высокий риск неоригинальности решения” + расшифровка сигналов.

---

## 5. Итоговая метрика (“майонезная”) и грейд

### 5.1. Оценка по скиллам вакансии

Для каждого `VacancySkill`:

* есть `requiredLevel ∈ [0..3]` и `weight`.
* из `CandidateProfile.skills` получаем `finalLevel ∈ [0..3]` (агрегируем из practice+theory).

Пример:

```ts
delta = finalLevel - requiredLevel;  // может быть отрицательным
scoreSkill = clamp(50 + 25 * delta, 0, 100); 
// требуемый уровень → ~50
// на 1 уровень выше → ~75
// на 1 ниже → ~25
weightedSkill = scoreSkill * skill.weight;
```

Дальше:

```ts
skillsMatchScore = Σ(weightedSkill) / Σ(skill.weight); // 0..100
```

### 5.2. Баллы по блокам

По каждой стадии есть свои `stageResult.finalScore`:

* `algoScore`
* `practicalScore`
* `theoryScore`
* `softScore` (оценка коммуникации LLM’ом)

Весовку берём из `Vacancy.scoringWeights`:

```ts
totalRaw =
  w.algo      * algoScore +
  w.practice  * practicalScore +
  w.theory    * theoryScore +
  w.soft      * softScore +
  w.skillsMatch * skillsMatchScore;

totalScore = totalRaw / (w.algo + w.practice + w.theory + w.soft + w.skillsMatch);
```

### 5.3. Учитываем читерство

```ts
const cheatRisk = computeCheatRisk(session.cheatSignals); // 0..1
const cheatPenaltyFactor = 1 - 0.3 * cheatRisk;
finalScore = totalScore * cheatPenaltyFactor;
```

### 5.4. Грейд и решение по вакансии

На основе `finalScore` и `Vacancy.gradeRequired`:

```ts
if finalScore < 40 -> "reject"
if 40 <= finalScore < 60 -> "consider", grade ~ junior
if 60 <= finalScore < 80 -> "hire", grade ~ middle
if finalScore >= 80 -> "hire", grade ~ senior (или сильный middle)
```

Плюс:

* если провален любой `criticalSkill` → можно автосбросить до `consider/reject`.

---

## 6. LLM-интеграция и “умные промпты”

### 6.1. Общая идея

Мы НЕ общаемся с LLM “вслепую”. Каждый запрос:

* строго структурирован (`intent`, `stage`, `direction` и т.д.),
* system prompt указывает модели, что она —  **интервьюер** , а не “сделай за меня задачу”.

### 6.2. Протокол запроса

В каждый `messages` отправляем:

* `system`: единый промпт-протокол.
* `user`: JSON с полями:

```json
{
  "intent": "ASK_QUESTION" | "EVALUATE_ANSWER" | "GIVE_HINT" | "ANALYZE_BUG" | "EXPLAIN_SOLUTION" | "SMALL_TALK" | "CLASSIFY_AI_LIKE" | "PARSE_RESUME" | "PARSE_VACANCY",
  "stage": "ALGO" | "PRACTICE" | "THEORY" | "META",
  "direction": "...",
  "difficulty": "junior" | "middle" | "senior",
  "language": "ru",
  "context": { ... } // специфичные поля: taskId, code, canonicalAnswer, keyPoints, candidateAnswer и т.д.
}
```

### 6.3. Пример system prompt (qwen3-32b-awq)

```text
/no_think
Ты ИИ-интервьюер платформы технических собеседований.
Ты НЕ обычный чат-бот и НЕ должен просто решать задачи за кандидата.

Каждый запрос к тебе приходит в виде JSON в последнем сообщении пользователя.
Твои правила:

1. Сначала распарсь JSON.
2. Посмотри поле "intent" и "stage".
3. Выполни строго то, что требуется для этого intent.
4. Отвечай ТОЛЬКО одним JSON-объектом без лишнего текста.

intent:
- "ASK_QUESTION": сгенерировать формулировку вопроса для кандидата.
- "EVALUATE_ANSWER": оценить ответ кандидата относительно canonical_answer и key_points.
- "GIVE_HINT": дать подсказку по задаче (без полного решения и рабочего кода).
- "ANALYZE_BUG": объяснить, почему решение кандидата не проходит скрытые тесты, и дать направление исправления.
- "EXPLAIN_SOLUTION": после завершения вопроса объяснить правильный подход (опционально с упрощённым примером).
- "SMALL_TALK": поддержать лёгкий диалог без раскрытия ответов или решений задач.
- "CLASSIFY_AI_LIKE": по куску кода оценить, насколько он похож на AI-сгенерированный (0..1).
- "PARSE_RESUME": извлечь скиллы и примерный грейд из текста резюме.
- "PARSE_VACANCY": извлечь скиллы и требования из описания вакансии.

Особо важно:
- В intent "ASK_QUESTION", "GIVE_HINT", "ANALYZE_BUG" и "SMALL_TALK" НИКОГДА не выдавай полный рабочий код решения задачи.
- Полные решения можно описывать только в intent "EXPLAIN_SOLUTION" И ТОлько если в контексте указано, что задача уже завершена.

Формат ответов:
- ASK_QUESTION: {"question_text": "...", "short_intro": "..."}
- EVALUATE_ANSWER: {"score": 0..3, "comment_for_interviewer": "...", "short_feedback_for_candidate": "...", "extra_topics": ["..."] }
- GIVE_HINT: {"hint_level": "light|medium|heavy", "hint_text": "..."}
- ANALYZE_BUG: {"analysis": "...", "suggested_focus": "..."}
- EXPLAIN_SOLUTION: {"explanation": "..."}
- SMALL_TALK: {"reply": "..."}
- CLASSIFY_AI_LIKE: {"ai_style_score": 0.0..1.0}
- PARSE_RESUME: {"proposed_grade": "...", "skills": [{ "id": "...", "level": 0..3 }]}
- PARSE_VACANCY: {"skills": [...], "critical_skills": [...], "weights": {...}}
```

Аналогичный протокол, но с уклоном в код — для `qwen3-coder` (ANALYZE_BUG, CLASSIFY_AI_LIKE, EXPLAIN_SOLUTION по коду).

---

## 7. Источники задач по направлениям (на будущее для наполнения)

Не строго для реализации, но как ориентир, откуда брать идеи/данные:

* **Алгоритмы:** покрытие easy/medium/hard по основным темам — массивы, строки, хеш-таблицы, деревья, графы, DP.

  (аналогично подборкам top-interview задач на LeetCode).([LeetCode](https://leetcode.com/explore/interview/card/top-interview-questions-easy/?utm_source=chatgpt.com "LeetCode's Interview Questions Easy Collection."))
* **ML & Data:** Deep-ML, репозитории ML-интервью вопросов, твоя PDF.([deep-ml.com](https://www.deep-ml.com/?utm_source=chatgpt.com "Deep-ML"))
* **Frontend:** BFE.dev (JS/React), Frontend-интервью вопросы.([bigfrontend.dev](https://bigfrontend.dev/?utm_source=chatgpt.com "BFE.dev - prepare for Front-End job interviews."))
* **DevOps:** KodeKloud Engineer, коллекции free labs.([KodeKloud Engineer](https://engineer.kodekloud.com/?utm_source=chatgpt.com "KodeKloud Engineer | Real Project Tasks on Real Systems"))
* **QA:** классика по тест-дизайну, кейсы на граничные значения, сценарии.

В коде всё это хранится как наши `Task`/`Question`.

---

## 8. Финальный отчёт и формат для скачивания

После завершения сессии генерим отчёт (JSON → PDF).

Структура отчёта:

```ts
type Report = {
  candidate: { name: string; id: string; };
  vacancy: { id: string; title: string; gradeRequired: string; };

  summary: {
    finalScore: number;           // 0..100
    finalGrade: "junior"|"middle"|"senior";
    decision: "hire"|"consider"|"reject";
    cheatRisk: number;            // 0..1
  };

  blocks: {
    algo: {
      score: number;
      difficultyStart: string;   // easy
      difficultyEnd: string;     // medium
      attempts: number;
      timeSeconds: number;
      complexityUnderstanding: number; // 0..100
      comments: string;
    };
    practice: {
      score: number;
      taskId: string;
      description: string;
      attempts: number;
      timeSeconds: number;
      comments: string;
    };
    theory: {
      score: number;
      perSkill: {
        skillId: string;
        requiredLevel: number;
        observedLevel: number;
        score: number;
        interviewerComment: string;
      }[];
    };
    soft: {
      score: number;
      comments: string;
    };
    hints: HintUsage[];
    cheatSignals: CheatSignals;
  };

  explanationForInterviewer: string; // текст от LLM для нанимающей стороны
  explanationForCandidate: string;   // мягкий фидбек для кандидата
};
```

**Ключевое в демо:**

* показать UI с:
  * финальными баллами,
  * пояснением грейда,
  * краткими “сильные стороны / зоны роста”.
* кнопка «Скачать отчёт» → генерим PDF из этого.

---

## 9. Сценарий демо-видео (чтобы всё это показать)

1. Открытие платформы.
2. Выбор вакансии (например, ML Junior) и **уровня собеса** (Junior).
3. Загрузка резюме → отображение короткого summary профиля.
4. Старт сессии: IDE, первая алго-задача (Junior/easy):
   * видно, как условие “печатается” (stream от LLM).
5. Кандидат пишет код:
   * запускает → видимые тесты зелёные.
6. LLM задаёт вопрос про асимптотику в чате.
7. Кандидат отвечает → LLM кратко оценивает.
8. LLM говорит, что **уровень повышается** → генерирует вторую задачу (Middle, medium):
   * опять real-time генерация условия.
9. Кандидат решает вторую:
   * видимые тесты ок,
   * скрытые падают (показать).
10. LLM анализирует ошибку, объясняет, куда смотреть.
11. Кандидат фиксит → все тесты зелёные.
12. Быстрый показ задачи по направлению (ML pipeline / простая практическая).
13. Демонстрация анти-читерства:
    * копипаста,
    * devtools,
    * где-то в UI подсвечиваем “Cheat signals: moderate”.
14. Теория:
    * вопрос по Git/Docker,
    * кандидат уходит в сторону (например, Kafka),
    * LLM подхватывает Kafka и задаёт follow-up.
15. Пара реплик туда-сюда (диалог).
16. Обновление метрик (настройки/индикаторы в UI).
17. Финальный отчёт:
    * общий скор,
    * грейд,
    * match к вакансии,
    * сильные/слабые стороны,
    * кнопка “Download PDF”.

---

Этот README можно кидать в Cursor/Claude как  **основное ТЗ** :

* тут описаны:
  * **база задач** и откуда её наполнять,
  * **логика вакансий и скилл-матриц** ,
  * **адаптивность задач** ,
  * **LLM-протоколы** (чтобы ассистент понимал, что от него хотят),
  * **анти-чит и подсказки** ,
  * **формула метрик и финальный отчёт** ,
  * **сценарий демо-видео** .

Дальше можно уже нарезать по задачам: сервис для задач, сервис для сессий, LLM-адаптер, фронт с IDE и отчётами.

```
::contentReference[oaicite:8]{index=8}
```
