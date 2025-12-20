"""
Anti-cheat API endpoints.
Receives telemetry events from frontend.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Literal
from pydantic import BaseModel

from ..core.db import get_db
from ..models.interview import AntiCheatEvent
from ..services.anti_cheat_advanced import calculate_full_trust_score

router = APIRouter()


class AntiCheatEventData(BaseModel):
    """Single anti-cheat event from frontend."""
    type: Literal["keydown", "paste", "copy", "cut", "focus", "blur", "visibility_change", "devtools"]
    taskId: str
    timestamp: int  # milliseconds since epoch
    meta: dict = {}


class BulkEventsRequest(BaseModel):
    """Bulk events submission."""
    interviewId: int
    events: List[AntiCheatEventData]


@router.post("/events")
async def submit_events(
    data: BulkEventsRequest,
    db: Session = Depends(get_db)
):
    """
    Submit anti-cheat events from frontend.
    
    Frontend buffers events and sends them in batches.
    """
    try:
        # Store events in database
        for event_data in data.events:
            event = AntiCheatEvent(
                interview_id=data.interviewId,
                task_id=event_data.taskId,
                event_type=event_data.type,
                timestamp_ms=event_data.timestamp,
                meta=event_data.meta
            )
            db.add(event)
        
        db.commit()
        
        return {
            "success": True,
            "events_received": len(data.events)
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store events: {str(e)}")


@router.get("/{interview_id}/trust-score")
async def get_trust_score(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get calculated trust score for interview.
    
    Returns complete trust analysis with signals and explanations.
    """
    try:
        result = await calculate_full_trust_score(interview_id, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trust score: {str(e)}")


@router.get("/{interview_id}/events")
async def get_events(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all anti-cheat events for interview (for debugging/admin).
    """
    events = db.query(AntiCheatEvent).filter(
        AntiCheatEvent.interview_id == interview_id
    ).order_by(AntiCheatEvent.timestamp_ms).all()
    
    return {
        "interview_id": interview_id,
        "events_count": len(events),
        "events": [
            {
                "id": e.id,
                "type": e.event_type,
                "task_id": e.task_id,
                "timestamp": e.timestamp_ms,
                "meta": e.meta
            }
            for e in events
        ]
    }

# пидормот
