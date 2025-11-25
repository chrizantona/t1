"""
Interview API endpoints.
Main endpoints for conducting interviews.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.db import get_db
from ..models.interview import Interview, Task, Submission, ChatMessage, Hint
from ..schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    TaskResponse,
    SubmissionCreate,
    SubmissionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    HintRequest,
    HintResponse,
    FinalReportResponse
)
from ..services.scibox_client import scibox_client
from ..services.adaptive import generate_first_task, generate_next_task as adaptive_generate_next_task
from ..services.code_runner import run_code
from ..services.anti_cheat import calculate_trust_score
from ..services.reporting import generate_final_report
from ..services.grading_service import calculate_start_grade, calculate_final_grade_for_interview
from ..services.task_pool import generate_or_select_task
from ..adaptive.engine import DifficultyLevel

router = APIRouter()


@router.post("/start", response_model=InterviewResponse)
async def start_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_db)
):
    """
    Start a new interview session.
    Creates interview and generates first task using LLM.
    """
    # Create interview
    interview = Interview(
        candidate_name=interview_data.candidate_name,
        candidate_email=interview_data.candidate_email,
        selected_level=interview_data.selected_level,
        direction=interview_data.direction,
        cv_text=interview_data.cv_text,
        status="in_progress"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Generate first task using LLM
    try:
        task = await generate_first_task(
            interview_id=interview.id,
            level=interview.selected_level,
            direction=interview.direction,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate task: {str(e)}")
    
    return interview


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(interview_id: int, db: Session = Depends(get_db)):
    """Get interview details."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.get("/{interview_id}/tasks", response_model=List[TaskResponse])
async def get_interview_tasks(interview_id: int, db: Session = Depends(get_db)):
    """Get all tasks for an interview."""
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get specific task details."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/submit", response_model=SubmissionResponse)
async def submit_code(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit code for a task.
    Runs tests and stores results.
    """
    task = db.query(Task).filter(Task.id == submission_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Run code against test cases
    try:
        result = run_code(
            code=submission_data.code,
            language=submission_data.language,
            visible_tests=task.visible_tests,
            hidden_tests=task.hidden_tests
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")
    
    # Calculate score for this submission
    from ..services.adaptive import calculate_task_score
    score = calculate_task_score(
        passed_visible=result["passed_visible"],
        total_visible=result["total_visible"],
        passed_hidden=result["passed_hidden"],
        total_hidden=result["total_hidden"],
        execution_time_ms=result.get("execution_time_ms"),
        max_score=task.max_score
    )
    
    # Create submission record
    submission = Submission(
        task_id=task.id,
        code=submission_data.code,
        language=submission_data.language,
        passed_visible=result["passed_visible"],
        total_visible=result["total_visible"],
        passed_hidden=result["passed_hidden"],
        total_hidden=result["total_hidden"],
        execution_time_ms=result.get("execution_time_ms"),
        error_message=result.get("error_message")
    )
    db.add(submission)
    
    # Update task with actual score if this is the best submission
    if task.actual_score is None or score > task.actual_score:
        task.actual_score = score
        if result["passed_visible"] == result["total_visible"] and result["passed_hidden"] == result["total_hidden"]:
            task.status = "completed"
    
    db.commit()
    db.refresh(submission)
    
    return submission


@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """
    Send message to AI interviewer and get response.
    """
    interview = db.query(Interview).filter(Interview.id == message_data.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Save user message
    user_message = ChatMessage(
        interview_id=message_data.interview_id,
        role="user",
        content=message_data.content,
        task_id=message_data.task_id
    )
    db.add(user_message)
    db.commit()
    
    # Get conversation history
    messages = db.query(ChatMessage).filter(
        ChatMessage.interview_id == message_data.interview_id
    ).order_by(ChatMessage.created_at).limit(10).all()
    
    # Build messages for LLM
    llm_messages = [
        {"role": "system", "content": "Ты опытный технический интервьюер. Задавай вопросы о подходе, сложности, граничных случаях. Будь дружелюбным и конструктивным."}
    ]
    for msg in messages:
        llm_messages.append({"role": msg.role, "content": msg.content})
    
    # Get AI response
    try:
        ai_response = await scibox_client.chat_completion(llm_messages, temperature=0.7, max_tokens=512)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response failed: {str(e)}")
    
    # Save AI message
    ai_message = ChatMessage(
        interview_id=message_data.interview_id,
        role="assistant",
        content=ai_response,
        task_id=message_data.task_id
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return ai_message


@router.post("/hint", response_model=HintResponse)
async def request_hint(
    hint_data: HintRequest,
    db: Session = Depends(get_db)
):
    """
    Request hint for current task.
    Applies score penalty based on hint level.
    """
    task = db.query(Task).filter(Task.id == hint_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Determine penalty
    penalties = {"light": 10, "medium": 20, "heavy": 35}
    penalty = penalties.get(hint_data.hint_level, 10)
    
    # Generate hint using LLM
    messages = [
        {"role": "system", "content": f"Дай {hint_data.hint_level} подсказку для задачи."},
        {"role": "user", "content": f"Задача: {task.description}\n\nТекущий код:\n{hint_data.current_code or 'Нет кода'}"}
    ]
    
    try:
        hint_content = await scibox_client.chat_completion(messages, temperature=0.5, max_tokens=256)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hint generation failed: {str(e)}")
    
    # Apply penalty
    task.max_score -= penalty
    
    # Save hint
    hint = Hint(
        task_id=task.id,
        hint_level=hint_data.hint_level,
        hint_content=hint_content,
        score_penalty=penalty
    )
    db.add(hint)
    db.commit()
    
    return HintResponse(
        hint_content=hint_content,
        score_penalty=penalty,
        new_max_score=task.max_score
    )


@router.get("/{interview_id}/report", response_model=FinalReportResponse)
async def get_final_report(interview_id: int, db: Session = Depends(get_db)):
    """
    Generate and return final interview report.
    Uses deterministic grading logic + LLM for skill assessment.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    try:
        # Calculate deterministic grade
        grade_data = calculate_final_grade_for_interview(interview_id, db)
        
        # Generate LLM-based skill assessment
        report = await generate_final_report(interview_id, db)
        
        # Merge deterministic grade with LLM report
        # The deterministic grade takes precedence
        if hasattr(report, 'interview'):
            report.interview.overall_grade = grade_data['final_grade']
            report.interview.overall_score = grade_data['overall_score']
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/{interview_id}/complete")
async def complete_interview(interview_id: int, db: Session = Depends(get_db)):
    """Mark interview as completed."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview.status = "completed"
    from datetime import datetime
    interview.completed_at = datetime.utcnow()
    db.commit()
    
    return {"status": "completed", "interview_id": interview_id}


@router.post("/{interview_id}/next-task", response_model=TaskResponse)
async def generate_next_task(interview_id: int, db: Session = Depends(get_db)):
    """
    Generate next adaptive task based on previous performance.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Get previous tasks to calculate performance
    previous_tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    
    if not previous_tasks:
        # If no previous tasks, generate first one
        task = await generate_first_task(interview_id, interview.selected_level, interview.direction, db)
    else:
        # Calculate average performance
        completed_tasks = [t for t in previous_tasks if t.actual_score is not None]
        if completed_tasks:
            avg_score = sum([t.actual_score for t in completed_tasks]) / len(completed_tasks)
        else:
            avg_score = 50  # Default if no completed tasks
        
        # Generate next task based on performance
        task = await adaptive_generate_next_task(
            interview_id=interview_id,
            previous_performance=avg_score,
            current_level=interview.selected_level,
            direction=interview.direction,
            db=db
        )
    
    return task

