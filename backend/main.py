"""
AR Laptop Troubleshooter - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
import json
from dotenv import load_dotenv
# Lazy load ML engine to avoid DLL loading issues on Windows
# from diagnosis.ml_engine import MLDiagnosisEngine, DiagnosisSession

# Try to load knowledge-based engine (from extracted manuals)
# DISABLED temporarily due to Windows DLL loading issues with sentence_transformers
# The V2 system (diagnosis/belief_engine.py) doesn't need this
use_knowledge_engine = False
# try:
#     from diagnosis.knowledge_engine import get_engine
#     use_knowledge_engine = True
#     print("[OK] Using Knowledge-Based Engine (learns from OEM manuals)")
# except Exception as e:
#     use_knowledge_engine = False
#     print(f"[WARN] Knowledge engine not available: {e}")
#     print("  Using standard ML engine")
print("[OK] Using Enhanced V2 Diagnosis System (belief_engine + input_processor)")

# Import AR layer API
try:
    from ar_layer.ar_api import router as ar_router
    ar_enabled = True
    print("[OK] AR detection API loaded")
except Exception as e:
    ar_enabled = False
    print(f"[WARN] AR detection API not available: {e}")

# Load environment variables
load_dotenv()

# Initialize ML diagnosis engine (lazy - not used in v2 system)
ml_engine = None  # Was: MLDiagnosisEngine()

# Store active sessions (in production, use Redis/DB)
active_sessions: Dict[str, Dict] = {}

# Initialize FastAPI app
app = FastAPI(
    title="AR Laptop Troubleshooter API",
    description="Diagnostic and repair assistant with AR-guided overlays",
    version="0.1.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AR detection router if available
if ar_enabled:
    app.include_router(ar_router, tags=["AR Detection"])
    print("[OK] AR detection routes registered")


# Pydantic models
class SymptomInput(BaseModel):
    """User symptom description"""
    device_model: str
    issue_description: str


class DiagnosisResponse(BaseModel):
    """Diagnosis result with questions or final result"""
    session_id: str
    questions: Optional[List[Dict]] = None
    diagnosis: Optional[Dict] = None
    debug_info: Dict[str, Any]
    confidence: float = 0.0


class QuestionResponse(BaseModel):
    """Diagnostic question for user"""
    question_id: str
    question_text: str
    expected_signal: str
    cost_level: str


class AnswerInput(BaseModel):
    """User answer to diagnostic question"""
    question_id: str
    answer: str
    session_id: str


class RepairStepResponse(BaseModel):
    """Single repair step with AR overlay data"""
    step_id: int
    action: str
    tools: List[str]
    risk_level: str
    image: str
    overlays: List[Dict]
    tts_text: str
    warnings: List[str]


# Health check endpoint
@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "service": "AR Laptop Troubleshooter",
        "version": "0.1.0",
        "endpoints": {
            "diagnose": "/api/diagnose",
            "answer": "/api/answer",
            "repair": "/api/repair/{device_model}/{issue}",
            "overlay": "/api/overlay/{step_id}"
        }
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with dependencies"""
    checks = {
        "api": "healthy",
        "database": await check_database(),
        "vector_db": await check_vector_db(),
        "ml_models": check_ml_models(),
        "assets_path": os.path.exists("../assets"),
        "manuals_path": os.path.exists("../manuals")
    }
    
    all_healthy = all(
        v == "healthy" or v is True 
        for v in checks.values()
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks
    }


