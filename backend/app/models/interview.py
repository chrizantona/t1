"""
Database models for interview system.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..core.db import Base


class Interview(Base):
    """
    Main interview session.
    Connected to a Vacancy - the center of the platform.
    """
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to vacancy (optional - can be direct interview without vacancy)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=True)
    
    # Candidate info
    candidate_name = Column(String, nullable=True)
    candidate_email = Column(String, nullable=True)
    
    # Level and direction
    suggested_level = Column(String, nullable=True)  # From CV analysis
    selected_level = Column(String, nullable=False)  # chosen by candidate: junior/middle/senior
    effective_level = Column(String, nullable=True)  # ADAPTIVE: may change during interview
    direction = Column(String, nullable=False)  # backend/frontend/algorithms/ml/devops/data
    
    # Interview stage tracking
    current_stage = Column(String, default="ALGO")  # ALGO/PRACTICE/THEORY/DONE
    
    # Status and decision
    status = Column(String, default="in_progress")  # in_progress/completed/cancelled
    decision = Column(String, nullable=True)  # hire/consider/reject
    
    # Final assessment
    overall_grade = Column(String, nullable=True)  # junior/middle/senior
    overall_score = Column(Float, nullable=True)  # 0-100
    trust_score = Column(Float, default=100.0)  # 0-100
    
    # Adaptive scoring
    confidence_score = Column(Float, default=50.0)  # 0-100, adaptive confidence
    code_quality_score = Column(Float, nullable=True)
    problem_solving_score = Column(Float, nullable=True)
    code_explanation_score = Column(Float, nullable=True)
    theory_knowledge_score = Column(Float, nullable=True)
    
    # Cheat signals aggregated (from AntiCheatEvents)
    cheat_signals = Column(JSON, default=lambda: {
        "copy_paste_count": 0,
        "devtools_opened": False,
        "focus_lost_count": 0,
        "ai_style_score": 0.0,
        "code_similarity_score": 0.0
    })
    
    # Stage results (scores per block)
    stage_results = Column(JSON, default=list)  # [{stage, taskId, rawScore, finalScore, details}]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # CV data
    cv_text = Column(Text, nullable=True)
    cv_analysis = Column(JSON, nullable=True)
    years_of_experience = Column(Float, nullable=True)  # Extracted from CV or manual input
    
    # Relationships
    vacancy = relationship("Vacancy", back_populates="interviews")
    candidate_profile = relationship("CandidateProfile", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="interview", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="interview", cascade="all, delete-orphan")
    anti_cheat_events = relationship("AntiCheatEvent", back_populates="interview", cascade="all, delete-orphan")
    skill_assessment = relationship("SkillAssessment", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    theory_answers = relationship("TheoryAnswer", back_populates="interview", cascade="all, delete-orphan")
    question_block = relationship("QuestionBlock", back_populates="interview", uselist=False, cascade="all, delete-orphan")


class Task(Base):
    """Coding task in interview."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    
    # Task order (1, 2, 3 for the three tasks)
    task_order = Column(Integer, default=1)  # 1=easy, 2=medium, 3=hard
    
    # Source question ID from questions.json
    source_question_id = Column(Integer, nullable=True)
    
    # Task details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False)  # easy/medium/hard
    category = Column(String, nullable=False)  # algorithms/data_structures/system_design
    
    # Input/Output format
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    
    # Test cases
    visible_tests = Column(JSON, nullable=False)  # List of test cases
    hidden_tests = Column(JSON, nullable=False)  # Hidden test cases
    
    # Scoring
    max_score = Column(Float, default=100.0)
    actual_score = Column(Float, nullable=True)
    
    # Status
    status = Column(String, default="active")  # active/completed/skipped
    
    # Robustness (AI Bug Hunter results)
    robustness_score = Column(Float, nullable=True)
    ai_generated_tests = Column(JSON, nullable=True)
    
    # Candidate's final code (for theory questions about solution)
    final_code = Column(Text, nullable=True)
    
    # Task generation metadata (NEW: for showing how LLM selected/generated the task)
    generation_meta = Column(JSON, nullable=True)  # {llm_model, track, difficulty, target_skills, selection_reason, ...}
    source_type = Column(String, default="from_pool")  # "from_pool" | "llm_generated"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="tasks")
    submissions = relationship("Submission", back_populates="task", cascade="all, delete-orphan")
    hints = relationship("Hint", back_populates="task", cascade="all, delete-orphan")


