"""
Smart Question Generator - LLM-like contextual question generation
Analyzes OEM manual content + user conversation history to generate targeted questions
"""

import re
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np


class SmartQuestionGenerator:
    """
    Generate contextual diagnostic questions by analyzing:
    1. OEM manual diagnostic sections
    2. Current diagnosis hypothesis
    3. User conversation history
    4. Information gaps
    """
    
    def __init__(self, model: SentenceTransformer):
        self.model = model
        
        # Question templates organized by diagnostic strategy
        self.question_strategies = {
            "power_delivery": [
                "When you press the power button, does anything happen at all? (lights, sounds, vibrations)",
                "Describe exactly what you see when you attempt to power on the laptop.",
                "Does the charging indicator light turn on when you plug in the charger?",
                "Have you tried a different power outlet or charger?",
            ],
            "display_issues": [
                "Is the screen completely black, or can you see a very faint image if you shine a light on it?",
                "Do you hear any startup sounds (fan spinning, hard drive activity)?",
                "Does connecting an external monitor show any display?",
                "When did you last see the screen working properly?",
            ],
            "thermal_problems": [
                "Where exactly does the laptop feel hot? (bottom panel, keyboard area, specific corner)",
                "When did you last clean the cooling vents?",
                "Does the fan make unusual noises or seem to spin faster than normal?",
                "How long can you use the laptop before it gets uncomfortably hot?",
            ],
            "boot_failure": [
                "What happens after you press the power button? Describe the sequence of events.",
                "Do you see any error messages, codes, or logos on screen?",
                "Does the laptop reach the manufacturer logo, Windows/Linux boot screen, or nothing?",
                "Have you installed new hardware or software recently?",
            ],
            "battery_issues": [
                "Does the laptop work when plugged in with AC adapter (without battery)?",
                "How long does the battery last compared to when it was new?",
                "Does the battery percentage jump around or show incorrect values?",
                "When did you start noticing battery problems?",
            ],
            "keyboard_issues": [
                "Are all keys affected or only specific keys/regions?",
                "Did liquid ever spill on the keyboard?",
                "Does an external USB keyboard work properly?",
                "When did the keyboard problem start?",
            ],
            "general_diagnostic": [
                "What exactly were you doing when the problem first appeared?",
                "Has the laptop experienced any physical impacts, drops, or pressure?",
                "Have you made any recent changes to the laptop (hardware, software, updates)?",
                "Does the problem happen consistently or intermittently?",
            ]
        }
        
        # Information extraction keywords for analyzing answers
        self.symptom_keywords = {
            "power_delivery": ["power", "charge", "led", "light", "button", "plug", "adapter", "outlet"],
            "display_issues": ["screen", "display", "black", "blank", "dim", "flicker", "external monitor"],
            "thermal_problems": ["hot", "heat", "overheat", "fan", "vent", "temperature", "warm", "burn"],
            "boot_failure": ["boot", "start", "logo", "bios", "error", "message", "loading", "startup"],
            "battery_issues": ["battery", "charge", "drain", "percentage", "ac adapter", "unplug"],
            "keyboard_issues": ["key", "keyboard", "type", "input", "spill", "liquid", "press", "sticky"],
        }
    
    def generate_contextual_questions(
        self,
        manual_text: str,
        issue_type: str,
        user_symptoms: str,
        conversation_history: List[Dict],
        confidence: float,
        max_questions: int = 3
    ) -> List[Dict]:
        """
        Generate smart, contextual questions like an LLM would
        
        Args:
            manual_text: Relevant section from OEM manual
            issue_type: Current hypothesis (no_boot, black_screen, etc.)
            user_symptoms: Original user input
            conversation_history: List of {question, answer} pairs
            confidence: Current diagnosis confidence
            max_questions: Maximum questions to generate
        
        Returns:
            List of question objects with context and reasoning
        """
        questions = []
        
        # Step 1: Identify information gaps
        info_gaps = self._identify_information_gaps(
            issue_type, user_symptoms, conversation_history
        )
        
        # Step 2: Extract diagnostic questions from manual
        manual_questions = self._extract_manual_questions(manual_text, issue_type)
        
        # Step 3: Get strategy-based questions
        strategy_questions = self._get_strategy_questions(issue_type)
        
        # Step 4: Rank and select best questions
        all_candidates = []
        
        # Prioritize manual-extracted questions (most authoritative)
        for mq in manual_questions[:2]:
            all_candidates.append({
                "text": mq,
                "type": "open_ended",
                "source": "manual",
                "priority": 3,
                "info_gain": self._estimate_information_gain(mq, info_gaps),
            })
        
        # Add strategy-based questions
        for sq in strategy_questions:
            if not self._is_already_asked(sq, conversation_history):
                all_candidates.append({
                    "text": sq,
                    "type": "open_ended",
                    "source": "strategy",
                    "priority": 2,
                    "info_gain": self._estimate_information_gain(sq, info_gaps),
                })
        
        # Add adaptive follow-ups based on last answer
        if conversation_history:
            adaptive_q = self._generate_adaptive_followup(
                conversation_history[-1], issue_type
            )
            if adaptive_q:
                all_candidates.append({
                    "text": adaptive_q,
                    "type": "open_ended",
                    "source": "adaptive",
                    "priority": 2.5,
                    "info_gain": 0.8,  # Adaptive questions have high value
                })
        
        # Sort by priority and info gain
        all_candidates.sort(key=lambda x: (x["priority"], x["info_gain"]), reverse=True)
        
        # Select top questions
        for idx, candidate in enumerate(all_candidates[:max_questions]):
            questions.append({
                "id": f"smart_q_{idx + 1}_{issue_type}",
                "text": candidate["text"],
                "type": candidate["type"],
                "source": candidate["source"],
                "reasoning": self._explain_question_reasoning(candidate, info_gaps),
                "expected_info": self._describe_expected_info(candidate["text"]),
            })
        
        return questions
    
    def _identify_information_gaps(
        self, issue_type: str, user_symptoms: str, conversation_history: List[Dict]
    ) -> Dict[str, bool]:
        """
        Identify what information we still need
        
        Returns:
            Dict of {info_category: is_missing}
        """
        gaps = {
            "power_state": True,
            "visual_feedback": True,
            "audio_feedback": True,
            "recent_changes": True,
            "physical_damage": True,
            "timing": True,
            "external_test": True,
        }
        
        # Analyze user symptoms
        symptoms_lower = user_symptoms.lower()
        if any(word in symptoms_lower for word in ["power", "led", "light", "on", "off"]):
            gaps["power_state"] = False
        if any(word in symptoms_lower for word in ["screen", "display", "see", "show"]):
            gaps["visual_feedback"] = False
        if any(word in symptoms_lower for word in ["fan", "sound", "noise", "beep"]):
            gaps["audio_feedback"] = False
        
        # Analyze conversation history
        for qa in conversation_history:
            answer = qa.get("answer", "").lower()
            if "yes" in answer or "no" in answer or len(answer) > 10:
                # Infer what gap this answer filled
                if any(word in answer for word in ["power", "led", "light"]):
                    gaps["power_state"] = False
                if any(word in answer for word in ["external", "monitor", "hdmi"]):
                    gaps["external_test"] = False
                if any(word in answer for word in ["drop", "fall", "impact", "spill"]):
                    gaps["physical_damage"] = False
                if any(word in answer for word in ["yesterday", "ago", "last", "recent"]):
                    gaps["timing"] = False
        
        return gaps
    
    def _extract_manual_questions(self, manual_text: str, issue_type: str) -> List[str]:
        """
        Extract diagnostic questions from OEM manual text
        
        Looks for patterns like:
        - "Check if..."
        - "Verify that..."
        - "Test..."
        - "Ensure..."
        """
        questions = []
        
        if not manual_text:
            return questions
        
        # Pattern 1: Imperative diagnostic instructions
        imperative_patterns = [
            r"Check (?:if |whether |that )?([^.]+\.)",
            r"Verify (?:if |whether |that )?([^.]+\.)",
            r"Test (?:if |whether |that )?([^.]+\.)",
            r"Ensure (?:if |whether |that )?([^.]+\.)",
            r"Confirm (?:if |whether |that )?([^.]+\.)",
            r"Inspect ([^.]+\.)",
        ]
        
        for pattern in imperative_patterns:
            matches = re.findall(pattern, manual_text, re.IGNORECASE)
            for match in matches:
                # Convert to question format
                question = f"Have you checked if {match}".strip()
                if not question.endswith("?"):
                    question += "?"
                questions.append(question)
        
        # Pattern 2: Direct questions in manual
        direct_questions = re.findall(r"([^.!?]+\?)", manual_text)
        questions.extend(direct_questions)
        
        # Deduplicate and clean
        seen = set()
        cleaned = []
        for q in questions:
            q = q.strip()
            if q and len(q) > 20 and q not in seen:
                seen.add(q)
                cleaned.append(q)
        
        return cleaned[:5]  # Top 5 manual questions
    
    def _get_strategy_questions(self, issue_type: str) -> List[str]:
        """Get pre-defined strategy questions for this issue type"""
        # Map issue types to strategies
        strategy_map = {
            "no_boot": ["power_delivery", "boot_failure", "general_diagnostic"],
            "black_screen": ["display_issues", "power_delivery", "general_diagnostic"],
            "no_display": ["display_issues", "power_delivery"],
            "overheating": ["thermal_problems", "general_diagnostic"],
            "overheat": ["thermal_problems", "general_diagnostic"],
            "battery_issue": ["battery_issues", "power_delivery"],
            "battery_not_charging": ["battery_issues", "power_delivery"],
            "keyboard_issue": ["keyboard_issues", "general_diagnostic"],
            "keyboard_not_working": ["keyboard_issues"],
        }
        
        strategies = strategy_map.get(issue_type, ["general_diagnostic"])
        
        questions = []
        for strategy in strategies:
            questions.extend(self.question_strategies.get(strategy, []))
        
        return questions
    
    def _is_already_asked(self, question: str, conversation_history: List[Dict]) -> bool:
        """Check if similar question already asked"""
        question_lower = question.lower()
        for qa in conversation_history:
            asked_q = qa.get("question", "").lower()
            # Simple similarity check (could use embeddings for better accuracy)
            if self._text_similarity(question_lower, asked_q) > 0.7:
                return True
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity (word overlap)"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)
    
    def _generate_adaptive_followup(
        self, last_qa: Dict, issue_type: str
    ) -> Optional[str]:
        """
        Generate follow-up question based on last answer
        Like an LLM would naturally follow up
        """
        last_answer = last_qa.get("answer", "").lower()
        
        # If user said "yes" to power LED, ask about screen
        if "power" in last_qa.get("question", "").lower() and "yes" in last_answer:
            return "Since the power LED is on, does anything appear on the screen at all?"
        
        # If user said "no" to external monitor, suggests internal issue
        if "external" in last_qa.get("question", "").lower() and "no" in last_answer:
            return "Since external monitor doesn't work either, can you describe what happens when you press the power button?"
        
        # If user mentioned spill, ask about timing
        if "spill" in last_answer or "liquid" in last_answer:
            return "How long after the liquid contact did the problem start?"
        
        # If user mentioned heat, ask about location
        if "hot" in last_answer or "heat" in last_answer:
            return "Can you point to the exact area that gets hot? (left side, right side, center, back)"
        
        # If user mentioned drop/fall, ask about immediately after
        if "drop" in last_answer or "fall" in last_answer or "impact" in last_answer:
            return "Did the laptop work immediately after the impact, or did it fail right away?"
        
        # If answer is detailed, ask for clarification on key point
        if len(last_answer) > 50:
            # Extract key concern and ask for more detail
            return "Thank you for the details. Just to clarify, does this happen every time you try, or only sometimes?"
        
        return None
    
    def _estimate_information_gain(self, question: str, info_gaps: Dict) -> float:
        """
        Estimate how much information this question would provide
        
        Returns:
            Score 0.0 to 1.0
        """
        question_lower = question.lower()
        gain = 0.0
        
        # Check which gaps this question addresses
        if any(word in question_lower for word in ["power", "led", "light"]) and info_gaps.get("power_state"):
            gain += 0.3
        if any(word in question_lower for word in ["screen", "display", "see"]) and info_gaps.get("visual_feedback"):
            gain += 0.3
        if any(word in question_lower for word in ["external", "monitor"]) and info_gaps.get("external_test"):
            gain += 0.25
        if any(word in question_lower for word in ["when", "timing", "start", "began"]) and info_gaps.get("timing"):
            gain += 0.2
        if any(word in question_lower for word in ["drop", "fall", "spill", "damage"]) and info_gaps.get("physical_damage"):
            gain += 0.25
        
        return min(gain, 1.0)
    
    def _explain_question_reasoning(self, candidate: Dict, info_gaps: Dict) -> str:
        """Generate explanation for why we're asking this question"""
        source = candidate["source"]
        
        if source == "manual":
            return "This is a diagnostic step from the official service manual"
        elif source == "adaptive":
            return "Follow-up based on your previous answer to narrow down the cause"
        else:
            # Explain based on info gaps
            missing_gaps = [k for k, v in info_gaps.items() if v]
            if missing_gaps:
                return f"This helps determine: {', '.join(missing_gaps[:2])}"
            return "This helps narrow down the root cause"
    
    def _describe_expected_info(self, question: str) -> str:
        """Describe what information we expect from this question"""
        question_lower = question.lower()
        
        if "power" in question_lower or "led" in question_lower:
            return "Power delivery status"
        elif "screen" in question_lower or "display" in question_lower:
            return "Display functionality"
        elif "external" in question_lower:
            return "Whether issue is internal or external"
        elif "when" in question_lower or "timing" in question_lower:
            return "Timeline and trigger events"
        elif "fan" in question_lower or "sound" in question_lower:
            return "System activity indicators"
        else:
            return "Detailed symptom information"
    
    def analyze_answer_for_confidence_update(
        self,
        answer: str,
        current_diagnosis: Dict,
        question_asked: str
    ) -> Tuple[float, List[str]]:
        """
        Analyze user answer to determine confidence adjustment
        
        Returns:
            (confidence_delta, extracted_keywords)
        """
        answer_lower = answer.lower()
        issue_type = current_diagnosis.get("issue_type", "")
        
        confidence_delta = 0.0
        extracted_keywords = []
        
        # Get relevant keywords for this issue type
        relevant_keywords = self.symptom_keywords.get(issue_type, [])
        
        # Count how many relevant keywords appear in answer
        keyword_matches = [kw for kw in relevant_keywords if kw in answer_lower]
        extracted_keywords = keyword_matches
        
        # More keywords = more confidence in diagnosis (balanced)
        if len(keyword_matches) >= 3:
            confidence_delta += 0.15  # Reduced from 0.20
        elif len(keyword_matches) >= 2:
            confidence_delta += 0.12  # Reduced from 0.15
        elif len(keyword_matches) >= 1:
            confidence_delta += 0.06  # Reduced from 0.08
        
        # Detailed answer (> 20 words) provides more confidence
        word_count = len(answer.split())
        if word_count > 30:
            confidence_delta += 0.10  # Reduced from 0.12
        elif word_count > 20:
            confidence_delta += 0.06  # Reduced from 0.08
        elif word_count > 10:
            confidence_delta += 0.03  # Reduced from 0.04
        
        # Check for contradicting signals (balanced bonuses)
        if issue_type == "black_screen" and "external monitor works" in answer_lower:
            # External working suggests internal display issue (confirms diagnosis)
            confidence_delta += 0.15  # Reduced from 0.18
        elif issue_type == "battery_issue" and "works on ac" in answer_lower:
            # Working on AC confirms battery issue
            confidence_delta += 0.15  # Reduced from 0.18
        elif issue_type == "overheating" or issue_type == "overheat":
            if any(word in answer_lower for word in ["hot", "heat", "burn", "warm"]):
                confidence_delta += 0.12  # Reduced from 0.15
        elif "not sure" in answer_lower or "don't know" in answer_lower:
            # Uncertain answer doesn't help much
            confidence_delta -= 0.03
        
        # Check for diagnostic confirmations
        if "faint image" in answer_lower or "barely see" in answer_lower:
            if issue_type == "black_screen":
                confidence_delta += 0.18  # Reduced from 0.20
        
        # Penalty for very short answers ("yes", "no" without detail)
        if word_count < 3:
            confidence_delta -= 0.05
        
        return confidence_delta, extracted_keywords
