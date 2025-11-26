"""
User models for authentication and roles.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.db import Base


class UserRole(str, enum.Enum):
    CANDIDATE = "candidate"
    ADMIN = "admin"


class User(Base):
    """User account with role."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="candidate")  # candidate | admin
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    candidate_profile = relationship("CandidateUserProfile", back_populates="user", uselist=False)
    admin_profile = relationship("AdminUserProfile", back_populates="user", uselist=False)


class CandidateUserProfile(Base):
    """Extended profile for candidates."""
    __tablename__ = "candidate_user_profiles"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    resume_text = Column(Text, nullable=True)
    resume_uploaded_at = Column(DateTime(timezone=True), nullable=True)
    telegram_handle = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    user = relationship("User", back_populates="candidate_profile")


class AdminUserProfile(Base):
    """Extended profile for admins/recruiters."""
    __tablename__ = "admin_user_profiles"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    company_name = Column(String, nullable=True)
    position = Column(String, nullable=True)
    
    user = relationship("User", back_populates="admin_profile")

