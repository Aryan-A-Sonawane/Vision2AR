"""
Updated API models for multi-modal ML diagnosis
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class MultiModalSymptomInput(BaseModel):
    """User symptom with text + optional media"""
    device_model: str
    issue_description: str
    images: Optional[List[str]] = None  # Base64 encoded images
    video_url: Optional[str] = None
    video_file: Optional[str] = None  # Base64 or file path


class AnswerInputV2(BaseModel):
    """User answer with optional media attachments"""
    session_id: str
    answer_text: str
    images: Optional[List[str]] = None
    video_url: Optional[str] = None


class DynamicQuestion(BaseModel):
    """LLM-generated dynamic question"""
    text: str
    type: str  # "open_ended", "multiple_choice", "media_request"
    allows_media: bool
    suggested_media: List[str]  # ["photo_of_leds", "video_of_boot", etc.]
    context: Optional[str] = None  # Why we're asking this


class DiagnosisResponseV2(BaseModel):
    """Enhanced diagnosis response"""
    session_id: str
    next_question: Optional[DynamicQuestion] = None
    diagnosis: Optional[Dict] = None
    current_understanding: Dict  # Show user what we know so far
    confidence: float
    conversation_summary: str  # Human-readable summary of conversation
    debug_info: Dict[str, Any]


class VisualAnalysisResult(BaseModel):
    """Result from image/video analysis"""
    description: str
    detected_issues: List[str]
    confidence: float
    bounding_boxes: Optional[List[Dict]] = None  # For highlighting issues
