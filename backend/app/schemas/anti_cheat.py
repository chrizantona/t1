"""
Pydantic schemas for anti-cheat system.
"""
from pydantic import BaseModel
from typing import Literal, List, Dict, Any


class AntiCheatEventSchema(BaseModel):
    """Anti-cheat event from frontend."""
    type: Literal["keydown", "paste", "copy", "cut", "focus", "blur", "visibility_change", "devtools"]
    taskId: str
    timestamp: int
    meta: Dict[str, Any] = {}


class BulkEventsRequest(BaseModel):
    """Bulk events submission."""
    interviewId: int
    events: List[AntiCheatEventSchema]


class TrustScoreResponse(BaseModel):
    """Trust score calculation result."""
    trust_score: int
    trust_status: Literal["ok", "suspicious", "high_risk"]
    trust_reasons: List[str]
    signals: Dict[str, Any]
    
    class Config:
        from_attributes = True
