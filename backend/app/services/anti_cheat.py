"""
Anti-cheat service.
Calculates trust score based on suspicious events.
"""
from sqlalchemy.orm import Session
from typing import List

from ..models.interview import AntiCheatEvent


def calculate_trust_score(interview_id: int, db: Session) -> float:
    """
    Calculate trust score for interview based on anti-cheat events.
    
    Args:
        interview_id: Interview ID
        db: Database session
    
    Returns:
        Trust score (0-100)
    """
    events = db.query(AntiCheatEvent).filter(
        AntiCheatEvent.interview_id == interview_id
    ).all()
    
    if not events:
        return 100.0
    
    # Penalty for each event type
    penalties = {
        "copy_paste": 5,
        "window_blur": 2,
        "devtools_open": 10,
        "fast_typing": 3,
        "tab_switch": 3
    }
    
    # Severity multipliers
    severity_multipliers = {
        "low": 1.0,
        "medium": 1.5,
        "high": 2.0
    }
    
    total_penalty = 0
    for event in events:
        base_penalty = penalties.get(event.event_type, 5)
        multiplier = severity_multipliers.get(event.severity, 1.0)
        total_penalty += base_penalty * multiplier
    
    # Calculate score (100 - penalties, minimum 0)
    trust_score = max(0, 100 - total_penalty)
    
    return round(trust_score, 2)


def analyze_ai_likeness(code: str, task_description: str) -> Dict[str, Any]:
    """
    Analyze code to detect AI-generated patterns.
    Part of Trust Score + AI-Likeness feature.
    
    Args:
        code: Code to analyze
        task_description: Task description
    
    Returns:
        Dict with ai_likeness_score and comments
    """
    # Placeholder for MVP
    # In production, would use LLM to analyze code patterns
    
    # Simple heuristics for MVP
    ai_indicators = 0
    
    # Check for overly perfect formatting
    if code.count('\n\n') > 5:
        ai_indicators += 1
    
    # Check for extensive comments
    comment_lines = code.count('#') + code.count('//')
    total_lines = code.count('\n') + 1
    if comment_lines / total_lines > 0.3:
        ai_indicators += 1
    
    # Check for type hints (common in AI-generated Python)
    if '->' in code and ':' in code:
        ai_indicators += 1
    
    ai_likeness_score = min(100, ai_indicators * 25)
    
    return {
        "ai_likeness_score": ai_likeness_score,
        "comment": "Базовый анализ для MVP. В продакшене используется LLM."
    }