async def check_database():
    """Check PostgreSQL connection"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return "not_configured"
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "healthy"
    except Exception as e:
        return f"error: {str(e)}"


async def check_vector_db():
    """Check Vector DB connection"""
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_key = os.getenv("WEAVIATE_API_KEY")
    
    if not weaviate_url or not weaviate_key:
        return "not_configured"
    
    try:
        # TODO: Test actual connection
        return "configured"  # Update after vector DB setup
    except Exception as e:
        return f"error: {str(e)}"


def check_ml_models():
    """Check if ML models are available"""
    try:
        import torch
        import transformers
        return "available"
    except ImportError:
        return "not_installed"


@app.post("/api/diagnose", response_model=DiagnosisResponse)
async def start_diagnosis(symptom: SymptomInput):
    """
    Start diagnostic workflow using ML engine
    Uses knowledge from extracted OEM manuals when available
    Returns questions or immediate diagnosis
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        print("\n" + "#"*70)
        print(f"# NEW DIAGNOSIS REQUEST")
        print("#"*70)
        print(f"Session ID: {session_id}")
        print(f"Device: {symptom.device_model}")
        print(f"Issue: {symptom.issue_description}")
        print("#"*70)
        
        # Try knowledge-based engine first (learns from manuals)
        # DISABLED: V1 system not used
        if False:  # use_knowledge_engine:
            try:
                # kb_engine = get_engine()
                best_match, alternatives = None, []  # kb_engine.diagnose(
                    # user_symptoms=symptom.issue_description,
                    # user_answers=None
                # )
                
                if best_match and best_match['confidence'] > 0.35:
                    # We have a good match from manuals!
                    print(f"\n✅ DIAGNOSIS THRESHOLD MET (confidence: {best_match['confidence']:.2%} > 35%)")
                    solution = kb_engine.format_solution(best_match)
                    solution['alternative_causes'] = [
                        {"cause": alt['issue_type'], "confidence": alt['confidence']}
                        for alt in alternatives
                    ]
                    print(f"✓ Formatted solution ready")
                    
                    # Store session
                    active_sessions[session_id] = {
                        "device_model": symptom.device_model,
                        "symptoms": symptom.issue_description,
                        "questions_asked": [],
                        "answers": [],
                        "belief_vector": {},
                        "knowledge_match": best_match,
                        "using_knowledge_engine": True,
                        "all_questions_asked": [],
                        "last_question_text": "",
                        "debug_trail": []
                    }
                    
                    # Generate follow-up question if confidence not high enough
                    if best_match['confidence'] < 0.7:
                        print(f"\n⚠️ Confidence below 70% - generating follow-up question...")
                        question_obj = kb_engine.generate_question(
                            current_understanding=best_match,
                            asked_questions=[],
                            conversation_history=[],
                            user_symptoms=symptom.issue_description
                        )
                        
                        if question_obj:
                            # Store question for next iteration
                            active_sessions[session_id]["last_question_text"] = question_obj["text"]
                            active_sessions[session_id]["all_questions_asked"] = [question_obj]
                            
                            print(f"❓ Question: {question_obj['text']}")
                            print(f"   Source: {question_obj.get('source', 'unknown')}")
                            print(f"   Reasoning: {question_obj.get('reasoning', 'N/A')}")
                            
                            return DiagnosisResponse(
                                session_id=session_id,
                                questions=[{
                                    "id": question_obj["id"],
                                    "text": question_obj["text"],
                                    "type": question_obj["type"],
                                    "context": f"Current match: {solution['diagnosis']} ({solution['confidence']:.0%} confidence)",
                                    "reasoning": question_obj.get("reasoning", "")
                                }],
                                diagnosis=None,
                                debug_info={
                                    "engine": "knowledge_based",
                                    "source": solution['source'],
                                    "initial_confidence": best_match['confidence'],
                                    "question_source": question_obj.get("source", "unknown")
                                },
                                confidence=best_match['confidence']
                            )
                    
                    # High confidence - return diagnosis
                    print(f"\n🎯 HIGH CONFIDENCE DIAGNOSIS - Returning complete solution")
                    print(f"   Cause: {solution['diagnosis']}")
                    print(f"   Steps: {len(solution['solution_steps'])}")
                    print(f"   Raw manual text: {len(solution.get('raw_manual_extract', ''))} chars")
                    
                    return DiagnosisResponse(
                        session_id=session_id,
                        questions=None,
                        diagnosis={
                            "cause": solution['diagnosis'],
                            "confidence": solution['confidence'],
                            "easy_fix": solution['solution_steps'][0] if solution['solution_steps'] else "See solution steps",
                            "solution_steps": solution['solution_steps'],
                            "tools_needed": solution['tools_needed'],
                            "risk_level": "medium",
                            "source_breakdown": {
                                solution['source']: ["Primary diagnostic source"]
                            },
                            "related_guides": [],
                            "raw_manual_extract": solution['raw_manual_text']
                        },
                        debug_info={
                            "engine": "knowledge_based",
                            "source_file": solution['source_file'],
                            "alternatives": solution['alternative_causes']
                        },
                        confidence=solution['confidence']
                    )
                    
            except Exception as kb_error:
                print(f"Knowledge engine error: {kb_error}")
                # Fall back to standard engine
        
        # Fallback: Use standard ML engine
        questions, result, debug_info = ml_engine.diagnose(
            device_model=symptom.device_model,
            symptoms=symptom.issue_description,
            session_id=session_id
        )
        
        # Store session
        active_sessions[session_id] = {
            "device_model": symptom.device_model,
            "symptoms": symptom.issue_description,
            "questions_asked": [],
            "answers": [],
            "belief_vector": {},
            "debug_trail": [debug_info],
            "using_knowledge_engine": False
        }
        
        # If immediate diagnosis available
        if result:
            return DiagnosisResponse(
                session_id=session_id,
                questions=None,
                diagnosis={
                    "cause": result.cause,
                    "confidence": result.confidence,
                    "easy_fix": result.easy_fix,
                    "solution_steps": result.solution_steps,
                    "tools_needed": result.tools_needed,
                    "risk_level": result.risk_level,
                    "source_breakdown": result.source_breakdown,
                    "related_guides": result.related_guides
                },
                debug_info=debug_info,
                confidence=result.confidence
            )
        
        # Return questions
        return DiagnosisResponse(
            session_id=session_id,
            questions=questions,
            diagnosis=None,
            debug_info=debug_info,
            confidence=0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis error: {str(e)}")


@app.post("/api/answer")
async def process_answer(answer: AnswerInput):
    """
    Process user answer using knowledge-based engine iteratively
    Updates diagnosis with each answer and generates smart follow-up questions
    """
    try:
        session_id = answer.session_id
        
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        
        print("\n" + "#"*70)
        print(f"# PROCESSING ANSWER")
        print("#"*70)
        print(f"Session ID: {session_id}")
        print(f"Question ID: {answer.question_id}")
        print(f"User Answer: {answer.answer}")
        print("#"*70)
        
        # Record answer in conversation history
        session["questions_asked"].append(answer.question_id)
        session["answers"].append({
            "question_id": answer.question_id,
            "question": session.get("last_question_text", ""),
            "answer": answer.answer
        })
        
        # Check if session is using knowledge engine
        # DISABLED: V1 system not used
        if False and session.get("using_knowledge_engine"):
            # kb_engine = get_engine()
            current_match = session.get("knowledge_match")
            
            if current_match:
                # Update diagnosis with new answer
                updated_match, confidence_delta = kb_engine.update_diagnosis_with_answer(
                    current_diagnosis=current_match,
                    user_symptoms=session["symptoms"],
                    answer=answer.answer,
                    question_asked=session.get("last_question_text", ""),
                    all_answers=session["answers"]
                )
                
                # Update session with new match
                session["knowledge_match"] = updated_match
                
                print(f"\n✅ DIAGNOSIS UPDATED")
                print(f"   Issue: {updated_match['issue_type']}")
                print(f"   Confidence: {updated_match['confidence']:.2%}")
                print(f"   Delta: {confidence_delta:+.2%}")
                
                # Check if confidence is now high enough (lowered from 80% to 75%)
                if updated_match['confidence'] >= 0.75:
                    print(f"\n🎯 CONFIDENCE THRESHOLD REACHED - Returning final diagnosis")
                    solution = kb_engine.format_solution(updated_match)
                    
                    return DiagnosisResponse(
                        session_id=session_id,
                        questions=None,
                        diagnosis={
                            "cause": solution['diagnosis'],
                            "confidence": solution['confidence'],
                            "easy_fix": solution['solution_steps'][0] if solution['solution_steps'] else "See solution steps",
                            "solution_steps": solution['solution_steps'],
                            "tools_needed": solution['tools_needed'],
                            "risk_level": "medium",
                            "source_breakdown": {
                                solution['source']: ["Primary diagnostic source"]
                            },
                            "related_guides": [],
                            "raw_manual_extract": solution['raw_manual_text']
                        },
                        debug_info={
                            "engine": "knowledge_based",
                            "source_file": solution['source_file'],
                            "confidence_evolution": f"Improved by {confidence_delta:+.2%}"
                        },
                        confidence=solution['confidence']
                    )
                
                # Generate next question
                print(f"\n⚠️ Confidence below 80% - generating next question...")
                
                # Build conversation history for smart question generator
                conversation_history = session["answers"]
                
                question_obj = kb_engine.generate_question(
                    current_understanding=updated_match,
                    asked_questions=[q["text"] for q in session.get("all_questions_asked", [])],
                    conversation_history=conversation_history,
                    user_symptoms=session["symptoms"]
                )
                
                if not question_obj:
                    # No more questions, return diagnosis
                    print(f"\n🎯 NO MORE QUESTIONS - Returning diagnosis at {updated_match['confidence']:.2%}")
                    solution = kb_engine.format_solution(updated_match)
                    
                    return DiagnosisResponse(
                        session_id=session_id,
                        questions=None,
                        diagnosis={
                            "cause": solution['diagnosis'],
                            "confidence": solution['confidence'],
                            "easy_fix": solution['solution_steps'][0] if solution['solution_steps'] else "See solution steps",
                            "solution_steps": solution['solution_steps'],
                            "tools_needed": solution['tools_needed'],
                            "risk_level": "medium",
                            "source_breakdown": {
                                solution['source']: ["Primary diagnostic source"]
                            },
                            "related_guides": [],
                            "raw_manual_extract": solution['raw_manual_text']
                        },
                        debug_info={
                            "engine": "knowledge_based",
                            "source_file": solution['source_file'],
                            "reason": "Exhausted diagnostic questions"
                        },
                        confidence=solution['confidence']
                    )
                
                # Store question text for next iteration
                session["last_question_text"] = question_obj["text"]
                if "all_questions_asked" not in session:
                    session["all_questions_asked"] = []
                session["all_questions_asked"].append(question_obj)
                
                print(f"\n❓ NEXT QUESTION:")
                print(f"   Text: {question_obj['text']}")
                print(f"   Source: {question_obj.get('source', 'unknown')}")
                print(f"   Reasoning: {question_obj.get('reasoning', 'N/A')}")
                
                return DiagnosisResponse(
                    session_id=session_id,
                    questions=[{
                        "id": question_obj["id"],
                        "text": question_obj["text"],
                        "type": question_obj["type"],
                        "context": f"Current diagnosis: {updated_match['issue_type']} ({updated_match['confidence']:.0%} confidence)",
                        "reasoning": question_obj.get("reasoning", ""),
                    }],
                    diagnosis=None,
                    debug_info={
                        "engine": "knowledge_based",
                        "question_source": question_obj.get("source", "unknown"),
                        "expected_info": question_obj.get("expected_info", ""),
                        "confidence_delta": confidence_delta
                    },
                    confidence=updated_match['confidence']
                )
        
        # Fallback to generic ML engine if not using knowledge engine
        print("\n⚠️ Session not using knowledge engine, falling back to generic ML")
        
        # Initialize or update belief vector
        if not session.get("belief_vector"):
            session["belief_vector"] = {
                "battery_issue": 0.33,
                "power_supply": 0.33,
                "motherboard": 0.34
            }
        
        # Process answer with ML engine
        next_q, result, debug_info = ml_engine.process_answer(
            session_id=session_id,
            question_id=answer.question_id,
            answer=answer.answer,
            belief_vector=session["belief_vector"],
            asked_questions=session["questions_asked"]
        )
        
        if "debug_trail" not in session:
            session["debug_trail"] = []
        session["debug_trail"].append(debug_info)
        session["belief_vector"] = debug_info.get("belief_update", session["belief_vector"])
        
        # If diagnosis complete
        if result:
            # Save session for learning (DISABLED - V1 system not used)
            # diag_session = DiagnosisSession(
            #     session_id=session_id,
            #     device_model=session["device_model"],
            #     initial_symptoms=session["symptoms"],
            #     questions_asked=session["questions_asked"],
            #     answers_given=[a if isinstance(a, str) else a.get("answer", "") for a in session["answers"]],
            #     final_diagnosis=result.cause,
            #     confidence=result.confidence,
            #     timestamp=debug_info["timestamp"] if "timestamp" in debug_info else "",
            #     source_contributions=result.source_breakdown
            # )
            # ml_engine.save_session(diag_session)
            pass  # V1 learning disabled
            
            return DiagnosisResponse(
                session_id=session_id,
                questions=None,
                diagnosis={
                    "cause": result.cause,
                    "confidence": result.confidence,
                    "easy_fix": result.easy_fix,
                    "solution_steps": result.solution_steps,
                    "tools_needed": result.tools_needed,
                    "risk_level": result.risk_level,
                    "source_breakdown": result.source_breakdown,
                    "related_guides": result.related_guides
                },
                debug_info={
                    **debug_info,
                    "full_trail": session["debug_trail"]
                },
                confidence=result.confidence
            )
        
        # Return next question
        return DiagnosisResponse(
            session_id=session_id,
            questions=[next_q] if next_q else [],
            diagnosis=None,
            debug_info={
                **debug_info,
                "full_trail": session["debug_trail"]
            },
            confidence=max(session["belief_vector"].values()) if session["belief_vector"] else 0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer processing error: {str(e)}")


@app.get("/api/repair/{device_model}/{issue}", response_model=List[RepairStepResponse])
async def get_repair_steps(device_model: str, issue: str):
    """
    Get merged repair tutorial for device and issue
    """
    # TODO: Load from database
    
    # Sample response
    return [
        RepairStepResponse(
            step_id=1,
            action="Disconnect AC adapter and remove battery",
            tools=["Torx-5"],
            risk_level="safe",
            image=f"assets/{device_model.replace('_', '/')}/step1.jpg",
            overlays=[{"x": 100, "y": 200, "type": "highlight"}],
            tts_text="Step 1. Disconnect AC adapter and remove battery. You will need a Torx-5 screwdriver.",
            warnings=["Ensure power is disconnected"]
        )
    ]


@app.get("/api/overlay/{step_id}")
async def get_overlay_metadata(step_id: int):
    """
    Get AR overlay metadata for specific step
    """
    # TODO: Load from overlay generator
    
    return {
        "step_id": step_id,
        "image": "assets/lenovo/ideapad_5/step1.jpg",
        "overlays": [
            {
                "x": 120,
                "y": 340,
                "width": 40,
                "height": 40,
                "type": "sequence",
                "label": "1. Screw location",
                "z_index": 1
            }
        ],
        "tts_text": "Remove this screw first"
    }


@app.post("/api/upload/image")
async def upload_symptom_image(file: UploadFile = File(...)):
    """
    Upload image of problem for vision-based diagnosis
    """
    # TODO: Implement YOLO/BLIP2 vision analysis
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    return {
        "status": "received",
        "filename": file.filename,
        "analysis": "pending_implementation"
    }


@app.post("/api/upload/video")
async def upload_symptom_video(file: UploadFile = File(...)):
    """
    Upload video of problem for analysis
    """
    # TODO: Implement video frame extraction + analysis
    
    if not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")
    
    return {
        "status": "received",
        "filename": file.filename,
        "analysis": "pending_implementation"
    }


# Device and model management
@app.get("/api/devices")
async def list_supported_devices():
    """Get list of supported device models"""
    # TODO: Query from database
    
    return {
        "brands": ["lenovo", "dell", "hp"],
        "models": {
            "lenovo": ["ideapad_5", "thinkpad_x1"],
            "dell": ["xps_15", "latitude_5420"],
            "hp": ["pavilion", "elitebook"]
        }
    }


# ============================================================================
# ENHANCED DIAGNOSTIC SYSTEM (Belief Engine + Multi-Modal Input)
# ============================================================================

# Initialize enhanced components (lazy loaded)
belief_engine = None
input_processor = None
tutorial_matcher = None
db_pool = None


async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
        db_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
    return db_pool


async def get_belief_engine():
    """Get or create belief engine"""
    global belief_engine
    if belief_engine is None:
        from diagnosis.belief_engine import BeliefEngine
        pool = await get_db_pool()
        belief_engine = BeliefEngine(pool)
    return belief_engine


async def get_input_processor():
    """Get or create input processor"""
    global input_processor
    if input_processor is None:
        from analysis.input_processor import InputProcessor
        pool = await get_db_pool()
        input_processor = InputProcessor(pool)
    return input_processor


async def get_tutorial_matcher():
    """Get or create tutorial matcher"""
    global tutorial_matcher
    if tutorial_matcher is None:
        from analysis.tutorial_matcher import TutorialMatcher
        import weaviate
        
        pool = await get_db_pool()
        
        # Initialize Weaviate client
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_key = os.getenv("WEAVIATE_API_KEY")
        
        weaviate_client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_key)
        )
        
        tutorial_matcher = TutorialMatcher(pool, weaviate_client)
    return tutorial_matcher


