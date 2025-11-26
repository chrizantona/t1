"""
Reporting service.
Generates final interview reports with skill assessments.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from ..models.interview import Interview, Task, Submission, Hint, SkillAssessment
from ..schemas.interview import FinalReportResponse, SkillScore, SkillAssessmentResponse
from .scibox_client import scibox_client
from .anti_cheat import calculate_trust_score


async def generate_skill_assessment(interview_id: int, db: Session) -> SkillAssessmentResponse:
    """
    Generate skill assessment using LLM analysis.
    Killer feature #2: Skill Radar Chart.
    
    Args:
        interview_id: Interview ID
        db: Database session
    
    Returns:
        Skill assessment with radar data
    """
    # Check if assessment already exists
    existing_assessment = db.query(SkillAssessment).filter(
        SkillAssessment.interview_id == interview_id
    ).first()
    
    if existing_assessment:
        # Return existing assessment
        return SkillAssessmentResponse(
            algorithms=SkillScore(score=existing_assessment.algorithms_score, comment=existing_assessment.algorithms_comment),
            architecture=SkillScore(score=existing_assessment.architecture_score, comment=existing_assessment.architecture_comment),
            clean_code=SkillScore(score=existing_assessment.clean_code_score, comment=existing_assessment.clean_code_comment),
            debugging=SkillScore(score=existing_assessment.debugging_score, comment=existing_assessment.debugging_comment),
            communication=SkillScore(score=existing_assessment.communication_score, comment=existing_assessment.communication_comment),
            next_grade_tips=existing_assessment.next_grade_tips or []
        )
    
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    
    # Gather metrics
    metrics = {
        "total_tasks": len(tasks),
        "completed_tasks": len([t for t in tasks if t.status == "completed"]),
        "average_score": sum([t.actual_score or 0 for t in tasks]) / len(tasks) if tasks else 0,
        "hints_used": sum([len(t.hints) for t in tasks]),
        "total_submissions": sum([len(t.submissions) for t in tasks])
    }
    
    # Get code samples
    code_samples = []
    for task in tasks[:3]:  # First 3 tasks
        if task.submissions:
            latest = task.submissions[-1]
            code_samples.append({
                "task": task.title,
                "code": latest.code[:500]  # First 500 chars
            })
    
    # Prompt for skill assessment
    system_prompt = """/no_think
Ты эксперт по оценке навыков разработчиков.
Проанализируй результаты интервью и верни JSON с полями:
- algorithms_score: 0-100
- algorithms_comment: краткий комментарий (до 100 символов)
- architecture_score: 0-100
- architecture_comment: краткий комментарий (до 100 символов)
- clean_code_score: 0-100
- clean_code_comment: краткий комментарий (до 100 символов)
- debugging_score: 0-100
- debugging_comment: краткий комментарий (до 100 символов)
- communication_score: 0-100
- communication_comment: краткий комментарий (до 100 символов)
- next_grade_tips: список из 3 советов для роста (каждый до 100 символов)

Отвечай ТОЛЬКО валидным JSON без markdown."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Метрики: {json.dumps(metrics, ensure_ascii=False)}\n\nПримеры кода: {json.dumps(code_samples, ensure_ascii=False)}"}
    ]
    
    try:
        response = await scibox_client.chat_completion(messages, temperature=0.3, max_tokens=1024)
        
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        assessment_data = json.loads(response.strip())
    except:
        # Fallback assessment
        assessment_data = {
            "algorithms_score": 70,
            "algorithms_comment": "Хорошо решает типовые задачи",
            "architecture_score": 65,
            "architecture_comment": "Базовое понимание архитектуры",
            "clean_code_score": 70,
            "clean_code_comment": "Код читаемый",
            "debugging_score": 60,
            "debugging_comment": "Требуется практика",
            "communication_score": 75,
            "communication_comment": "Хорошо объясняет решения",
            "next_grade_tips": [
                "Больше практики с алгоритмами",
                "Изучить паттерны проектирования",
                "Улучшить навыки отладки"
            ]
        }
    
    # Save to database
    skill_assessment = SkillAssessment(
        interview_id=interview_id,
        algorithms_score=assessment_data.get("algorithms_score", 70),
        algorithms_comment=assessment_data.get("algorithms_comment", ""),
        architecture_score=assessment_data.get("architecture_score", 65),
        architecture_comment=assessment_data.get("architecture_comment", ""),
        clean_code_score=assessment_data.get("clean_code_score", 70),
        clean_code_comment=assessment_data.get("clean_code_comment", ""),
        debugging_score=assessment_data.get("debugging_score", 60),
        debugging_comment=assessment_data.get("debugging_comment", ""),
        communication_score=assessment_data.get("communication_score", 75),
        communication_comment=assessment_data.get("communication_comment", ""),
        next_grade_tips=assessment_data.get("next_grade_tips", [])
    )
    db.add(skill_assessment)
    db.commit()
    
    return SkillAssessmentResponse(
        algorithms=SkillScore(score=skill_assessment.algorithms_score, comment=skill_assessment.algorithms_comment),
        architecture=SkillScore(score=skill_assessment.architecture_score, comment=skill_assessment.architecture_comment),
        clean_code=SkillScore(score=skill_assessment.clean_code_score, comment=skill_assessment.clean_code_comment),
        debugging=SkillScore(score=skill_assessment.debugging_score, comment=skill_assessment.debugging_comment),
        communication=SkillScore(score=skill_assessment.communication_score, comment=skill_assessment.communication_comment),
        next_grade_tips=skill_assessment.next_grade_tips or []
    )


async def generate_final_report(interview_id: int, db: Session) -> FinalReportResponse:
    """
    Generate complete final report.
    
    Args:
        interview_id: Interview ID
        db: Database session
    
    Returns:
        Complete report
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    
    # Calculate trust score using advanced system
    from .anti_cheat_advanced import calculate_full_trust_score
    trust_data = await calculate_full_trust_score(interview_id, db)
    interview.trust_score = trust_data["trust_score"]
    
    # Generate skill assessment if not exists
    skill_assessment = await generate_skill_assessment(interview_id, db)
    
    # Calculate overall score
    avg_skill = (
        skill_assessment.algorithms.score +
        skill_assessment.architecture.score +
        skill_assessment.clean_code.score +
        skill_assessment.debugging.score +
        skill_assessment.communication.score
    ) / 5
    
    interview.overall_score = avg_skill
    
    # Determine grade
    if avg_skill >= 85:
        interview.overall_grade = "senior"
    elif avg_skill >= 70:
        interview.overall_grade = "middle+"
    elif avg_skill >= 55:
        interview.overall_grade = "middle"
    else:
        interview.overall_grade = "junior"
    
    db.commit()
    
    # Calculate statistics
    total_hints = sum([len(task.hints) for task in tasks])
    total_submissions = sum([len(task.submissions) for task in tasks])
    
    from ..schemas.interview import InterviewResponse, TaskResponse
    
    return FinalReportResponse(
        interview=InterviewResponse.from_orm(interview),
        tasks=[TaskResponse.from_orm(task) for task in tasks],
        skill_assessment=skill_assessment,
        total_hints_used=total_hints,
        total_submissions=total_submissions,
        average_task_time=None  # TODO: calculate from timestamps
    )

