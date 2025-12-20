"""
Pydantic schemas for Claude prompts responses.
"""
from pydantic import BaseModel
from typing import Optional
from enum import Enum


# Enums
class Track(str, Enum):
    backend = "backend"
    frontend = "frontend"
    fullstack = "fullstack"
    data = "data"
    devops = "devops"
    mobile = "mobile"
    ml = "ml"
    other = "other"


class Grade(str, Enum):
    junior = "junior"
    junior_plus = "junior_plus"
    middle = "middle"
    middle_plus = "middle_plus"
    senior = "senior"


class Difficulty(str, Enum):
    easy = "easy"
    middle = "middle"
    hard = "hard"


class HireRecommendation(str, Enum):
    strong_yes = "strong_yes"
    yes = "yes"
    borderline = "borderline"
    no = "no"


# 1. Resume Analyzer
class ResumeAnalysisResult(BaseModel):
    years_of_experience: float
    tracks: list[str]
    resume_self_grade: Optional[str] = None
    tech_stack: list[str]
    domains: list[str]
    summary: str


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str


# 2. Vacancy Analyzer
class VacancyAnalysisResult(BaseModel):
    role_title: str
    expected_grade: str
    tracks: list[str]
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    domains: list[str]
    soft_requirements: list[str]
    focus_areas: list[str]


class VacancyAnalyzeRequest(BaseModel):
    vacancy_text: str


# 2.3. Resume-Vacancy Matcher
class MatchResult(BaseModel):
    match_score: int
    match_summary: str
    strong_fit: list[str]
    gaps: list[str]
    recommended_topics_for_tasks: list[str]
    recommended_difficulty: str


class MatchRequest(BaseModel):
    resume_parsed: dict
    vacancy_parsed: dict
    interview_summary: Optional[str] = None


# 3. Task Generator
class TaskExample(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None


class HiddenTest(BaseModel):
    input: str
    output: str
    tags: list[str] = []


class LLMRubric(BaseModel):
    should_use_tests: bool
    key_requirements: list[str]
    common_mistakes: list[str]


class GeneratedTask(BaseModel):
    task_type: str
    track: str
    difficulty: str
    title: str
    description: str
    input_format: str
    output_format: str
    constraints: str
    visible_examples: list[TaskExample]
    hidden_tests: list[HiddenTest]
    llm_rubric: LLMRubric


class TaskGenerateRequest(BaseModel):
    track: str
    difficulty: str
    mode: str  # coding|theory
    target_skills: list[str]
    vacancy_summary: Optional[str] = None


# 4. Hint Generator
class HintsResult(BaseModel):
    soft_hint: str
    medium_hint: str
    hard_hint: str


class HintRequest(BaseModel):
    task_description: str
    candidate_code: Optional[str] = None
    test_results: str
    grade: str
    difficulty: str


# 5. Live Assistant
class LiveAssistantRequest(BaseModel):
    mode: str  # reactive|proactive
    task_description: str
    candidate_code: Optional[str] = None
    test_results: str
    user_message: Optional[str] = None
    grade: str
    difficulty: str


class LiveAssistantResponse(BaseModel):
    message: str


# 6. Solution Reviewer
class SolutionReviewResult(BaseModel):
    correctness_score: int
    robustness_score: int
    code_quality_score: int
    algo_complexity_level: str
    short_verdict: str
    strengths: list[str]
    weaknesses: list[str]
    suggested_improvements: list[str]


class SolutionReviewRequest(BaseModel):
    task_description: str
    candidate_code: str
    test_results: str
    grade: str
    difficulty: str


# 7. AI Code Detector
class AIDetectionResult(BaseModel):
    ai_likeness_score: int
    explanation: str
    suspicious_signals: list[str]


class AIDetectionRequest(BaseModel):
    candidate_code: str


# 8. Final Report
class FinalReportResult(BaseModel):
    final_grade: str
    final_track: str
    hire_recommendation: str
    hire_comment: str
    report_markdown: str
    key_strengths: list[str]
    key_risks: list[str]
    suggested_next_steps: list[str]


class FinalReportRequest(BaseModel):
    resume_parsed: dict
    vacancy_parsed: dict
    match_result: dict
    interview_metrics: dict
    trust_and_ai: dict
    solution_review_summary: dict

# пидормот
