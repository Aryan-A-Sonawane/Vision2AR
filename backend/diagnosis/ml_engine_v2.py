"""
ML-Powered Diagnosis Engine V2 - True ML Implementation
Features:
- Multi-modal input (text, images, video)
- LLM-based dynamic question generation
- Computer vision for visual diagnosis
- Semantic understanding with embeddings
- Continuous learning from interactions
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass, asdict
import torch
import base64
from PIL import Image
import io


@dataclass
class MultiModalInput:
    """Input with text, images, and video"""
    text: str
    images: List[str] = None  # Base64 encoded or file paths
    video_path: Optional[str] = None
    timestamp: str = None


@dataclass
class DiagnosisSession:
    """Track diagnosis session for learning"""
    session_id: str
    device_model: str
    conversation_history: List[Dict]  # Full conversation with multi-modal inputs
    final_diagnosis: Optional[str]
    confidence: float
    timestamp: str
    media_analysis: List[Dict]  # Results from image/video analysis


@dataclass
class DiagnosisResult:
    """Complete diagnosis with solution"""
    cause: str
    confidence: float
    solution_steps: List[str]
    easy_fix: Optional[str]
    tools_needed: List[str]
    risk_level: str
    source_breakdown: Dict[str, List[str]]
    related_guides: List[str]
    visual_evidence: List[str]  # Images/video timestamps that helped diagnosis


class MLDiagnosisEngineV2:
    """
    Advanced ML-powered diagnosis engine with:
    - Multi-modal understanding (text + vision)
    - Dynamic question generation using LLM
    - Context-aware conversation flow
    - Visual analysis for hardware issues
    """
    
    def __init__(self, db_path: str = "diagnosis_knowledge.db"):
        """Initialize ML models"""
        print("Loading ML models...")
        
        # Text understanding
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Image analysis models (will load on demand)
        self.vision_model = None
        self.vlm_model = None  # Vision-Language Model for image understanding
        
        # LLM for question generation (would use OpenAI/Anthropic API or local model)
        self.llm_available = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        
        # Knowledge base
        self.db_path = db_path
        self.knowledge_base = self._load_knowledge_base()
        
        print(f"✓ Text model loaded: {self.text_model}")
        print(f"✓ LLM available: {self.llm_available}")
        
    def _load_knowledge_base(self) -> Dict:
        """Load repair knowledge from database"""
        # TODO: Connect to PostgreSQL and load repair procedures
        return {
            "device_patterns": {},
            "symptom_embeddings": [],
            "repair_procedures": []
        }
    
    def _load_vision_models(self):
        """Lazy load vision models only when needed"""
        if self.vision_model is None:
            try:
                from transformers import AutoProcessor, AutoModelForVision2Seq
                print("Loading vision-language model...")
                # Use BLIP-2 or LLaVA for image understanding
                model_name = "Salesforce/blip2-opt-2.7b"
                self.vlm_processor = AutoProcessor.from_pretrained(model_name)
                self.vlm_model = AutoModelForVision2Seq.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                print("✓ Vision model loaded")
            except Exception as e:
                print(f"⚠ Vision model not available: {e}")
    
    async def start_diagnosis(
        self,
        device_model: str,
        initial_input: MultiModalInput
    ) -> Tuple[str, Optional[DiagnosisResult], Dict]:
        """
        Start diagnosis with multi-modal input
        Returns: (next_question, diagnosis_if_complete, debug_info)
        """
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "device": device_model,
            "input_modalities": {
                "text": bool(initial_input.text),
                "images": len(initial_input.images) if initial_input.images else 0,
                "video": bool(initial_input.video_path)
            }
        }
        
        # 1. Analyze text symptoms
        text_embedding = self.text_model.encode(initial_input.text)
        text_analysis = await self._analyze_text_symptoms(
            initial_input.text,
            text_embedding,
            device_model
        )
        debug_info["text_analysis"] = text_analysis
        
        # 2. Analyze images if provided
        image_analysis = []
        if initial_input.images:
            self._load_vision_models()
            for img in initial_input.images:
                analysis = await self._analyze_image(img, initial_input.text)
                image_analysis.append(analysis)
        debug_info["image_analysis"] = image_analysis
        
        # 3. Analyze video if provided
        video_analysis = None
        if initial_input.video_path:
            video_analysis = await self._analyze_video(
                initial_input.video_path,
                initial_input.text
            )
        debug_info["video_analysis"] = video_analysis
        
        # 4. Combine all signals to build initial understanding
        combined_understanding = self._combine_multimodal_signals(
            text_analysis,
            image_analysis,
            video_analysis
        )
        debug_info["combined_confidence"] = combined_understanding.get("confidence", 0.0)
        
        # 5. Check if we have enough confidence for immediate diagnosis
        if combined_understanding["confidence"] > 0.75:
            diagnosis = self._build_diagnosis(
                combined_understanding["top_cause"],
                combined_understanding["confidence"],
                debug_info
            )
            return None, diagnosis, debug_info
        
        # 6. Generate next question using LLM based on current understanding
        next_question = await self._generate_contextual_question(
            initial_input.text,
            image_analysis,
            combined_understanding,
            conversation_history=[]
        )
        
        return next_question, None, debug_info
    
    async def _analyze_text_symptoms(
        self,
        text: str,
        embedding: np.ndarray,
        device_model: str
    ) -> Dict:
        """Deep analysis of text symptoms using NLP"""
        
        # Extract key information from text
        analysis = {
            "raw_text": text,
            "key_symptoms": [],
            "implicit_info": {},
            "confidence": 0.0,
            "potential_causes": []
        }
        
        # Use embeddings to find similar past cases
        # TODO: Query vector database for similar symptoms
        
        # Extract implicit information (e.g., "won't turn on" implies power issue)
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["won't turn on", "not turning on", "dead", "no power"]):
            analysis["key_symptoms"].append("power_failure")
            analysis["implicit_info"]["power_related"] = True
            analysis["potential_causes"] = ["battery_issue", "power_supply", "motherboard"]
            
        if any(word in text_lower for word in ["screen", "display", "black screen", "no display"]):
            analysis["key_symptoms"].append("display_issue")
            analysis["implicit_info"]["display_related"] = True
            
        if any(word in text_lower for word in ["fan", "noise", "loud", "spinning"]):
            analysis["key_symptoms"].append("fan_issue")
            analysis["implicit_info"]["cooling_related"] = True
            
        if any(word in text_lower for word in ["hot", "heat", "overheating", "warm"]):
            analysis["key_symptoms"].append("thermal_issue")
            
        if any(word in text_lower for word in ["slow", "lag", "freeze", "hang"]):
            analysis["key_symptoms"].append("performance_issue")
        
        # Initial confidence based on specificity
        if len(analysis["key_symptoms"]) > 0:
            analysis["confidence"] = 0.3 + (len(analysis["key_symptoms"]) * 0.1)
        
        return analysis
    
    async def _analyze_image(self, image_data: str, context: str) -> Dict:
        """Analyze image using computer vision"""
        
        if self.vlm_model is None:
            return {"error": "Vision model not loaded", "confidence": 0.0}
        
        try:
            # Decode base64 image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Generate description using vision-language model
            prompt = f"Analyze this laptop image in context of: {context}. Describe any visible issues, damage, or indicators."
            
            inputs = self.vlm_processor(image, prompt, return_tensors="pt").to(
                self.vlm_model.device, torch.float16
            )
            
            generated_ids = self.vlm_model.generate(**inputs, max_new_tokens=100)
            description = self.vlm_processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]
            
            # Extract findings from description
            analysis = {
                "description": description,
                "detected_issues": [],
                "confidence": 0.5,
                "visual_evidence": True
            }
            
            # Parse description for specific issues
            desc_lower = description.lower()
            if any(word in desc_lower for word in ["crack", "broken", "damage"]):
                analysis["detected_issues"].append("physical_damage")
                analysis["confidence"] = 0.8
                
            if any(word in desc_lower for word in ["led", "light", "indicator"]):
                analysis["detected_issues"].append("led_status")
                analysis["confidence"] = 0.7
            
            return analysis
            
        except Exception as e:
            return {"error": str(e), "confidence": 0.0}
    
    async def _analyze_video(self, video_path: str, context: str) -> Dict:
        """Analyze video for dynamic issues (fans, sounds, boot sequence)"""
        
        # TODO: Implement video analysis
        # - Extract frames at intervals
        # - Analyze each frame
        # - Detect motion (fan spinning)
        # - Audio analysis for beeps/sounds
        
        return {
            "frames_analyzed": 0,
            "motion_detected": False,
            "audio_analysis": {},
            "confidence": 0.0
        }
    
    def _combine_multimodal_signals(
        self,
        text_analysis: Dict,
        image_analysis: List[Dict],
        video_analysis: Optional[Dict]
    ) -> Dict:
        """Combine text, image, and video analysis into unified understanding"""
        
        combined = {
            "top_cause": None,
            "confidence": 0.0,
            "evidence": {
                "text": text_analysis.get("key_symptoms", []),
                "visual": [],
                "audio": []
            },
            "belief_vector": {}
        }
        
        # Start with text-based causes
        potential_causes = text_analysis.get("potential_causes", [])
        
        # Initialize belief vector
        if potential_causes:
            base_prob = 1.0 / len(potential_causes)
            for cause in potential_causes:
                combined["belief_vector"][cause] = base_prob
        
        # Boost confidence if visual evidence supports
        for img_analysis in image_analysis:
            if img_analysis.get("visual_evidence"):
                combined["confidence"] += 0.15
                combined["evidence"]["visual"].extend(
                    img_analysis.get("detected_issues", [])
                )
        
        # Update belief vector based on visual evidence
        for img_analysis in image_analysis:
            for issue in img_analysis.get("detected_issues", []):
                if "damage" in issue:
                    combined["belief_vector"]["physical_damage"] = 0.7
                elif "led" in issue:
                    combined["belief_vector"]["power_supply"] = \
                        combined["belief_vector"].get("power_supply", 0.3) * 1.5
        
        # Normalize belief vector
        total = sum(combined["belief_vector"].values())
        if total > 0:
            combined["belief_vector"] = {
                k: v/total for k, v in combined["belief_vector"].items()
            }
            combined["top_cause"] = max(
                combined["belief_vector"].items(),
                key=lambda x: x[1]
            )[0]
            combined["confidence"] = combined["belief_vector"][combined["top_cause"]]
        
        return combined
    
    async def _generate_contextual_question(
        self,
        initial_symptoms: str,
        image_analysis: List[Dict],
        current_understanding: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """Generate next question using LLM based on conversation context"""
        
        # Build context for LLM
        context = f"""You are diagnosing a laptop issue. 

