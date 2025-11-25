"""
Claude/SciBox LLM service for all prompts.
"""
import json
from typing import Optional, Any
from openai import OpenAI

from app.core.config import settings
from app.prompts import (
    RESUME_ANALYZER_SYSTEM, RESUME_ANALYZER_USER,
    VACANCY_ANALYZER_SYSTEM, VACANCY_ANALYZER_USER,
    MATCHER_SYSTEM, MATCHER_USER,
    TASK_GENERATOR_SYSTEM, TASK_GENERATOR_USER,
    HINT_GENERATOR_SYSTEM, HINT_GENERATOR_USER,
    LIVE_ASSISTANT_SYSTEM, LIVE_ASSISTANT_USER,
    SOLUTION_REVIEWER_SYSTEM, SOLUTION_REVIEWER_USER,
    AI_DETECTOR_SYSTEM, AI_DETECTOR_USER,
    FINAL_REPORT_SYSTEM, FINAL_REPORT_USER,
)


# Initialize SciBox client
client = OpenAI(
    api_key=settings.SCIBOX_API_KEY,
    base_url=settings.SCIBOX_BASE_URL,
)


def _call_llm(system_prompt: str, user_prompt: str, expect_json: bool = True) -> Any:
    """
    Call LLM with system and user prompts.
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        expect_json: Whether to parse response as JSON
        
    Returns:
        Parsed JSON or raw text
    """
    # Add /no_think prefix for JSON responses
    if expect_json:
        system_prompt = "/no_think " + system_prompt
    
    response = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=4096,
        temperature=0.1,
    )
    
    content = response.choices[0].message.content
    
    if expect_json:
        # Try to parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
            raise ValueError(f"Failed to parse JSON from response: {content[:200]}")
    
    return content


# 1. Resume Analyzer
async def analyze_resume(resume_text: str) -> dict:
    """
    Analyze resume and extract structured data.
    
    Args:
        resume_text: Raw text from PDF resume
        
    Returns:
        Dict with years_of_experience, tracks, resume_self_grade, tech_stack, domains, summary
    """
    user_prompt = RESUME_ANALYZER_USER.format(resume_text=resume_text)
    return _call_llm(RESUME_ANALYZER_SYSTEM, user_prompt)


# 2. Vacancy Analyzer
async def analyze_vacancy(vacancy_text: str) -> dict:
    """
    Analyze vacancy and extract structured requirements.
    
    Args:
        vacancy_text: Raw text of vacancy
        
    Returns:
        Dict with role_title, expected_grade, tracks, must_have_skills, etc.
    """
    user_prompt = VACANCY_ANALYZER_USER.format(vacancy_text=vacancy_text)
    return _call_llm(VACANCY_ANALYZER_SYSTEM, user_prompt)


# 2.3. Resume-Vacancy Matcher
async def match_resume_vacancy(
    resume_parsed: dict,
    vacancy_parsed: dict,
    interview_summary: Optional[str] = None
) -> dict:
    """
    Match resume to vacancy and provide recommendations.
    
    Args:
        resume_parsed: Parsed resume JSON
        vacancy_parsed: Parsed vacancy JSON
        interview_summary: Optional interview summary
        
    Returns:
        Dict with match_score, match_summary, strong_fit, gaps, etc.
    """
    user_prompt = MATCHER_USER.format(
        resume_parsed_json=json.dumps(resume_parsed, ensure_ascii=False),
        vacancy_parsed_json=json.dumps(vacancy_parsed, ensure_ascii=False),
        interview_summary=interview_summary or "null"
    )
    return _call_llm(MATCHER_SYSTEM, user_prompt)


# 3. Task Generator
async def generate_task(
    track: str,
    difficulty: str,
    mode: str,
    target_skills: list[str],
    vacancy_summary: Optional[str] = None
) -> dict:
    """
    Generate a task with tests (offline pipeline).
    
    Args:
        track: backend|frontend|data|devops|algorithms|...
        difficulty: easy|middle|hard
        mode: coding|theory
        target_skills: List of target skills
        vacancy_summary: Optional vacancy context
        
    Returns:
        Dict with task_type, title, description, visible_examples, hidden_tests, etc.
    """
    user_prompt = TASK_GENERATOR_USER.format(
        track=track,
        difficulty=difficulty,
        mode=mode,
        target_skills="\n".join(target_skills),
        vacancy_summary=vacancy_summary or ""
    )
    return _call_llm(TASK_GENERATOR_SYSTEM, user_prompt)


