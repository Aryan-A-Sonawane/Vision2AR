"""
API Endpoints for ML-Powered Multi-Modal Diagnosis
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from models_v2 import (
    MultiModalSymptomInput,
    AnswerInputV2,
    DiagnosisResponseV2,
    DynamicQuestion
)
from diagnosis.ml_engine_v2 import MLDiagnosisEngineV2, MultiModalInput

app = FastAPI(
    title="ML-Powered AR Laptop Diagnosis",
    description="True ML-based diagnosis with multi-modal input support",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML engine
ml_engine = MLDiagnosisEngineV2()

# Active sessions store
active_sessions: Dict[str, Dict] = {}


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ML-Powered AR Laptop Diagnosis",
        "version": "2.0.0",
        "features": [
            "Multi-modal input (text + images + video)",
            "LLM-based dynamic question generation",
            "Computer vision for hardware analysis",
            "Continuous learning from interactions"
        ]
    }


@app.post("/api/v2/diagnose", response_model=DiagnosisResponseV2)
async def start_diagnosis_v2(symptom: MultiModalSymptomInput):
    """
    Start ML-powered diagnosis with multi-modal input
    
    Accepts:
    - Text description (required)
    - Images (optional, base64 encoded)
    - Video (optional)
    
    Returns:
    - Dynamic contextual question OR immediate diagnosis if confidence high
    """
    
    try:
        session_id = str(uuid.uuid4())
        
        # Create multi-modal input
        mm_input = MultiModalInput(
            text=symptom.issue_description,
            images=symptom.images,
            video_path=symptom.video_url or symptom.video_file,
            timestamp=datetime.now().isoformat()
        )
        
        # Run ML analysis
        next_question, diagnosis, debug_info = await ml_engine.start_diagnosis(
            device_model=symptom.device_model,
            initial_input=mm_input
        )
        
        # Initialize session
        active_sessions[session_id] = {
            "device_model": symptom.device_model,
            "conversation_history": [
                {
                    "role": "user",
                    "content": symptom.issue_description,
                    "images": len(symptom.images) if symptom.images else 0,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "current_understanding": debug_info.get("combined_confidence", {}),
            "media_provided": []
        }
        
        # Generate conversation summary
        summary = f"Analyzing your report: '{symptom.issue_description[:100]}...'. "
        if symptom.images:
            summary += f"Reviewed {len(symptom.images)} image(s). "
        
        if debug_info.get("combined_confidence", 0) > 0:
            summary += f"Initial confidence: {debug_info['combined_confidence']:.0%}"
        
        # If immediate diagnosis
        if diagnosis:
            return DiagnosisResponseV2(
                session_id=session_id,
                next_question=None,
                diagnosis={
                    "cause": diagnosis.cause,
                    "confidence": diagnosis.confidence,
                    "solution_steps": diagnosis.solution_steps,
                    "easy_fix": diagnosis.easy_fix,
                    "tools_needed": diagnosis.tools_needed,
                    "risk_level": diagnosis.risk_level,
                    "visual_evidence": diagnosis.visual_evidence
                },
                current_understanding=debug_info,
                confidence=diagnosis.confidence,
                conversation_summary=summary + " Diagnosis complete!",
                debug_info=debug_info
            )
        
        # Return next question
        question_obj = DynamicQuestion(
            text=next_question.get("text"),
            type=next_question.get("type", "open_ended"),
            allows_media=next_question.get("allows_media", True),
            suggested_media=next_question.get("suggested_media", []),
            context="We need more information to narrow down the issue"
        )
        
        # Store question in session
        active_sessions[session_id]["conversation_history"].append({
            "role": "assistant",
            "content": question_obj.text,
            "timestamp": datetime.now().isoformat()
        })
        
        return DiagnosisResponseV2(
            session_id=session_id,
            next_question=question_obj,
            diagnosis=None,
            current_understanding=debug_info,
            confidence=debug_info.get("combined_confidence", 0.0),
            conversation_summary=summary,
            debug_info=debug_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis error: {str(e)}")


@app.post("/api/v2/answer", response_model=DiagnosisResponseV2)
async def process_answer_v2(answer: AnswerInputV2):
    """
    Process user's answer with optional media attachments
    
    Accepts:
    - Text answer (required)
    - Images (optional)
    - Video (optional)
    
    Returns:
    - Next contextual question OR final diagnosis
    """
    
    try:
        if answer.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[answer.session_id]
        
        # Add answer to conversation history
        session["conversation_history"].append({
            "role": "user",
            "content": answer.answer_text,
            "images": len(answer.images) if answer.images else 0,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create multi-modal input for answer
        mm_input = None
        if answer.images or answer.video_url:
            mm_input = MultiModalInput(
                text=answer.answer_text,
                images=answer.images,
                video_path=answer.video_url,
                timestamp=datetime.now().isoformat()
            )
        
        # Process answer with ML engine
        next_question, diagnosis, debug_info = await ml_engine.process_answer(
            session_id=answer.session_id,
            answer_text=answer.answer_text,
            media=mm_input,
            conversation_history=session["conversation_history"],
            current_understanding=session["current_understanding"]
        )
        
        # Update session
        session["current_understanding"] = {
            "confidence": debug_info.get("updated_confidence", 0.0),
            "top_cause": debug_info.get("top_cause")
        }
        
        # Generate summary
        summary = f"Processed your response. Current confidence: {debug_info.get('updated_confidence', 0.0):.0%}. "
        if debug_info.get("top_cause"):
            summary += f"Most likely: {debug_info['top_cause'].replace('_', ' ')}"
        
        # If diagnosis complete
        if diagnosis:
            return DiagnosisResponseV2(
                session_id=answer.session_id,
                next_question=None,
                diagnosis={
                    "cause": diagnosis.cause,
                    "confidence": diagnosis.confidence,
                    "solution_steps": diagnosis.solution_steps,
                    "easy_fix": diagnosis.easy_fix,
                    "tools_needed": diagnosis.tools_needed,
                    "risk_level": diagnosis.risk_level,
                    "visual_evidence": diagnosis.visual_evidence
                },
                current_understanding=session["current_understanding"],
                confidence=diagnosis.confidence,
                conversation_summary=summary + " Diagnosis complete!",
                debug_info=debug_info
            )
        
        # Return next question
        question_obj = DynamicQuestion(
            text=next_question.get("text"),
            type=next_question.get("type", "open_ended"),
            allows_media=next_question.get("allows_media", True),
            suggested_media=next_question.get("suggested_media", []),
            context="Gathering more details to confirm diagnosis"
        )
        
        # Store question in session
        session["conversation_history"].append({
            "role": "assistant",
            "content": question_obj.text,
            "timestamp": datetime.now().isoformat()
        })
        
        return DiagnosisResponseV2(
            session_id=answer.session_id,
            next_question=question_obj,
            diagnosis=None,
            current_understanding=session["current_understanding"],
            confidence=session["current_understanding"]["confidence"],
            conversation_summary=summary,
            debug_info=debug_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer processing error: {str(e)}")


@app.post("/api/v2/upload-media")
async def upload_media(file: UploadFile = File(...)):
    """
    Upload image or video for analysis
    
    Returns base64 encoded data or file path
    """
    
    try:
        import base64
        
        contents = await file.read()
        encoded = base64.b64encode(contents).decode('utf-8')
        
        # Determine mime type
        mime_type = file.content_type or "image/jpeg"
        
        return {
            "success": True,
            "data": f"data:{mime_type};base64,{encoded}",
            "filename": file.filename,
            "size": len(contents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@app.get("/api/v2/session/{session_id}")
async def get_session_info(session_id: str):
    """Get current session state and conversation history"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "device_model": session["device_model"],
        "conversation_turns": len(session["conversation_history"]),
        "current_confidence": session["current_understanding"].get("confidence", 0.0),
        "suspected_cause": session["current_understanding"].get("top_cause"),
        "conversation_history": session["conversation_history"]
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_v2:app", host="0.0.0.0", port=port, reload=False)