Initial symptoms: {initial_symptoms}

Current understanding:
- Top suspected cause: {current_understanding.get('top_cause', 'unknown')}
- Confidence: {current_understanding.get('confidence', 0.0):.0%}
- Evidence so far: {current_understanding.get('evidence', {})}

Visual analysis: {image_analysis if image_analysis else 'No images provided'}

Conversation so far:
{self._format_conversation_history(conversation_history)}

Generate the MOST IMPORTANT follow-up question to ask the user to narrow down the diagnosis. 
The question should:
1. Be open-ended to gather maximum information
2. Help distinguish between possible causes
3. Be technically specific but user-friendly
4. Request specific observations, not yes/no

Return ONLY the question text, nothing else."""

        # If LLM available, use it for dynamic question generation
        if self.llm_available:
            question = await self._call_llm(context)
        else:
            # Fallback: Use template-based questions
            question = self._generate_template_question(current_understanding)
        
        return {
            "text": question,
            "type": "open_ended",
            "allows_media": True,
            "suggested_media": self._suggest_media_type(current_understanding)
        }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API for question generation"""
        
        # TODO: Implement actual LLM API call
        # For now, return intelligent template
        
        return "Can you describe exactly what happens when you press the power button? Include any lights, sounds, or screen activity you observe, and feel free to upload a photo or video."
    
    def _generate_template_question(self, understanding: Dict) -> str:
        """Fallback question generation using templates"""
        
        top_cause = understanding.get("top_cause")
        
        if top_cause == "battery_issue":
            return "When you plug in the charger, do you see any LED indicators? If yes, what color are they and do they blink or stay solid? A photo would be very helpful."
            
        elif top_cause == "power_supply":
            return "Describe what happens in the first 3-5 seconds after pressing power. Do you hear any sounds (fans, beeps)? See any lights? Feel free to record a short video."
            
        elif top_cause == "motherboard":
            return "Can you describe the screen behavior? Is it completely black, showing backlight, or displaying anything at all? A photo of the screen would help."
            
        else:
            return "Please provide more details about the issue. What exactly happens (or doesn't happen) when you try to use the laptop? Include any unusual sounds, lights, or behaviors."
    
    def _suggest_media_type(self, understanding: Dict) -> List[str]:
        """Suggest what type of media would be most helpful"""
        
        top_cause = understanding.get("top_cause")
        suggestions = []
        
        if top_cause in ["battery_issue", "power_supply"]:
            suggestions.append("photo_of_leds")
            suggestions.append("video_of_boot_attempt")
            
        elif top_cause == "motherboard":
            suggestions.append("photo_of_screen")
            suggestions.append("video_of_boot_sequence")
            
        elif top_cause == "display_issue":
            suggestions.append("photo_of_screen")
            
        return suggestions
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation for LLM context"""
        
        formatted = []
        for entry in history:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    async def process_answer(
        self,
        session_id: str,
        answer_text: str,
        media: Optional[MultiModalInput],
        conversation_history: List[Dict],
        current_understanding: Dict
    ) -> Tuple[Optional[str], Optional[DiagnosisResult], Dict]:
        """
        Process user's answer with optional media attachments
        Returns: (next_question, diagnosis_if_complete, debug_info)
        """
        
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "answer_length": len(answer_text),
            "media_provided": bool(media)
        }
        
        # 1. Analyze the text answer
        answer_embedding = self.text_model.encode(answer_text)
        answer_analysis = await self._analyze_text_symptoms(
            answer_text,
            answer_embedding,
            ""  # Device model already in session
        )
        
        # 2. Analyze any new media
        new_image_analysis = []
        if media and media.images:
            self._load_vision_models()
            for img in media.images:
                analysis = await self._analyze_image(img, answer_text)
                new_image_analysis.append(analysis)
        
        # 3. Update understanding based on new information
        updated_understanding = self._update_understanding(
            current_understanding,
            answer_analysis,
            new_image_analysis
        )
        
        debug_info["updated_confidence"] = updated_understanding["confidence"]
        debug_info["top_cause"] = updated_understanding["top_cause"]
        
        # 4. Check if we have enough confidence for diagnosis
        if updated_understanding["confidence"] >= 0.65 or len(conversation_history) >= 4:
            diagnosis = self._build_diagnosis(
                updated_understanding["top_cause"],
                updated_understanding["confidence"],
                debug_info
            )
            return None, diagnosis, debug_info
        
        # 5. Generate next question
        next_question = await self._generate_contextual_question(
            "",  # Initial symptoms already in context
            new_image_analysis,
            updated_understanding,
            conversation_history
        )
        
        return next_question, None, debug_info
    
    def _update_understanding(
        self,
        current: Dict,
        new_text_analysis: Dict,
        new_image_analysis: List[Dict]
    ) -> Dict:
        """Update belief vector and confidence with new information"""
        
        updated = current.copy()
        
        # Merge new symptoms
        updated["evidence"]["text"].extend(
            new_text_analysis.get("key_symptoms", [])
        )
        
        # Update belief vector with new text insights
        for cause in new_text_analysis.get("potential_causes", []):
            if cause in updated["belief_vector"]:
                updated["belief_vector"][cause] *= 1.5
            else:
                updated["belief_vector"][cause] = 0.4
        
        # Boost from visual evidence
        for img_analysis in new_image_analysis:
            if img_analysis.get("visual_evidence"):
                updated["confidence"] += 0.1
                for issue in img_analysis.get("detected_issues", []):
                    related_cause = self._map_visual_issue_to_cause(issue)
                    if related_cause:
                        updated["belief_vector"][related_cause] = \
                            updated["belief_vector"].get(related_cause, 0.3) * 1.8
        
        # Normalize
        total = sum(updated["belief_vector"].values())
        if total > 0:
            updated["belief_vector"] = {
                k: v/total for k, v in updated["belief_vector"].items()
            }
            updated["top_cause"] = max(
                updated["belief_vector"].items(),
                key=lambda x: x[1]
            )[0]
            updated["confidence"] = updated["belief_vector"][updated["top_cause"]]
        
        return updated
    
    def _map_visual_issue_to_cause(self, visual_issue: str) -> Optional[str]:
        """Map visual findings to diagnostic causes"""
        
        mapping = {
            "physical_damage": "motherboard",
            "led_status": "power_supply",
            "screen_issue": "display_issue",
            "crack": "physical_damage"
        }
        
        for keyword, cause in mapping.items():
            if keyword in visual_issue:
                return cause
        
        return None
    
    def _build_diagnosis(
        self,
        cause: str,
        confidence: float,
        debug_info: Dict
    ) -> DiagnosisResult:
        """Build final diagnosis result"""
        
        # TODO: Query database for repair procedures
        
        # Placeholder diagnosis
        return DiagnosisResult(
            cause=cause,
            confidence=confidence,
            solution_steps=[
                "Step 1: Detailed repair step",
                "Step 2: Next action",
                "Step 3: Verification"
            ],
            easy_fix="Try this quick fix first",
            tools_needed=["Screwdriver", "Thermal paste"],
            risk_level="medium",
            source_breakdown={
                "OEM": ["Power diagnosis"],
                "iFixit": ["Disassembly guide"],
                "Community": ["Similar cases"]
            },
            related_guides=[],
            visual_evidence=[]
        )
    
    def save_session(self, session: DiagnosisSession):
        """Save session for ML training"""
        
        # TODO: Save to database for future learning
        pass
