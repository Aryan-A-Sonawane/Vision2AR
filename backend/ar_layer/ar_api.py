"""
FastAPI endpoint for AR component detection and overlay generation

Provides real-time component detection API for AR mode
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image

from ar_layer.component_detector import ARComponentDetector

router = APIRouter()

# Global detector instance (initialize on startup)
ar_detector = ARComponentDetector()

class ReferenceImageRequest(BaseModel):
    tutorial_id: int
    step_number: int
    image_url: str
    image_data: Optional[str] = None  # Base64 encoded image (if provided, overrides image_url)
    category: str  # laptop, phone, tablet

class DetectionResponse(BaseModel):
    success: bool
    anchors_count: int
    anchors: List[dict]
    message: str

class LiveFrameRequest(BaseModel):
    tutorial_id: int
    step_number: int
    frame_data: str  # Base64 encoded image

class AROverlayResponse(BaseModel):
    success: bool
    annotated_frame: str  # Base64 encoded annotated image
    matched_components: List[dict]
    guidance: str


@router.post("/api/ar/process-reference", response_model=DetectionResponse)
async def process_reference_image(request: ReferenceImageRequest):
    """
    Phase 1: Process tutorial step image to extract component anchors
    
    This should be called once per step (can be cached)
    """
    try:
        # Load appropriate YOLO model
        if not ar_detector.load_model_for_category(request.category):
            raise HTTPException(500, "Failed to load YOLO model")
        
        # Check cache first
        cache_loaded = ar_detector.load_anchors_for_step(
            request.tutorial_id,
            request.step_number,
            "data/ar_anchors"
        )
        
        if cache_loaded:
            return DetectionResponse(
                success=True,
                anchors_count=len(ar_detector.reference_anchors),
                anchors=[
                    {
                        'id': a.component_id,
                        'label': a.label,
                        'action': a.action,
                        'importance': a.importance
                    }
                    for a in ar_detector.reference_anchors
                ],
                message="Loaded from cache"
            )
        
        # Process reference image
        if request.image_data:
            # Decode base64 image data from frontend
            try:
                image_bytes = base64.b64decode(request.image_data.split(',')[1] if ',' in request.image_data else request.image_data)
                image_pil = Image.open(BytesIO(image_bytes))
                image_np = np.array(image_pil)
                image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                
                # Save to cache directory for future use
                cache_dir = f"assets/tutorials/{request.tutorial_id}"
                import os
                os.makedirs(cache_dir, exist_ok=True)
                cache_path = f"{cache_dir}/step_{request.step_number}.jpg"
                cv2.imwrite(cache_path, image_cv)
                
                anchors = ar_detector.process_reference_image(cache_path, request.step_number)
            except Exception as e:
                raise HTTPException(500, f"Failed to decode image data: {str(e)}")
        else:
            # Fallback to local file path
            image_path = f"assets/tutorials/{request.tutorial_id}/step_{request.step_number}.jpg"
            anchors = ar_detector.process_reference_image(image_path, request.step_number)
        
        # Save to cache
        ar_detector.save_anchors_for_step(
            request.tutorial_id,
            request.step_number,
            "data/ar_anchors"
        )
        
        return DetectionResponse(
            success=True,
            anchors_count=len(anchors),
            anchors=[
                {
                    'id': a.component_id,
                    'label': a.label,
                    'action': a.action,
                    'importance': a.importance
                }
                for a in anchors
            ],
            message="Reference processed successfully"
        )
        
    except Exception as e:
        raise HTTPException(500, f"Reference processing failed: {str(e)}")


@router.post("/api/ar/detect-live", response_model=AROverlayResponse)
async def detect_in_live_frame(request: LiveFrameRequest):
    """
    Phase 2: Detect components in live camera frame and generate AR overlay
    
    This is called continuously (e.g., 5-10 FPS) while in AR mode
    """
    try:
        # Decode base64 frame
        frame_bytes = base64.b64decode(request.frame_data.split(',')[1] if ',' in request.frame_data else request.frame_data)
        frame_image = Image.open(BytesIO(frame_bytes))
        frame = np.array(frame_image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Ensure anchors are loaded
        if not ar_detector.reference_anchors:
            ar_detector.load_anchors_for_step(
                request.tutorial_id,
                request.step_number,
                "data/ar_anchors"
            )
        
        # Detect components in live frame
        detections = ar_detector.detect_in_live_feed(frame)
        
        # Match with reference and draw overlay
        annotated_frame, matched = ar_detector.match_and_overlay(frame, detections)
        
        # Encode annotated frame to base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Generate guidance message
        guidance = _generate_guidance_message(matched, ar_detector.reference_anchors)
        
        return AROverlayResponse(
            success=True,
            annotated_frame=f"data:image/jpeg;base64,{annotated_base64}",
            matched_components=matched,
            guidance=guidance
        )
        
    except Exception as e:
        raise HTTPException(500, f"Live detection failed: {str(e)}")


@router.get("/api/ar/models")
async def list_available_models():
    """List available YOLO models by category"""
    return {
        "models": [
            {"category": "laptop", "model": "laptop_yolo_v8.pt", "status": "available"},
            {"category": "phone", "model": "phone_yolo_v8.pt", "status": "training"},
            {"category": "tablet", "model": "tablet_yolo_v8.pt", "status": "planned"},
        ]
    }


def _generate_guidance_message(matched: List[dict], anchors: List) -> str:
    """Generate helpful AR guidance based on detection results"""
    if not matched:
        return "Move camera closer to the device to detect components"
    
    matched_critical = [m for m in matched if any(
        a.component_id == m['component_id'] and a.importance == 'critical' 
        for a in anchors
    )]
    
    if len(matched_critical) == len([a for a in anchors if a.importance == 'critical']):
        return "✓ All critical components detected. Follow highlighted instructions."
    else:
        return f"Detected {len(matched)}/{len(anchors)} components. Adjust camera angle for better view."
