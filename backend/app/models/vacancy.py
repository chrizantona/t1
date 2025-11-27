"""
Database models for Vacancy system.
Vacancy is the CENTER of the platform - everything revolves around it.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.db import Base


class Vacancy(Base):
    """
    Vacancy - центр платформы.
    Кандидат выбирает вакансию, и все задачи/метрики строятся вокруг неё.
    """
    __tablename__ = "vacancies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    title = Column(String, nullable=False)  # "ML Engineer Junior"
    description = Column(Text, nullable=True)
    company = Column(String, nullable=True)  # Optional company name
    
    # Direction and grade
    direction = Column(String, nullable=False)  # ML, Backend, Frontend, DevOps, QA, Data
    grade_required = Column(String, nullable=False)  # junior, middle, senior
    
    # Task slots - JSON arrays of task IDs
    algo_slots = Column(JSON, default=list)  # ["two_sum", "binary_search", ...]
    practice_slots = Column(JSON, default=list)  # Practice task IDs
    theory_question_ids = Column(JSON, default=list)  # Theory question IDs
    
    # Scoring weights (how much each block contributes to final score)
    scoring_weights = Column(JSON, default=lambda: {
        "algo": 0.3,
        "practice": 0.25,
        "theory": 0.2,
        "soft": 0.1,
        "skills_match": 0.15
    })
    
    # Decision thresholds
    decision_thresholds = Column(JSON, default=lambda: {
        "hire": 75,      # >= 75 = hire
        "consider": 50   # >= 50 but < 75 = consider
    })
    
    # Critical skills - IDs of skills without which auto-reject
    critical_skills = Column(JSON, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    skills = relationship("VacancySkill", back_populates="vacancy", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="vacancy")


class VacancySkill(Base):
    """
    Skill requirement for a vacancy.
    Each skill has required level and weight for scoring.
    """
    __tablename__ = "vacancy_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=False)
    
    # Skill identification
    skill_id = Column(String, nullable=False)  # "python", "ml_basics", "docker", etc.
    skill_name = Column(String, nullable=False)  # Human-readable name
    
    # Requirements
    required_level = Column(Integer, default=1)  # 0-3: 0=nice-to-have, 3=expert required
    weight = Column(Float, default=1.0)  # Weight in final scoring
    
    # Skill type determines what kind of questions/tasks test this skill
    skill_type = Column(String, default="theory")  # algo, practice, theory, system_design
    
    # Is this skill critical (auto-reject if failed)?
    is_critical = Column(Boolean, default=False)
    
    # Relationship
    vacancy = relationship("Vacancy", back_populates="skills")


class CandidateProfile(Base):
    """
    Candidate profile built from resume analysis.
    Stores extracted skills and estimated grade.
    """
    __tablename__ = "candidate_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False, unique=True)
    
    # Basic info extracted from resume
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Resume data
    resume_raw = Column(Text, nullable=True)  # Original text from PDF
    resume_summary = Column(Text, nullable=True)  # LLM-generated summary
    
    # Estimated grade from resume
    initial_grade = Column(String, nullable=True)  # junior, middle, senior
    years_of_experience = Column(Float, nullable=True)
    
    # Extracted skills - JSON array of skill snapshots
    skills = Column(JSON, default=list)  # [{skill_id, level_from_resume, ...}]
    
    # Tech stack
    tech_stack = Column(JSON, default=list)  # ["Python", "Django", "PostgreSQL", ...]
    
    # Domains/industries
    domains = Column(JSON, default=list)  # ["fintech", "e-commerce", ...]
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    interview = relationship("Interview", back_populates="candidate_profile")


class CandidateSkillSnapshot(Base):
    """
    Snapshot of candidate's skill assessment during interview.
    Tracks skill level from different sources: resume, practice, theory.
    """
    __tablename__ = "candidate_skill_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    
    # Skill identification
    skill_id = Column(String, nullable=False)  # Matches VacancySkill.skill_id
    
    # Levels from different sources (0-3 scale)
    level_from_resume = Column(Float, nullable=True)
    level_from_practice = Column(Float, nullable=True)
    level_from_theory = Column(Float, nullable=True)
    
    # Final computed level (weighted average)
    final_level = Column(Float, nullable=True)
    
    # Notes from evaluation
    notes = Column(Text, nullable=True)


