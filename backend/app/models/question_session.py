"""
Models for the questions block (Part 2 of interview).
20 random questions matching candidate's vacancy/stack.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.db import Base


class QuestionBlock(Base):
    """
    A block of 20 questions for Part 2 of the interview.
    Questions are selected based on vacancy requirements.
    """
    __tablename__ = "question_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False, unique=True)
    
    # Configuration
    total_questions = Column(Integer, default=20)
    current_question_index = Column(Integer, default=0)  # 0-based, which question is active
    
    # Categories selected for this block (based on vacancy)
    selected_categories = Column(JSON, default=list)  # e.g. ["python", "fastapi", "sql"]
    difficulty_distribution = Column(JSON, default=dict)  # e.g. {"easy": 8, "medium": 8, "hard": 4}
    
    # Status
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    
    # Statistics
    total_answered = Column(Integer, default=0)
    total_skipped = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)  # Score >= 70
    average_score = Column(Float, nullable=True)
    average_response_time = Column(Float, nullable=True)  # In seconds
    
    # Score breakdown by category
    category_scores = Column(JSON, default=dict)  # {"python": 85, "sql": 72, ...}
    difficulty_scores = Column(JSON, default=dict)  # {"easy": 90, "medium": 70, "hard": 50}
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    interview = relationship("Interview", back_populates="question_block")
    question_answers = relationship("QuestionAnswer", back_populates="question_block", 
                                    cascade="all, delete-orphan", order_by="QuestionAnswer.question_order")


class QuestionAnswer(Base):
    """
    Individual question and answer in the questions block.
    Tracks timing, score, and whether it was skipped.
    """
    __tablename__ = "question_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_block_id = Column(Integer, ForeignKey("question_blocks.id"), nullable=False)
    
    # Question data (from questions.json)
    source_question_id = Column(Integer, nullable=False)  # ID from questions.json
    question_order = Column(Integer, nullable=False)  # 1-20, order in this block
    
    # Question metadata
    category = Column(String, nullable=False)  # python, sql, etc.
    difficulty = Column(String, nullable=False)  # easy, medium, hard
    question_type = Column(String, nullable=False)  # coding, theory
    question_text = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=True)  # Expected answer if available
    
    # Candidate's answer
    candidate_answer = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending, answered, skipped
    
    # Timing
    shown_at = Column(DateTime(timezone=True), nullable=True)  # When question was shown
    answered_at = Column(DateTime(timezone=True), nullable=True)  # When answer was submitted
    response_time_seconds = Column(Float, nullable=True)  # Time taken to answer
    
    # Evaluation
    score = Column(Float, nullable=True)  # 0-100
    is_correct = Column(Boolean, nullable=True)  # True if score >= 70
    evaluation_details = Column(JSON, nullable=True)  # Full LLM evaluation
    feedback = Column(Text, nullable=True)  # Short feedback for candidate
    
    # Retry tracking
    attempt_number = Column(Integer, default=1)  # Current attempt (1, 2, 3...)
    score_multiplier = Column(Float, default=1.0)  # 1.0, 0.5, 0.25, etc.
    
    # Difficulty adjustment signal
    suggested_next_difficulty = Column(String, nullable=True)  # For adaptive questioning
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question_block = relationship("QuestionBlock", back_populates="question_answers")

