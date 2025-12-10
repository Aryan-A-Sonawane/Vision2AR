"""
AR Overlay Generator

Generates WebXR-compatible overlay metadata for AR rendering.
Maps repair step instructions to bounding boxes on device images.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class OverlayType(Enum):
    """Types of AR overlays"""
    HIGHLIGHT = "highlight"  # Highlight component area
    ARROW = "arrow"  # Directional arrow
    LABEL = "label"  # Text label
    DANGER = "danger"  # Warning indicator
    SEQUENCE = "sequence"  # Numbered sequence


@dataclass
class BoundingBox:
    """Bounding box coordinates for AR overlay"""
    x: int  # Top-left X
    y: int  # Top-left Y
    width: int
    height: int
    type: OverlayType
    label: str  # Display text
    z_index: int = 1  # Layer order


class AROverlayGenerator:
    """
    Generates AR overlay data for WebXR rendering.
    
    Workflow:
    1. Load repair step metadata
    2. Load image with overlay anchor points
    3. Generate bounding boxes for AR highlights
    4. Return overlay.json for frontend
    """
    
    def __init__(self, image_width: int = 1920, image_height: int = 1080):
        self.image_width = image_width
        self.image_height = image_height
    
    def generate_overlay(
        self,
        step_metadata: Dict,
        anchor_points: List[Dict]
    ) -> Dict:
        """
        Generate complete overlay metadata for a repair step.
        
        Args:
            step_metadata: Step data from TutorialMerger
            anchor_points: List of {"x": int, "y": int, "type": str}
        
        Returns:
            Overlay JSON for WebXR rendering
        """
        overlays = []
        
        # Generate bounding boxes for each anchor
        for idx, anchor in enumerate(anchor_points):
            bbox = self._create_bounding_box(
                anchor["x"],
                anchor["y"],
                anchor["type"],
                step_metadata.get("action", ""),
                idx + 1
            )
            overlays.append(bbox)
        
        # Add warning overlays for high-risk steps
        if step_metadata.get("risk") == "high":
            warning_overlay = self._create_warning_overlay(
                step_metadata.get("warnings", [])
            )
            overlays.append(warning_overlay)
        
        return {
            "step_id": step_metadata["id"],
            "image": step_metadata["image"],
            "overlays": [self._bbox_to_dict(o) for o in overlays],
            "tts_text": step_metadata.get("tts_text", ""),
            "video_timestamp": step_metadata.get("video")
        }
    
    def _create_bounding_box(
        self,
        x: int,
        y: int,
        anchor_type: str,
        action: str,
        sequence_num: int
    ) -> BoundingBox:
        """Create bounding box based on anchor type"""
        size_map = {
            "screw": (40, 40),
            "connector": (80, 60),
            "component": (150, 100),
            "cable": (100, 200)
        }
        
        width, height = size_map.get(anchor_type, (60, 60))
        
        overlay_type_map = {
            "screw": OverlayType.SEQUENCE,
            "connector": OverlayType.ARROW,
            "component": OverlayType.HIGHLIGHT,
            "cable": OverlayType.HIGHLIGHT
        }
        
        return BoundingBox(
            x=x - width // 2,  # Center the box
            y=y - height // 2,
            width=width,
            height=height,
            type=overlay_type_map.get(anchor_type, OverlayType.HIGHLIGHT),
            label=f"{sequence_num}. {action}" if anchor_type == "screw" else "",
            z_index=1
        )
    
    def _create_warning_overlay(self, warnings: List[str]) -> BoundingBox:
        """Create warning overlay at top of image"""
        return BoundingBox(
            x=self.image_width // 2 - 200,
            y=50,
            width=400,
            height=80,
            type=OverlayType.DANGER,
            label=warnings[0] if warnings else "Caution required",
            z_index=10  # Always on top
        )
    
    def _bbox_to_dict(self, bbox: BoundingBox) -> Dict:
        """Convert BoundingBox to JSON-serializable dict"""
        return {
            "x": bbox.x,
            "y": bbox.y,
            "width": bbox.width,
            "height": bbox.height,
            "type": bbox.type.value,
            "label": bbox.label,
            "z_index": bbox.z_index
        }
    
    def validate_anchors(self, anchors: List[Dict]) -> bool:
        """
        Validate anchor points are within image bounds.
        
        Critical: Prevent out-of-bounds overlays that break AR rendering.
        """
        for anchor in anchors:
            if not (0 <= anchor["x"] <= self.image_width):
                return False
            if not (0 <= anchor["y"] <= self.image_height):
                return False
        return True
    
    def load_overlay_config(self, config_path: str) -> Dict:
        """
        Load pre-configured overlay anchors from JSON.
        
        Expected format:
        {
          "image": "assets/lenovo/ideapad_5/step6_cover.jpg",
          "anchors": [
            {"x": 120, "y": 340, "type": "screw"},
            {"x": 180, "y": 340, "type": "screw"}
          ]
        }
        """
        import json
        with open(config_path, 'r') as f:
            return json.load(f)


# Example usage
if __name__ == "__main__":
    generator = AROverlayGenerator()
    
    # Example step metadata from TutorialMerger
    step_metadata = {
        "id": 6,
        "action": "Remove bottom cover",
        "tools": ["Torx-5"],
        "risk": "safe",
        "image": "assets/lenovo/ideapad_5/step6_cover.jpg",
        "tts_text": "Step 6. Remove bottom cover. You will need: Torx-5.",
        "video": "03:20-03:40"
    }
    
    # Example anchor points
    anchor_points = [
        {"x": 120, "y": 340, "type": "screw"},
        {"x": 180, "y": 340, "type": "screw"},
        {"x": 120, "y": 640, "type": "screw"},
        {"x": 180, "y": 640, "type": "screw"}
    ]
    
    # Validate anchors
    if generator.validate_anchors(anchor_points):
        overlay = generator.generate_overlay(step_metadata, anchor_points)
        print("Generated overlay:")
        import json
        print(json.dumps(overlay, indent=2))
    else:
        print("Invalid anchor points!")
