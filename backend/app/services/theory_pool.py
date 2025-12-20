"""
Theory Questions Pool.

Structured theory questions by direction and topic.
Each question has:
- question_text: The question itself
- canonical_answer: Expected correct answer
- key_points: Points that must be mentioned
- difficulty: junior/middle/senior
- direction: backend/frontend/ml/devops/data/any
- topic: specific topic
"""
from typing import Dict, List, Any, Optional
import random


THEORY_QUESTIONS: Dict[str, Dict[str, Any]] = {
    # ==================== ALGORITHMS ====================
    "algo_time_complexity": {
        "id": "algo_time_complexity",
        "question_text": "Что такое Big O нотация и зачем она нужна? Приведите примеры.",
        "canonical_answer": "Big O — асимптотическая нотация для описания верхней границы времени выполнения или памяти алгоритма при росте входных данных. Позволяет сравнивать эффективность алгоритмов. Примеры: O(1) — константное время (доступ к элементу массива), O(log n) — бинарный поиск, O(n) — линейный поиск, O(n log n) — эффективные сортировки (merge sort), O(n²) — bubble sort.",
        "key_points": ["верхняя граница", "рост данных", "O(1)", "O(n)", "O(n²)"],
        "difficulty": "junior",
        "direction": "any",
        "topic": "algorithms"
    },
    "algo_hash_table": {
        "id": "algo_hash_table",
        "question_text": "Как работает хеш-таблица? Что такое коллизии и как с ними бороться?",
        "canonical_answer": "Хеш-таблица — структура данных с O(1) доступом по ключу. Хеш-функция преобразует ключ в индекс. Коллизия — когда разные ключи дают одинаковый хеш. Методы разрешения: цепочки (списки в ячейках), открытая адресация (линейное/квадратичное пробирование).",
        "key_points": ["O(1) доступ", "хеш-функция", "коллизия", "цепочки", "открытая адресация"],
        "difficulty": "junior",
        "direction": "any",
        "topic": "data_structures"
    },
    "algo_sorting": {
        "id": "algo_sorting",
        "question_text": "Сравните quicksort и mergesort. Когда какой лучше использовать?",
        "canonical_answer": "Quicksort: O(n log n) в среднем, O(n²) в худшем, in-place, нестабильная. Mergesort: O(n log n) всегда, требует O(n) памяти, стабильная. Quicksort лучше для массивов в памяти. Mergesort — для связных списков, внешней сортировки, когда важна стабильность.",
        "key_points": ["O(n log n)", "in-place", "стабильность", "худший случай quicksort"],
        "difficulty": "middle",
        "direction": "any",
        "topic": "algorithms"
    },
    
    # ==================== BACKEND ====================
    "http_methods": {
        "id": "http_methods",
        "question_text": "Какие HTTP методы вы знаете? В чём разница между PUT и PATCH?",
        "canonical_answer": "GET — получение, POST — создание, PUT — полное обновление, PATCH — частичное обновление, DELETE — удаление. PUT заменяет ресурс целиком, PATCH изменяет только переданные поля. PUT идемпотентен, PATCH может быть неидемпотентен.",
        "key_points": ["GET", "POST", "PUT", "PATCH", "идемпотентность", "полное/частичное обновление"],
        "difficulty": "junior",
        "direction": "backend",
        "topic": "api"
    },
    "sql_joins": {
        "id": "sql_joins",
        "question_text": "Объясните разницу между INNER JOIN, LEFT JOIN, RIGHT JOIN и FULL JOIN.",
        "canonical_answer": "INNER JOIN — только совпадающие строки из обеих таблиц. LEFT JOIN — все строки из левой + совпадения из правой (NULL если нет). RIGHT JOIN — наоборот. FULL JOIN — все строки из обеих таблиц с NULL где нет совпадений.",
        "key_points": ["INNER - только совпадения", "LEFT - все из левой", "NULL для несовпадающих"],
        "difficulty": "junior",
        "direction": "backend",
        "topic": "sql"
    },
    "sql_indexes": {
        "id": "sql_indexes",
        "question_text": "Что такое индексы в БД? Когда их стоит создавать, а когда нет?",
        "canonical_answer": "Индекс — структура (обычно B-tree) для быстрого поиска. Создавать: для частых SELECT, WHERE, JOIN, ORDER BY. Не создавать: для маленьких таблиц, часто обновляемых колонок, колонок с низкой селективностью. Индексы замедляют INSERT/UPDATE.",
        "key_points": ["B-tree", "ускоряет SELECT", "замедляет INSERT/UPDATE", "селективность"],
        "difficulty": "middle",
        "direction": "backend",
        "topic": "sql"
    },
    "docker_basics": {
        "id": "docker_basics",
        "question_text": "Что такое Docker? В чём отличие контейнера от виртуальной машины?",
        "canonical_answer": "Docker — платформа контейнеризации. Контейнер использует ядро хост-системы (лёгкий, быстрый старт). VM имеет своё ядро и гипервизор (тяжелее, полная изоляция). Контейнеры изолируют процессы через namespaces и cgroups Linux.",
        "key_points": ["общее ядро", "namespaces", "cgroups", "легковесность", "быстрый старт"],
        "difficulty": "junior",
        "direction": "backend",
        "topic": "devops"
    },
    "redis_cache": {
        "id": "redis_cache",
        "question_text": "Что такое Redis? Какие сценарии использования кеширования вы знаете?",
        "canonical_answer": "Redis — in-memory key-value хранилище. Сценарии: кеширование запросов к БД, сессии пользователей, очереди задач, pub/sub, rate limiting. Стратегии: write-through, write-behind, cache-aside. Важно учитывать инвалидацию кеша.",
        "key_points": ["in-memory", "key-value", "кеширование", "сессии", "очереди", "инвалидация"],
        "difficulty": "middle",
        "direction": "backend",
        "topic": "databases"
    },
    "rest_vs_graphql": {
        "id": "rest_vs_graphql",
        "question_text": "Сравните REST и GraphQL. Когда какой подход лучше?",
        "canonical_answer": "REST: фиксированные эндпоинты, over/under-fetching, простой кеш (HTTP). GraphQL: гибкие запросы, один эндпоинт, сложный кеш. REST лучше для простых CRUD API с кешированием. GraphQL — для сложных связей данных, мобильных приложений, когда клиент контролирует данные.",
        "key_points": ["over-fetching", "under-fetching", "один эндпоинт", "гибкость запросов"],
        "difficulty": "middle",
        "direction": "backend",
        "topic": "api"
    },
    
    # ==================== FRONTEND ====================
    "react_hooks": {
        "id": "react_hooks",
        "question_text": "Что такое React Hooks? Какие основные хуки вы используете?",
        "canonical_answer": "Hooks — функции для использования состояния и lifecycle в функциональных компонентах. useState — локальное состояние. useEffect — side effects (запросы, подписки). useContext — контекст. useMemo/useCallback — мемоизация. useRef — ссылки на DOM/значения между рендерами.",
        "key_points": ["useState", "useEffect", "useContext", "useMemo", "useCallback"],
        "difficulty": "junior",
        "direction": "frontend",
        "topic": "react"
    },
    "css_flexbox": {
        "id": "css_flexbox",
        "question_text": "Объясните основные свойства Flexbox. Как работают justify-content и align-items?",
        "canonical_answer": "Flexbox — одномерная модель раскладки. display: flex создаёт flex-контейнер. justify-content — выравнивание по главной оси (flex-start, center, space-between). align-items — по поперечной оси. flex-direction задаёт главную ось (row/column).",
        "key_points": ["главная ось", "поперечная ось", "justify-content", "align-items", "flex-direction"],
        "difficulty": "junior",
        "direction": "frontend",
        "topic": "css"
    },
    "js_async": {
        "id": "js_async",
        "question_text": "Как работает асинхронность в JavaScript? Что такое Event Loop?",
        "canonical_answer": "JS однопоточный, асинхронность через Event Loop. Call Stack — синхронные вызовы. Web APIs — таймеры, fetch. Callback Queue — коллбэки готовые к выполнению. Event Loop берёт из очереди когда стек пуст. Microtask Queue (промисы) имеет приоритет над макротасками.",
        "key_points": ["однопоточность", "Event Loop", "Call Stack", "Callback Queue", "Microtask"],
        "difficulty": "middle",
        "direction": "frontend",
        "topic": "javascript"
    },
    
    # ==================== ML ====================
    "ml_regularization": {
        "id": "ml_regularization",
        "question_text": "Что такое регуляризация в машинном обучении? Зачем она нужна?",
        "canonical_answer": "Регуляризация — метод предотвращения переобучения путём добавления штрафа к loss функции. L1 (Lasso) — сумма модулей весов, даёт разреженные решения. L2 (Ridge) — сумма квадратов весов, уменьшает веса плавно. Dropout в нейросетях — случайное отключение нейронов.",
        "key_points": ["переобучение", "L1/Lasso", "L2/Ridge", "штраф", "dropout"],
        "difficulty": "junior",
        "direction": "ML",
        "topic": "ml_basics"
    },
    "ml_overfitting": {
        "id": "ml_overfitting",
        "question_text": "Что такое переобучение (overfitting)? Как его обнаружить и предотвратить?",
        "canonical_answer": "Переобучение — модель запоминает шум в данных вместо паттернов. Признак: низкая ошибка на train, высокая на validation. Методы: больше данных, регуляризация, dropout, early stopping, cross-validation, data augmentation, уменьшение сложности модели.",
        "key_points": ["train vs validation gap", "регуляризация", "dropout", "early stopping", "cross-validation"],
        "difficulty": "junior",
        "direction": "ML",
        "topic": "ml_basics"
    },
    "ml_metrics": {
        "id": "ml_metrics",
        "question_text": "Какие метрики качества классификации вы знаете? Когда какую использовать?",
        "canonical_answer": "Accuracy — доля правильных. Precision — точность положительных. Recall — полнота, сколько нашли из реальных положительных. F1 — гармоническое среднее P и R. AUC-ROC — площадь под кривой. При дисбалансе классов accuracy обманчива, лучше F1 или AUC.",
        "key_points": ["accuracy", "precision", "recall", "F1", "AUC-ROC", "дисбаланс классов"],
        "difficulty": "junior",
        "direction": "ML",
        "topic": "ml_basics"
    },
    "ml_gradient_descent": {
        "id": "ml_gradient_descent",
        "question_text": "Как работает градиентный спуск? Чем отличаются SGD, Mini-batch и Batch GD?",
        "canonical_answer": "Градиентный спуск — итеративная оптимизация, движение против градиента loss функции. Batch — весь датасет (точно, медленно). SGD — один пример (шумно, быстро). Mini-batch — компромисс (батч 32-256). Важны: learning rate, momentum, adaptive methods (Adam).",
        "key_points": ["против градиента", "learning rate", "batch vs SGD", "mini-batch", "Adam"],
        "difficulty": "middle",
        "direction": "ML",
        "topic": "ml_basics"
    },
    
    # ==================== DEVOPS ====================
    "k8s_pods": {
        "id": "k8s_pods",
        "question_text": "Что такое Pod в Kubernetes? Чем отличается от контейнера?",
        "canonical_answer": "Pod — минимальная единица развертывания в K8s, может содержать 1+ контейнеров. Контейнеры в Pod делят network namespace (localhost), storage (volumes). Pod эфемерен, управляется через Deployment/ReplicaSet. Контейнер — изолированный процесс, Pod — группа связанных контейнеров.",
        "key_points": ["минимальная единица", "общий network", "volumes", "Deployment", "ReplicaSet"],
        "difficulty": "middle",
        "direction": "DevOps",
        "topic": "kubernetes"
    },
    "linux_permissions": {
        "id": "linux_permissions",
        "question_text": "Объясните систему прав доступа в Linux. Что означает chmod 755?",
        "canonical_answer": "Права: read (r=4), write (w=2), execute (x=1). Три группы: owner, group, others. chmod 755: owner=7(rwx), group=5(r-x), others=5(r-x). chmod +x — добавить execute. chown меняет владельца. Sticky bit, SUID, SGID — специальные биты.",
        "key_points": ["rwx", "owner/group/others", "числовое представление", "chmod", "chown"],
        "difficulty": "junior",
        "direction": "DevOps",
        "topic": "linux"
    },
    "ci_cd": {
        "id": "ci_cd",
        "question_text": "Что такое CI/CD? Какие этапы обычно включает пайплайн?",
        "canonical_answer": "CI (Continuous Integration) — автоматическая сборка и тестирование при каждом коммите. CD (Continuous Delivery/Deployment) — автоматический деплой. Этапы: lint, build, unit tests, integration tests, security scan, deploy to staging, deploy to production. Инструменты: GitLab CI, Jenkins, GitHub Actions.",
        "key_points": ["CI - сборка и тесты", "CD - деплой", "lint", "build", "tests", "deploy"],
        "difficulty": "junior",
        "direction": "DevOps",
        "topic": "cicd"
    },
    
    # ==================== DATA ====================
    "sql_window": {
        "id": "sql_window",
        "question_text": "Что такое оконные функции (Window Functions) в SQL? Приведите примеры.",
        "canonical_answer": "Оконные функции — вычисления над набором строк, связанных с текущей строкой. OVER() определяет окно. PARTITION BY — группировка. ORDER BY — сортировка в окне. Примеры: ROW_NUMBER(), RANK(), LAG(), LEAD(), SUM() OVER(). Не уменьшают количество строк как GROUP BY.",
        "key_points": ["OVER()", "PARTITION BY", "ROW_NUMBER", "RANK", "LAG/LEAD", "не группируют"],
        "difficulty": "middle",
        "direction": "Data",
        "topic": "sql"
    },
    "etl_best_practices": {
        "id": "etl_best_practices",
        "question_text": "Что такое ETL? Какие best practices вы знаете для построения ETL пайплайнов?",
        "canonical_answer": "ETL: Extract (извлечение), Transform (преобразование), Load (загрузка). Best practices: идемпотентность (можно перезапустить), инкрементальная загрузка, логирование и мониторинг, data quality checks, версионирование схем, партиционирование, backfill strategy.",
        "key_points": ["Extract/Transform/Load", "идемпотентность", "инкрементальная загрузка", "data quality", "партиционирование"],
        "difficulty": "junior",
        "direction": "Data",
        "topic": "etl"
    }
}


