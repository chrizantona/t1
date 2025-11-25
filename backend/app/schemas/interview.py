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
    """CV analysis result."""
    suggested_level: str
    suggested_direction: str
    years_of_experience: Optional[float]
    key_technologies: List[str]
    reasoning: str


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

