"""
Multi-Modal Input Processor
Handles text analysis + context-conditioned BLIP-2 image analysis
"""
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import asyncpg
from sentence_transformers import SentenceTransformer

# BLIP-2 imports (will be lazy-loaded)
BLIP2_MODEL = None
BLIP2_PROCESSOR = None

class InputProcessor:
    """Processes text and image inputs for diagnostic system"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        
        # Load sentence transformer for text embeddings
        self.text_encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("[OK] Loaded text encoder (all-MiniLM-L6-v2)")
        
        # Brand detection patterns
        self.brand_patterns = {
            "lenovo": r"\b(lenovo|ideapad|thinkpad|yoga)\b",
            "dell": r"\b(dell|inspiron|xps|latitude|precision)\b",
            "hp": r"\b(hp|hewlett[\s-]?packard|pavilion|elitebook|omen)\b",
            "apple": r"\b(apple|macbook|imac|mac\s+pro)\b",
            "asus": r"\b(asus|vivobook|zenbook|rog)\b",
            "acer": r"\b(acer|aspire|predator|nitro)\b",
            "microsoft": r"\b(microsoft|surface)\b",
            "samsung": r"\b(samsung|galaxy\s+book)\b"
        }
        
        # Symptom detection patterns
        self.symptom_keywords = {
            "blue_screen": ["blue screen", "bsod", "stop error", "blue death"],
            "no_boot": ["won't boot", "no boot", "won't start", "won't turn on", "not starting", "dead", "not powering"],
            "black_screen": ["black screen", "blank screen", "no display", "screen is black", "screen off", "display off"],
            "overheating": ["hot", "overheat", "thermal", "burning", "very warm", "gets hot"],
            "screen_flickering": ["flicker", "flickering", "display artifact", "screen glitch", "lines on screen"],
            "battery_not_charging": ["battery", "charging", "won't charge", "not charging", "battery dead", "no charge"],
            "slow_performance": ["slow", "lag", "sluggish", "freeze", "hang", "unresponsive", "taking forever"],
            "fan_noise": ["fan noise", "loud fan", "fan rattling", "noisy", "loud noise", "making noise", "grinding noise", "fan spinning", "whirring"],
            "wifi_not_working": ["wifi", "wi-fi", "wireless", "no internet", "network", "can't connect", "disconnects"],
            "keyboard_issue": ["keyboard", "keys not working", "typing", "key stuck", "keys sticking"],
            "trackpad_issue": ["trackpad", "touchpad", "mouse pad", "cursor", "pointer"],
            "random_shutdown": ["random shutdown", "shuts down", "turns off", "powers off randomly", "unexpected shutdown"],
            "hard_drive_issue": ["hard drive", "disk", "storage", "ssd", "hdd", "not detected", "disk error"],
            "usb_not_working": ["usb", "port", "not recognized", "device not detected"],
            "strange_smell": ["smell", "burning smell", "smoke", "odor"],
            "physical_damage": ["cracked", "broken", "damaged", "dropped", "spilled", "liquid damage"],
            "boot_loop": ["keeps restarting", "boot loop", "reboot loop", "restart loop"],
            "beeping": ["beep", "beeping", "beeps", "beeping sound"]
        }
        
        # Error code patterns
        self.error_code_pattern = re.compile(
            r"(0x[0-9A-Fa-f]{8}|error[\s:]?\d+|stop[\s:]?0x[0-9A-Fa-f]+)",
            re.IGNORECASE
        )
    
    def _lazy_load_blip2(self):
        """Lazy load BLIP-2 model when first image is processed - NON-BLOCKING"""
        global BLIP2_MODEL, BLIP2_PROCESSOR
        
        if BLIP2_MODEL is None:
            try:
                from transformers import Blip2Processor, Blip2ForConditionalGeneration
                import torch
                import os
                import threading
                
                # Suppress symlink warnings on Windows
                os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
                
                print("[INFO] Starting BLIP-2 model loading in background thread...")
                print("⏳ Model will load in 2-3 minutes. Image analysis will be available after loading completes.")
                print("   Backend will remain responsive during this time.")
                
                def load_in_background():
                    global BLIP2_MODEL, BLIP2_PROCESSOR
                    try:
                        model_name = "Salesforce/blip2-opt-2.7b"
                        
                        print("   [1/2] Loading processor...")
                        BLIP2_PROCESSOR = Blip2Processor.from_pretrained(model_name)
                        
                        print("   [2/2] Loading model weights (15GB)...")
                        BLIP2_MODEL = Blip2ForConditionalGeneration.from_pretrained(
                            model_name,
                            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                            device_map="auto" if torch.cuda.is_available() else None,
                            low_cpu_mem_usage=True
                        )
                        
                        print("✅ BLIP-2 model loaded successfully!")
                        print(f"   Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
                    except Exception as e:
                        print(f"[WARN] BLIP-2 loading failed in background: {e}")
                        print("   Image analysis will not be available")
                
                # Start loading in background thread (non-blocking)
                loading_thread = threading.Thread(target=load_in_background, daemon=True)
                loading_thread.start()
                
            except Exception as e:
                print(f"[WARN] Failed to start BLIP-2 background loading: {e}")
                print("   Continuing without image analysis capability")
    
    async def process_text(self, text: str) -> Dict:
        """
        Process text input to extract keywords, brand, symptoms
        
        Returns: {
            "keywords": List[str],
            "brand": Optional[str],
            "brand_confidence": float,
            "symptoms": List[str],
            "error_codes": List[str],
            "category": str
        }
        """
        text_lower = text.lower()
        
        # Extract keywords (simple tokenization)
        words = re.findall(r'\b[a-z]{4,}\b', text_lower)
        keywords = list(set(words))[:10]  # Top 10 unique keywords
        
        # Brand detection
        brand = None
        brand_confidence = 0.0
        
        for brand_name, pattern in self.brand_patterns.items():
            if re.search(pattern, text_lower):
                brand = brand_name
                brand_confidence = 0.95
                break
        
        # Symptom detection
        symptoms = []
        for symptom, keyword_list in self.symptom_keywords.items():
            for kw in keyword_list:
                if kw in text_lower:
                    symptoms.append(symptom)
                    break
        
        # Error code extraction
        error_codes = self.error_code_pattern.findall(text)
        
        # Add error codes as symptoms
        if error_codes:
            for code in error_codes:
                symptom_key = f"error_{code.replace('0x', '').replace('x', '')}"
                symptoms.append(symptom_key)
        
        # Category detection (simplified)
        category = "PC"
        if brand == "apple":
            category = "Mac"
        elif any(word in text_lower for word in ["phone", "iphone", "android", "galaxy"]):
            category = "Phone"
        
        return {
            "keywords": keywords,
            "brand": brand,
            "brand_confidence": brand_confidence,
            "symptoms": list(set(symptoms)),
            "error_codes": error_codes,
            "category": category,
            "raw_text": text
        }
    
    async def process_image(
        self, 
        image_bytes: bytes, 
        context_text: Optional[str] = None
    ) -> Dict:
        """
        Process image with context-conditioned BLIP-2
        Uses user's text to guide image analysis
        
        Returns: {
            "caption": str,
            "visual_symptoms": List[str],
            "error_codes": List[str],
            "image_hash": str
        }
        """
        # Calculate image hash for caching
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        # Check cache first
        async with self.db_pool.acquire() as conn:
            cached = await conn.fetchrow("""
                SELECT blip_caption, visual_symptoms, context_text
                FROM image_caption_cache
                WHERE image_hash = $1
            """, image_hash)
            
            if cached and cached["context_text"] == context_text:
                print(f"[CACHE HIT] Image {image_hash[:8]}")
                return {
                    "caption": cached["blip_caption"],
                    "visual_symptoms": cached["visual_symptoms"],
                    "error_codes": [],
                    "image_hash": image_hash,
                    "cached": True
                }
        
        # Lazy load BLIP-2 if not already loaded
        self._lazy_load_blip2()
        
        if BLIP2_MODEL is None:
            return {
                "caption": "[Image analysis unavailable]",
                "visual_symptoms": [],
                "error_codes": [],
                "image_hash": image_hash,
                "cached": False
            }
        
        try:
            from PIL import Image
            import io
            
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Enhanced context-conditioned prompt with better instructions
            if context_text:
                # Extract key info from context
                context_lower = context_text.lower()
                
                # Build focused prompt based on symptoms
                if "screen" in context_lower or "display" in context_lower:
                    prompt = f"Question: What problems are visible on this laptop screen? Context: {context_text}. Answer: This image shows"
                elif "power" in context_lower or "turn on" in context_lower or "boot" in context_lower:
                    prompt = f"Question: What LED lights or indicators are visible when attempting to power on? Context: {context_text}. Answer: The image shows"
                elif "error" in context_lower or "message" in context_lower or "code" in context_lower:
                    prompt = f"Question: What error messages or codes are displayed on the screen? Context: {context_text}. Answer: The screen displays"
                elif "damage" in context_lower or "physical" in context_lower or "broken" in context_lower:
                    prompt = f"Question: What physical damage is visible on this device? Context: {context_text}. Answer: There is visible"
                else:
                    prompt = f"Question: Describe the laptop problem shown in this image. The user reports: {context_text}. Answer: This laptop has"
            else:
                prompt = "Question: What laptop or computer hardware problem is shown in this photo? Look for error messages, LED colors, screen issues, or physical damage. Answer: This image shows"
            
            print(f"[BLIP] Prompt: {prompt[:100]}...")
            
            # Check if BLIP-2 is loaded yet
            if BLIP2_MODEL is None:
                print("[WARN] BLIP-2 model still loading in background. Skipping image analysis for now.")
                return {
                    "caption": "Image uploaded. Visual analysis will be available once BLIP-2 finishes loading (2-3 minutes).",
                    "visual_symptoms": [],
                    "cached": False
                }
            
            # Generate caption
            inputs = BLIP2_PROCESSOR(images=image, text=prompt, return_tensors="pt")
            
            if BLIP2_MODEL.device.type == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            generated_ids = BLIP2_MODEL.generate(**inputs, max_length=150, min_length=20)
            caption = BLIP2_PROCESSOR.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            
            print(f"[BLIP] Caption: {caption}")
            print(f"[BLIP] Full response length: {len(caption)} chars")
            
            # Extract visual symptoms from caption
            visual_symptoms = []
            caption_lower = caption.lower()
            
            # Check for visual indicators
            if "blue screen" in caption_lower or "bsod" in caption_lower:
                visual_symptoms.append("blue_screen")
            
            if "black screen" in caption_lower or "blank" in caption_lower:
                visual_symptoms.append("black_screen")
            
            if "flicker" in caption_lower or "glitch" in caption_lower:
                visual_symptoms.append("screen_flickering")
            
            if "error" in caption_lower or "warning" in caption_lower:
                visual_symptoms.append("error_message_visible")
            
            if "led" in caption_lower or "light" in caption_lower:
                visual_symptoms.append("led_indicator")
            
            if "damage" in caption_lower or "crack" in caption_lower:
                visual_symptoms.append("physical_damage")
            
            # Extract error codes from caption
            error_codes = self.error_code_pattern.findall(caption)
            
            # Cache result
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO image_caption_cache 
                    (image_hash, blip_caption, visual_symptoms, context_text)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (image_hash) 
                    DO UPDATE SET 
                        blip_caption = EXCLUDED.blip_caption,
                        visual_symptoms = EXCLUDED.visual_symptoms,
                        context_text = EXCLUDED.context_text,
                        cached_at = CURRENT_TIMESTAMP
                """, image_hash, caption, visual_symptoms, context_text)
            
            return {
                "caption": caption,
                "visual_symptoms": visual_symptoms,
                "error_codes": error_codes,
                "image_hash": image_hash,
                "cached": False
            }
            
        except Exception as e:
            print(f"[ERROR] Image processing error: {e}")
            return {
                "caption": f"[Error: {str(e)}]",
                "visual_symptoms": [],
                "error_codes": [],
                "image_hash": image_hash,
                "cached": False
            }
    
    async def process_input(
        self,
        text_input: str,
        image_bytes: Optional[bytes] = None
    ) -> Dict:
        """
        Process complete user input (text + optional image)
        
        Returns: Complete processed input dict
        """
        # Process text
        text_result = await self.process_text(text_input)
        
        # Process image if provided
        image_result = None
        if image_bytes:
            image_result = await self.process_image(
                image_bytes,
                context_text=text_input[:200]  # First 200 chars as context
            )
        
        # Combine results
        combined = {
            **text_result,
            "visual_symptoms": image_result["visual_symptoms"] if image_result else [],
            "image_caption": image_result["caption"] if image_result else None,
            "image_hash": image_result["image_hash"] if image_result else None,
            "image_cached": image_result.get("cached", False) if image_result else False
        }
        
        # Merge error codes
        if image_result:
            combined["error_codes"].extend(image_result["error_codes"])
            combined["error_codes"] = list(set(combined["error_codes"]))
        
        return combined