class Submission(Base):
    """Code submission for a task."""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Code
    code = Column(Text, nullable=False)
    language = Column(String, nullable=False)  # python/javascript/java/etc
    
    # Results
    passed_visible = Column(Integer, default=0)
    total_visible = Column(Integer, default=0)
    passed_hidden = Column(Integer, default=0)
    total_hidden = Column(Integer, default=0)
    
    # Execution details
    execution_time_ms = Column(Float, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # AI analysis
    ai_likeness_score = Column(Float, nullable=True)
    code_quality_score = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="submissions")


class ChatMessage(Base):
    """Chat message between candidate and AI interviewer."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    
    role = Column(String, nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    
    # Context
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    interview = relationship("Interview", back_populates="chat_messages")


class Hint(Base):
    """Hint requested by candidate."""
    __tablename__ = "hints"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Hint details
    hint_level = Column(String, nullable=False)  # light/medium/heavy
    hint_content = Column(Text, nullable=False)
    score_penalty = Column(Float, nullable=False)  # Percentage reduction
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="hints")


class AntiCheatEvent(Base):
    """Anti-cheat event tracking."""
    __tablename__ = "anti_cheat_events"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    
    # Event details
    event_type = Column(String, nullable=False)  # copy_paste/window_blur/devtools_open/fast_typing
    severity = Column(String, nullable=False)  # low/medium/high
    details = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    interview = relationship("Interview", back_populates="anti_cheat_events")


class SkillAssessment(Base):
    """Final skill assessment with radar chart data."""
    __tablename__ = "skill_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False, unique=True)
    
    # Skill scores (0-100)
    algorithms_score = Column(Float, nullable=True)
    architecture_score = Column(Float, nullable=True)
    clean_code_score = Column(Float, nullable=True)
    debugging_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    
    # Comments for each skill
    algorithms_comment = Column(Text, nullable=True)
    architecture_comment = Column(Text, nullable=True)
    clean_code_comment = Column(Text, nullable=True)
    debugging_comment = Column(Text, nullable=True)
    communication_comment = Column(Text, nullable=True)
    
    # Next level tips
    next_grade_tips = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    interview = relationship("Interview", back_populates="skill_assessment")


class SolutionFollowup(Base):
    """Follow-up question about candidate's solution after task completion."""
    __tablename__ = "solution_followups"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Question
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="complexity")  # complexity/algorithm/optimization/edge_cases
    
    # Answer
    candidate_answer = Column(Text, nullable=True)
    
    # Evaluation
    score = Column(Float, nullable=True)  # 0-100
    correctness = Column(Float, nullable=True)
    completeness = Column(Float, nullable=True)
    understanding = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending/answered
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    answered_at = Column(DateTime(timezone=True), nullable=True)


class TheoryAnswer(Base):
    """Theory question answer during interview."""
    __tablename__ = "theory_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    
    # Question info
    question_id = Column(Integer, nullable=True)  # ID from questions.json if exists
    question_type = Column(String, nullable=False)  # "solution_algorithm", "solution_complexity", "theory"
    question_text = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=True)  # Expected answer if available
    
    # Related task (for solution questions)
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Answer
    candidate_answer = Column(Text, nullable=True)
    
    # Evaluation
    score = Column(Float, nullable=True)  # 0-100
    correctness = Column(Float, nullable=True)
    completeness = Column(Float, nullable=True)
    evaluation_details = Column(JSON, nullable=True)  # Full LLM evaluation
    
    # Order in interview
    question_order = Column(Integer, nullable=False)
    
    # Status
    status = Column(String, default="pending")  # pending/answered/skipped
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    answered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="theory_answers")
    related_task = relationship("Task")

