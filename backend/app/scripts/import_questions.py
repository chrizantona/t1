"""
Script to import questions from JSON file into database.
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.db import SessionLocal, init_db
from app.models.questions import TechQuestion
from app.schemas.questions import QuestionImport
from app.services.questions_importer import detect_panel_and_eval


def import_questions():
    """Import questions from JSON file."""
    # Initialize database
    init_db()
    
    # Load questions JSON
    questions_path = Path(__file__).parent.parent.parent.parent / "tasks_base" / "questions.json"
    
    if not questions_path.exists():
        print(f"❌ Questions file not found: {questions_path}")
        return
    
    with open(questions_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Create session
    db = SessionLocal()
    
    try:
        imported_count = 0
        skipped_count = 0
        
        for item in data:
            # Parse question
            raw = QuestionImport(**item)
            
            # Check if already exists
            existing = db.query(TechQuestion).filter(TechQuestion.id == raw.id).first()
            if existing:
                skipped_count += 1
                continue
            
            # Detect panel type and eval mode
            panel_type, eval_mode, lang_hint = detect_panel_and_eval(raw)
            
            # Create question
            question = TechQuestion(
                id=raw.id,
                category=raw.category.value,
                difficulty=raw.difficulty.value,
                question_text=raw.question,
                panel_type=panel_type,
                eval_mode=eval_mode,
                language_hint=lang_hint,
            )
            
            db.add(question)
            imported_count += 1
        
        # Commit changes
        db.commit()
        
        print(f"✅ Import completed:")
        print(f"   - Imported: {imported_count} questions")
        print(f"   - Skipped: {skipped_count} questions (already exist)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during import: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_questions()
