"""
Interview API endpoints.
Main endpoints for conducting interviews.
V2: New interview flow with 3 tasks + theory questions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.db import get_db
from ..models.interview import Interview, Task, Submission, ChatMessage, Hint, TheoryAnswer, SolutionFollowup
from ..schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    InterviewResponseV2,
    TaskResponse,
    TaskResponseV2,
    AllTasksResponse,
    SubmissionCreate,
    SubmissionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    HintRequest,
    HintResponse,
    FinalReportResponse,
    StageTransitionRequest,
    StageTransitionResponse,
    TheoryQuestionResponse,
    TheoryAnswerSubmit,
    TheoryAnswerEvaluation,
    TheoryAnswerResponse,
    InterviewProgressResponse,
    FinalScoresResponse,
    TaskWithOpeningQuestion,
    InitialChatMessage
)
from ..services.scibox_client import scibox_client
from ..services.adaptive import generate_first_task, generate_next_task as adaptive_generate_next_task
from ..services.code_runner import run_code
from ..services.anti_cheat import calculate_trust_score
from ..services.reporting import generate_final_report
from ..services.grading_service import calculate_start_grade, calculate_final_grade_for_interview
from ..services.interview_flow import (
    create_interview_tasks,
    generate_adaptive_task,
    generate_solution_questions,
    get_next_theory_question,
    evaluate_theory_answer,
    generate_final_scores
)
from ..adaptive.engine import DifficultyLevel

router = APIRouter()


@router.post("/start", response_model=InterviewResponse)
async def start_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_db)
):
    """
    Start a new interview session.
    Creates interview and generates FIRST task only (adaptive flow).
    """
    # Extract years of experience from CV if available
    years_exp = None
    if interview_data.cv_text:
        try:
            from ..api.resume import scibox_client as resume_client
            cv_analysis = await resume_client.analyze_resume(interview_data.cv_text)
            years_exp = cv_analysis.get("years_of_experience", None)
        except:
            pass
    
    # If no CV or failed to extract, use default based on level
    if years_exp is None:
        level_to_years = {
            "intern": 0.5,
            "junior": 1.0,
            "middle": 2.5,
            "senior": 5.0
        }
        years_exp = level_to_years.get(interview_data.selected_level, 2.5)
    
    # Determine starting difficulty based on level
    level_to_difficulty = {
        "intern": "easy",
        "junior": "easy", 
        "middle": "medium",
        "senior": "hard"
    }
    start_difficulty = level_to_difficulty.get(interview_data.selected_level, "medium")
    
    # Create interview
    # Note: vacancy_id is string from pool, not DB FK - store separately if needed
    interview = Interview(
        candidate_name=interview_data.candidate_name,
        candidate_email=interview_data.candidate_email,
        selected_level=interview_data.selected_level,
        direction=interview_data.direction,
        cv_text=interview_data.cv_text,
        years_of_experience=years_exp,
        status="in_progress",
        current_stage="coding",
        effective_level=interview_data.selected_level  # Track adaptive level
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Generate FIRST task only (adaptive: more tasks generated after solving)
    try:
        task = await generate_adaptive_task(
            interview_id=interview.id,
            direction=interview.direction,
            difficulty=start_difficulty,
            task_order=1,
            db=db
        )
        print(f"Created first task (difficulty={start_difficulty}) for interview {interview.id}")
    except Exception as e:
        print(f"Failed to generate first task: {e}")
        import traceback
        traceback.print_exc()
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


@router.post("/submit")
async def submit_code(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit code for a task.
    Runs tests and stores results with detailed test output.
    On failure: generates auto-hint and reduces max_score by 15.
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
    
    # Check if submission failed (not all visible tests passed)
    all_visible_passed = result["passed_visible"] == result["total_visible"] and result["total_visible"] > 0
    auto_hint = None
    
    # Generate auto-hint on failure and reduce max_score
    if not all_visible_passed and submission_data.code.strip():
        try:
            auto_hint = await scibox_client.generate_auto_hint_on_failure(
                task_title=task.title,
                task_description=task.description,
                visible_tests=task.visible_tests or [],
                user_code=submission_data.code,
                error_message=result.get("error_message", "")
            )
            # Reduce max_score by 15 (minimum 10)
            if task.max_score > 25:
                task.max_score = max(10, task.max_score - 15)
                print(f"⚠️ Auto-hint given, max_score reduced to {task.max_score}")
        except Exception as e:
            print(f"Failed to generate auto-hint: {e}")
            auto_hint = {
                "hint_text": "Проверь внимательно формат входных данных и ожидаемый результат.",
                "input_format_tip": "Убедись, что читаешь данные правильно.",
                "common_mistake": "Обрати внимание на граничные случаи."
            }
            # Still reduce score even if hint generation failed
            if task.max_score > 25:
                task.max_score = max(10, task.max_score - 15)
    
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
        # Task is completed if ALL visible tests pass (hidden tests are bonus)
        if all_visible_passed:
            task.status = "completed"
    
    db.commit()
    db.refresh(submission)
    
    # Return submission with test details and auto-hint if failed
    response = {
        "id": submission.id,
        "passed_visible": submission.passed_visible,
        "total_visible": submission.total_visible,
        "passed_hidden": submission.passed_hidden,
        "total_hidden": submission.total_hidden,
        "execution_time_ms": submission.execution_time_ms,
        "error_message": submission.error_message,
        "ai_likeness_score": submission.ai_likeness_score,
        "visible_test_details": result.get("visible_test_details", []),
        "max_score": task.max_score  # Return updated max_score
    }
    
    # Add auto-hint if submission failed
    if auto_hint:
        response["auto_hint"] = auto_hint
        response["score_penalty_applied"] = True
    
    return response


@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """
    💬 Send message to AI interviewer and get response.
    Uses killer prompts for natural, helpful interviewer personality.
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
    
    # Get current task context
    current_task = None
    task_title = "Текущая задача"
    task_description = "Задача не выбрана"
    user_code = ""
    
    if message_data.task_id:
        current_task = db.query(Task).filter(Task.id == message_data.task_id).first()
        if current_task:
            task_title = current_task.title
            task_description = current_task.description
            # Get latest submission code
            latest_submission = db.query(Submission).filter(
                Submission.task_id == current_task.id
            ).order_by(Submission.created_at.desc()).first()
            if latest_submission:
                user_code = latest_submission.code
    
    # Get conversation history for context
    chat_history = db.query(ChatMessage).filter(
        ChatMessage.interview_id == message_data.interview_id
    ).order_by(ChatMessage.created_at).limit(10).all()
    
    history_for_llm = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_history
    ]
    
    # Get AI response using killer prompts
    try:
        ai_response = await scibox_client.chat_with_interviewer(
            task_text=task_description,
            level=interview.selected_level or "middle",
            direction=interview.direction or "backend",
            task_title=task_title,
            user_code=user_code,
            user_message=message_data.content,
            chat_history=history_for_llm
        )
        
        # Clean response - remove ALL <think> tags and their content
        import re
        ai_response = re.sub(r'<think>.*?</think>', '', ai_response, flags=re.DOTALL).strip()
        ai_response = re.sub(r'</?think>', '', ai_response).strip()
        
        if not ai_response:
            ai_response = "Интересный вопрос! Давай разберёмся вместе. 🤔"
            
    except Exception as e:
        print(f"❌ AI chat error: {e}")
        ai_response = "Хороший вопрос! Давай подумаем над этим. 💡"
    
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
    💡 Request hint for current task.
    Uses killer prompts for helpful, progressive hints.
    """
    task = db.query(Task).filter(Task.id == hint_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Penalty based on hint level
    penalties = {"light": 10, "medium": 25, "heavy": 40}
    penalty = penalties.get(hint_data.hint_level, 10)
    
    # Get test results summary
    latest_submission = db.query(Submission).filter(
        Submission.task_id == task.id
    ).order_by(Submission.created_at.desc()).first()
    
    test_results = "Тесты еще не запускались"
    if latest_submission:
        test_results = (
            f"Видимые: {latest_submission.passed_visible or 0}/{latest_submission.total_visible or 0}, "
            f"Скрытые: {latest_submission.passed_hidden or 0}/{latest_submission.total_hidden or 0}"
        )
        if latest_submission.error_message:
            test_results += f"\nОшибка: {latest_submission.error_message}"
    
    try:
        # Use killer hint prompts
        hint_result = await scibox_client.generate_hint(
            task_text=task.description,
            user_code=hint_data.current_code or "# Код пока не написан",
            test_results=test_results,
            hint_level=hint_data.hint_level
        )
        
        # Extract hint text with encouragement
        hint_text = hint_result.get("hint_text", "Попробуй начать с базового случая.")
        encouragement = hint_result.get("encouragement", "")
        next_step = hint_result.get("next_step", "")
        
        # Build rich hint content
        hint_content = hint_text
        if encouragement:
            hint_content = f"{encouragement}\n\n{hint_content}"
        if next_step:
            hint_content += f"\n\n💡 Следующий шаг: {next_step}"
        
        import re
        hint_content = re.sub(r'<think>.*?</think>', '', hint_content, flags=re.DOTALL).strip()
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
    import traceback
    import logging
    logger = logging.getLogger(__name__)
    
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    try:
        logger.info(f"🔍 Generating report for interview {interview_id}")
        
        # Calculate deterministic grade
        logger.info("📊 Calculating grade...")
        grade_data = calculate_final_grade_for_interview(interview_id, db)
        logger.info(f"✅ Grade calculated: {grade_data.get('final_grade')}")
        
        # Generate LLM-based skill assessment
        logger.info("🤖 Generating skill assessment...")
        report = await generate_final_report(interview_id, db)
        logger.info("✅ Skill assessment generated")
        
        # Merge deterministic grade with LLM report
        # The deterministic grade takes precedence
        if hasattr(report, 'interview'):
            report.interview.overall_grade = grade_data['final_grade']
            report.interview.overall_score = grade_data['overall_score']
        
        logger.info("✅ Report ready to return")
        return report
    except Exception as e:
        logger.error(f"❌ Report generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
    Generate next ADAPTIVE task based on previous performance.
    This is the core of real-time task generation.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Get previous tasks
    previous_tasks = db.query(Task).filter(
        Task.interview_id == interview_id
    ).order_by(Task.task_order).all()
    
    # Max 3 tasks per interview
    if len(previous_tasks) >= 3:
        raise HTTPException(status_code=400, detail="Maximum tasks reached. Complete the interview.")
    
    # Calculate next difficulty based on performance
    next_order = len(previous_tasks) + 1
    
    if not previous_tasks:
        # First task - use level-based difficulty
        level_to_difficulty = {
            "intern": "easy",
            "junior": "easy",
            "middle": "medium",
            "senior": "hard"
        }
        next_difficulty = level_to_difficulty.get(interview.selected_level, "medium")
    else:
        # Calculate average performance from completed tasks
        completed = [t for t in previous_tasks if t.actual_score is not None and t.actual_score > 0]
        
        if completed:
            avg_score = sum(t.actual_score for t in completed) / len(completed)
            last_difficulty = previous_tasks[-1].difficulty
            
            # Adaptive logic: increase difficulty if score > 70, decrease if < 40
            difficulty_order = ["easy", "medium", "hard"]
            current_idx = difficulty_order.index(last_difficulty) if last_difficulty in difficulty_order else 1
            
            if avg_score >= 70:
                # Good performance - increase difficulty
                next_idx = min(current_idx + 1, 2)
                # Update effective level if upgraded
                if next_idx > current_idx:
                    levels = ["intern", "junior", "middle", "senior"]
                    current_level_idx = levels.index(interview.effective_level or interview.selected_level)
                    if current_level_idx < len(levels) - 1:
                        interview.effective_level = levels[current_level_idx + 1]
                        db.commit()
            elif avg_score < 40:
                # Poor performance - decrease difficulty
                next_idx = max(current_idx - 1, 0)
            else:
                # Keep same difficulty
                next_idx = current_idx
            
            next_difficulty = difficulty_order[next_idx]
        else:
            # No completed tasks yet, use medium
            next_difficulty = "medium"
    
    # Generate the new task with generation_meta and opening question
    task = await generate_adaptive_task(
        interview_id=interview_id,
        direction=interview.direction,
        difficulty=next_difficulty,
        task_order=next_order,
        db=db,
        generate_opening_question=True
    )
    
    print(f"Generated adaptive task #{next_order} (difficulty={next_difficulty}) for interview {interview_id}")
    return task


@router.post("/{interview_id}/next-task/with-meta")
async def generate_next_task_with_meta(interview_id: int, db: Session = Depends(get_db)):
    """
    Generate next ADAPTIVE task with full metadata and opening question.
    Returns task, generation_meta, and initial chat messages.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Get previous tasks
    previous_tasks = db.query(Task).filter(
        Task.interview_id == interview_id
    ).order_by(Task.task_order).all()
    
    # Max 3 tasks per interview
    if len(previous_tasks) >= 3:
        raise HTTPException(status_code=400, detail="Maximum tasks reached. Complete the interview.")
    
    # Calculate next difficulty
    next_order = len(previous_tasks) + 1
    
    if not previous_tasks:
        level_to_difficulty = {
            "intern": "easy",
            "junior": "easy",
            "middle": "medium",
            "senior": "hard"
        }
        next_difficulty = level_to_difficulty.get(interview.selected_level, "medium")
    else:
        completed = [t for t in previous_tasks if t.actual_score is not None and t.actual_score > 0]
        
        if completed:
            avg_score = sum(t.actual_score for t in completed) / len(completed)
            last_difficulty = previous_tasks[-1].difficulty
            difficulty_order = ["easy", "medium", "hard"]
            current_idx = difficulty_order.index(last_difficulty) if last_difficulty in difficulty_order else 1
            
            if avg_score >= 70:
                next_idx = min(current_idx + 1, 2)
            elif avg_score < 40:
                next_idx = max(current_idx - 1, 0)
            else:
                next_idx = current_idx
            
            next_difficulty = difficulty_order[next_idx]
        else:
            next_difficulty = "medium"
    
    # Generate the new task
    task = await generate_adaptive_task(
        interview_id=interview_id,
        direction=interview.direction,
        difficulty=next_difficulty,
        task_order=next_order,
        db=db,
        generate_opening_question=True
    )
    
    # Get initial messages (opening question)
    initial_messages = db.query(ChatMessage).filter(
        ChatMessage.interview_id == interview_id,
        ChatMessage.task_id == task.id,
        ChatMessage.role == "assistant"
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "task": TaskResponseV2.model_validate(task),
        "generation_meta": task.generation_meta or {},
        "initial_messages": [
            {
                "sender_type": "bot",
                "sender_name": "VibeCode AI",
                "message_text": msg.content
            }
            for msg in initial_messages
        ]
    }


