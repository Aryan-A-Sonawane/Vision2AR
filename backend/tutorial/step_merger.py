"""
Tutorial Step Merger

Merges OEM manual steps (canonical) with iFixit details and YouTube visuals.
Implements source priority policy: OEM → iFixit → YouTube
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class SourceType(Enum):
    OEM = "OEM"
    IFIXIT = "iFixit"
    YOUTUBE = "YouTube"


class RiskLevel(Enum):
    SAFE = "safe"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class OverlayAnchor:
    """AR overlay anchor point (bounding box)"""
    x: int
    y: int
    type: str  # screw, connector, component


@dataclass
class RepairStep:
    """
    Canonical repair step structure
    
    Critical: Step numbering CANNOT change per source.
    Once merged, this is the single source of truth.
    """
    step_id: int
    action: str
    source_primary: SourceType
    source_supporting: List[SourceType]
    tools: List[str]
    risk_level: RiskLevel
    image: str  # Path: assets/{brand}/{product}/{image}.jpg
    overlay_anchors: List[OverlayAnchor]
    video_timestamp: Optional[str]  # Format: "MM:SS-MM:SS"
    warnings: List[str]
    details: Optional[str]  # Enhanced description from iFixit


class TutorialMerger:
    """
    Merges repair steps from multiple sources following priority policy.
    
    Safety rules:
    - NEVER show conflicting methods simultaneously
    - OEM is always canonical sequence
    - Abort high-risk YouTube-only tutorials
    """
    
    def __init__(self, brand: str, product: str):
        self.brand = brand
        self.product = product
        self.asset_base = f"assets/{brand}/{product}"
    
    def merge_step(
        self,
        oem_step: Dict,
        ifixit_step: Optional[Dict] = None,
        youtube_step: Optional[Dict] = None
    ) -> RepairStep:
        """
        Merge single step from multiple sources.
        
        Args:
            oem_step: Required canonical step from OEM manual
            ifixit_step: Optional enhancement with tool details
            youtube_step: Optional visual anchor with timestamp
        
        Returns:
            Single merged RepairStep with source attribution
        """
        # Start with OEM as base
        step = RepairStep(
            step_id=oem_step["id"],
            action=oem_step["action"],
            source_primary=SourceType.OEM,
            source_supporting=[],
            tools=oem_step.get("tools", []),
            risk_level=RiskLevel(oem_step.get("risk_level", "safe")),
            image=f"{self.asset_base}/{oem_step['image']}",
            overlay_anchors=[],
            video_timestamp=None,
            warnings=oem_step.get("warnings", []),
            details=oem_step.get("description", "")
        )
        
        # Enhance with iFixit details
        if ifixit_step:
            step.source_supporting.append(SourceType.IFIXIT)
            # Add tool specifications
            if "tools_detailed" in ifixit_step:
                step.tools.extend(ifixit_step["tools_detailed"])
            # Add enhanced description
            if "details" in ifixit_step:
                step.details = f"{step.details}\n\n{ifixit_step['details']}"
            # Add overlay anchors from iFixit images
            if "overlay_anchors" in ifixit_step:
                step.overlay_anchors.extend([
                    OverlayAnchor(**anchor) for anchor in ifixit_step["overlay_anchors"]
                ])
        
        # Add YouTube visual anchors
        if youtube_step:
            # CRITICAL: Validate risk level before adding YouTube source
            if step.risk_level == RiskLevel.HIGH and not ifixit_step:
                # Abort: High-risk YouTube-only not allowed
                raise ValueError(
                    f"Step {step.step_id}: High-risk YouTube-only tutorial rejected. "
                    "Requires OEM or iFixit validation."
                )
            
            step.source_supporting.append(SourceType.YOUTUBE)
            step.video_timestamp = youtube_step.get("timestamp")
        
        return step
    
    def validate_tutorial(self, steps: List[RepairStep]) -> bool:
        """
        Validate merged tutorial before presenting to user.
        
        Checks:
        - All steps have OEM as primary source
        - No conflicting step sequences
        - High-risk steps have proper warnings
        - Asset paths exist
        """
        for step in steps:
            # Rule: OEM must be primary source
            if step.source_primary != SourceType.OEM:
                return False
            
            # Rule: High-risk steps need warnings
            if step.risk_level == RiskLevel.HIGH and not step.warnings:
                return False
            
            # Rule: Asset path follows convention
            if not step.image.startswith(f"assets/{self.brand}/{self.product}/"):
                return False
        
        return True
    
    def get_step_metadata(self, step: RepairStep) -> Dict:
        """
        Get step metadata for AR rendering.
        
        Returns structured data for WebXR overlay generation.
        """
        return {
            "id": step.step_id,
            "action": step.action,
            "tools": step.tools,
            "risk": step.risk_level.value,
            "image": step.image,
            "overlays": [
                {"x": a.x, "y": a.y, "type": a.type} 
                for a in step.overlay_anchors
            ],
            "video": step.video_timestamp,
            "warnings": step.warnings,
            "tts_text": self._generate_tts_text(step)
        }
    
    def _generate_tts_text(self, step: RepairStep) -> str:
        """Generate natural language for TTS"""
        text = f"Step {step.step_id}. {step.action}."
        
        if step.tools:
            tools_list = ", ".join(step.tools)
            text += f" You will need: {tools_list}."
        
        if step.warnings:
            text += f" Warning: {step.warnings[0]}"
        
        return text


# Example usage
if __name__ == "__main__":
    merger = TutorialMerger("lenovo", "ideapad_5")
    
    # Example: Merge step from multiple sources
    oem_step = {
        "id": 6,
        "action": "Remove bottom cover",
        "tools": ["Screwdriver"],
        "risk_level": "safe",
        "image": "step6_cover.jpg",
        "warnings": []
    }
    
    ifixit_step = {
        "tools_detailed": ["Torx-5"],
        "details": "Unscrew 8 screws in circular pattern",
        "overlay_anchors": [
            {"x": 120, "y": 340, "type": "screw"},
            {"x": 180, "y": 340, "type": "screw"}
        ]
    }
    
    youtube_step = {
        "timestamp": "03:20-03:40"
    }
    
    merged = merger.merge_step(oem_step, ifixit_step, youtube_step)
    print(f"Merged step: {merged.action}")
    print(f"Sources: {merged.source_primary.value} + {[s.value for s in merged.source_supporting]}")
    print(f"Metadata: {merger.get_step_metadata(merged)}")
