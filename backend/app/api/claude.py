"""
API endpoints for Claude/LLM services.
"""
from fastapi import APIRouter, HTTPException

from app.schemas.claude import (
    ResumeAnalyzeRequest, ResumeAnalysisResult,
    VacancyAnalyzeRequest, VacancyAnalysisResult,
    MatchRequest, MatchResult,
    TaskGenerateRequest, GeneratedTask,
    HintRequest, HintsResult,
    LiveAssistantRequest, LiveAssistantResponse,
    SolutionReviewRequest, SolutionReviewResult,
    AIDetectionRequest, AIDetectionResult,
    FinalReportRequest, FinalReportResult,
)
from app.services.claude_service import (
    analyze_resume,
    analyze_vacancy,
    match_resume_vacancy,
    generate_task,
    generate_hints,
    live_assistant_response,
    review_solution,
    detect_ai_code,
    generate_final_report,
)


router = APIRouter()


# 1. Resume Analyzer
@router.post("/resume/analyze", response_model=ResumeAnalysisResult)
async def api_analyze_resume(request: ResumeAnalyzeRequest):
    """
    Analyze resume text and extract structured data.
    
    Returns years of experience, tracks, grade, tech stack, domains, summary.
    """
    try:
        result = await analyze_resume(request.resume_text)
        return ResumeAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2. Vacancy Analyzer
@router.post("/vacancy/analyze", response_model=VacancyAnalysisResult)
async def api_analyze_vacancy(request: VacancyAnalyzeRequest):
    """
    Analyze vacancy text and extract structured requirements.
    
    Returns role title, expected grade, tracks, skills, domains, etc.
    """
    try:
        result = await analyze_vacancy(request.vacancy_text)
        return VacancyAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2.3. Resume-Vacancy Matcher
@router.post("/match", response_model=MatchResult)
async def api_match_resume_vacancy(request: MatchRequest):
    """
    Match resume to vacancy and provide recommendations.
    
    Returns match score, summary, strong fit areas, gaps, recommended topics.
    """
    try:
        result = await match_resume_vacancy(
            request.resume_parsed,
            request.vacancy_parsed,
            request.interview_summary
        )
        return MatchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. Task Generator
@router.post("/task/generate", response_model=GeneratedTask)
async def api_generate_task(request: TaskGenerateRequest):
    """
    Generate a task with tests (offline pipeline).
    
    Returns task with description, examples, hidden tests, rubric.
    """
    try:
        result = await generate_task(
            request.track,
            request.difficulty,
            request.mode,
            request.target_skills,
            request.vacancy_summary
        )
        return GeneratedTask(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. Hint Generator
@router.post("/hints/generate", response_model=HintsResult)
async def api_generate_hints(request: HintRequest):
    """
    Generate three levels of hints for a task.
    
    Returns soft, medium, and hard hints.
    """
    try:
        result = await generate_hints(
            request.task_description,
            request.candidate_code or "",
            request.test_results,
            request.grade,
            request.difficulty
        )
        return HintsResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 5. Live Interview Assistant
@router.post("/chat/respond", response_model=LiveAssistantResponse)
async def api_live_assistant(request: LiveAssistantRequest):
    """
    Generate live chat response (reactive or proactive).
    
    Returns text response for chat.
    """
    try:
        message = await live_assistant_response(
            request.mode,
            request.task_description,
            request.candidate_code or "",
            request.test_results,
            request.user_message,
            request.grade,
            request.difficulty
        )
        return LiveAssistantResponse(message=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 6. Solution Reviewer
@router.post("/solution/review", response_model=SolutionReviewResult)
async def api_review_solution(request: SolutionReviewRequest):
    """
    Review solution quality beyond tests.
    
    Returns correctness, robustness, code quality scores, verdict, strengths, weaknesses.
    """
    try:
        result = await review_solution(
            request.task_description,
            request.candidate_code,
            request.test_results,
            request.grade,
            request.difficulty
        )
        return SolutionReviewResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 7. AI Code Detector
@router.post("/ai/detect", response_model=AIDetectionResult)
async def api_detect_ai_code(request: AIDetectionRequest):
    """
    Detect if code looks AI-generated.
    
    Returns AI likeness score, explanation, suspicious signals.
    """
    try:
        result = await detect_ai_code(request.candidate_code)
        return AIDetectionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 8. Final Report Generator
@router.post("/report/generate", response_model=FinalReportResult)
async def api_generate_final_report(request: FinalReportRequest):
    """
    Generate final candidate report.
    
    Returns final grade, track, hire recommendation, markdown report, strengths, risks.
    """
    try:
        result = await generate_final_report(
            request.resume_parsed,
            request.vacancy_parsed,
            request.match_result,
            request.interview_metrics,
            request.trust_and_ai,
            request.solution_review_summary
        )
        return FinalReportResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# пидормот
