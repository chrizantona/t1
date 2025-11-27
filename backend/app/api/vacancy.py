"""
Vacancy API endpoints.
Vacancies are the CENTER of the platform.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from ..core.db import get_db
from ..models.vacancy import Vacancy, VacancySkill
from ..services.vacancy_pool import (
    get_all_vacancies,
    get_vacancy_by_id,
    get_vacancies_by_direction,
    get_vacancies_by_grade,
    VACANCY_POOL,
    add_vacancy_to_pool,
    remove_vacancy_from_pool
)


router = APIRouter()


# ============ Schemas ============

class VacancySkillCreate(BaseModel):
    skill_id: str
    skill_name: str
    required_level: int = 3
    weight: float = 1.0
    skill_type: str = "technical"
    is_critical: bool = False


class VacancySkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    required_level: int
    weight: float
    skill_type: str
    is_critical: bool
    
    class Config:
        from_attributes = True


class VacancyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    company: Optional[str] = None
    direction: str  # backend, frontend, ml, data, devops
    grade_required: str  # junior, middle, senior
    skills: List[VacancySkillCreate] = []


class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    direction: Optional[str] = None
    grade_required: Optional[str] = None
    skills: Optional[List[VacancySkillCreate]] = None


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


# ============ Admin CRUD Endpoints ============

@router.post("/", response_model=VacancyResponse)
async def create_vacancy(vacancy_data: VacancyCreate):
    """
    Create a new vacancy.
    """
    vacancy_id = f"vacancy_{uuid.uuid4().hex[:8]}"
    
    # Build skills list
    skills = [
        {
            "skill_id": s.skill_id,
            "skill_name": s.skill_name,
            "required_level": s.required_level,
            "weight": s.weight,
            "skill_type": s.skill_type,
            "is_critical": s.is_critical
        }
        for s in vacancy_data.skills
    ]
    
    # Create vacancy dict
    new_vacancy = {
        "id": vacancy_id,
        "title": vacancy_data.title,
        "description": vacancy_data.description,
        "company": vacancy_data.company,
        "direction": vacancy_data.direction,
        "grade_required": vacancy_data.grade_required,
        "skills": skills,
        "algo_slots": [],
        "practice_slots": [],
        "theory_question_ids": [],
        "scoring_weights": {
            "algo": 0.4,
            "practice": 0.35,
            "theory": 0.25
        },
        "decision_thresholds": {
            "strong_yes": 85,
            "yes": 70,
            "maybe": 50,
            "no": 0
        },
        "critical_skills": [s.skill_id for s in vacancy_data.skills if s.is_critical]
    }
    
    # Add to pool
    add_vacancy_to_pool(new_vacancy)
    
    return VacancyResponse(
        id=new_vacancy["id"],
        title=new_vacancy["title"],
        description=new_vacancy.get("description"),
        company=new_vacancy.get("company"),
        direction=new_vacancy["direction"],
        grade_required=new_vacancy["grade_required"],
        skills=[VacancySkillResponse(**s) for s in skills],
        algo_slots=new_vacancy["algo_slots"],
        practice_slots=new_vacancy["practice_slots"],
        theory_question_ids=new_vacancy["theory_question_ids"],
        scoring_weights=new_vacancy["scoring_weights"],
        decision_thresholds=new_vacancy["decision_thresholds"],
        critical_skills=new_vacancy["critical_skills"]
    )


@router.put("/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(vacancy_id: str, vacancy_data: VacancyUpdate):
    """
    Update an existing vacancy.
    """
    vacancy = get_vacancy_by_id(vacancy_id)
    
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    # Update fields
    if vacancy_data.title is not None:
        vacancy["title"] = vacancy_data.title
    if vacancy_data.description is not None:
        vacancy["description"] = vacancy_data.description
    if vacancy_data.company is not None:
        vacancy["company"] = vacancy_data.company
    if vacancy_data.direction is not None:
        vacancy["direction"] = vacancy_data.direction
    if vacancy_data.grade_required is not None:
        vacancy["grade_required"] = vacancy_data.grade_required
    if vacancy_data.skills is not None:
        vacancy["skills"] = [
            {
                "skill_id": s.skill_id,
                "skill_name": s.skill_name,
                "required_level": s.required_level,
                "weight": s.weight,
                "skill_type": s.skill_type,
                "is_critical": s.is_critical
            }
            for s in vacancy_data.skills
        ]
        vacancy["critical_skills"] = [s.skill_id for s in vacancy_data.skills if s.is_critical]
    
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


@router.delete("/{vacancy_id}")
async def delete_vacancy(vacancy_id: str):
    """
    Delete a vacancy.
    """
    if not remove_vacancy_from_pool(vacancy_id):
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return {"message": "Vacancy deleted", "id": vacancy_id}


