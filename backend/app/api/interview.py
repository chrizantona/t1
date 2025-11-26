"""
Interview API endpoints.
Main endpoints for conducting interviews.
V2: New interview flow with 3 tasks + theory questions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.db import get_db
from ..models.interview import Interview, Task, Submission, ChatMessage, Hint, TheoryAnswer
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
    FinalScoresResponse
)
from ..services.scibox_client import scibox_client
from ..services.adaptive import generate_first_task, generate_next_task as adaptive_generate_next_task
from ..services.code_runner import run_code
from ..services.anti_cheat import calculate_trust_score
from ..services.reporting import generate_final_report
from ..services.grading_service import calculate_start_grade, calculate_final_grade_for_interview
from ..services.interview_flow import (
    create_interview_tasks,
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
    Creates interview and generates first task using LLM.
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
            "junior": 1.0,
            "junior_plus": 1.5,
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


@router.post("/submit")
async def submit_code(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit code for a task.
    Runs tests and stores results with detailed test output.
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
    
    # Return submission with test details
    return {
        "id": submission.id,
        "passed_visible": submission.passed_visible,
        "total_visible": submission.total_visible,
        "passed_hidden": submission.passed_hidden,
        "total_hidden": submission.total_hidden,
        "execution_time_ms": submission.execution_time_ms,
        "error_message": submission.error_message,
        "ai_likeness_score": submission.ai_likeness_score,
        "visible_test_details": result.get("visible_test_details", [])
    }


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
        {"role": "system", "content": "/no_think\nТы опытный технический интервьюер. Отвечай кратко и по делу (2-3 предложения)."}
    ]
    for msg in messages:
        llm_messages.append({"role": msg.role, "content": msg.content})
    
    # Get AI response
    try:
        ai_response = await scibox_client.chat_completion(llm_messages, temperature=0.7, max_tokens=512)
        # Remove <think> tags if present
        import re
        ai_response = re.sub(r'<think>.*?</think>', '', ai_response, flags=re.DOTALL).strip()
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
    hint_prompts = {
        "light": "Дай лёгкую подсказку - намекни на алгоритм или подход, но не раскрывай решение.",
        "medium": "Дай среднюю подсказку - опиши алгоритм решения и ключевые шаги.",
        "heavy": "Дай сильную подсказку - покажи детальный алгоритм с примером кода."
    }
    system_prompt = f"/no_think\nТы - система подсказок. {hint_prompts.get(hint_data.hint_level, hint_prompts['light'])} Отвечай кратко (максимум 2-3 предложения)."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Задача: {task.description}\n\nТекущий код:\n{hint_data.current_code or 'Нет кода'}"}
    ]
    
    try:
        hint_content = await scibox_client.chat_completion(messages, temperature=0.5, max_tokens=256)
        # Remove <think> tags if present
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
        if result["passed_visible"] == result["total_visible"] and result["passed_hidden"] == result["total_hidden"]:
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

