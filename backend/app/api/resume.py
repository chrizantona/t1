"""
Resume analysis API endpoints.
CV-based level suggestion feature with deterministic grading logic.
Supports both text and PDF file uploads.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from io import BytesIO

from ..core.db import get_db
from ..schemas.interview import CVAnalysisRequest, CVAnalysisResponse
from ..services.scibox_client import scibox_client
from ..grading.tracks import determine_track
from ..services.grading_service import calculate_start_grade

router = APIRouter()


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file bytes."""
    try:
        from pypdf import PdfReader
        
        pdf_file = BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n".join(text_parts)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse PDF: {str(e)}"
        )


@router.post("/upload", response_model=CVAnalysisResponse)
async def upload_and_analyze_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze resume from PDF or text file.
    Supports PDF and TXT formats.
    """
    # Validate file type
    filename = file.filename or ""
    content_type = file.content_type or ""
    
    allowed_extensions = [".pdf", ".txt"]
    allowed_mime_types = ["application/pdf", "text/plain"]
    
    file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    
    if file_ext not in allowed_extensions and content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: PDF, TXT. Got: {content_type or file_ext}"
        )
    
    # Read file content
    file_content = await file.read()
    
    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    
    # Extract text based on file type
    if file_ext == ".pdf" or content_type == "application/pdf":
        cv_text = extract_text_from_pdf(file_content)
    else:
        # Try to decode as text
        try:
            cv_text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                cv_text = file_content.decode("cp1251")  # Try Windows Cyrillic
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Could not decode text file. Please use UTF-8 encoding."
                )
    
    if not cv_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from file")
    
    # Now analyze the extracted text (reuse existing logic)
    return await _analyze_cv_text(cv_text)


async def _analyze_cv_text(cv_text: str) -> CVAnalysisResponse:
    """
    🔥 Internal function to analyze CV text with enhanced AI analysis.
    Returns comprehensive candidate assessment.
    """
    try:
        print(f"📄 Analyzing CV ({len(cv_text)} chars)...")
        
        # Use killer prompts for deep analysis
        response = await scibox_client.analyze_resume(cv_text)
        
        print(f"✅ LLM response: {response}")
        
        # Extract data from enhanced LLM response
        years_exp = response.get("years_of_experience", 2.0)
        resume_tracks = response.get("tracks", [])
        key_techs = response.get("key_technologies", [])
        resume_grade = response.get("recommended_grade", "middle")
        confidence = response.get("confidence", 70)
        strengths = response.get("strengths", [])
        weaknesses = response.get("weaknesses", [])
        risk_factors = response.get("risk_factors", [])
        interview_focus = response.get("interview_focus", [])
        justification = response.get("justification", "")
        
        # Deterministic track determination
        suggested_direction = determine_track(
            self_claimed_track=None,
            resume_text=cv_text,
            resume_tracks=resume_tracks
        )
        
        # Deterministic grade calculation
        grade_calc = calculate_start_grade(
            years_of_experience=years_exp,
            self_claimed_grade="middle",
            resume_grade=resume_grade
        )
        
        suggested_level = grade_calc["start_grade"]
        
        # Build reasoning without emojis
        tech_str = ", ".join(key_techs[:5]) if key_techs else "не определены"
        tracks_str = ", ".join(resume_tracks[:3]) if resume_tracks else suggested_direction
        
        reasoning = (
            f"Анализ резюме (уверенность: {confidence}%)\n\n"
            f"Рекомендуемый грейд: {suggested_level.upper()}\n"
            f"Направление: {suggested_direction} (обнаружены: {tracks_str})\n"
            f"Опыт: {years_exp:.1f} лет\n"
            f"Ключевые технологии: {tech_str}\n\n"
        )
        
        if justification:
            reasoning += f"{justification}\n\n"
        
        if strengths:
            reasoning += f"Сильные стороны: {', '.join(strengths[:3])}\n"
        
        if weaknesses:
            reasoning += f"Зоны роста: {', '.join(weaknesses[:3])}\n"
        
        if risk_factors:
            reasoning += f"Обратить внимание: {', '.join(risk_factors[:2])}\n"
        
        return CVAnalysisResponse(
            suggested_level=suggested_level,
            suggested_direction=suggested_direction,
            years_of_experience=years_exp,
            key_technologies=key_techs[:10],  # Top 10 techs
            reasoning=reasoning.strip(),
            confidence=confidence,
            all_tracks=resume_tracks,
            strengths=strengths[:5],
            weaknesses=weaknesses[:5],
            risk_factors=risk_factors[:5],
            interview_focus=interview_focus[:5]
        )
    
    except Exception as e:
        print(f"CV analysis error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback with deterministic defaults
        return CVAnalysisResponse(
            suggested_level="middle",
            suggested_direction="backend",
            years_of_experience=2.0,
            key_technologies=[],
            reasoning=(
                "Не удалось полностью проанализировать резюме.\n"
                "Рекомендуем начать с уровня MIDDLE по направлению Backend.\n"
                "На собеседовании уточним ваш опыт и подберём задачи."
            ),
            confidence=50,
            all_tracks=["backend"],
            strengths=[],
            weaknesses=[],
            risk_factors=["Требуется уточнение на собеседовании"],
            interview_focus=["Проверить реальный опыт работы"]
        )


@router.post("/analyze", response_model=CVAnalysisResponse)
async def analyze_resume(
    cv_data: CVAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze CV text and suggest level and direction.
    Killer feature #1: CV-based Level Suggestion.
    """
    return await _analyze_cv_text(cv_data.cv_text)

