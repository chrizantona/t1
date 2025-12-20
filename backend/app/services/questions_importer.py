"""
Service for importing questions from JSON and determining panel/eval types.
"""
from app.schemas.questions import QuestionImport, QuestionCategory
from app.models.questions import QuestionPanelType, QuestionEvalMode


def detect_panel_and_eval(
    raw: QuestionImport
) -> tuple[QuestionPanelType, QuestionEvalMode, str | None]:
    """
    Determine panel type, eval mode, and language hint based on question category.
    
    Args:
        raw: Question import data
        
    Returns:
        Tuple of (panel_type, eval_mode, language_hint)
    """
    if raw.category == QuestionCategory.algorithms:
        return QuestionPanelType.code_python, QuestionEvalMode.llm_code, "python"
    
    if raw.category == QuestionCategory.frontend:
        return QuestionPanelType.code_frontend, QuestionEvalMode.llm_code, "typescript-react"
    
    if raw.category == QuestionCategory.backend:
        return QuestionPanelType.code_backend, QuestionEvalMode.llm_code, "python/sql"
    
    if raw.category == QuestionCategory.data_science:
        return QuestionPanelType.code_ds, QuestionEvalMode.llm_code, "python-ds"
    
    return QuestionPanelType.text_only, QuestionEvalMode.llm_theory, None

# пидормот
