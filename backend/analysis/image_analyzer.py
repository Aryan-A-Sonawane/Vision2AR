"""
Image Analysis Module using BLIP (Bootstrapping Language-Image Pre-training)
Converts laptop problem images to text descriptions
"""

import torch
from PIL import Image
import io
import base64
from typing import Optional
from transformers import BlipProcessor, BlipForConditionalGeneration


class ImageAnalyzer:
    """
    Analyze laptop images to extract visual symptoms
    Uses BLIP model for image-to-text captioning
    """
    
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        print("🖼️  Initializing BLIP Image Analyzer...")
        
        # Load BLIP model and processor
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Device: {self.device}")
        
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name).to(self.device)
        
        print("  ✓ BLIP model loaded")
    
    def analyze_image(
        self,
        image_data: str = None,
        image_path: str = None,
        context: str = ""
    ) -> str:
        """
        Analyze laptop image and generate text description
        
        Args:
            image_data: Base64 encoded image string
            image_path: Path to image file
            context: Optional context (e.g., "laptop screen problem")
        
        Returns:
            Text description of what's in the image
        """
        
        # Load image
        if image_data:
            image = self._load_from_base64(image_data)
        elif image_path:
            image = Image.open(image_path).convert('RGB')
        else:
            raise ValueError("Must provide either image_data or image_path")
        
        print(f"\n🔍 ANALYZING IMAGE:")
        print(f"  Size: {image.size}")
        print(f"  Mode: {image.mode}")
        if context:
            print(f"  Context: {context}")
        
        # Generate description
        description = self._generate_description(image, context)
        
        print(f"  ✓ Generated Description: {description}")
        
        return description
    
    def _load_from_base64(self, base64_string: str) -> Image.Image:
        """Load image from base64 string"""
        # Remove data URL prefix if present
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        # Decode and load
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        return image
    
    def _generate_description(self, image: Image.Image, context: str = "") -> str:
        """Generate text description from image"""
        
        # Prepare inputs
        if context:
            # Conditional caption with context
            inputs = self.processor(
                image,
                text=f"A laptop with {context}",
                return_tensors="pt"
            ).to(self.device)
        else:
            # Unconditional caption
            inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        # Generate caption
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=50,
                num_beams=5,
                temperature=0.7
            )
        
        # Decode to text
        description = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        return description
    
    def analyze_error_screen(self, image_data: str = None, image_path: str = None) -> dict:
        """
        Specialized analysis for error screen images
        Tries to extract error messages, codes, logos
        
        Returns:
            {
                "description": str,
                "error_detected": bool,
                "visual_symptoms": List[str]
            }
        """
        
        # Get general description
        description = self.analyze_image(
            image_data=image_data,
            image_path=image_path,
            context="error screen or problem"
        )
        
        # Check for error indicators
        error_indicators = [
            "error", "blue screen", "black screen", "warning",
            "code", "message", "fail", "problem", "issue"
        ]
        
        error_detected = any(indicator in description.lower() 
                            for indicator in error_indicators)
        
        # Extract visual symptoms
        visual_symptoms = []
        
        # Common visual issues
        symptom_patterns = {
            "black screen": ["black", "dark", "blank"],
            "blue screen": ["blue", "bsod"],
            "distorted display": ["distorted", "glitch", "artifacts"],
            "physical damage": ["crack", "broken", "damaged", "shattered"],
            "discoloration": ["yellow", "purple", "tint", "color"],
            "lines on screen": ["line", "stripe", "band"],
            "no display": ["blank", "nothing", "empty"]
        }
        
        description_lower = description.lower()
        for symptom, keywords in symptom_patterns.items():
            if any(kw in description_lower for kw in keywords):
                visual_symptoms.append(symptom)
        
        print(f"\n📷 ERROR SCREEN ANALYSIS:")
        print(f"  Description: {description}")
        print(f"  Error Detected: {error_detected}")
        print(f"  Visual Symptoms: {visual_symptoms}")
        
        return {
            "description": description,
            "error_detected": error_detected,
            "visual_symptoms": visual_symptoms
        }


# Singleton instance
_analyzer = None

def get_image_analyzer() -> ImageAnalyzer:
    """Get or create global image analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ImageAnalyzer()
    return _analyzer
