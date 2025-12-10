"""
ML-Powered Diagnosis Engine with Learning
Uses sentence transformers for symptom embedding and pattern matching
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass, asdict
import torch


@dataclass
class DiagnosisSession:
    """Track diagnosis session for learning"""
    session_id: str
    device_model: str
    initial_symptoms: str
    questions_asked: List[Dict]
    answers_given: List[Dict]
    final_diagnosis: Optional[str]
    confidence: float
    timestamp: str
    source_contributions: Dict[str, float]  # Track which source helped


@dataclass
class DiagnosisResult:
    """Complete diagnosis with solution"""
    cause: str
    confidence: float
    solution_steps: List[str]
    easy_fix: Optional[str]
    tools_needed: List[str]
    risk_level: str
    source_breakdown: Dict[str, List[str]]  # Which source contributed what
    related_guides: List[str]


class MLDiagnosisEngine:
    """
    ML-powered diagnosis engine that:
    1. Embeds symptoms using sentence transformers
    2. Matches against known patterns
    3. Generates dynamic questions
    4. Learns from user interactions
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Load embedding model
        cache_dir = os.getenv("TRANSFORMERS_CACHE", ".cache/huggingface")
        self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
        
        # Learning storage (initialize before knowledge base)
        self.sessions_file = "diagnosis_sessions.jsonl"
        self.patterns_file = "learned_patterns.json"
        self.learned_patterns = self._load_learned_patterns()
        
        # Load knowledge base (from ingested data + learned patterns)
        self.knowledge_base = self._load_knowledge_base()
        self.question_templates = self._load_question_templates()
    
    def _load_knowledge_base(self) -> List[Dict]:
        """Load repair procedures from ingested data"""
        kb = []
        ingested_dir = "ingested_data"
        
        if os.path.exists(ingested_dir):
            for file in os.listdir(ingested_dir):
                if file.endswith('.json'):
                    with open(os.path.join(ingested_dir, file), 'r') as f:
                        data = json.load(f)
                        kb.append(data)
        
        # Add common issues from learned patterns
        kb.extend(self.learned_patterns.get("common_issues", []))
        
        return kb
    
    def _load_question_templates(self) -> List[Dict]:
        """Load dynamic question templates"""
        return [
            {
                "id": "power_led_check",
                "template": "Does the {indicator} light up when you {action}?",
                "signals": ["visual"],
                "cost": "safe",
                "gain": 0.35
            },
            {
                "id": "fan_spin_check",
                "template": "Do you hear the fan spin for {duration} when you power on?",
                "signals": ["audio"],
                "cost": "safe",
                "gain": 0.30
            },
            {
                "id": "display_check",
                "template": "Does the screen show {display_state}?",
                "signals": ["visual"],
                "cost": "safe",
                "gain": 0.40
            },
            {
                "id": "keyboard_response",
                "template": "Does the {key} key respond when pressed?",
                "signals": ["keyboard"],
                "cost": "safe",
                "gain": 0.25
            },
            {
                "id": "battery_behavior",
                "template": "Does the battery {behavior}?",
                "signals": ["visual", "time"],
                "cost": "safe",
                "gain": 0.30
            }
        ]
    
    def _load_learned_patterns(self) -> Dict:
        """Load patterns learned from previous sessions"""
        if os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return {"common_issues": [], "question_sequences": {}}
    
    def diagnose(
        self, 
        device_model: str, 
        symptoms: str,
        session_id: str
    ) -> Tuple[List[Dict], DiagnosisResult, Dict]:
        """
        Main diagnosis flow
        Returns: (questions, result, debug_info)
        """
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "device": device_model,
            "embedding_model": "all-MiniLM-L6-v2",
            "sources_used": [],
            "confidence_evolution": []
        }
        
        # 1. Embed symptoms
        symptom_embedding = self.model.encode(symptoms)
        debug_info["embedding_generated"] = True
        
        # 2. Find matching issues from knowledge base
        matches = self._find_matching_issues(symptom_embedding, device_model)
        debug_info["matches_found"] = len(matches)
        
        if matches:
            top_match = matches[0]
            debug_info["sources_used"].append({
                "source": top_match.get("source", "OEM"),
                "confidence": top_match["score"],
                "contribution": "Initial symptom match"
            })
        
        # 3. Generate adaptive questions
        questions = self._generate_questions(matches, device_model)
        debug_info["questions_generated"] = len(questions)
        
        # 4. If high confidence, return diagnosis
        if matches and matches[0]["score"] > 0.75:
            result = self._build_diagnosis_result(matches[0], debug_info)
            debug_info["early_diagnosis"] = True
            return questions, result, debug_info
        
        # Return questions for clarification
        return questions, None, debug_info
    
    def _find_matching_issues(
        self, 
        symptom_embedding: np.ndarray, 
        device_model: str
    ) -> List[Dict]:
        """Find matching issues using embedding similarity"""
        matches = []
        
        for issue in self.knowledge_base:
            # Filter by device if specified
            if "device_model" in issue:
                if device_model.lower() not in issue["device_model"].lower():
                    continue
            
            # Generate issue description for embedding
            issue_desc = f"{issue.get('component', '')} {issue.get('summary', '')}"
            if not issue_desc.strip():
                continue
            
            issue_embedding = self.model.encode(issue_desc)
            
            # Cosine similarity
            similarity = np.dot(symptom_embedding, issue_embedding) / (
                np.linalg.norm(symptom_embedding) * np.linalg.norm(issue_embedding)
            )
            
            matches.append({
                "issue": issue,
                "score": float(similarity),
                "source": issue.get("sources_used", ["OEM"])[0]
            })
        
        # Sort by similarity
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:5]  # Top 5 matches
    
    def _generate_questions(
        self, 
        matches: List[Dict], 
        device_model: str
    ) -> List[Dict]:
        """Generate dynamic questions based on matches"""
        questions = []
        
        if not matches:
            # Fallback to generic questions
            questions.append({
                "id": "power_led_check",
                "text": "Does the power LED light up when you press the power button?",
                "type": "binary",
                "expected_signal": "visual",
                "cost": "safe",
                "gain": 0.35
            })
            questions.append({
                "id": "fan_spin_check",
                "text": "Do you hear the fan spin for 2-3 seconds when you power on?",
                "type": "binary",
                "expected_signal": "audio",
                "cost": "safe",
                "gain": 0.30
            })
        else:
            # Generate context-aware questions
            top_issue = matches[0]["issue"]
            component = top_issue.get("component", "battery")
            
            if "battery" in component.lower():
                questions.append({
                    "id": "battery_led",
                    "text": "Does the battery charging LED light up when you plug in the charger?",
                    "type": "binary",
                    "expected_signal": "yes",
                    "cost": "safe",
                    "gain": 0.40
                })
                questions.append({
                    "id": "battery_drain",
                    "text": "Does the battery percentage drop rapidly even when not in use?",
                    "type": "binary",
                    "expected_signal": "yes",
                    "cost": "safe",
                    "gain": 0.35
                })
            
            elif "display" in component.lower() or "screen" in component.lower():
                questions.append({
                    "id": "display_flicker",
                    "text": "Does the screen flicker or show distorted images?",
                    "type": "binary",
                    "expected_signal": "yes",
                    "cost": "safe",
                    "gain": 0.40
                })
            
            elif "keyboard" in component.lower():
                questions.append({
                    "id": "keyboard_responsive",
                    "text": "Do some keys work while others don't?",
                    "type": "binary",
                    "expected_signal": "yes",
                    "cost": "safe",
                    "gain": 0.35
                })
        
        return questions
    
    def process_answer(
        self, 
        session_id: str,
        question_id: str,
        answer: str,
        belief_vector: Dict[str, float],
        asked_questions: List[str] = None
    ) -> Tuple[Optional[Dict], Optional[DiagnosisResult], Dict]:
        """
        Process user answer and update beliefs
        Returns: (next_question, diagnosis_result, debug_info)
        """
        if asked_questions is None:
            asked_questions = []
            
        debug_info = {
            "question_answered": question_id,
            "answer": answer,
            "belief_update": {},
            "confidence_change": 0.0,
            "questions_count": len(asked_questions)
        }
        
        # Update belief vector based on answer
        old_max = max(belief_vector.values()) if belief_vector else 0
        
        # Update beliefs based on question context and answer
        answer_lower = answer.lower()
        
        if "power_led" in question_id:
            if answer_lower == "no":
                belief_vector["power_supply"] = belief_vector.get("power_supply", 0.33) * 1.6
                belief_vector["battery_issue"] = belief_vector.get("battery_issue", 0.33) * 1.4
            else:
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.5
                belief_vector["battery_issue"] = belief_vector.get("battery_issue", 0.33) * 0.7
        elif "fan_spin" in question_id:
            if answer_lower == "no":
                belief_vector["power_supply"] = belief_vector.get("power_supply", 0.33) * 1.7
            else:
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.4
        elif "screen" in question_id or "display" in question_id:
            if answer_lower == "no":
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.8
            else:
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.3
        elif "caps" in question_id or "keyboard" in question_id:
            if answer_lower == "yes":
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.6
            else:
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.9
        elif "battery" in question_id or "charg" in question_id:
            if answer_lower == "yes":
                belief_vector["battery_issue"] = belief_vector.get("battery_issue", 0.33) * 1.9
            else:
                belief_vector["battery_issue"] = belief_vector.get("battery_issue", 0.33) * 0.6
                belief_vector["power_supply"] = belief_vector.get("power_supply", 0.33) * 1.5
        elif "adapter" in question_id or "power" in question_id:
            if answer_lower == "yes":
                belief_vector["power_supply"] = belief_vector.get("power_supply", 0.33) * 1.8
            else:
                belief_vector["power_supply"] = belief_vector.get("power_supply", 0.33) * 0.7
        elif "bios" in question_id or "logo" in question_id:
            if answer_lower == "yes":
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.4
            else:
                belief_vector["motherboard"] = belief_vector.get("motherboard", 0.33) * 1.8
        
        # Normalize
        total = sum(belief_vector.values())
        if total > 0:
            belief_vector = {k: v/total for k, v in belief_vector.items()}
        
        new_max = max(belief_vector.values()) if belief_vector else 0
        debug_info["confidence_change"] = new_max - old_max
        debug_info["belief_update"] = belief_vector
        
        # Check if we should stop asking questions (lower threshold or max questions)
        if new_max >= 0.55 or len(asked_questions) >= 5:
            # Generate diagnosis based on top cause
            top_cause = max(belief_vector.items(), key=lambda x: x[1])
            result = self._build_diagnosis_from_cause(top_cause[0], top_cause[1], debug_info)
            return None, result, debug_info
        
        # Generate next question based on current belief state
        next_q = self._generate_next_question(question_id, answer, belief_vector, asked_questions)
        return next_q, None, debug_info
    
    def _generate_next_question(
        self,
        previous_question_id: str,
        previous_answer: str,
        belief_vector: Dict[str, float],
        asked_questions: List[str] = None
    ) -> Dict:
        """Generate next question based on previous answer and belief state"""
        
        if asked_questions is None:
            asked_questions = []
        
        # Helper to check if question was asked
        def not_asked(q_id: str) -> bool:
            return q_id not in asked_questions
        
        # Determine what to ask next based on context
        if "power_led" in previous_question_id:
            if previous_answer.lower() == "no":
                if not_asked("fan_spin_check"):
                    return {
                        "id": "fan_spin_check",
                        "text": "Do you hear the fan spin for 2-3 seconds when you power on?",
                        "type": "binary",
                        "expected_signal": "audio",
                        "cost": "safe",
                        "gain": 0.30
                    }
            else:
                if not_asked("screen_display"):
                    return {
                        "id": "screen_display",
                        "text": "Does anything appear on the screen at all, even briefly?",
                        "type": "binary",
                        "expected_signal": "visual",
                        "cost": "safe",
                        "gain": 0.35
                    }
        
        elif "screen" in previous_question_id or "display" in previous_question_id:
            if previous_answer.lower() == "no":
                if not_asked("caps_lock_toggle"):
                    return {
                        "id": "caps_lock_toggle",
                        "text": "Does the CapsLock LED toggle when you press the key?",
                        "type": "binary",
                        "expected_signal": "yes",
                        "cost": "safe",
                        "gain": 0.30
                    }
            else:
                if not_asked("bios_screen"):
                    return {
                        "id": "bios_screen",
                        "text": "Do you see the manufacturer logo or BIOS screen?",
                        "type": "binary",
                        "expected_signal": "visual",
                        "cost": "safe",
                        "gain": 0.35
                    }
        
        elif "caps" in previous_question_id:
            # After caps lock, ask about external display
            if not_asked("external_display"):
                return {
                    "id": "external_display",
                    "text": "Have you tried connecting to an external monitor?",
                    "type": "binary",
                    "expected_signal": "yes",
                    "cost": "safe",
                    "gain": 0.40
                }
        
        elif "fan_spin" in previous_question_id:
            if previous_answer.lower() == "no":
                if not_asked("battery_removable"):
                    return {
                        "id": "battery_removable",
                        "text": "Have you tried removing and reconnecting the battery?",
                        "type": "binary",
                        "expected_signal": "yes",
                        "cost": "safe",
                        "gain": 0.40
                    }
            else:
                if not_asked("bios_screen"):
                    return {
                        "id": "bios_screen",
                        "text": "Do you see the manufacturer logo or BIOS screen when starting?",
                        "type": "binary",
                        "expected_signal": "visual",
                        "cost": "safe",
                        "gain": 0.35
                    }
        
        # Fallback: Ask questions based on highest belief (that haven't been asked)
        top_cause = max(belief_vector.items(), key=lambda x: x[1])[0]
        
        if "battery" in top_cause and not_asked("battery_charging"):
            return {
                "id": "battery_charging",
                "text": "Does the battery charging indicator light up when you plug in the charger?",
                "type": "binary",
                "expected_signal": "yes",
                "cost": "safe",
                "gain": 0.40
            }
        elif "power" in top_cause and not_asked("adapter_check"):
            return {
                "id": "adapter_check",
                "text": "Have you tried a different power adapter?",
                "type": "binary",
                "expected_signal": "yes",
                "cost": "safe",
                "gain": 0.35
            }
        elif not_asked("recent_changes"):
            return {
                "id": "recent_changes",
                "text": "Did this issue start after any hardware changes or software updates?",
                "type": "binary",
                "expected_signal": "yes",
                "cost": "safe",
                "gain": 0.30
            }
        
        # If all questions exhausted, return a generic final question
        return {
            "id": "other_symptoms",
            "text": "Are there any unusual sounds, smells, or other symptoms?",
            "type": "binary",
            "expected_signal": "yes",
            "cost": "safe",
            "gain": 0.25
        }
    
    def _build_diagnosis_result(
        self, 
        match: Dict, 
        debug_info: Dict
    ) -> DiagnosisResult:
        """Build diagnosis result from match"""
        issue = match["issue"]
        
        # Extract solution steps
        steps = issue.get("steps", [])
        solution_steps = [
            step.get("action", step.get("title", "")) 
            for step in steps
        ]
        
        # Find easy fix
        easy_fix = None
        if steps and len(steps) > 0:
            first_step = steps[0]
            if first_step.get("risk_level", "") == "safe":
                easy_fix = first_step.get("action", "Try restarting the device")
        
        # Extract tools
        tools = []
        for step in steps:
            tools.extend(step.get("tools", []))
        tools = list(set(tools))  # Unique
        
        # Source breakdown
        source_breakdown = {
            "OEM": [],
            "iFixit": [],
            "YouTube": [],
            "ML_Model": ["Symptom analysis", "Question generation"]
        }
        
        sources_used = issue.get("sources_used", ["OEM"])
        for source in sources_used:
            if source in source_breakdown:
                source_breakdown[source].append("Repair procedure")
        
        return DiagnosisResult(
            cause=issue.get("component", "Unknown issue"),
            confidence=match["score"],
            solution_steps=solution_steps[:5],  # First 5 steps
            easy_fix=easy_fix or "Check power connections and restart",
            tools_needed=tools[:5],
            risk_level=issue.get("risk_level", "medium"),
            source_breakdown=source_breakdown,
            related_guides=[f"/guides/{issue.get('brand', 'lenovo')}/{issue.get('device_model', 'ideapad-5')}/{issue.get('component', 'battery')}-replacement"]
        )
    
    def _build_diagnosis_from_cause(
        self,
        cause: str,
        confidence: float,
        debug_info: Dict
    ) -> DiagnosisResult:
        """Build diagnosis from belief vector cause"""
        # Simplified version - use knowledge base to find solution
        for issue in self.knowledge_base:
            if cause.lower() in str(issue).lower():
                return self._build_diagnosis_result(
                    {"issue": issue, "score": confidence, "source": "OEM"},
                    debug_info
                )
        
        # Fallback
        return DiagnosisResult(
            cause=cause,
            confidence=confidence,
            solution_steps=["Consult service manual", "Check component connections"],
            easy_fix="Restart the device and check connections",
            tools_needed=["Phillips screwdriver"],
            risk_level="medium",
            source_breakdown={
                "OEM": ["Generic recommendation"],
                "ML_Model": ["Symptom analysis"]
            },
            related_guides=["/guides"]
        )
    
    def save_session(self, session: DiagnosisSession) -> None:
        """Save session for learning"""
        with open(self.sessions_file, 'a') as f:
            f.write(json.dumps(asdict(session)) + '\n')
    
    def learn_from_sessions(self) -> None:
        """
        Analyze saved sessions to improve:
        1. Question effectiveness
        2. Common symptom patterns
        3. Optimal question sequences
        """
        if not os.path.exists(self.sessions_file):
            return
        
        sessions = []
        with open(self.sessions_file, 'r') as f:
            for line in f:
                sessions.append(json.loads(line))
        
        # Analyze patterns
        symptom_patterns = {}
        question_effectiveness = {}
        
        for session in sessions:
            # Track which questions led to correct diagnosis
            if session.get("final_diagnosis"):
                symptoms = session["initial_symptoms"]
                if symptoms not in symptom_patterns:
                    symptom_patterns[symptoms] = []
                symptom_patterns[symptoms].append(session["final_diagnosis"])
        
        # Update learned patterns
        self.learned_patterns["common_issues"] = list(symptom_patterns.keys())[:100]
        
        with open(self.patterns_file, 'w') as f:
            json.dump(self.learned_patterns, f, indent=2)
