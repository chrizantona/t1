"""
Scoring Formula - Calculate final grade according to ТЗ.

Formula:
rawSkillScore[s] = (practice_score[s] * 0.5 + theory_score[s] * 0.3 + resume_score[s] * 0.2)
effectiveSkillScore[s] = rawSkillScore[s] - cheatPenalty(s)

totalScore = Σ (effectiveSkillScore[s] * vacancy.skills[s].weight) / Σ (vacancy.skills[s].weight)

Decision:
- if totalScore >= hire_threshold → "HIRE"
- if totalScore >= consider_threshold → "CONSIDER"  
- else → "REJECT"

Cheat adjustments:
- if aiStyleScore > 0.7 or copyPasteCount > 3 → auto REJECT
- if moderate cheat signals → max grade = "middle", no "HIRE"
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CheatSignals:
    """Aggregated cheat signals from interview."""
    copy_paste_count: int = 0
    devtools_opened: bool = False
    focus_lost_count: int = 0
    ai_style_score: float = 0.0  # 0-1
    code_similarity_score: float = 0.0  # 0-1


@dataclass
class ScoringWeights:
    """Weights for different components."""
    algo: float = 0.3
    practice: float = 0.25
    theory: float = 0.2
    soft: float = 0.1
    skills_match: float = 0.15


@dataclass
class DecisionThresholds:
    """Thresholds for hire/consider decisions."""
    hire: float = 75.0
    consider: float = 50.0


# ============ Cheat Penalty Calculation ============

def calculate_cheat_penalty(cheat: CheatSignals) -> float:
    """
    Calculate score penalty based on cheat signals.
    
    Returns penalty value (0-50) to subtract from score.
    """
    penalty = 0.0
    
    # Copy-paste penalty (each copy-paste = -3 points)
    penalty += min(cheat.copy_paste_count * 3, 15)
    
    # DevTools penalty (-10 points if opened)
    if cheat.devtools_opened:
        penalty += 10
    
    # Focus loss penalty (each loss = -2 points, max -10)
    penalty += min(cheat.focus_lost_count * 2, 10)
    
    # AI style penalty (scaled 0-15)
    penalty += cheat.ai_style_score * 15
    
    # Code similarity penalty (scaled 0-10)
    if cheat.code_similarity_score > 0.8:
        penalty += 10
    elif cheat.code_similarity_score > 0.6:
        penalty += 5
    
    return min(penalty, 50)  # Cap at 50


def should_auto_reject(cheat: CheatSignals) -> tuple[bool, str]:
    """
    Check if candidate should be auto-rejected due to severe cheating.
    
    Returns:
        (should_reject, reason)
    """
    if cheat.ai_style_score > 0.7:
        return True, "Код с высокой вероятностью сгенерирован AI"
    
    if cheat.copy_paste_count > 3:
        return True, "Подозрительное количество copy-paste операций"
    
    if cheat.ai_style_score > 0.5 and cheat.code_similarity_score > 0.8:
        return True, "Код подозрительно похож на эталонные решения и AI-стиль"
    
    return False, ""


def should_cap_grade(cheat: CheatSignals) -> tuple[bool, str]:
    """
    Check if grade should be capped at middle due to moderate cheating.
    
    Returns:
        (should_cap, reason)
    """
    moderate_signals = 0
    reasons = []
    
    if cheat.ai_style_score > 0.4:
        moderate_signals += 1
        reasons.append("AI-подобный стиль кода")
    
    if cheat.copy_paste_count > 2:
        moderate_signals += 1
        reasons.append("Copy-paste активность")
    
    if cheat.devtools_opened:
        moderate_signals += 1
        reasons.append("Открытие DevTools")
    
    if cheat.focus_lost_count > 5:
        moderate_signals += 1
        reasons.append("Частая потеря фокуса")
    
    if moderate_signals >= 2:
        return True, "; ".join(reasons)
    
    return False, ""


# ============ Score Calculation ============

def calculate_algo_score(
    tasks_completed: int,
    tasks_total: int,
    avg_task_score: float,
    hint_penalty: float = 0.0
) -> float:
    """
    Calculate algorithm block score.
    
    Args:
        tasks_completed: Number of completed tasks
        tasks_total: Total tasks
        avg_task_score: Average score per task (0-100)
        hint_penalty: Total hint penalty (0-100)
        
    Returns:
        Score 0-100
    """
    if tasks_total == 0:
        return 0
    
    completion_bonus = (tasks_completed / tasks_total) * 20
    base_score = avg_task_score
    
    return max(0, min(100, base_score + completion_bonus - hint_penalty))


def calculate_theory_score(
    answers: List[Dict[str, Any]]
) -> float:
    """
    Calculate theory block score.
    
    Args:
        answers: List of {score: 0-100, ...} for each answer
        
    Returns:
        Score 0-100
    """
    if not answers:
        return 0
    
    return sum(a.get("score", 0) for a in answers) / len(answers)


def calculate_skills_match_score(
    candidate_skills: Dict[str, float],  # skill_id -> level (0-3)
    vacancy_skills: List[Dict[str, Any]]  # List of vacancy skill requirements
) -> float:
    """
    Calculate how well candidate matches vacancy requirements.
    
    Returns:
        Score 0-100
    """
    if not vacancy_skills:
        return 50  # Default if no requirements
    
    total_weight = 0
    weighted_match = 0
    
    for vs in vacancy_skills:
        skill_id = vs.get("skill_id")
        required_level = vs.get("required_level", 1)
        weight = vs.get("weight", 1.0)
        
        candidate_level = candidate_skills.get(skill_id, 0)
        
        # Calculate match (0-1)
        if required_level == 0:
            match = 1.0  # Nice-to-have, always matches
        else:
            match = min(1.0, candidate_level / required_level)
        
        weighted_match += match * weight
        total_weight += weight
    
    if total_weight == 0:
        return 50
    
    return (weighted_match / total_weight) * 100


def calculate_total_score(
    algo_score: float,
    practice_score: float,
    theory_score: float,
    soft_score: float,
    skills_match_score: float,
    weights: ScoringWeights,
    cheat: CheatSignals
) -> Dict[str, Any]:
    """
    Calculate total score with all components.
    
    Returns:
        {
            "total_score": 0-100,
            "component_scores": {...},
            "cheat_penalty": float,
            "adjusted_score": 0-100
        }
    """
    # Calculate raw total
    raw_total = (
        algo_score * weights.algo +
        practice_score * weights.practice +
        theory_score * weights.theory +
        soft_score * weights.soft +
        skills_match_score * weights.skills_match
    )
    
    # Apply cheat penalty
    cheat_penalty = calculate_cheat_penalty(cheat)
    adjusted_score = max(0, raw_total - cheat_penalty)
    
    return {
        "total_score": raw_total,
        "component_scores": {
            "algo": algo_score,
            "practice": practice_score,
            "theory": theory_score,
            "soft": soft_score,
            "skills_match": skills_match_score
        },
        "weights_used": {
            "algo": weights.algo,
            "practice": weights.practice,
            "theory": weights.theory,
            "soft": weights.soft,
            "skills_match": weights.skills_match
        },
        "cheat_penalty": cheat_penalty,
        "adjusted_score": adjusted_score
    }


# ============ Grade Determination ============

GRADE_THRESHOLDS = {
    "senior": 85,
    "middle+": 75,
    "middle": 60,
    "junior+": 45,
    "junior": 30,
    "intern": 0
}


def score_to_grade(score: float) -> str:
    """Convert score to grade."""
    for grade, threshold in GRADE_THRESHOLDS.items():
        if score >= threshold:
            return grade
    return "intern"


def determine_decision(
    total_score: float,
    thresholds: DecisionThresholds,
    cheat: CheatSignals
) -> Dict[str, Any]:
    """
    Determine final hiring decision.
    
    Returns:
        {
            "decision": "HIRE|CONSIDER|REJECT",
            "reason": "...",
            "grade": "junior|middle|senior",
            "capped": bool,
            "auto_rejected": bool
        }
    """
    # Check for auto-reject
    auto_reject, reject_reason = should_auto_reject(cheat)
    if auto_reject:
        return {
            "decision": "REJECT",
            "reason": reject_reason,
            "grade": "rejected",
            "capped": False,
            "auto_rejected": True
        }
    
    # Calculate base grade
    base_grade = score_to_grade(total_score)
    
    # Check for grade capping
    should_cap, cap_reason = should_cap_grade(cheat)
    if should_cap:
        # Cap at middle
        if base_grade in ["senior", "middle+"]:
            base_grade = "middle"
        
        if total_score >= thresholds.hire:
            return {
                "decision": "CONSIDER",  # Downgrade from HIRE
                "reason": f"Грейд ограничен из-за: {cap_reason}",
                "grade": base_grade,
                "capped": True,
                "auto_rejected": False
            }
    
    # Normal decision
    if total_score >= thresholds.hire:
        return {
            "decision": "HIRE",
            "reason": "Кандидат успешно прошёл все этапы",
            "grade": base_grade,
            "capped": False,
            "auto_rejected": False
        }
    elif total_score >= thresholds.consider:
        return {
            "decision": "CONSIDER",
            "reason": "Кандидат показал средние результаты, требуется дополнительная оценка",
            "grade": base_grade,
            "capped": False,
            "auto_rejected": False
        }
    else:
        return {
            "decision": "REJECT",
            "reason": "Кандидат не достиг минимальных требований",
            "grade": base_grade,
            "capped": False,
            "auto_rejected": False
        }


# ============ Full Report Generation ============

def generate_full_report(
    interview_data: Dict[str, Any],
    vacancy_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate full interview report.
    
    Args:
        interview_data: {
            "tasks": [...],
            "theory_answers": [...],
            "cheat_signals": {...},
            "candidate_info": {...},
            "timing": {...}
        }
        vacancy_data: Optional vacancy requirements
        
    Returns:
        Complete report structure
    """
    # Parse cheat signals
    cheat_raw = interview_data.get("cheat_signals", {})
    cheat = CheatSignals(
        copy_paste_count=cheat_raw.get("copy_paste_count", 0),
        devtools_opened=cheat_raw.get("devtools_opened", False),
        focus_lost_count=cheat_raw.get("focus_lost_count", 0),
        ai_style_score=cheat_raw.get("ai_style_score", 0.0),
        code_similarity_score=cheat_raw.get("code_similarity_score", 0.0)
    )
    
    # Get weights from vacancy or use defaults
    if vacancy_data and "scoring_weights" in vacancy_data:
        w = vacancy_data["scoring_weights"]
        weights = ScoringWeights(
            algo=w.get("algo", 0.3),
            practice=w.get("practice", 0.25),
            theory=w.get("theory", 0.2),
            soft=w.get("soft", 0.1),
            skills_match=w.get("skills_match", 0.15)
        )
    else:
        weights = ScoringWeights()
    
    # Get thresholds
    if vacancy_data and "decision_thresholds" in vacancy_data:
        t = vacancy_data["decision_thresholds"]
        thresholds = DecisionThresholds(
            hire=t.get("hire", 75),
            consider=t.get("consider", 50)
        )
    else:
        thresholds = DecisionThresholds()
    
    # Calculate component scores
    tasks = interview_data.get("tasks", [])
    tasks_scores = [t.get("score", 0) for t in tasks if t.get("score")]
    avg_task_score = sum(tasks_scores) / len(tasks_scores) if tasks_scores else 0
    
    algo_score = calculate_algo_score(
        tasks_completed=len([t for t in tasks if t.get("status") == "completed"]),
        tasks_total=len(tasks),
        avg_task_score=avg_task_score,
        hint_penalty=interview_data.get("hint_penalty", 0)
    )
    
    theory_answers = interview_data.get("theory_answers", [])
    theory_score = calculate_theory_score(theory_answers)
    
    # Practice and soft scores (can be same as algo for now)
    practice_score = algo_score  # TODO: separate practice tasks
    soft_score = interview_data.get("soft_score", 60)  # Default moderate
    
    # Skills match (if vacancy provided)
    candidate_skills = interview_data.get("candidate_skills", {})
    vacancy_skills = vacancy_data.get("skills", []) if vacancy_data else []
    skills_match_score = calculate_skills_match_score(candidate_skills, vacancy_skills)
    
    # Calculate total
    total_result = calculate_total_score(
        algo_score=algo_score,
        practice_score=practice_score,
        theory_score=theory_score,
        soft_score=soft_score,
        skills_match_score=skills_match_score,
        weights=weights,
        cheat=cheat
    )
    
    # Determine decision
    decision = determine_decision(
        total_score=total_result["adjusted_score"],
        thresholds=thresholds,
        cheat=cheat
    )
    
    return {
        "scores": total_result,
        "decision": decision,
        "breakdown": {
            "tasks": [
                {
                    "title": t.get("title", "Task"),
                    "score": t.get("score", 0),
                    "difficulty": t.get("difficulty"),
                    "hints_used": t.get("hints_used", 0)
                }
                for t in tasks
            ],
            "theory": [
                {
                    "question": a.get("question_text", "")[:100],
                    "score": a.get("score", 0)
                }
                for a in theory_answers
            ]
        },
        "cheat_report": {
            "signals": cheat_raw,
            "penalty_applied": total_result["cheat_penalty"],
            "auto_rejected": decision["auto_rejected"],
            "grade_capped": decision["capped"]
        },
        "recommendations": generate_recommendations(
            grade=decision["grade"],
            component_scores=total_result["component_scores"],
            cheat=cheat
        )
    }


