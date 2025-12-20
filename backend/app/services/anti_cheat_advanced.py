"""
Advanced Anti-Cheat System for VibeCode.
Implements full trust score calculation according to ANTICHEAT.md specification.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Literal
from pydantic import BaseModel
from datetime import datetime

from ..models.interview import AntiCheatEvent, Task, Interview


# Configuration constants
BIG_PASTE_THRESHOLD = 150  # characters
LONG_BLUR_MS = 60000  # 60 seconds
FAST_THRESHOLD_SEC = 60  # 60 seconds for middle/hard tasks


class AntiCheatSignals(BaseModel):
    """Aggregated anti-cheat signals."""
    big_pastes_count: int = 0
    pastes_after_long_blur: int = 0
    suspiciously_fast_solutions: int = 0
    devtools_opened: bool = False
    ai_likeness_score: float | None = None
    # Tab switch / focus lost tracking
    focus_lost_count: int = 0


TrustStatus = Literal["ok", "suspicious", "high_risk"]


def build_signals(interview_id: int, db: Session) -> AntiCheatSignals:
    """
    Build anti-cheat signals from events.
    
    Args:
        interview_id: Interview ID
        db: Database session
    
    Returns:
        AntiCheatSignals object
    """
    signals = AntiCheatSignals()
    
    # Get all events for this interview
    events = db.query(AntiCheatEvent).filter(
        AntiCheatEvent.interview_id == interview_id
    ).order_by(AntiCheatEvent.created_at).all()
    
    if not events:
        return signals
    
    # Track blur/focus state
    last_blur_time = None
    
    for event in events:
        meta = event.meta or {}
        
        # 1. Big pastes
        if event.event_type == "paste":
            length = meta.get("length", 0)
            from_empty = meta.get("fromEmpty", False)
            
            if length >= BIG_PASTE_THRESHOLD:
                signals.big_pastes_count += 1
        
        # 2. Track blur/focus for paste detection
        if event.event_type == "blur" or (
            event.event_type == "visibility_change" and not meta.get("visible", True)
        ):
            last_blur_time = int(event.created_at.timestamp() * 1000) if event.created_at else 0
        
        if event.event_type == "focus" or (
            event.event_type == "visibility_change" and meta.get("visible", False)
        ):
            last_blur_time = None
        
        # 3. Paste after long blur
        if event.event_type == "paste" and last_blur_time:
            current_time_ms = int(event.created_at.timestamp() * 1000) if event.created_at else 0
            blur_duration = current_time_ms - last_blur_time
            if blur_duration >= LONG_BLUR_MS:
                signals.pastes_after_long_blur += 1
        
        # 4. DevTools detection
        if event.event_type == "devtools":
            if meta.get("opened", False):
                signals.devtools_opened = True
        
        # 5. Focus lost / tab switch detection
        if event.event_type == "visibility_change" and not meta.get("visible", True):
            signals.focus_lost_count += 1
        if event.event_type == "blur":
            signals.focus_lost_count += 1
    
    # 6. Suspiciously fast solutions
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    
    for task in tasks:
        if task.difficulty in ("middle", "hard") and task.status == "completed":
            # Calculate time to first successful submit
            if task.created_at and task.submissions:
                # Find first successful submission
                for submission in task.submissions:
                    if submission.passed_tests and submission.passed_tests >= 0.8:
                        time_diff = (submission.created_at - task.created_at).total_seconds()
                        if time_diff < FAST_THRESHOLD_SEC:
                            signals.suspiciously_fast_solutions += 1
                        break
    
    return signals


async def get_ai_likeness_for_interview(
    interview_id: int,
    db: Session
) -> float | None:
    """
    Get AI-likeness score for interview's final solutions.
    
    Uses LLM to analyze code patterns.
    """
    from .scibox_client import scibox_client
    
    tasks = db.query(Task).filter(
        Task.interview_id == interview_id,
        Task.status == "completed"
    ).all()
    
    if not tasks:
        return None
    
    # Analyze last submission of each task
    ai_scores = []
    
    for task in tasks:
        if task.submissions:
            last_submission = task.submissions[-1]
            if last_submission.code:
                try:
                    result = await scibox_client.check_ai_likeness(last_submission.code)
                    ai_scores.append(result["ai_likeness_score"])
                except:
                    pass
    
    if not ai_scores:
        return None
    
    # Return average AI-likeness
    return sum(ai_scores) / len(ai_scores)


def calc_trust_score(signals: AntiCheatSignals) -> int:
    """
    Calculate trust score (0-100) from signals.
    
    Formula:
    - Start with 100
    - Subtract penalties for each suspicious pattern
    - Clamp to [0, 100]
    
    Args:
        signals: AntiCheatSignals object
    
    Returns:
        Trust score 0-100
    """
    score = 100
    
    # 1. Big pastes penalty
    if signals.big_pastes_count >= 1:
        score -= 10 * min(signals.big_pastes_count, 3)  # max -30
    
    # 2. Pastes after long blur
    if signals.pastes_after_long_blur > 0:
        score -= 15
    
    # 3. Suspiciously fast solutions
    if signals.suspiciously_fast_solutions > 0:
        score -= 15 * min(signals.suspiciously_fast_solutions, 2)  # max -30
    
    # 4. DevTools
    if signals.devtools_opened:
        score -= 10
    
    # 5. AI-likeness
    if signals.ai_likeness_score is not None:
        ai = signals.ai_likeness_score
        if ai >= 80:
            score -= 25
        elif ai >= 60:
            score -= 10
    
    # 6. Focus lost / tab switching - STRONG PENALTY
    # First switch is a warning (no penalty), but subsequent switches hurt badly
    if signals.focus_lost_count > 1:
        # Progressive penalty: 8 points for 2nd, 10 for 3rd, etc.
        penalty = sum(min(8 + (i * 2), 15) for i in range(signals.focus_lost_count - 1))
        score -= min(penalty, 50)  # Cap at -50 total for tab switching
    
    return max(0, min(100, score))


def get_trust_status(trust_score: int) -> TrustStatus:
    """
    Convert trust score to status.
    
    Rules:
    - 80-100 → ok
    - 50-79 → suspicious
    - 0-49 → high_risk
    """
    if trust_score >= 80:
        return "ok"
    elif trust_score >= 50:
        return "suspicious"
    else:
        return "high_risk"


def build_trust_explanation(signals: AntiCheatSignals, trust_score: int) -> List[str]:
    """
    Build human-readable explanation of trust score.
    
    Args:
        signals: AntiCheatSignals object
        trust_score: Calculated trust score
    
    Returns:
        List of reason strings
    """
    reasons = []
    
    if signals.big_pastes_count > 0:
        reasons.append(f"обнаружено {signals.big_pastes_count} больших вставок кода")
    
    if signals.pastes_after_long_blur > 0:
        reasons.append(
            "фиксировались вставки кода сразу после длительного отсутствия во вкладке"
        )
    
    if signals.suspiciously_fast_solutions > 0:
        reasons.append(
            f"{signals.suspiciously_fast_solutions} задач решены подозрительно быстро "
            f"при высоком покрытии тестов"
        )
    
    if signals.devtools_opened:
        reasons.append(
            "во время решения задачи было открыто окно разработчика (DevTools)"
        )
    
    if signals.ai_likeness_score is not None:
        ai = signals.ai_likeness_score
        if ai >= 80:
            reasons.append(
                f"код сильно похож на LLM-генерированный (AI-likeness ~{ai:.0f}%)"
            )
        elif ai >= 60:
            reasons.append(
                f"код частично похож на LLM-генерированный (AI-likeness ~{ai:.0f}%)"
            )
    
    # Focus lost / tab switching
    if signals.focus_lost_count > 0:
        if signals.focus_lost_count == 1:
            reasons.append("зафиксировано переключение с вкладки (1 раз, предупреждение)")
        else:
            reasons.append(
                f"многократные переключения вкладок ({signals.focus_lost_count} раз) — "
                f"серьёзное снижение доверия"
            )
    
    if not reasons:
        reasons.append("аномалий в поведении не обнаружено")
    
    return reasons


async def calculate_full_trust_score(
    interview_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Calculate complete trust score with all components.
    
    Returns:
        {
            "trust_score": 85,
            "trust_status": "ok",
            "trust_reasons": ["..."],
            "signals": {...}
        }
    """
    # Build signals from events
    signals = build_signals(interview_id, db)
    
    # Get AI-likeness (async)
    ai_likeness = await get_ai_likeness_for_interview(interview_id, db)
    signals.ai_likeness_score = ai_likeness
    
    # Calculate score
    trust_score = calc_trust_score(signals)
    trust_status = get_trust_status(trust_score)
    trust_reasons = build_trust_explanation(signals, trust_score)
    
    return {
        "trust_score": trust_score,
        "trust_status": trust_status,
        "trust_reasons": trust_reasons,
        "signals": signals.dict()
    }


def get_trust_badge_color(trust_score: int) -> str:
    """Get color for trust score badge."""
    if trust_score >= 80:
        return "green"
    elif trust_score >= 50:
        return "yellow"
    else:
        return "red"


def get_trust_recommendation(trust_status: TrustStatus) -> str:
    """Get recommendation based on trust status."""
    recommendations = {
        "ok": "Поведение кандидата выглядит естественным. Явных признаков внешней помощи не обнаружено.",
        "suspicious": "Обнаружены признаки копипаста или внешних подсказчиков. Рекомендуем ручной просмотр кода и логов.",
        "high_risk": "Сильные признаки того, что решение получено не самостоятельно. Результат стоит использовать с осторожностью."
    }
    return recommendations.get(trust_status, "")

# пидормот
