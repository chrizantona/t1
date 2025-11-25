"""
Pydantic schemas for tech questions.
"""
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class QuestionCategory(str, Enum):
    """Question category."""
    algorithms = "algorithms"
    frontend = "frontend"
    backend = "backend"
    data_science = "data-science"


class QuestionDifficulty(str, Enum):
    """Question difficulty."""
    easy = "easy"
    medium = "medium"
    hard = "hard"


class PanelType(str, Enum):
    """Panel type for frontend."""
    code_python = "code_python"
    code_frontend = "code_frontend"
    code_backend = "code_backend"
    code_ds = "code_ds"
    text_only = "text_only"


class QuestionImport(BaseModel):
    """Schema for importing questions from JSON."""
    id: int
    category: QuestionCategory
    difficulty: QuestionDifficulty
    question: str


class QuestionOut(BaseModel):
    """Schema for question response."""
    id: int
    category: str
    difficulty: str
    question_text: str
    panel_type: PanelType
    language_hint: Optional[str] = None

    class Config:
        from_attributes = True


class QuestionAnswerIn(BaseModel):
    """Schema for submitting answer."""
    question_id: int
    answer_code: Optional[str] = None
    answer_text: Optional[str] = None


class QuestionAnswerEval(BaseModel):
    """Schema for evaluation result."""
    score: int  # 0-100
    passed: bool
    short_feedback: str
    mistakes: list[str] = []