def generate_recommendations(
    grade: str,
    component_scores: Dict[str, float],
    cheat: CheatSignals
) -> List[str]:
    """Generate personalized recommendations for improvement."""
    recommendations = []
    
    # Find weak areas
    weakest = min(component_scores.items(), key=lambda x: x[1])
    
    if weakest[0] == "algo" and weakest[1] < 60:
        recommendations.append("Рекомендуем прокачать навыки алгоритмов на LeetCode или Codeforces")
    
    if weakest[0] == "theory" and weakest[1] < 60:
        recommendations.append("Стоит углубить теоретические знания в выбранном направлении")
    
    if weakest[0] == "practice" and weakest[1] < 60:
        recommendations.append("Больше практики в реальных проектах")
    
    # Grade-specific
    if grade in ["intern", "junior"]:
        recommendations.append("Фокус на базовых алгоритмах и структурах данных")
    elif grade in ["junior+", "middle"]:
        recommendations.append("Изучение паттернов проектирования и архитектуры")
    elif grade in ["middle+", "senior"]:
        recommendations.append("Развитие навыков system design и лидерства")
    
    # Cheat warnings
    if cheat.ai_style_score > 0.3:
        recommendations.append("Рекомендуем писать код самостоятельно без помощи AI")
    
    return recommendations[:5]  # Max 5 recommendations



# пидормот
