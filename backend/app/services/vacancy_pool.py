"""
Predefined vacancies for demo.
Each vacancy has skills, task slots, and scoring weights.
"""
from typing import Dict, List, Any

# Predefined vacancies for demo
VACANCY_POOL: Dict[str, Dict[str, Any]] = {
    "ml_engineer_junior": {
        "title": "ML Engineer Junior",
        "description": "Разработка и внедрение ML моделей в production. Работа с данными, feature engineering, обучение моделей.",
        "company": "T1 Digital",
        "direction": "ML",
        "grade_required": "junior",
        "skills": [
            {"skill_id": "python", "skill_name": "Python", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "ml_basics", "skill_name": "ML Basics (sklearn, numpy, pandas)", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "algorithms", "skill_name": "Алгоритмы и структуры данных", "required_level": 1, "weight": 1.0, "skill_type": "algo", "is_critical": False},
            {"skill_id": "sql", "skill_name": "SQL", "required_level": 1, "weight": 0.8, "skill_type": "theory", "is_critical": False},
            {"skill_id": "git", "skill_name": "Git", "required_level": 1, "weight": 0.5, "skill_type": "theory", "is_critical": False},
            {"skill_id": "docker", "skill_name": "Docker", "required_level": 1, "weight": 0.5, "skill_type": "theory", "is_critical": False},
        ],
        "algo_slots": ["two_sum", "max_subarray", "binary_search"],
        "practice_slots": ["ml_classifier", "data_preprocessing"],
        "theory_question_ids": ["ml_regularization", "ml_overfitting", "ml_metrics"],
        "scoring_weights": {
            "algo": 0.25,
            "practice": 0.35,
            "theory": 0.2,
            "soft": 0.1,
            "skills_match": 0.1
        },
        "decision_thresholds": {
            "hire": 70,
            "consider": 50
        },
        "critical_skills": ["python", "ml_basics"]
    },
    
    "backend_developer_middle": {
        "title": "Backend Developer Middle",
        "description": "Разработка высоконагруженных backend сервисов. Python/Go, PostgreSQL, Redis, Kafka.",
        "company": "T1 Digital",
        "direction": "Backend",
        "grade_required": "middle",
        "skills": [
            {"skill_id": "python", "skill_name": "Python", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "algorithms", "skill_name": "Алгоритмы и структуры данных", "required_level": 2, "weight": 1.2, "skill_type": "algo", "is_critical": True},
            {"skill_id": "sql", "skill_name": "SQL и PostgreSQL", "required_level": 2, "weight": 1.3, "skill_type": "theory", "is_critical": True},
            {"skill_id": "api_design", "skill_name": "REST API Design", "required_level": 2, "weight": 1.0, "skill_type": "theory", "is_critical": False},
            {"skill_id": "docker", "skill_name": "Docker & Containers", "required_level": 2, "weight": 0.8, "skill_type": "theory", "is_critical": False},
            {"skill_id": "redis", "skill_name": "Redis", "required_level": 1, "weight": 0.7, "skill_type": "theory", "is_critical": False},
            {"skill_id": "kafka", "skill_name": "Kafka", "required_level": 1, "weight": 0.6, "skill_type": "theory", "is_critical": False},
            {"skill_id": "git", "skill_name": "Git", "required_level": 2, "weight": 0.5, "skill_type": "theory", "is_critical": False},
        ],
        "algo_slots": ["two_sum", "max_subarray", "binary_search"],
        "practice_slots": ["rest_api", "database_query"],
        "theory_question_ids": ["http_methods", "sql_joins", "docker_basics", "redis_cache"],
        "scoring_weights": {
            "algo": 0.3,
            "practice": 0.3,
            "theory": 0.2,
            "soft": 0.1,
            "skills_match": 0.1
        },
        "decision_thresholds": {
            "hire": 75,
            "consider": 55
        },
        "critical_skills": ["python", "algorithms", "sql"]
    },
    
    "frontend_developer_junior": {
        "title": "Frontend Developer Junior",
        "description": "Разработка пользовательских интерфейсов на React. TypeScript, CSS, responsive design.",
        "company": "T1 Digital",
        "direction": "Frontend",
        "grade_required": "junior",
        "skills": [
            {"skill_id": "javascript", "skill_name": "JavaScript/TypeScript", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "react", "skill_name": "React", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "algorithms", "skill_name": "Алгоритмы и структуры данных", "required_level": 1, "weight": 1.0, "skill_type": "algo", "is_critical": False},
            {"skill_id": "css", "skill_name": "CSS/SCSS", "required_level": 2, "weight": 1.0, "skill_type": "theory", "is_critical": False},
            {"skill_id": "html", "skill_name": "HTML5", "required_level": 2, "weight": 0.8, "skill_type": "theory", "is_critical": False},
            {"skill_id": "git", "skill_name": "Git", "required_level": 1, "weight": 0.5, "skill_type": "theory", "is_critical": False},
        ],
        "algo_slots": ["two_sum", "palindrome", "valid_parentheses"],
        "practice_slots": ["react_component", "css_layout"],
        "theory_question_ids": ["react_hooks", "css_flexbox", "js_async"],
        "scoring_weights": {
            "algo": 0.25,
            "practice": 0.35,
            "theory": 0.2,
            "soft": 0.1,
            "skills_match": 0.1
        },
        "decision_thresholds": {
            "hire": 70,
            "consider": 50
        },
        "critical_skills": ["javascript", "react"]
    },
    
    "devops_engineer_middle": {
        "title": "DevOps Engineer Middle",
        "description": "Построение и поддержка CI/CD пайплайнов. Kubernetes, Docker, Terraform, мониторинг.",
        "company": "T1 Digital",
        "direction": "DevOps",
        "grade_required": "middle",
        "skills": [
            {"skill_id": "linux", "skill_name": "Linux Administration", "required_level": 2, "weight": 1.5, "skill_type": "theory", "is_critical": True},
            {"skill_id": "docker", "skill_name": "Docker & Containers", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "kubernetes", "skill_name": "Kubernetes", "required_level": 2, "weight": 1.3, "skill_type": "theory", "is_critical": True},
            {"skill_id": "ci_cd", "skill_name": "CI/CD (GitLab, Jenkins)", "required_level": 2, "weight": 1.2, "skill_type": "practice", "is_critical": False},
            {"skill_id": "scripting", "skill_name": "Bash/Python scripting", "required_level": 2, "weight": 1.0, "skill_type": "algo", "is_critical": False},
            {"skill_id": "terraform", "skill_name": "Terraform/IaC", "required_level": 1, "weight": 0.8, "skill_type": "theory", "is_critical": False},
            {"skill_id": "monitoring", "skill_name": "Prometheus/Grafana", "required_level": 1, "weight": 0.7, "skill_type": "theory", "is_critical": False},
        ],
        "algo_slots": ["two_sum", "binary_search", "fibonacci"],
        "practice_slots": ["dockerfile", "bash_script"],
        "theory_question_ids": ["docker_compose", "k8s_pods", "linux_permissions"],
        "scoring_weights": {
            "algo": 0.2,
            "practice": 0.35,
            "theory": 0.25,
            "soft": 0.1,
            "skills_match": 0.1
        },
        "decision_thresholds": {
            "hire": 75,
            "consider": 55
        },
        "critical_skills": ["linux", "docker", "kubernetes"]
    },
    
    "data_engineer_junior": {
        "title": "Data Engineer Junior",
        "description": "Построение ETL пайплайнов, работа с большими данными. Python, SQL, Airflow, Spark.",
        "company": "T1 Digital",
        "direction": "Data",
        "grade_required": "junior",
        "skills": [
            {"skill_id": "python", "skill_name": "Python", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "sql", "skill_name": "SQL", "required_level": 2, "weight": 1.5, "skill_type": "practice", "is_critical": True},
            {"skill_id": "algorithms", "skill_name": "Алгоритмы и структуры данных", "required_level": 1, "weight": 1.0, "skill_type": "algo", "is_critical": False},
            {"skill_id": "etl", "skill_name": "ETL процессы", "required_level": 1, "weight": 1.0, "skill_type": "theory", "is_critical": False},
            {"skill_id": "airflow", "skill_name": "Apache Airflow", "required_level": 1, "weight": 0.8, "skill_type": "theory", "is_critical": False},
            {"skill_id": "spark", "skill_name": "Apache Spark basics", "required_level": 1, "weight": 0.7, "skill_type": "theory", "is_critical": False},
        ],
        "algo_slots": ["two_sum", "max_subarray", "contains_duplicate"],
        "practice_slots": ["sql_query", "data_transformation"],
        "theory_question_ids": ["sql_window", "etl_best_practices", "data_quality"],
        "scoring_weights": {
            "algo": 0.25,
            "practice": 0.35,
            "theory": 0.2,
            "soft": 0.1,
            "skills_match": 0.1
        },
        "decision_thresholds": {
            "hire": 70,
            "consider": 50
        },
        "critical_skills": ["python", "sql"]
    }
}