# 4. Hint Generator
async def generate_hints(
    task_description: str,
    candidate_code: str,
    test_results: str,
    grade: str,
    difficulty: str
) -> dict:
    """
    Generate three levels of hints for a task.
    
    Args:
        task_description: Task description
        candidate_code: Current candidate code
        test_results: JSON string with test results
        grade: junior|middle|senior
        difficulty: easy|middle|hard
        
    Returns:
        Dict with soft_hint, medium_hint, hard_hint
    """
    user_prompt = HINT_GENERATOR_USER.format(
        task_description=task_description,
        candidate_code=candidate_code or "",
        test_results=test_results,
        grade=grade,
        difficulty=difficulty
    )
    return _call_llm(HINT_GENERATOR_SYSTEM, user_prompt)


# 5. Live Interview Assistant
async def live_assistant_response(
    mode: str,
    task_description: str,
    candidate_code: str,
    test_results: str,
    user_message: Optional[str],
    grade: str,
    difficulty: str
) -> str:
    """
    Generate live chat response (reactive or proactive).
    
    Args:
        mode: reactive|proactive
        task_description: Task description
        candidate_code: Current candidate code
        test_results: JSON string with test results
        user_message: User message (for reactive mode)
        grade: junior|middle|senior
        difficulty: easy|middle|hard
        
    Returns:
        Text response for chat
    """
    user_prompt = LIVE_ASSISTANT_USER.format(
        mode=mode,
        task_description=task_description,
        candidate_code=candidate_code or "",
        test_results=test_results,
        user_message=user_message or "",
        grade=grade,
        difficulty=difficulty
    )
    return _call_llm(LIVE_ASSISTANT_SYSTEM, user_prompt, expect_json=False)


# 6. Solution Reviewer
async def review_solution(
    task_description: str,
    candidate_code: str,
    test_results: str,
    grade: str,
    difficulty: str
) -> dict:
    """
    Review solution quality beyond tests.
    
    Args:
        task_description: Task description
        candidate_code: Candidate's code
        test_results: JSON string with test results
        grade: junior|middle|senior
        difficulty: easy|middle|hard
        
    Returns:
        Dict with correctness_score, robustness_score, code_quality_score, etc.
    """
    user_prompt = SOLUTION_REVIEWER_USER.format(
        task_description=task_description,
        candidate_code=candidate_code,
        test_results=test_results,
        grade=grade,
        difficulty=difficulty
    )
    return _call_llm(SOLUTION_REVIEWER_SYSTEM, user_prompt)


# 7. AI Code Detector
async def detect_ai_code(candidate_code: str) -> dict:
    """
    Detect if code looks AI-generated.
    
    Args:
        candidate_code: Code to analyze
        
    Returns:
        Dict with ai_likeness_score, explanation, suspicious_signals
    """
    user_prompt = AI_DETECTOR_USER.format(candidate_code=candidate_code)
    return _call_llm(AI_DETECTOR_SYSTEM, user_prompt)


# 8. Final Report Generator
async def generate_final_report(
    resume_parsed: dict,
    vacancy_parsed: dict,
    match_result: dict,
    interview_metrics: dict,
    trust_and_ai: dict,
    solution_review_summary: dict
) -> dict:
    """
    Generate final candidate report.
    
    Args:
        resume_parsed: Parsed resume JSON
        vacancy_parsed: Parsed vacancy JSON
        match_result: Match result JSON
        interview_metrics: Interview metrics JSON
        trust_and_ai: Trust and AI metrics JSON
        solution_review_summary: Solution review summary JSON
        
    Returns:
        Dict with final_grade, final_track, hire_recommendation, report_markdown, etc.
    """
    user_prompt = FINAL_REPORT_USER.format(
        resume_parsed_json=json.dumps(resume_parsed, ensure_ascii=False),
        vacancy_parsed_json=json.dumps(vacancy_parsed, ensure_ascii=False),
        match_result_json=json.dumps(match_result, ensure_ascii=False),
        interview_metrics_json=json.dumps(interview_metrics, ensure_ascii=False),
        trust_and_ai_json=json.dumps(trust_and_ai, ensure_ascii=False),
        solution_review_summary_json=json.dumps(solution_review_summary, ensure_ascii=False)
    )
    return _call_llm(FINAL_REPORT_SYSTEM, user_prompt)
