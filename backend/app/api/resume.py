"""
Resume analysis API endpoints.
CV-based level suggestion feature with deterministic grading logic.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..schemas.interview import CVAnalysisRequest, CVAnalysisResponse
from ..services.scibox_client import scibox_client
from ..grading.tracks import determine_track
from ..services.grading_service import calculate_start_grade

router = APIRouter()


@router.post("/analyze", response_model=CVAnalysisResponse)
async def analyze_resume(
    cv_data: CVAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze CV and suggest level and direction.
    Killer feature #1: CV-based Level Suggestion.
    """
    
    # Prompt for CV analysis
    system_prompt = """/no_think
Ты эксперт по оценке резюме разработчиков.
Проанализируй резюме и верни JSON с полями:
- suggested_level: junior/middle/middle+/senior
- suggested_direction: backend/frontend/fullstack/algorithms/data
- years_of_experience: число лет опыта
- key_technologies: список ключевых технологий
- reasoning: краткое объяснение рекомендации

Отвечай ТОЛЬКО валидным JSON без markdown, без ```json тегов."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Резюме:\n\n{cv_data.cv_text}"}
    ]
    
    try:
        # Use LLM as parser only (not decision maker)
        response = await scibox_client.analyze_resume(cv_data.cv_text)
        
        # Extract data from LLM
        years_exp = response.get("years_of_experience", 2.0)
        resume_tracks = response.get("tracks", [])
        key_techs = response.get("key_technologies", [])
        resume_grade = response.get("recommended_grade")
        
        # Deterministic track determination
        suggested_direction = determine_track(
            self_claimed_track=None,  # User hasn't claimed yet
            resume_text=cv_data.cv_text,
            resume_tracks=resume_tracks
        )
        
        # Deterministic grade calculation
        # Assume user will claim "middle" if not specified
        grade_calc = calculate_start_grade(
            years_of_experience=years_exp,
            self_claimed_grade="middle",  # Default assumption
            resume_grade=resume_grade
        )
        
        suggested_level = grade_calc["start_grade"]
        
        reasoning = (
            f"На основе {years_exp:.1f} лет опыта и анализа технологий "
            f"({', '.join(key_techs[:3])}) рекомендуем начать с уровня {suggested_level}. "
            f"Направление: {suggested_direction}."
        )
        
        return CVAnalysisResponse(
            suggested_level=suggested_level,
            suggested_direction=suggested_direction,
            years_of_experience=years_exp,
            key_technologies=key_techs,
            reasoning=reasoning
        )
    
    except Exception as e:
        # Fallback with deterministic defaults
        return CVAnalysisResponse(
            suggested_level="middle",
            suggested_direction="backend",
            years_of_experience=2.0,
            key_technologies=[],
            reasoning="Рекомендуем начать с уровня Middle по направлению Backend."
        )