def get_all_vacancies() -> List[Dict[str, Any]]:
    """Get all predefined vacancies."""
    return [
        {"id": key, **value}
        for key, value in VACANCY_POOL.items()
    ]


def get_vacancy_by_id(vacancy_id: str) -> Dict[str, Any]:
    """Get a specific vacancy by ID."""
    if vacancy_id in VACANCY_POOL:
        return {"id": vacancy_id, **VACANCY_POOL[vacancy_id]}
    return None


def get_vacancies_by_direction(direction: str) -> List[Dict[str, Any]]:
    """Get vacancies filtered by direction."""
    return [
        {"id": key, **value}
        for key, value in VACANCY_POOL.items()
        if value["direction"].lower() == direction.lower()
    ]


def get_vacancies_by_grade(grade: str) -> List[Dict[str, Any]]:
    """Get vacancies filtered by required grade."""
    return [
        {"id": key, **value}
        for key, value in VACANCY_POOL.items()
        if value["grade_required"].lower() == grade.lower()
    ]


def add_vacancy_to_pool(vacancy: Dict[str, Any]) -> None:
    """Add a new vacancy to the pool."""
    vacancy_id = vacancy.get("id")
    if vacancy_id:
        # Remove 'id' from the dict since we use it as key
        vacancy_copy = {k: v for k, v in vacancy.items() if k != "id"}
        VACANCY_POOL[vacancy_id] = vacancy_copy


def remove_vacancy_from_pool(vacancy_id: str) -> bool:
    """Remove a vacancy from the pool."""
    if vacancy_id in VACANCY_POOL:
        del VACANCY_POOL[vacancy_id]
        return True
    return False


def update_vacancy_in_pool(vacancy_id: str, updates: Dict[str, Any]) -> bool:
    """Update a vacancy in the pool."""
    if vacancy_id in VACANCY_POOL:
        VACANCY_POOL[vacancy_id].update(updates)
        return True
    return False

