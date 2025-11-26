"""
Vacancy API endpoints.
Vacancies are the CENTER of the platform.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..core.db import get_db
from ..models.vacancy import Vacancy, VacancySkill
from ..services.vacancy_pool import (
    get_all_vacancies,
    get_vacancy_by_id,
    get_vacancies_by_direction,
    get_vacancies_by_grade,
    VACANCY_POOL
)


router = APIRouter()


# ============ Schemas ============

class VacancySkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    required_level: int
    weight: float
    skill_type: str
    is_critical: bool
    
    class Config:
        from_attributes = True


class VacancyResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    company: Optional[str] = None
    direction: str
    grade_required: str
    skills: List[VacancySkillResponse]
    algo_slots: List[str]
    practice_slots: List[str]
    theory_question_ids: List[str]
    scoring_weights: dict
    decision_thresholds: dict
    critical_skills: List[str]
    
    class Config:
        from_attributes = True


class VacancyListItem(BaseModel):
    id: str
    title: str
    company: Optional[str] = None
    direction: str
    grade_required: str
    skills_count: int
    
    class Config:
        from_attributes = True


# ============ Endpoints ============

@router.get("/", response_model=List[VacancyListItem])
async def list_vacancies(
    direction: Optional[str] = None,
    grade: Optional[str] = None
):
    """
    List all available vacancies.
    Can filter by direction and/or grade.
    """
    vacancies = get_all_vacancies()
    
    if direction:
        vacancies = [v for v in vacancies if v["direction"].lower() == direction.lower()]
    
    if grade:
        vacancies = [v for v in vacancies if v["grade_required"].lower() == grade.lower()]
    
    return [
        VacancyListItem(
            id=v["id"],
            title=v["title"],
            company=v.get("company"),
            direction=v["direction"],
            grade_required=v["grade_required"],
            skills_count=len(v.get("skills", []))
        )
        for v in vacancies
    ]


@router.get("/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(vacancy_id: str):
    """
    Get detailed vacancy information.
    """
    vacancy = get_vacancy_by_id(vacancy_id)
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    # Convert skills to response format
    skills = [
        VacancySkillResponse(
            skill_id=s["skill_id"],
            skill_name=s["skill_name"],
            required_level=s["required_level"],
            weight=s["weight"],
            skill_type=s["skill_type"],
            is_critical=s.get("is_critical", False)
        )
        for s in vacancy.get("skills", [])
    ]
    
    return VacancyResponse(
        id=vacancy["id"],
        title=vacancy["title"],
        description=vacancy.get("description"),
        company=vacancy.get("company"),
        direction=vacancy["direction"],
        grade_required=vacancy["grade_required"],
        skills=skills,
        algo_slots=vacancy.get("algo_slots", []),
        practice_slots=vacancy.get("practice_slots", []),
        theory_question_ids=vacancy.get("theory_question_ids", []),
        scoring_weights=vacancy.get("scoring_weights", {}),
        decision_thresholds=vacancy.get("decision_thresholds", {}),
        critical_skills=vacancy.get("critical_skills", [])
    )


@router.get("/direction/{direction}", response_model=List[VacancyListItem])
async def get_vacancies_for_direction(direction: str):
    """
    Get all vacancies for a specific direction.
    """
    vacancies = get_vacancies_by_direction(direction)
    
    return [
        VacancyListItem(
            id=v["id"],
            title=v["title"],
            company=v.get("company"),
            direction=v["direction"],
            grade_required=v["grade_required"],
            skills_count=len(v.get("skills", []))
        )
        for v in vacancies
    ]


@router.get("/skills/{vacancy_id}", response_model=List[VacancySkillResponse])
async def get_vacancy_skills(vacancy_id: str):
    """
    Get required skills for a vacancy.
    """
    vacancy = get_vacancy_by_id(vacancy_id)
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return [
        VacancySkillResponse(
            skill_id=s["skill_id"],
            skill_name=s["skill_name"],
            required_level=s["required_level"],
            weight=s["weight"],
            skill_type=s["skill_type"],
            is_critical=s.get("is_critical", False)
        )
        for s in vacancy.get("skills", [])
    ]

