"""
Tech questions models for LLM-based evaluation.
"""
from sqlalchemy import Column, Integer, String, Text, ARRAY, TIMESTAMP, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.db import Base


class QuestionCategory(str, enum.Enum):
    """Question category enum."""
    algorithms = "algorithms"
    frontend = "frontend"
    backend = "backend"
    data_science = "data-science"


class QuestionDifficulty(str, enum.Enum):
    """Question difficulty enum."""
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionPanelType(str, enum.Enum):
    """Panel type for frontend rendering."""
    code_python = "code_python"
    code_frontend = "code_frontend"
    code_backend = "code_backend"
    code_ds = "code_ds"
    text_only = "text_only"


class QuestionEvalMode(str, enum.Enum):
    """Evaluation mode for LLM."""
    llm_code = "llm_code"
    llm_theory = "llm_theory"


class TechQuestion(Base):
    """Tech question model."""
    __tablename__ = "tech_questions"

    id = Column(Integer, primary_key=True)
    category = Column(SQLEnum(QuestionCategory), nullable=False)
    difficulty = Column(SQLEnum(QuestionDifficulty), nullable=False)
    question_text = Column(Text, nullable=False)
    
    panel_type = Column(SQLEnum(QuestionPanelType), nullable=False)
    eval_mode = Column(SQLEnum(QuestionEvalMode), nullable=False)
    
    language_hint = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), default=[])
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

# пидормот
