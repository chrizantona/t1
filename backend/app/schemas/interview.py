"""
Pydantic schemas for interview API.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Interview schemas
class InterviewCreate(BaseModel):
    """Create new interview."""
    candidate_name: Optional[str] = None
    candidate_email: Optional[EmailStr] = None
    selected_level: str  # junior/middle/senior
    direction: str  # backend/frontend/algorithms
    cv_text: Optional[str] = None


class InterviewResponse(BaseModel):
    """Interview response."""
    id: int
    candidate_name: Optional[str]
    selected_level: str
    direction: str
    status: str
    overall_grade: Optional[str]
    overall_score: Optional[float]
    trust_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# CV Analysis schemas
class CVAnalysisRequest(BaseModel):
    """Request to analyze CV."""
    cv_text: str


class CVAnalysisResponse(BaseModel):
    """
    🔥 Enhanced CV analysis result.
    Includes full candidate assessment with strengths, weaknesses, and interview focus.
    """
    suggested_level: str
    suggested_direction: str
    years_of_experience: Optional[float] = None
    key_technologies: List[str] = []
    reasoning: str
    
    # 🆕 Enhanced analysis fields
    confidence: Optional[int] = None  # 0-100 confidence score
    all_tracks: List[str] = []  # All detected tracks
    strengths: List[str] = []  # Key strengths
    weaknesses: List[str] = []  # Areas to improve
    risk_factors: List[str] = []  # Red flags
    interview_focus: List[str] = []  # What to check on interview


# Task schemas
class TestCase(BaseModel):
    """Test case for task."""
    input: Any
    expected_output: Any
    description: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response."""
    id: int
    title: str
    description: str
    difficulty: str
    category: str
    visible_tests: List[Dict[str, Any]]
    max_score: float
    actual_score: Optional[float] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Submission schemas
class SubmissionCreate(BaseModel):
    """Create code submission."""
    task_id: int
    code: str
    language: str


class TestDetailResponse(BaseModel):
    """Single test result detail."""
    index: int
    input: Any
    expected: Any
    actual: Optional[Any] = None
    passed: bool
    error: Optional[str] = None
    description: Optional[str] = None


class SubmissionResponse(BaseModel):
    """Submission result."""
    id: int
    passed_visible: int
    total_visible: int
    passed_hidden: int
    total_hidden: int
    execution_time_ms: Optional[float]
    error_message: Optional[str]
    ai_likeness_score: Optional[float]
    visible_test_details: Optional[List[TestDetailResponse]] = None
    
    class Config:
        from_attributes = True


# Chat schemas
class ChatMessageCreate(BaseModel):
    """Create chat message."""
    interview_id: int
    content: str
    task_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Hint schemas
class HintRequest(BaseModel):
    """Request hint."""
    task_id: int
    hint_level: str  # light/medium/heavy
    current_code: Optional[str] = None


class HintResponse(BaseModel):
    """Hint response."""
    hint_content: str
    score_penalty: float
    new_max_score: float


# Anti-cheat schemas
class AntiCheatEventCreate(BaseModel):
    """Report anti-cheat event."""
    interview_id: int
    event_type: str
    severity: str
    details: Optional[Dict[str, Any]] = None


# Skill assessment schemas
class SkillScore(BaseModel):
    """Single skill score with comment."""
    score: float
    comment: str


class SkillAssessmentResponse(BaseModel):
    """Skill assessment with radar data."""
    algorithms: SkillScore
    architecture: SkillScore
    clean_code: SkillScore
    debugging: SkillScore
    communication: SkillScore
    next_grade_tips: List[str]


# Final report schemas
class FinalReportResponse(BaseModel):
    """Complete final report."""
    interview: InterviewResponse
    tasks: List[TaskResponse]
    skill_assessment: SkillAssessmentResponse
    total_hints_used: int
    total_submissions: int
    average_task_time: Optional[float] = None


# ============ New Interview Flow Schemas ============

class InterviewResponseV2(BaseModel):
    """Extended interview response with stage info."""
    id: int
    candidate_name: Optional[str]
    selected_level: str
    direction: str
    status: str
    current_stage: str  # coding/theory/completed
    overall_grade: Optional[str]
    overall_score: Optional[float]
    trust_score: Optional[float]
    confidence_score: Optional[float]
    code_quality_score: Optional[float]
    problem_solving_score: Optional[float]
    code_explanation_score: Optional[float]
    theory_knowledge_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskResponseV2(BaseModel):
    """Extended task response with order info."""
    id: int
    task_order: int
    title: str
    description: str
    difficulty: str
    category: str
    visible_tests: List[Dict[str, Any]]
    max_score: float
    actual_score: Optional[float] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AllTasksResponse(BaseModel):
    """Response with all 3 tasks for the interview."""
    interview_id: int
    current_stage: str
    tasks: List[TaskResponseV2]


class StageTransitionRequest(BaseModel):
    """Request to move to next stage."""
    interview_id: int


class StageTransitionResponse(BaseModel):
    """Response after stage transition."""
    interview_id: int
    new_stage: str
    message: str


# Theory Question Schemas
class TheoryQuestionResponse(BaseModel):
    """Theory question for candidate."""
    id: int
    question_order: int
    question_type: str  # solution_algorithm, solution_complexity, theory
    question_text: str
    related_task_id: Optional[int] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    total_answered: int
    max_questions: int
    
    class Config:
        from_attributes = True


class TheoryAnswerSubmit(BaseModel):
    """Submit answer to theory question."""
    answer_id: int
    answer_text: str


class TheoryAnswerEvaluation(BaseModel):
    """Evaluation of theory answer."""
    score: float
    feedback: str
    correctness: Optional[float] = None
    completeness: Optional[float] = None
    evaluation: Dict[str, Any]


class TheoryAnswerResponse(BaseModel):
    """Full theory answer with evaluation."""
    id: int
    question_order: int
    question_type: str
    question_text: str
    candidate_answer: Optional[str]
    score: Optional[float]
    status: str
    evaluation_details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class InterviewProgressResponse(BaseModel):
    """Current interview progress."""
    interview_id: int
    current_stage: str
    tasks_completed: int
    tasks_total: int
    questions_answered: int
    questions_max: int
    confidence_score: float
    can_proceed_to_theory: bool


class FinalScoresResponse(BaseModel):
    """Final interview scores."""
    scores: Dict[str, float]
    overall_score: float
    suggested_grade: str
    grade_confidence: Optional[float] = None
    claimed_vs_actual: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    summary: str

