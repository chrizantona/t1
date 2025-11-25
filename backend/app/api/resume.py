"""
Resume analysis API endpoints.
CV-based level suggestion feature.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..schemas.interview import CVAnalysisRequest, CVAnalysisResponse
from ..services.scibox_client import scibox_client

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
    system_prompt = """Ты эксперт по оценке резюме разработчиков.
Проанализируй резюме и верни JSON с полями:
- suggested_level: junior/middle/middle+/senior
- suggested_direction: backend/frontend/fullstack/algorithms/data
- years_of_experience: число лет опыта
- key_technologies: список ключевых технологий
- reasoning: краткое объяснение рекомендации

Отвечай ТОЛЬКО валидным JSON, без дополнительного текста."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Резюме:\n\n{cv_data.cv_text}"}
    ]
    
    try:
        response = scibox_client.chat_completion(messages, temperature=0.3, max_tokens=512)
        
        # Parse JSON response
        import json
        # Try to extract JSON from response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        result = json.loads(response.strip())
        
        return CVAnalysisResponse(
            suggested_level=result.get("suggested_level", "middle"),
            suggested_direction=result.get("suggested_direction", "backend"),
            years_of_experience=result.get("years_of_experience"),
            key_technologies=result.get("key_technologies", []),
            reasoning=result.get("reasoning", "")
        )
    
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return CVAnalysisResponse(
            suggested_level="middle",
            suggested_direction="backend",
            years_of_experience=None,
            key_technologies=[],
            reasoning="Не удалось полностью проанализировать резюме, рекомендую начать с уровня Middle."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV analysis failed: {str(e)}")