def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific question by ID."""
    return THEORY_QUESTIONS.get(question_id)


def get_questions_by_direction(direction: str) -> List[Dict[str, Any]]:
    """Get all questions for a direction (including 'any')."""
    return [
        q for q in THEORY_QUESTIONS.values()
        if q["direction"].lower() == direction.lower() or q["direction"] == "any"
    ]


def get_questions_by_topic(topic: str) -> List[Dict[str, Any]]:
    """Get all questions for a topic."""
    return [
        q for q in THEORY_QUESTIONS.values()
        if q["topic"].lower() == topic.lower()
    ]


def get_questions_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Get all questions for a difficulty level."""
    return [
        q for q in THEORY_QUESTIONS.values()
        if q["difficulty"].lower() == difficulty.lower()
    ]


def select_theory_questions(
    direction: str,
    difficulty: str,
    count: int = 3,
    exclude_ids: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Select theory questions for an interview.
    
    Args:
        direction: Interview direction (backend, frontend, ml, etc.)
        difficulty: Difficulty level
        count: Number of questions to select
        exclude_ids: IDs to exclude (already asked)
        
    Returns:
        List of selected questions
    """
    if exclude_ids is None:
        exclude_ids = []
    
    # Get questions matching direction
    candidates = get_questions_by_direction(direction)
    
    # Filter by difficulty (allow adjacent difficulties)
    difficulty_map = {
        "intern": ["junior"],
        "junior": ["junior"],
        "junior+": ["junior", "middle"],
        "middle": ["junior", "middle"],
        "middle+": ["middle", "senior"],
        "senior": ["middle", "senior"]
    }
    allowed_difficulties = difficulty_map.get(difficulty.lower(), ["junior", "middle"])
    candidates = [q for q in candidates if q["difficulty"] in allowed_difficulties]
    
    # Exclude already asked
    candidates = [q for q in candidates if q["id"] not in exclude_ids]
    
    # Select random subset
    if len(candidates) <= count:
        return candidates
    
    return random.sample(candidates, count)


def get_all_questions() -> List[Dict[str, Any]]:
    """Get all available theory questions."""
    return list(THEORY_QUESTIONS.values())



# пидормот