@router.get("/{interview_id}/tasks/{task_id}/chat-messages")
async def get_task_chat_messages(
    interview_id: int, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get all chat messages for a specific task (including opening question).
    """
    import re
    messages = db.query(ChatMessage).filter(
        ChatMessage.interview_id == interview_id,
        ChatMessage.task_id == task_id
    ).order_by(ChatMessage.created_at).all()
    
    def clean_think_tags(text: str) -> str:
        """Remove <think> tags from text."""
        if not text:
            return text
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        text = re.sub(r'</?think>', '', text).strip()
        return text
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": clean_think_tags(msg.content),
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]


# ============ Solution Follow-up Endpoints ============

@router.post("/tasks/{task_id}/solution-followup")
async def get_solution_followup_question(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a follow-up question about candidate's solution after task completion.
    Called after successful code submission.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    interview = db.query(Interview).filter(Interview.id == task.interview_id).first()
    
    # Check if there's already a pending followup question
    existing = db.query(SolutionFollowup).filter(
        SolutionFollowup.task_id == task_id,
        SolutionFollowup.status == "pending"
    ).first()
    
    if existing:
        return {
            "followup_id": existing.id,
            "question": existing.question_text,
            "status": "pending"
        }
    
    # Get best submission code
    best_submission = db.query(Submission).filter(
        Submission.task_id == task_id
    ).order_by(Submission.passed_visible.desc(), Submission.passed_hidden.desc()).first()
    
    if not best_submission:
        raise HTTPException(status_code=400, detail="No submission found for this task")
    
    # Generate follow-up question
    try:
        question = await scibox_client.generate_solution_followup_question(
            task_title=task.title,
            task_description=task.description,
            candidate_code=best_submission.code,
            candidate_level=interview.selected_level if interview else "middle",
            difficulty=task.difficulty
        )
    except Exception as e:
        print(f"Failed to generate followup question: {e}")
        question = "🤔 Какова временная и пространственная сложность твоего решения?"
    
    # Save followup question
    followup = SolutionFollowup(
        interview_id=task.interview_id,
        task_id=task_id,
        question_text=question,
        question_type="complexity",
        status="pending"
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)
    
    # Also add as chat message
    chat_message = ChatMessage(
        interview_id=task.interview_id,
        role="assistant",
        content=question,
        task_id=task_id
    )
    db.add(chat_message)
    db.commit()
    
    return {
        "followup_id": followup.id,
        "question": question,
        "status": "pending"
    }


@router.post("/solution-followup/{followup_id}/answer")
async def submit_solution_followup_answer(
    followup_id: int,
    answer_text: str,
    db: Session = Depends(get_db)
):
    """
    Submit answer to a solution follow-up question.
    Evaluates the answer and updates the task score.
    """
    from pydantic import BaseModel
    
    followup = db.query(SolutionFollowup).filter(SolutionFollowup.id == followup_id).first()
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up question not found")
    
    if followup.status != "pending":
        raise HTTPException(status_code=400, detail="Question already answered")
    
    task = db.query(Task).filter(Task.id == followup.task_id).first()
    interview = db.query(Interview).filter(Interview.id == followup.interview_id).first()
    
    # Get best submission code
    best_submission = db.query(Submission).filter(
        Submission.task_id == followup.task_id
    ).order_by(Submission.passed_visible.desc()).first()
    
    candidate_code = best_submission.code if best_submission else ""
    
    # Evaluate answer
    try:
        evaluation = await scibox_client.evaluate_solution_answer(
            task_title=task.title,
            candidate_code=candidate_code,
            question=followup.question_text,
            candidate_answer=answer_text,
            candidate_level=interview.selected_level if interview else "middle"
        )
    except Exception as e:
        print(f"Failed to evaluate answer: {e}")
        evaluation = {
            "score": 50,
            "feedback": "Ответ учтён.",
            "correct_answer": None
        }
    
    # Update followup record
    from datetime import datetime
    followup.candidate_answer = answer_text
    followup.score = evaluation.get("score", 50)
    followup.correctness = evaluation.get("correctness")
    followup.completeness = evaluation.get("completeness")
    followup.understanding = evaluation.get("understanding")
    followup.feedback = evaluation.get("feedback")
    followup.correct_answer = evaluation.get("correct_answer")
    followup.status = "answered"
    followup.answered_at = datetime.utcnow()
    
    # Update task score: 70% code + 30% followup answer
    # Code score is based on tests passed (stored in task.actual_score before followup)
    code_score = task.actual_score if task.actual_score is not None else 0
    followup_score = evaluation.get("score", 50)  # 0-100
    
    # Calculate weighted total: 70% code + 30% followup
    # Both scores are normalized to max_score
    max_score = task.max_score or 100
    code_weight = 0.7
    followup_weight = 0.3
    
    # Code score is already scaled to max_score, normalize to 0-100
    code_normalized = (code_score / max_score) * 100 if max_score > 0 else 0
    
    # Calculate final score
    final_score = (code_normalized * code_weight + followup_score * followup_weight) * (max_score / 100)
    task.actual_score = max(0, min(max_score, final_score))
    
    # Save candidate answer as chat message
    user_message = ChatMessage(
        interview_id=followup.interview_id,
        role="user",
        content=answer_text,
        task_id=followup.task_id
    )
    db.add(user_message)
    
    # Add feedback as bot response
    feedback_content = evaluation.get("feedback", "Ответ учтён.")
    if evaluation.get("correct_answer"):
        feedback_content += f"\n\n📚 Правильный ответ: {evaluation['correct_answer']}"
    
    bot_response = ChatMessage(
        interview_id=followup.interview_id,
        role="assistant",
        content=feedback_content,
        task_id=followup.task_id
    )
    db.add(bot_response)
    
    db.commit()
    
    return {
        "followup_id": followup_id,
        "score": followup.score,
        "feedback": followup.feedback,
        "correct_answer": followup.correct_answer,
        "task_score_updated": task.actual_score
    }


@router.get("/tasks/{task_id}/solution-followup")
async def get_task_solution_followup(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Get solution follow-up question for a task if exists.
    """
    followup = db.query(SolutionFollowup).filter(
        SolutionFollowup.task_id == task_id
    ).order_by(SolutionFollowup.created_at.desc()).first()
    
    if not followup:
        return None
    
    import re
    def clean_think_tags(text: str) -> str:
        if not text:
            return text
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        text = re.sub(r'</?think>', '', text).strip()
        return text
    
    return {
        "followup_id": followup.id,
        "question": clean_think_tags(followup.question_text),
        "status": followup.status,
        "score": followup.score,
        "feedback": clean_think_tags(followup.feedback) if followup.feedback else None,
        "correct_answer": followup.correct_answer
    }


@router.post("/submit/enhanced")
async def submit_code_with_edge_cases(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit code with enhanced AI-powered edge case testing.
    1. Validates code security (anti prompt injection)
    2. Runs regular tests
    3. Generates AI edge case tests
    4. Runs edge case tests
    5. Returns comprehensive results
    """
    from ..services.code_runner import run_edge_case_tests, validate_code_safety
    
    task = db.query(Task).filter(Task.id == submission_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Step 1: Security validation
    security_check = validate_code_safety(submission_data.code)
    
    if security_check["risk_level"] == "high":
        return {
            "security_blocked": True,
            "security_report": security_check,
            "message": "Код заблокирован по соображениям безопасности",
            "submission": None,
            "edge_case_results": None
        }
    
    # Step 2: Run regular tests
    try:
        result = run_code(
            code=submission_data.code,
            language=submission_data.language,
            visible_tests=task.visible_tests,
            hidden_tests=task.hidden_tests
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")
    
    # Step 3: Generate AI edge case tests
    try:
        # Prepare existing tests summary
        existing_tests_summary = []
        for t in task.visible_tests[:3]:  # First 3 visible tests
            existing_tests_summary.append(f"Input: {t.get('input')}, Output: {t.get('expected_output')}")
        
        edge_case_response = await scibox_client.generate_edge_case_tests_enhanced(
            task_description=task.description,
            input_format=task.input_format or "Не указан",
            output_format=task.output_format or "Не указан",
            examples="\n".join(existing_tests_summary),
            candidate_code=submission_data.code,
            existing_tests="\n".join(existing_tests_summary)
        )
    except Exception as e:
        edge_case_response = {
            "security_blocked": False,
            "analysis": {"error": str(e)},
            "edge_case_tests": []
        }
    
    # Step 4: Run edge case tests if generated
    edge_case_results = None
    if not edge_case_response.get("security_blocked") and edge_case_response.get("edge_case_tests"):
        try:
            edge_case_results = run_edge_case_tests(
                code=submission_data.code,
                language=submission_data.language,
                edge_case_tests=edge_case_response["edge_case_tests"]
            )
        except Exception as e:
            edge_case_results = {"error": str(e)}
    
    # Step 5: Calculate score
    from ..services.adaptive import calculate_task_score
    score = calculate_task_score(
        passed_visible=result["passed_visible"],
        total_visible=result["total_visible"],
        passed_hidden=result["passed_hidden"],
        total_hidden=result["total_hidden"],
        execution_time_ms=result.get("execution_time_ms"),
        max_score=task.max_score
    )
    
    # Apply edge case penalty if tests failed
    edge_case_penalty = 0
    if edge_case_results and not edge_case_results.get("error"):
        failed_edge_cases = edge_case_results.get("failed", 0)
        if failed_edge_cases > 0:
            edge_case_penalty = min(15, failed_edge_cases * 5)  # Max 15 points penalty
            score = max(0, score - edge_case_penalty)
    
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
    
    # Update task score
    if task.actual_score is None or score > task.actual_score:
        task.actual_score = score
        # Task is completed if ALL visible tests pass (hidden tests are bonus)
        if result["passed_visible"] == result["total_visible"] and result["total_visible"] > 0:
            task.status = "completed"
    
    db.commit()
    db.refresh(submission)
    
    return {
        "security_blocked": False,
        "security_report": security_check,
        "submission": {
            "id": submission.id,
            "passed_visible": submission.passed_visible,
            "total_visible": submission.total_visible,
            "passed_hidden": submission.passed_hidden,
            "total_hidden": submission.total_hidden,
            "execution_time_ms": submission.execution_time_ms,
            "error_message": submission.error_message,
            "score": score,
            "edge_case_penalty": edge_case_penalty
        },
        "edge_case_analysis": edge_case_response.get("analysis"),
        "edge_case_results": edge_case_results,
        "ai_generated_tests": edge_case_response.get("edge_case_tests", [])
    }


# ============ V2 Interview Flow Endpoints ============

@router.post("/v2/start", response_model=InterviewResponseV2)
async def start_interview_v2(
    interview_data: InterviewCreate,
    db: Session = Depends(get_db)
):
    """
    Start new interview with V2 flow.
    Creates interview and generates all 3 tasks at once.
    """
    # Extract years of experience from CV if available
    years_exp = None
    if interview_data.cv_text:
        try:
            from ..api.resume import scibox_client as resume_client
            cv_analysis = await resume_client.analyze_resume(interview_data.cv_text)
            years_exp = cv_analysis.get("years_of_experience", None)
        except:
            pass
    
    # If no CV or failed to extract, use default based on level
    if years_exp is None:
        level_to_years = {
            "intern": 0.5,
            "junior": 1.0,
            "junior+": 1.5,
            "middle": 3.0,
            "middle+": 4.5,
            "senior": 6.0
        }
        years_exp = level_to_years.get(interview_data.selected_level, 3.0)
    
    # Create interview
    interview = Interview(
        candidate_name=interview_data.candidate_name,
        candidate_email=interview_data.candidate_email,
        selected_level=interview_data.selected_level,
        direction=interview_data.direction,
        cv_text=interview_data.cv_text,
        years_of_experience=years_exp,
        status="in_progress",
        current_stage="coding",
        confidence_score=50.0
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Generate all 3 tasks using LLM
    try:
        tasks = await create_interview_tasks(
            interview_id=interview.id,
            direction=interview.direction,
            level=interview.selected_level,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tasks: {str(e)}")
    
    return interview


@router.get("/v2/{interview_id}", response_model=InterviewResponseV2)
async def get_interview_v2(interview_id: int, db: Session = Depends(get_db)):
    """Get interview details with V2 schema."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.get("/v2/{interview_id}/tasks", response_model=AllTasksResponse)
async def get_all_tasks(interview_id: int, db: Session = Depends(get_db)):
    """Get all 3 tasks for the interview."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    tasks = db.query(Task).filter(
        Task.interview_id == interview_id
    ).order_by(Task.task_order).all()
    
    return AllTasksResponse(
        interview_id=interview_id,
        current_stage=interview.current_stage,
        tasks=[TaskResponseV2.model_validate(t) for t in tasks]
    )


@router.get("/v2/{interview_id}/progress", response_model=InterviewProgressResponse)
async def get_interview_progress(interview_id: int, db: Session = Depends(get_db)):
    """Get current interview progress."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    tasks = db.query(Task).filter(Task.interview_id == interview_id).all()
    completed_tasks = [t for t in tasks if t.status == "completed"]
    
    theory_answers = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id
    ).all()
    answered_questions = [a for a in theory_answers if a.status in ["answered", "skipped"]]
    
    # Can proceed to theory if at least tried all tasks
    submissions_exist = all([
        db.query(Submission).filter(Submission.task_id == t.id).first() is not None
        for t in tasks
    ])
    
    return InterviewProgressResponse(
        interview_id=interview_id,
        current_stage=interview.current_stage,
        tasks_completed=len(completed_tasks),
        tasks_total=len(tasks),
        questions_answered=len(answered_questions),
        questions_max=25,
        confidence_score=interview.confidence_score or 50.0,
        can_proceed_to_theory=submissions_exist or len(completed_tasks) > 0
    )


@router.post("/v2/{interview_id}/proceed-to-theory", response_model=StageTransitionResponse)
async def proceed_to_theory_stage(interview_id: int, db: Session = Depends(get_db)):
    """
    Move from coding stage to theory stage.
    Generates solution questions based on completed tasks.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.current_stage != "coding":
        raise HTTPException(status_code=400, detail="Interview is not in coding stage")
    
    # Generate solution questions
    try:
        await generate_solution_questions(interview_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")
    
    # Update stage
    interview.current_stage = "theory"
    db.commit()
    
    return StageTransitionResponse(
        interview_id=interview_id,
        new_stage="theory",
        message="Переход к этапу теоретических вопросов"
    )


@router.get("/v2/{interview_id}/next-question", response_model=Optional[TheoryQuestionResponse])
async def get_next_theory_question_endpoint(interview_id: int, db: Session = Depends(get_db)):
    """
    Get next theory question using adaptive selection.
    Returns null if interview should end.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.current_stage != "theory":
        raise HTTPException(status_code=400, detail="Interview is not in theory stage")
    
    question = await get_next_theory_question(interview_id, db)
    
    if question is None:
        return None
    
    return TheoryQuestionResponse(**question)


@router.post("/v2/submit-answer", response_model=TheoryAnswerEvaluation)
async def submit_theory_answer(
    answer_data: TheoryAnswerSubmit,
    db: Session = Depends(get_db)
):
    """
    Submit answer to a theory question.
    Returns evaluation with score and feedback.
    """
    theory_answer = db.query(TheoryAnswer).filter(
        TheoryAnswer.id == answer_data.answer_id
    ).first()
    
    if not theory_answer:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if theory_answer.status != "pending":
        raise HTTPException(status_code=400, detail="Question already answered")
    
    try:
        evaluation = await evaluate_theory_answer(
            answer_id=answer_data.answer_id,
            candidate_answer=answer_data.answer_text,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    
    return TheoryAnswerEvaluation(**evaluation)


@router.get("/v2/{interview_id}/theory-answers", response_model=List[TheoryAnswerResponse])
async def get_all_theory_answers(interview_id: int, db: Session = Depends(get_db)):
    """Get all theory answers for the interview."""
    answers = db.query(TheoryAnswer).filter(
        TheoryAnswer.interview_id == interview_id
    ).order_by(TheoryAnswer.question_order).all()
    
    return [TheoryAnswerResponse.model_validate(a) for a in answers]


@router.post("/v2/{interview_id}/complete", response_model=FinalScoresResponse)
async def complete_interview_v2(interview_id: int, db: Session = Depends(get_db)):
    """
    Complete the interview and generate final scores.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    try:
        scores = await generate_final_scores(interview_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scores: {str(e)}")
    
    return FinalScoresResponse(**scores)


# ============ Complexity Check Endpoints ============

@router.post("/tasks/{task_id}/complexity-question")
async def get_complexity_question(task_id: int, db: Session = Depends(get_db)):
    """
    Generate a question about time/space complexity after task is solved.
    Called automatically after successful submission.
    """
    from ..services.complexity_checker import generate_complexity_question
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    interview = db.query(Interview).filter(Interview.id == task.interview_id).first()
    
    # Get candidate's best submission code
    best_submission = db.query(Submission).filter(
        Submission.task_id == task_id
    ).order_by(Submission.passed_visible.desc(), Submission.passed_hidden.desc()).first()
    
    candidate_code = best_submission.code if best_submission else ""
    
    question = await generate_complexity_question(
        task_title=task.title,
        task_description=task.description,
        candidate_code=candidate_code,
        difficulty=interview.selected_level if interview else "junior"
    )
    
    return {
        "task_id": task_id,
        "task_title": task.title,
        "question": question
    }


@router.post("/tasks/{task_id}/complexity-answer")
async def submit_complexity_answer(
    task_id: int,
    answer: str,
    db: Session = Depends(get_db)
):
    """
    Submit answer to complexity question and get evaluation.
    Compares candidate's understanding with actual code analysis.
    """
    from ..services.complexity_checker import full_complexity_check
    from pydantic import BaseModel
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    interview = db.query(Interview).filter(Interview.id == task.interview_id).first()
    
    # Get candidate's best submission code
    best_submission = db.query(Submission).filter(
        Submission.task_id == task_id
    ).order_by(Submission.passed_visible.desc(), Submission.passed_hidden.desc()).first()
    
    if not best_submission:
        raise HTTPException(status_code=400, detail="No submission found for this task")
    
    result = await full_complexity_check(
        task_title=task.title,
        task_description=task.description,
        candidate_code=best_submission.code,
        candidate_answer=answer,
        difficulty=interview.selected_level if interview else "junior"
    )
    
    # Store complexity evaluation in task
    task.robustness_score = result.get("complexity_score", 0)
    db.commit()
    
    return {
        "task_id": task_id,
        "result": result,
        "score_bonus": 10 if result.get("candidate_understands") else 0
    }

