"""
AR Component Detection System - Multi-Model Architecture

Each device category has its own fine-tuned YOLOv8 model:
- laptop_yolo_v8.pt (trained on laptop components)
- phone_yolo_v8.pt (trained on phone components)
- tablet_yolo_v8.pt (trained on tablet components)

Process:
1. Load tutorial step image → Detect components → Store reference anchors
2. Live camera feed → Detect components → Match with reference → Draw AR overlay
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class DetectedComponent:
    """Component detected by YOLO"""
    label: str              # e.g., "screw", "battery", "RAM"
    confidence: float       # 0.0 - 1.0
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int] # Center point for overlay
    
@dataclass
class ReferenceAnchor:
    """Pre-processed anchor from tutorial step image"""
    component_id: str       # Unique ID (e.g., "screw_top_left")
    label: str
    bbox: Tuple[int, int, int, int]
    center: Tuple[int, int]
    importance: str         # "critical", "important", "optional"
    action: str             # "remove", "reconnect", "observe"


class ARComponentDetector:
    """Manages YOLO models for different device categories"""
    
    def __init__(self, models_dir: str = "models/yolo"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.current_model = None
        self.reference_anchors: List[ReferenceAnchor] = []
        
        # Model mapping
        self.model_map = {
            'laptop': 'laptop_yolo_v8.pt',
            'pc': 'laptop_yolo_v8.pt',
            'computer': 'laptop_yolo_v8.pt',
            'phone': 'phone_yolo_v8.pt',
            'tablet': 'tablet_yolo_v8.pt',
            'mac': 'laptop_yolo_v8.pt',  # Macs use laptop model
        }
        
    def load_model_for_category(self, category: str) -> bool:
        """Load appropriate YOLO model based on device category"""
        try:
            category_lower = category.lower()
            model_name = self.model_map.get(category_lower, 'laptop_yolo_v8.pt')
            
            if model_name not in self.models:
                # TODO: Load actual YOLOv8 model
                # from ultralytics import YOLO
                # self.models[model_name] = YOLO(self.models_dir / model_name)
                print(f"[AR] Loading model: {model_name} for category: {category}")
                # Placeholder for now
                self.models[model_name] = None
            
            self.current_model = self.models[model_name]
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load model for {category}: {e}")
            return False
    
    def process_reference_image(self, image_path: str, step_number: int) -> List[ReferenceAnchor]:
        """
        Phase 1: Analyze tutorial step image to extract component positions
        
        Args:
            image_path: Path to tutorial step image
            step_number: Current step number
            
        Returns:
            List of reference anchors for this step
        """
        anchors = []
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"[WARN] Could not load reference image: {image_path}")
                return anchors
            
            # TODO: Run YOLO detection on reference image
            # results = self.current_model(image)
            # for detection in results:
            #     anchor = self._create_anchor_from_detection(detection, step_number)
            #     anchors.append(anchor)
            
            # Placeholder: Mock detection results
            print(f"[AR] Processing reference image for step {step_number}")
            print(f"[AR] Image: {image_path}")
            
            # Example anchors (in real implementation, these come from YOLO)
            if step_number == 1:
                anchors = [
                    ReferenceAnchor(
                        component_id=f"step{step_number}_screw_1",
                        label="screw",
                        bbox=(150, 200, 170, 220),
                        center=(160, 210),
                        importance="critical",
                        action="remove"
                    ),
                    ReferenceAnchor(
                        component_id=f"step{step_number}_screw_2",
                        label="screw",
                        bbox=(400, 200, 420, 220),
                        center=(410, 210),
                        importance="critical",
                        action="remove"
                    )
                ]
            
            self.reference_anchors = anchors
            return anchors
            
        except Exception as e:
            print(f"[ERROR] Reference image processing failed: {e}")
            return []
    
    def detect_in_live_feed(self, frame: np.ndarray) -> List[DetectedComponent]:
        """
        Phase 2: Detect components in live camera feed
        
        Args:
            frame: Current camera frame (numpy array)
            
        Returns:
            List of detected components
        """
        detections = []
        
        try:
            if self.current_model is None:
                return detections
            
            # TODO: Run YOLO on live frame when model is trained
            # results = self.current_model(frame)
            # for result in results:
            #     component = self._create_component_from_result(result)
            #     detections.append(component)
            
            # Placeholder: Will be implemented after YOLO training
            
        except Exception as e:
            print(f"[ERROR] Live detection failed: {e}")
            
        return detections
    
    def match_and_overlay(
        self, 
        frame: np.ndarray, 
        detections: List[DetectedComponent]
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Phase 3: Match detected components with reference anchors and draw AR overlay
        
        Args:
            frame: Current camera frame
            detections: Components detected in current frame
            
        Returns:
            (annotated_frame, matched_components)
        """
        annotated_frame = frame.copy()
        matched = []
        
        for anchor in self.reference_anchors:
            # Find closest matching detection
            best_match = self._find_best_match(anchor, detections)
            
            if best_match:
                # Draw AR overlay on matched component
                color = self._get_overlay_color(anchor.importance, anchor.action)
                annotated_frame = self._draw_ar_overlay(
                    annotated_frame, 
                    best_match.bbox,
                    anchor.label,
                    anchor.action,
                    color
                )
                
                matched.append({
                    'component_id': anchor.component_id,
                    'label': anchor.label,
                    'confidence': best_match.confidence,
                    'action': anchor.action
                })
        
        return annotated_frame, matched
    
    def _find_best_match(
        self, 
        anchor: ReferenceAnchor, 
        detections: List[DetectedComponent]
    ) -> Optional[DetectedComponent]:
        """Find detection that best matches reference anchor"""
        candidates = [d for d in detections if d.label == anchor.label]
        
        if not candidates:
            return None
        
        # For now, return highest confidence match
        # TODO: Use spatial proximity + confidence score
        return max(candidates, key=lambda x: x.confidence)
    
    def _get_overlay_color(self, importance: str, action: str) -> Tuple[int, int, int]:
        """Get color for AR overlay based on importance and action"""
        if action == "remove":
            return (0, 0, 255)  # Red for removal
        elif action == "reconnect":
            return (0, 255, 0)  # Green for connection
        elif importance == "critical":
            return (255, 0, 0)  # Blue for critical observation
        else:
            return (255, 255, 0)  # Cyan for optional
    
    def _draw_ar_overlay(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        label: str,
        action: str,
        color: Tuple[int, int, int]
    ) -> np.ndarray:
        """Draw AR overlay on detected component"""
        x1, y1, x2, y2 = bbox
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        
        # Draw label with action
        text = f"{action.upper()} {label}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Text background
        (text_width, text_height), _ = cv2.getTextSize(text, font, 0.6, 2)
        cv2.rectangle(
            frame, 
            (x1, y1 - text_height - 10), 
            (x1 + text_width + 10, y1),
            color,
            -1
        )
        
        # Text
        cv2.putText(
            frame, 
            text, 
            (x1 + 5, y1 - 5), 
            font, 
            0.6, 
            (255, 255, 255), 
            2
        )
        
        # Draw arrow or highlight for emphasis
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        cv2.drawMarker(
            frame,
            (center_x, center_y),
            color,
            markerType=cv2.MARKER_CROSS,
            markerSize=30,
            thickness=3
        )
        
        return frame
    
    def save_anchors_for_step(self, tutorial_id: int, step_number: int, output_dir: str):
        """Save processed anchors to JSON for caching"""
        output_path = Path(output_dir) / f"tutorial_{tutorial_id}_step_{step_number}_anchors.json"
        
        anchors_data = [
            {
                'component_id': a.component_id,
                'label': a.label,
                'bbox': a.bbox,
                'center': a.center,
                'importance': a.importance,
                'action': a.action
            }
            for a in self.reference_anchors
        ]
        
        with open(output_path, 'w') as f:
            json.dump(anchors_data, f, indent=2)
        
        print(f"[AR] Saved {len(anchors_data)} anchors to {output_path}")
    
    def load_anchors_for_step(self, tutorial_id: int, step_number: int, anchors_dir: str) -> bool:
        """Load pre-processed anchors from cache"""
        anchors_path = Path(anchors_dir) / f"tutorial_{tutorial_id}_step_{step_number}_anchors.json"
        
        if not anchors_path.exists():
            return False
        
        try:
            with open(anchors_path, 'r') as f:
                anchors_data = json.load(f)
            
            self.reference_anchors = [
                ReferenceAnchor(
                    component_id=a['component_id'],
                    label=a['label'],
                    bbox=tuple(a['bbox']),
                    center=tuple(a['center']),
                    importance=a['importance'],
                    action=a['action']
                )
                for a in anchors_data
            ]
            
            print(f"[AR] Loaded {len(self.reference_anchors)} anchors from cache")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load anchors: {e}")
            return False


# Example usage
if __name__ == "__main__":
    detector = ARComponentDetector()
    
    # Load laptop model
    detector.load_model_for_category('laptop')
    
    # Process reference image
    anchors = detector.process_reference_image(
        "assets/lenovo/ideapad_5/step1_bottom_cover.jpg",
        step_number=1
    )
    
    print(f"\nExtracted {len(anchors)} reference anchors:")
    for anchor in anchors:
        print(f"  - {anchor.component_id}: {anchor.label} ({anchor.action})")