class EnhancedDiagnosisInput(BaseModel):
    """Input for enhanced diagnostic system"""
    text_input: str
    image_base64: Optional[str] = None


class EnhancedDiagnosisResponse(BaseModel):
    """Response from enhanced diagnostic system"""
    session_id: str
    diagnosis_state: str  # "questioning", "complete", "uncertain"
    initial_belief: Optional[Dict[str, float]] = None
    current_belief: Optional[Dict[str, float]] = None
    next_question: Optional[Dict] = None
    tutorials: Optional[List[Dict]] = None
    logs: List[Dict]


class AnswerQuestionInput(BaseModel):
    """User answer to diagnostic question"""
    session_id: str
    question_id: str
    answer: str
    response_type: Optional[str] = "binary"  # "binary" or "text"


class FeedbackInput(BaseModel):
    """User feedback on tutorial"""
    session_id: str
    tutorial_id: int
    resolved: bool
    clarity_rating: int  # 1-5
    accuracy_rating: int  # 1-5
    time_spent: Optional[int] = None  # seconds


@app.post("/api/v2/diagnose/start", response_model=EnhancedDiagnosisResponse)
async def start_enhanced_diagnosis(input_data: EnhancedDiagnosisInput):
    """
    Start enhanced diagnostic session with belief engine and multi-modal input
    Processes text + optional image, initializes beliefs, asks first question
    """
    try:
        session_id = str(uuid.uuid4())
        
        print(f"\n{'='*70}")
        print(f"🚀 ENHANCED DIAGNOSIS SESSION: {session_id}")
        print(f"{'='*70}")
        
        # Get components
        processor = await get_input_processor()
        engine = await get_belief_engine()
        pool = await get_db_pool()
        
        # Process input (text + image)
        image_bytes = None
        if input_data.image_base64:
            import base64
            image_bytes = base64.b64decode(input_data.image_base64)
        
        print(f"📥 Processing input...")
        processed_input = await processor.process_input(
            text_input=input_data.text_input,
            image_bytes=image_bytes
        )
        
        print(f"✅ Processed input:")
        print(f"   Brand: {processed_input.get('brand')} ({processed_input.get('brand_confidence', 0):.2f})")
        print(f"   Category: {processed_input.get('category')}")
        print(f"   Symptoms: {processed_input.get('symptoms')}")
        print(f"   Visual symptoms: {processed_input.get('visual_symptoms')}")
        
        # Initialize belief vector
        print(f"\n🧠 Initializing belief vector...")
        initial_belief = await engine.initialize_beliefs(
            symptoms=processed_input["symptoms"],
            visual_symptoms=processed_input["visual_symptoms"],
            category=processed_input["category"],
            brand=processed_input.get("brand")
        )
        
        print(f"✅ Belief vector initialized:")
        for cause, prob in list(initial_belief.items())[:5]:
            print(f"   {cause}: {prob:.3f}")
        
        # Create diagnostic session in database
        async with pool.acquire() as conn:
            session_db_id = await conn.fetchval("""
                INSERT INTO diagnostic_sessions 
                (session_id, initial_input_text, brand, device_category, initial_symptoms)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, session_id, input_data.text_input, processed_input.get("brand"), 
                processed_input["category"], processed_input["symptoms"])
            
            # Store initial belief snapshot
            await conn.execute("""
                INSERT INTO belief_snapshots
                (session_id, snapshot_order, belief_vector, trigger_event)
                VALUES ($1, 0, $2, 'initial_belief_calculated')
            """, session_id, json.dumps(initial_belief))
            
            # Log input processing with enhanced metadata
            await conn.execute("""
                INSERT INTO diagnostic_logs 
                (session_id, log_order, stage, action, data, confidence)
                VALUES ($1, 1, 'input_processing', 'text_processed', $2, $3)
            """, session_id, json.dumps({
                "keywords": processed_input["keywords"],
                "symptoms": processed_input["symptoms"],
                "brand": processed_input.get("brand"),
                "initial_belief": initial_belief,
                "top_causes": sorted(initial_belief.items(), key=lambda x: x[1], reverse=True)[:5],
                "reasoning": f"Initialized from {len(processed_input['symptoms'])} symptoms and {len(processed_input['keywords'])} keywords"
            }), processed_input.get("brand_confidence", 0))
            
            if processed_input.get("image_caption"):
                await conn.execute("""
                    INSERT INTO diagnostic_logs 
                    (session_id, log_order, stage, action, data, confidence)
                    VALUES ($1, 2, 'input_processing', 'image_analyzed', $2, 0.8)
                """, session_id, json.dumps({
                    "caption": processed_input["image_caption"],
                    "visual_symptoms": processed_input["visual_symptoms"],
                    "cached": processed_input.get("image_cached", False),
                    "blip2_model": "Salesforce/blip2-opt-2.7b",
                    "reasoning": f"BLIP-2 detected {len(processed_input.get('visual_symptoms', []))} visual symptoms from image"
                }))
        
        # Check if we should ask question or proceed to tutorial matching
        max_confidence = engine.get_confidence(initial_belief)
        
        if max_confidence >= 0.75:
            # High confidence - skip to tutorial matching
            print(f"\n🎯 High confidence ({max_confidence:.2f}) - matching tutorials...")
            
            top_cause, confidence = engine.get_diagnosis(initial_belief)
            
            matcher = await get_tutorial_matcher()
            tutorials = await matcher.search_tutorials_hybrid(
                diagnosis=top_cause,
                symptoms=processed_input["symptoms"],
                keywords=processed_input["keywords"],
                category=processed_input["category"],
                brand=processed_input.get("brand"),
                limit=5
            )
            
            # Store session
            active_sessions[session_id] = {
                "session_db_id": session_db_id,
                "processed_input": processed_input,
                "initial_belief": initial_belief,
                "current_belief": initial_belief,
                "asked_questions": [],
                "diagnosis": top_cause,
                "confidence": confidence
            }
            
            return EnhancedDiagnosisResponse(
                session_id=session_id,
                diagnosis_state="complete",
                initial_belief=initial_belief,
                current_belief=initial_belief,
                tutorials=[{
                    "tutorial_id": t["tutorial_id"],
                    "title": t["title"],
                    "brand": t["brand"],
                    "difficulty": t["difficulty"],
                    "final_score": t.get("final_score", t.get("hybrid_score", 0))
                } for t in tutorials],
                logs=[{
                    "stage": "diagnosis",
                    "action": "high_confidence_match",
                    "data": {"cause": top_cause, "confidence": confidence}
                }]
            )
        
        # Ask first question - TRY TEXT QUESTION FIRST
        print(f"\n❓ Selecting first question...")
        
        # First, try to generate a text-based question (more flexible)
        text_question = engine.generate_text_question(
            current_beliefs=initial_belief,
            asked_questions=[]
        )
        
        if text_question:
            print(f"✅ Generated TEXT question (open-ended)")
            next_question = text_question
        else:
            # Fallback to binary questions
            print(f"   No text question available, using binary question...")
            next_question = await engine.select_next_question(
                current_beliefs=initial_belief,
                processed_input=processed_input,
                asked_questions=[],
                category=processed_input["category"]
            )
        
        if not next_question:
            # No questions available - match tutorials
            print(f"⚠️ No questions available - proceeding to tutorials...")
            top_cause, confidence = engine.get_diagnosis(initial_belief)
            
            matcher = await get_tutorial_matcher()
            tutorials = await matcher.search_tutorials_hybrid(
                diagnosis=top_cause,
                symptoms=processed_input["symptoms"],
                keywords=processed_input["keywords"],
                category=processed_input["category"],
                brand=processed_input.get("brand"),
                limit=5
            )
            
            active_sessions[session_id] = {
                "session_db_id": session_db_id,
                "processed_input": processed_input,
                "initial_belief": initial_belief,
                "current_belief": initial_belief,
                "asked_questions": [],
                "diagnosis": top_cause,
                "confidence": confidence
            }
            
            return EnhancedDiagnosisResponse(
                session_id=session_id,
                diagnosis_state="uncertain",
                initial_belief=initial_belief,
                current_belief=initial_belief,
                tutorials=[{
                    "tutorial_id": t["tutorial_id"],
                    "title": t["title"],
                    "brand": t["brand"],
                    "difficulty": t["difficulty"],
                    "final_score": t.get("final_score", t.get("hybrid_score", 0))
                } for t in tutorials],
                logs=[{
                    "stage": "diagnosis",
                    "action": "no_questions_available",
                    "data": {"cause": top_cause, "confidence": confidence}
                }]
            )
        
        print(f"✅ Selected question: {next_question.get('text', next_question.get('id'))}")
        
        # Store session
        active_sessions[session_id] = {
            "session_db_id": session_db_id,
            "processed_input": processed_input,
            "initial_belief": initial_belief,
            "current_belief": initial_belief,
            "asked_questions": [],
            "last_question_text": next_question.get("text", ""),
            "confidence_history": [max(initial_belief.values()) if initial_belief else 0.0]  # Track confidence progression
        }
        
        return EnhancedDiagnosisResponse(
            session_id=session_id,
            diagnosis_state="questioning",
            initial_belief=initial_belief,
            current_belief=initial_belief,
            next_question=next_question,
            logs=[{
                "stage": "question_selection",
                "action": "first_question_selected",
                "data": {"question_id": next_question["id"], "info_gain": next_question.get("information_gain_estimate"), "response_type": next_question.get("response_type", "binary")}
            }]
        )
        
    except Exception as e:
        import traceback
        print(f"❌ Error in enhanced diagnosis: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/diagnose/answer", response_model=EnhancedDiagnosisResponse)
async def answer_diagnostic_question(answer_data: AnswerQuestionInput):
    """
    Process user answer to diagnostic question
    Updates belief vector, decides next question or shows tutorials
    """
    try:
        session_id = answer_data.session_id
        
        if session_id not in active_sessions:
            raise HTTPException(404, "Session not found")
        
        session = active_sessions[session_id]
        
        print(f"\n{'='*70}")
        print(f"💬 ANSWER RECEIVED: {session_id}")
        print(f"   Question: {answer_data.question_id}")
        print(f"   Answer: {answer_data.answer}")
        print(f"{'='*70}")
        
        # Check for bypass keywords
        bypass_keywords = ["show tutorials", "skip questions", "just show me tutorials", "show me solutions"]
        if any(keyword in answer_data.answer.lower() for keyword in bypass_keywords):
            print("🚪 BYPASS DETECTED: User requested tutorials directly")
            session["current_belief"] = session.get("current_belief", session["initial_belief"])
            top_cause = max(session["current_belief"].items(), key=lambda x: x[1])
            
            # Return with tutorials immediately
            return EnhancedDiagnosisResponse(
                session_id=session_id,
                diagnosis_state="tutorials",
                current_belief=session["current_belief"],
                diagnosis=top_cause[0],
                confidence=top_cause[1],
                tutorials=[],  # Frontend will fetch these
                logs=[{"stage": "bypass", "action": "user_requested_tutorials", "data": {"answer": answer_data.answer}}]
            )
        
        # Get components
        engine = await get_belief_engine()
        pool = await get_db_pool()
        processor = await get_input_processor()
        
        # Update belief vector - use semantic if text response
        print(f"\n🔄 Updating belief vector...")
        if answer_data.response_type == "text" and len(answer_data.answer) > 10:
            print(f"   Using SEMANTIC update for text response")
            # Get question text from session
            question_text = session.get("last_question_text", "")
            updated_belief = await engine.update_beliefs_semantic(
                current_beliefs=session["current_belief"],
                question_text=question_text,
                answer_text=answer_data.answer,
                processor=processor
            )
        else:
            print(f"   Using RULE-BASED update for binary response")
            updated_belief = await engine.update_beliefs(
                current_beliefs=session["current_belief"],
                question_id=answer_data.question_id,
                answer=answer_data.answer
            )
        
        # Calculate belief changes for learning
        belief_before = session["current_belief"]
        belief_changes = {}
        for cause in set(list(belief_before.keys()) + list(updated_belief.keys())):
            before_val = belief_before.get(cause, 0)
            after_val = updated_belief.get(cause, 0)
            change = after_val - before_val
            if abs(change) > 0.01:  # Only track significant changes
                belief_changes[cause] = {"before": before_val, "after": after_val, "change": change}
        
        # Calculate information gain (entropy reduction)
        import math
        def entropy(beliefs):
            return -sum(p * math.log2(p + 1e-10) for p in beliefs.values() if p > 0)
        
        info_gain = entropy(belief_before) - entropy(updated_belief)
        
        # Find top changes
        top_changes = sorted(belief_changes.items(), key=lambda x: abs(x[1]["change"]), reverse=True)[:3]
        
        session["current_belief"] = updated_belief
        session["asked_questions"].append(answer_data.question_id)
        
        # Track confidence progression
        current_max_confidence = max(updated_belief.values()) if updated_belief else 0.0
        if "confidence_history" not in session:
            session["confidence_history"] = []
        session["confidence_history"].append(current_max_confidence)
        
        print(f"✅ Updated beliefs:")
        for cause, prob in list(updated_belief.items())[:5]:
            print(f"   {cause}: {prob:.3f}")
        if top_changes:
            changes_str = ', '.join([f"{c[0]}: {c[1]['change']:+.3f}" for c in top_changes])
            print(f"   Top changes: {changes_str}")
        print(f"   Information gain: {info_gain:.3f}")
        
        # Check if confidence is stagnating (no improvement in last 2-3 questions)
        confidence_stagnating = False
        if len(session["confidence_history"]) >= 3:
            last_3_confidences = session["confidence_history"][-3:]
            improvement = last_3_confidences[-1] - last_3_confidences[0]
            if improvement < 0.05:  # Less than 5% improvement
                confidence_stagnating = True
                print(f"⚠️ Confidence stagnating: {last_3_confidences[0]:.3f} → {last_3_confidences[-1]:.3f} (improvement: {improvement:.3f})")
        
        # Log to database with enhanced metadata
        async with pool.acquire() as conn:
            snapshot_order = len(session["asked_questions"])
            log_order = len(session["asked_questions"]) + 2
            
            # Store belief snapshot
            await conn.execute("""
                INSERT INTO belief_snapshots
                (session_id, snapshot_order, belief_vector, trigger_event)
                VALUES ($1, $2, $3, $4)
            """, session_id, snapshot_order, json.dumps(updated_belief), 
                f"question_answered:{answer_data.question_id}")
            
            # Store question interaction with before/after beliefs
            await conn.execute("""
                INSERT INTO question_interactions
                (session_id, question_id, question_text, question_type, answer, answer_timestamp, 
                 belief_change, information_gain)
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, $6, $7)
            """, session_id, answer_data.question_id, 
                session.get("last_question_text", answer_data.question_id),
                answer_data.response_type or "binary",
                answer_data.answer,
                json.dumps(belief_changes),
                info_gain)
            
            # Enhanced diagnostic log with rich metadata
            reasoning = "Belief updated based on user answer. "
            if top_changes:
                reasoning += f"Most affected: {top_changes[0][0]} ({top_changes[0][1]['change']:+.2f})."
            if info_gain > 0.2:
                reasoning += f" High information gain ({info_gain:.2f}) - question was very helpful."
            elif info_gain < 0.05:
                reasoning += f" Low information gain ({info_gain:.2f}) - question didn't help much."
            
            await conn.execute("""
                INSERT INTO diagnostic_logs
                (session_id, log_order, stage, action, data, confidence)
                VALUES ($1, $2, 'questioning', 'answer_received', $3, $4)
            """, session_id, log_order, json.dumps({
                "question_id": answer_data.question_id,
                "question_text": session.get("last_question_text", answer_data.question_id),
                "response_type": answer_data.response_type or "binary",
                "answer": answer_data.answer,
                "belief_change": belief_changes,
                "top_changes": [{"cause": c[0], "before": c[1]["before"], "after": c[1]["after"], "change": c[1]["change"]} for c in top_changes],
                "information_gain": info_gain,
                "confidence_before": max(belief_before.values()) if belief_before else 0.0,
                "confidence_after": current_max_confidence,
                "reasoning": reasoning
            }), current_max_confidence)
        
        # Check if we have high confidence
        max_confidence = engine.get_confidence(updated_belief)
        
        # ESCAPE ROUTE: If confidence stagnating after 2-3 questions, show tutorials anyway
        if confidence_stagnating and len(session["asked_questions"]) >= 2:
            print(f"\n🚪 ESCAPE ROUTE: Confidence stagnating after {len(session['asked_questions'])} questions - showing top tutorials...")
            
            top_cause, confidence = engine.get_diagnosis(updated_belief)
            session["diagnosis"] = top_cause
            session["confidence"] = confidence
            
            matcher = await get_tutorial_matcher()
            tutorials = await matcher.search_tutorials_hybrid(
                diagnosis=top_cause,
                symptoms=session["processed_input"]["symptoms"],
                keywords=session["processed_input"]["keywords"],
                category=session["processed_input"]["category"],
                brand=session["processed_input"].get("brand"),
                limit=8  # Show more options since we're uncertain
            )
            
            return EnhancedDiagnosisResponse(
                session_id=session_id,
                diagnosis_state="uncertain",
                initial_belief=session["initial_belief"],
                current_belief=updated_belief,
                tutorials=[{
                    "tutorial_id": t["tutorial_id"],
                    "title": t["title"],
                    "brand": t["brand"],
                    "difficulty": t["difficulty"],
                    "final_score": t.get("final_score", t.get("hybrid_score", 0))
                } for t in tutorials],
                logs=[{
                    "stage": "diagnosis",
                    "action": "confidence_stagnating_escape",
                    "data": {
                        "cause": top_cause,
                        "confidence": confidence,
                        "questions_asked": len(session["asked_questions"]),
                        "confidence_progression": session["confidence_history"]
                    }
                }]
            )
        
        if max_confidence >= 0.75:
            # High confidence - match tutorials
            print(f"\n🎯 Confidence threshold reached ({max_confidence:.2f}) - matching tutorials...")
            
            top_cause, confidence = engine.get_diagnosis(updated_belief)
            session["diagnosis"] = top_cause
            session["confidence"] = confidence
            
            matcher = await get_tutorial_matcher()
            tutorials = await matcher.search_tutorials_hybrid(
                diagnosis=top_cause,
                symptoms=session["processed_input"]["symptoms"],
                keywords=session["processed_input"]["keywords"],
                category=session["processed_input"]["category"],
                brand=session["processed_input"].get("brand"),
                limit=5
            )
            
            return EnhancedDiagnosisResponse(
                session_id=session_id,
                diagnosis_state="complete",
                initial_belief=session["initial_belief"],
                current_belief=updated_belief,
                tutorials=[{
                    "tutorial_id": t["tutorial_id"],
                    "title": t["title"],
                    "brand": t["brand"],
                    "difficulty": t["difficulty"],
                    "final_score": t.get("final_score", t.get("hybrid_score", 0))
                } for t in tutorials],
                logs=[{
                    "stage": "diagnosis",
                    "action": "confidence_threshold_reached",
                    "data": {"cause": top_cause, "confidence": confidence, "questions_asked": len(session["asked_questions"])}
                }]
            )
        
        # Ask next question - TRY TEXT QUESTION FIRST
        print(f"\n❓ Selecting next question...")
        
        # First, try to generate a text-based question (more flexible)
        text_question = engine.generate_text_question(
            current_beliefs=updated_belief,
            asked_questions=session["asked_questions"]
        )
        
        if text_question:
            print(f"✅ Generated TEXT question (open-ended)")
            next_question = text_question
        else:
            # Fallback to binary questions
            print(f"   No text question available, using binary question...")
            next_question = await engine.select_next_question(
                current_beliefs=updated_belief,
                processed_input=session["processed_input"],
                asked_questions=session["asked_questions"],
                category=session["processed_input"]["category"]
            )
        
        if not next_question:
            # No more questions - provide best guess
            print(f"⚠️ No more questions - providing best guess...")
            top_cause, confidence = engine.get_diagnosis(updated_belief)
            
            matcher = await get_tutorial_matcher()
            tutorials = await matcher.search_tutorials_hybrid(
                diagnosis=top_cause,
                symptoms=session["processed_input"]["symptoms"],
                keywords=session["processed_input"]["keywords"],
                category=session["processed_input"]["category"],
                brand=session["processed_input"].get("brand"),
                limit=5
            )
            
            return EnhancedDiagnosisResponse(
                session_id=session_id,
                diagnosis_state="uncertain",
                initial_belief=session["initial_belief"],
                current_belief=updated_belief,
                tutorials=[{
                    "tutorial_id": t["tutorial_id"],
                    "title": t["title"],
                    "brand": t["brand"],
                    "difficulty": t["difficulty"],
                    "final_score": t.get("final_score", t.get("hybrid_score", 0))
                } for t in tutorials],
                logs=[{
                    "stage": "diagnosis",
                    "action": "no_more_questions",
                    "data": {"cause": top_cause, "confidence": confidence, "questions_asked": len(session["asked_questions"])}
                }]
            )
        
        print(f"✅ Next question selected: {next_question.get('text', next_question.get('id'))}")
        
        # Store question text for semantic updates
        session["last_question_text"] = next_question.get("text", "")
        
        return EnhancedDiagnosisResponse(
            session_id=session_id,
            diagnosis_state="questioning",
            initial_belief=session["initial_belief"],
            current_belief=updated_belief,
            next_question=next_question,
            logs=[{
                "stage": "questioning",
                "action": "next_question_selected",
                "data": {"question_id": next_question["id"], "questions_asked": len(session["asked_questions"]), "response_type": next_question.get("response_type", "binary")}
            }]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Error processing answer: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/diagnose/logs/{session_id}")
async def get_diagnostic_logs(session_id: str):
    """Get complete diagnostic log for session (for frontend terminal display)"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(404, "Session not found")
        
        session = active_sessions[session_id]
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            logs = await conn.fetch("""
                SELECT log_order, stage, action, data_json, confidence, created_at
                FROM diagnostic_logs
                WHERE session_id = $1
                ORDER BY log_order
            """, session["session_db_id"])
            
            return {
                "session_id": session_id,
                "logs": [{
                    "timestamp": log["created_at"].isoformat(),
                    "stage": log["stage"],
                    "action": log["action"],
                    "data": json.loads(log["data_json"]) if log["data_json"] else {},
                    "confidence": log["confidence"]
                } for log in logs]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/feedback")
async def submit_feedback(feedback: FeedbackInput):
    """Submit user feedback on tutorial outcome"""
    try:
        if feedback.session_id not in active_sessions:
            raise HTTPException(404, "Session not found")
        
        session = active_sessions[feedback.session_id]
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Store feedback
            await conn.execute("""
                INSERT INTO user_feedback
                (session_id, tutorial_id, resolved, clarity_rating, accuracy_rating, time_spent_seconds)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, session["session_db_id"], feedback.tutorial_id, feedback.resolved,
                feedback.clarity_rating, feedback.accuracy_rating, feedback.time_spent)
            
            # If resolved, mark session as successful
            if feedback.resolved:
                await conn.execute("""
                    UPDATE diagnostic_sessions
                    SET resolved = true, final_diagnosis = $1, ended_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, session.get("diagnosis", "unknown"), session["session_db_id"])
        
        learning_triggered = feedback.resolved  # Trigger learning cycle for successful resolutions
        
        return {
            "message": "Feedback received",
            "learning_triggered": learning_triggered,
            "session_id": feedback.session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/tutorial/{tutorial_id}")
async def get_tutorial_details(tutorial_id: int):
    """Get complete tutorial details including steps, tools, warnings"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get tutorial basic info
            tutorial = await conn.fetchrow(
                """
                SELECT id, brand, model, issue_type, title, difficulty, source, 
                       keywords, description, estimated_time_minutes
                FROM tutorials 
                WHERE id = $1
                """,
                tutorial_id
            )
            
            if not tutorial:
                raise HTTPException(404, "Tutorial not found")
            
            # Get steps
            steps = await conn.fetch(
                """
                SELECT step_number as step, title as action, description, 
                       image_url as image, video_timestamp
                FROM tutorial_steps 
                WHERE tutorial_id = $1 
                ORDER BY step_number
                """,
                tutorial_id
            )
            
            # Get tools
            tools = await conn.fetch(
                """
                SELECT tool_name
                FROM tutorial_tools 
                WHERE tutorial_id = $1
                """,
                tutorial_id
            )
            
            # Get warnings
            warnings = await conn.fetch(
                """
                SELECT warning_text, severity, step_number
                FROM tutorial_warnings 
                WHERE tutorial_id = $1
                ORDER BY step_number NULLS FIRST
                """,
                tutorial_id
            )
            
            # Convert to dict and build response
            tutorial_dict = dict(tutorial)
            tutorial_dict['steps'] = [dict(s) for s in steps]
            tutorial_dict['tools'] = [t['tool_name'] for t in tools]
            tutorial_dict['warnings'] = [w['warning_text'] for w in warnings]
            tutorial_dict['images'] = [s.get('image') for s in steps if s.get('image')]
            tutorial_dict['estimated_time'] = f"{tutorial_dict.get('estimated_time_minutes', 30)} min" if tutorial_dict.get('estimated_time_minutes') else "30 min"
            
            return {"tutorial": tutorial_dict}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching tutorial {tutorial_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tutorials")
async def browse_tutorials(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    issue_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Browse all tutorials with optional filters - ONLY myfixit source with images"""
    try:
        pool = await get_db_pool()
        
        query = """
            SELECT 
                id,
                brand,
                model,
                issue_type,
                title,
                difficulty,
                source,
                keywords
            FROM tutorials
            WHERE source = 'myfixit' AND id >= 42
        """
        params = []
        param_count = 1
        
        if brand:
            query += f" AND LOWER(brand) = LOWER(${param_count})"
            params.append(brand)
            param_count += 1
        
        # Category filter with ID ranges: PC (42-3653), Mac (3654-5877), Computer Hardware (5878-6392)
        if category:
            if category.lower() in ['laptop', 'pc', 'desktop']:
                query += f" AND id BETWEEN 42 AND 3653"
            elif category.lower() == 'mac':
                query += f" AND id BETWEEN 3654 AND 5877"
            elif category.lower() in ['computer hardware', 'hardware']:
                query += f" AND id BETWEEN 5878 AND 6392"
        
        if issue_type:
            query += f" AND LOWER(issue_type) = LOWER(${param_count})"
            params.append(issue_type)
            param_count += 1
        
        if difficulty:
            query += f" AND LOWER(difficulty) = LOWER(${param_count})"
            params.append(difficulty)
            param_count += 1
        
        if search:
            query += f" AND (LOWER(title) LIKE LOWER(${param_count}) OR keywords && ARRAY[LOWER(${param_count})]::text[])"
            params.append(f'%{search}%')
            param_count += 1
        
        query += f" ORDER BY id LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            tutorials = await conn.fetch(query, *params)
            total = await conn.fetchval("SELECT COUNT(*) FROM tutorials")
            
            return {
                "tutorials": [dict(t) for t in tutorials],
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        print(f"Error browsing tutorials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )


