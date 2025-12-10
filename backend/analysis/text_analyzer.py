"""
Text Analysis Module
Tokenize user queries, extract keywords, generate embeddings
"""

import re
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np


class TextAnalyzer:
    """
    Analyze user text input to extract meaningful information
    """
    
    def __init__(self, model: SentenceTransformer):
        self.model = model
        
        # Laptop-specific symptom keywords
        self.symptom_keywords = {
            # Display issues
            "display": ["screen", "display", "monitor", "lcd", "backlight", "dim", "flicker", 
                       "black", "blank", "dark", "bright", "lines", "artifacts"],
            # Power issues
            "power": ["power", "boot", "start", "turn on", "dead", "won't start", "no power",
                     "led", "light", "charge", "charging", "adapter", "battery"],
            # Performance
            "performance": ["slow", "freeze", "hang", "lag", "stuck", "unresponsive", 
                           "crash", "restart", "reboot"],
            # Thermal
            "thermal": ["hot", "heat", "overheat", "burn", "warm", "fan", "vent", 
                       "temperature", "thermal", "cooling"],
            # Audio
            "audio": ["sound", "audio", "speaker", "volume", "noise", "beep", 
                     "static", "distorted"],
            # Input
            "input": ["keyboard", "key", "type", "trackpad", "mouse", "touchpad",
                     "click", "button", "usb", "port"],
            # Storage
            "storage": ["hard drive", "ssd", "disk", "storage", "data", "file",
                       "not recognized", "slow loading"],
            # Network
            "network": ["wifi", "wireless", "internet", "network", "bluetooth",
                       "connection", "lan", "ethernet"]
        }
        
        # Common laptop components
        self.components = [
            "screen", "display", "lcd", "panel", "backlight",
            "battery", "charger", "adapter", "power",
            "keyboard", "trackpad", "touchpad",
            "fan", "heatsink", "thermal paste", "cooling",
            "ram", "memory", "ssd", "hard drive", "hdd",
            "motherboard", "mainboard", "cpu", "processor",
            "speaker", "audio", "webcam", "camera",
            "wifi", "bluetooth", "network card",
            "usb", "hdmi", "port", "connector"
        ]
        
        # Action words
        self.actions = [
            "not working", "broken", "damaged", "failed", "dead",
            "won't", "can't", "doesn't", "unable", "stopped",
            "replace", "fix", "repair", "troubleshoot", "diagnose"
        ]
    
    def analyze(self, text: str, brand: str = None) -> Dict:
        """
        Comprehensive text analysis
        
        Returns:
            {
                "original_text": str,
                "cleaned_text": str,
                "keywords": List[str],
                "symptom_categories": List[str],
                "components": List[str],
                "embedding": np.ndarray,
                "brand": str
            }
        """
        
        # Clean and normalize text
        cleaned = self._clean_text(text)
        
        # Extract keywords
        keywords = self._extract_keywords(cleaned)
        
        # Identify symptom categories
        categories = self._identify_categories(cleaned, keywords)
        
        # Identify components mentioned
        components = self._identify_components(cleaned)
        
        # Generate embedding
        embedding = self.model.encode(cleaned)
        
        print(f"\n📝 TEXT ANALYSIS:")
        print(f"  Original: {text}")
        print(f"  Cleaned: {cleaned}")
        print(f"  Keywords: {keywords}")
        print(f"  Categories: {categories}")
        print(f"  Components: {components}")
        print(f"  Embedding: {embedding.shape}")
        if brand:
            print(f"  Brand Filter: {brand}")
        
        return {
            "original_text": text,
            "cleaned_text": cleaned,
            "keywords": keywords,
            "symptom_categories": categories,
            "components": components,
            "embedding": embedding,
            "brand": brand
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        words = text.split()
        
        keywords = []
        
        # Add component keywords
        for component in self.components:
            comp_words = component.split()
            if len(comp_words) == 1:
                if component in words:
                    keywords.append(component)
            else:
                # Multi-word component
                if component in text:
                    keywords.append(component)
        
        # Add symptom keywords
        for category, symptom_words in self.symptom_keywords.items():
            for symptom in symptom_words:
                symptom_parts = symptom.split()
                if len(symptom_parts) == 1:
                    if symptom in words:
                        keywords.append(symptom)
                else:
                    if symptom in text:
                        keywords.append(symptom)
        
        # Add action keywords
        for action in self.actions:
            if action in text:
                keywords.append(action)
        
        # Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:15]  # Limit to top 15 keywords
    
    def _identify_categories(self, text: str, keywords: List[str]) -> List[str]:
        """Identify which symptom categories apply"""
        categories = []
        
        for category, symptom_words in self.symptom_keywords.items():
            # Check if any symptom words from this category are in text or keywords
            for symptom in symptom_words:
                if symptom in text or symptom in keywords:
                    categories.append(category)
                    break  # Category matched, move to next
        
        return categories
    
    def _identify_components(self, text: str) -> List[str]:
        """Identify laptop components mentioned in text"""
        mentioned = []
        
        for component in self.components:
            if component in text:
                mentioned.append(component)
        
        return mentioned
    
    def combine_with_image_analysis(
        self,
        text_analysis: Dict,
        image_description: str
    ) -> Dict:
        """
        Combine text analysis with image analysis
        
        Args:
            text_analysis: Output from self.analyze()
            image_description: BLIP model output
        
        Returns:
            Combined analysis with merged keywords and embedding
        """
        
        print(f"\n🖼️  COMBINING TEXT + IMAGE:")
        print(f"  Image Description: {image_description}")
        
        # Analyze image description
        image_analysis = self.analyze(image_description)
        
        # Merge keywords (deduplicate)
        combined_keywords = list(set(
            text_analysis["keywords"] + image_analysis["keywords"]
        ))
        
        # Merge categories
        combined_categories = list(set(
            text_analysis["symptom_categories"] + image_analysis["symptom_categories"]
        ))
        
        # Merge components
        combined_components = list(set(
            text_analysis["components"] + image_analysis["components"]
        ))
        
        # Create combined text for re-embedding
        combined_text = f"{text_analysis['cleaned_text']} {image_analysis['cleaned_text']}"
        
        # Generate combined embedding
        combined_embedding = self.model.encode(combined_text)
        
        print(f"  Combined Keywords: {combined_keywords}")
        print(f"  Combined Categories: {combined_categories}")
        print(f"  Combined Components: {combined_components}")
        
        return {
            "original_text": text_analysis["original_text"],
            "image_description": image_description,
            "combined_text": combined_text,
            "keywords": combined_keywords,
            "symptom_categories": combined_categories,
            "components": combined_components,
            "embedding": combined_embedding,
            "brand": text_analysis.get("brand")
        }
