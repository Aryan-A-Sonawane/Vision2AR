"""
Adaptive Belief Engine
Loads base rules + learned patterns, computes belief vectors with skip logic
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncpg
import math

class BeliefEngine:
    """Manages belief propagation and question selection with adaptive learning"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.base_patterns = None
        self.base_questions = None
        self._load_base_knowledge()
    
    def _load_base_knowledge(self):
        """Load symptom mappings and questions from JSON files"""
        base_path = Path(__file__).parent
        
        # Load symptom mappings
        with open(base_path / "symptom_mappings.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.base_patterns = data["patterns"]
        
        # Load questions
        with open(base_path / "questions.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.base_questions = {q["id"]: q for q in data["questions"]}
        
        print(f"[OK] Loaded {len(self.base_patterns)} base patterns")
        print(f"[OK] Loaded {len(self.base_questions)} base questions")
    
    async def initialize_beliefs(
        self, 
        symptoms: List[str], 
        visual_symptoms: List[str],
        category: str,
        brand: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Initialize belief vector from symptoms
        Combines base patterns + learned patterns with confidence weighting
        
        Returns: belief_vector = {"cause": probability, ...}
        """
        print(f"[DEBUG] Initializing beliefs with symptoms: {symptoms}")
        print(f"[DEBUG] Total base patterns loaded: {len(self.base_patterns)}")
        
        beliefs = {}
        
        all_symptoms = set(symptoms + visual_symptoms)
        print(f"[DEBUG] All symptoms (combined): {all_symptoms}")
        
        # Step 1: Load base patterns
        alpha = 0.7  # Base knowledge weight (will decay over time as system learns)
        
        matched_patterns = 0
        for pattern in self.base_patterns:
            # Check category match
            if pattern.get("category") != category:
                continue
            
            # Calculate symptom overlap
            pattern_symptoms = set(pattern["symptoms"])
            overlap = pattern_symptoms & all_symptoms
            
            if overlap:
                matched_patterns += 1
                print(f"[DEBUG] Pattern matched: {pattern['symptoms']} -> {list(pattern['causes'].keys())}")
                overlap_ratio = len(overlap) / len(pattern_symptoms)
                pattern_confidence = pattern.get("confidence", 1.0)
                
                for cause, prob in pattern["causes"].items():
                    if cause not in beliefs:
                        beliefs[cause] = 0.0
                    beliefs[cause] += alpha * prob * overlap_ratio * pattern_confidence
        
        print(f"[DEBUG] Matched {matched_patterns} patterns from base knowledge")
        print(f"[DEBUG] Beliefs after base patterns: {dict(list(beliefs.items())[:3])}")
        
        # Step 2: Load learned patterns from database
        learned_weight = 1.0 - alpha
        
        async with self.db_pool.acquire() as conn:
            learned_patterns = await conn.fetch("""
                SELECT symptom_combination, cause, confidence, success_rate, support_count
                FROM learned_patterns
                WHERE approved = true AND category = $1
            """, category)
            
            for lp in learned_patterns:
                pattern_symptoms = set(lp["symptom_combination"])
                overlap = pattern_symptoms & all_symptoms
                
                if overlap:
                    overlap_ratio = len(overlap) / len(pattern_symptoms)
                    
                    # Confidence-weighted belief fusion
                    # w(π) = r(π) · (1 - exp(-n(π)/n₀))
                    n = lp["support_count"]
                    r = lp["success_rate"]
                    n0 = 5  # Temperature parameter
                    w = r * (1 - math.exp(-n / n0))
                    
                    cause = lp["cause"]
                    if cause not in beliefs:
                        beliefs[cause] = 0.0
                    beliefs[cause] += learned_weight * w * overlap_ratio
        
        # Step 3: Normalize belief vector
        total = sum(beliefs.values())
        if total > 0:
            beliefs = {k: v / total for k, v in beliefs.items()}
        
        # Step 4: Sort by confidence
        beliefs = dict(sorted(beliefs.items(), key=lambda x: x[1], reverse=True))
        
        return beliefs
    
    async def update_beliefs_semantic(
        self,
        current_beliefs: Dict[str, float],
        question_text: str,
        answer_text: str,
        processor
    ) -> Dict[str, float]:
        """
        Update beliefs based on semantic analysis of text response
        Uses keyword extraction and intent matching
        """
        print(f"\n🔍 SEMANTIC BELIEF UPDATE")
        print(f"   Question: {question_text[:80]}...")
        print(f"   Answer: {answer_text[:80]}...")
        
        # Extract keywords and symptoms from answer
        answer_lower = answer_text.lower()
        detected_symptoms = []
        
        # Check symptom keywords from processor
        symptom_keywords = {
            "driver_issue": ["driver", "software", "update", "install"],
            "malware": ["virus", "malware", "suspicious", "popup", "slow"],
            "hardware_failure": ["hardware", "physical", "damaged", "broken"],
            "display_cable_loose": ["screen", "display", "flicker", "blank"],
            "gpu_overheating": ["hot", "overheat", "thermal", "fan loud"],
            "ram_failure": ["memory", "ram", "beep"],
            "power_supply_failure": ["power", "won't turn on", "dead"],
            "motherboard_dead": ["motherboard", "no power", "nothing happens"],
            "os_corruption": ["corrupt", "boot loop", "startup repair"],
            "thermal_throttling": ["slow", "throttle", "performance drop", "overheat"],
            "disk_fragmentation": ["slow", "lag", "disk", "storage"],
            "background_processes": ["background", "startup", "many programs"]
        }
        
        # Score each cause based on keyword matches
        keyword_scores = {}
        for cause, keywords in symptom_keywords.items():
            score = sum(1 for kw in keywords if kw in answer_lower)
            if score > 0:
                keyword_scores[cause] = score
                detected_symptoms.extend([kw for kw in keywords if kw in answer_lower])
        
        print(f"   Detected keywords: {detected_symptoms[:5]}")
        print(f"   Keyword scores: {keyword_scores}")
        
        # Apply semantic updates
        if keyword_scores:
            # Boost causes that match keywords
            for cause, score in keyword_scores.items():
                if cause in current_beliefs:
                    multiplier = 1.0 + (score * 0.5)  # +50% per keyword match
                    old_val = current_beliefs[cause]
                    current_beliefs[cause] *= multiplier
                    print(f"   {cause}: {old_val:.3f} → {current_beliefs[cause]:.3f} (×{multiplier:.2f})")
                elif score >= 2:  # Strong match, add to beliefs
                    current_beliefs[cause] = 0.1 * score
                    print(f"   {cause}: NEW → {current_beliefs[cause]:.3f}")
            
            # Normalize
            total = sum(current_beliefs.values())
            if total > 0:
                current_beliefs = {k: v / total for k, v in current_beliefs.items()}
            
            # Sort
            current_beliefs = dict(sorted(current_beliefs.items(), key=lambda x: x[1], reverse=True))
        else:
            print(f"   ⚠️ No semantic matches found - beliefs unchanged")
        
        return current_beliefs
    
    async def update_beliefs(
        self,
        current_beliefs: Dict[str, float],
        question_id: str,
        answer: str
    ) -> Dict[str, float]:
        """
        Update belief vector based on question answer
        Uses Bayesian-inspired update with belief_updates from question
        
        Returns: updated belief vector
        """
        question = self.base_questions.get(question_id)
        if not question:
            print(f"⚠️ WARNING: Question '{question_id}' not found in base questions!")
            print(f"   Available questions: {list(self.base_questions.keys())[:10]}...")
            # Check if it's a learned question from DB
            async with self.db_pool.acquire() as conn:
                learned_q = await conn.fetchrow("""
                    SELECT question_id, belief_updates_json
                    FROM learned_questions
                    WHERE question_id = $1 AND approved = true
                """, question_id)
                
                if learned_q and learned_q["belief_updates_json"]:
                    print(f"✓ Found as learned question - using stored belief updates")
                    updates = learned_q["belief_updates_json"].get(answer, {})
                else:
                    print(f"✗ Question not found in learned questions either - returning unchanged beliefs")
                    return current_beliefs
        else:
            # Get update rules from base question
            updates = question.get("belief_updates", {}).get(answer, {})
        
        if not updates:
            print(f"⚠️ No belief updates found for answer '{answer}' to question '{question_id}'")
            return current_beliefs
        
        print(f"📊 Applying {len(updates)} belief updates for answer '{answer}':")
        # Apply updates
        for cause, multiplier in updates.items():
            old_value = current_beliefs.get(cause, 0.0)
            if cause in current_beliefs:
                if isinstance(multiplier, str) and multiplier.startswith("*"):
                    factor = float(multiplier[1:])
                    current_beliefs[cause] *= factor
                    print(f"   {cause}: {old_value:.3f} → {current_beliefs[cause]:.3f} (×{factor})")
        
        # Normalize
        total = sum(current_beliefs.values())
        if total > 0:
            current_beliefs = {k: v / total for k, v in current_beliefs.items()}
        
        # Sort
        current_beliefs = dict(sorted(current_beliefs.items(), key=lambda x: x[1], reverse=True))
        
        return current_beliefs
    
    def should_ask_question(
        self,
        question_id: str,
        current_beliefs: Dict[str, float],
        processed_input: Dict,
        asked_questions: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Implement smart skip logic with 3 criteria:
        1. Redundancy check (information already known)
        2. Low expected gain (not helpful given current beliefs)
        3. Irrelevance (question doesn't apply to high-probability causes)
        
        Returns: (should_ask: bool, skip_reason: Optional[str])
        """
        question = self.base_questions.get(question_id)
        if not question:
            return False, "Question not found"
        
        if question_id in asked_questions:
            return False, "Already asked"
        
        skip_conditions = question.get("skip_if", {})
        
        # Criterion 1: Redundancy check
        # Skip if brand already known with high confidence
        if "brand_confidence" in skip_conditions:
            threshold_str = skip_conditions["brand_confidence"]
            threshold = float(threshold_str.replace(">", "").replace("<", ""))
            brand_conf = processed_input.get("brand_confidence", 0.0)
            
            if ">" in threshold_str and brand_conf > threshold:
                return False, f"Brand already known (confidence: {brand_conf:.2f})"
        
        # Skip if symptom already detected
        if "symptom_present" in skip_conditions:
            required_symptoms = skip_conditions["symptom_present"]
            detected_symptoms = processed_input.get("symptoms", []) + processed_input.get("visual_symptoms", [])
            
            if any(s in detected_symptoms for s in required_symptoms):
                return False, "Symptom already detected from input"
        
        if "symptom_not_present" in skip_conditions:
            required_symptoms = skip_conditions["symptom_not_present"]
            detected_symptoms = processed_input.get("symptoms", []) + processed_input.get("visual_symptoms", [])
            
            if not any(s in detected_symptoms for s in required_symptoms):
                return False, "Question not relevant to detected symptoms"
        
        # Skip if visual symptom already answered question
        if "visual_symptoms_detected" in skip_conditions:
            required = skip_conditions["visual_symptoms_detected"]
            visual = processed_input.get("visual_symptoms", [])
            
            if any(v in visual for v in required):
                return False, "Visual analysis already provided this information"
        
        # Criterion 2: Low expected gain
        # Skip if information gain estimate is below threshold
        ig_estimate = question.get("information_gain_estimate", 0.0)
        if ig_estimate < 0.6:  # Threshold
            return False, f"Low information gain ({ig_estimate:.2f})"
        
        # Criterion 3: Irrelevance check
        # Skip if question doesn't help distinguish between top causes
        # Check if any of the top-3 causes are affected by this question
        top_causes = list(current_beliefs.keys())[:3]
        question_affects_top_causes = False
        
        for answer_key in question.get("belief_updates", {}).keys():
            updates = question["belief_updates"][answer_key]
            if any(cause in top_causes for cause in updates.keys()):
                question_affects_top_causes = True
                break
        
        if not question_affects_top_causes:
            return False, "Question doesn't help distinguish top causes"
        
        # Check if any top cause probability is too low to matter
        max_cause_prob = max(current_beliefs.values()) if current_beliefs else 0.0
        if max_cause_prob > 0.9:  # Very high confidence already
            return False, f"Already have very high confidence ({max_cause_prob:.2f})"
        
        return True, None
    
    async def select_next_question(
        self,
        current_beliefs: Dict[str, float],
        processed_input: Dict,
        asked_questions: List[str],
        category: str
    ) -> Optional[Dict]:
        """
        Select next question using information-theoretic approach
        Applies skip logic and selects question with highest expected information gain
        
        Returns: question dict or None if no more questions
        """
        # Get candidate questions for this category
        candidate_questions = [
            q for q_id, q in self.base_questions.items()
            if q.get("category") == category and q_id not in asked_questions
        ]
        
        # Also load learned questions
        async with self.db_pool.acquire() as conn:
            learned_q = await conn.fetch("""
                SELECT question_id, question_text, category, information_gain_avg
                FROM learned_questions
                WHERE approved = true AND category = $1
            """, category)
            
            for lq in learned_q:
                if lq["question_id"] not in asked_questions:
                    candidate_questions.append({
                        "id": lq["question_id"],
                        "text": lq["question_text"],
                        "category": lq["category"],
                        "information_gain_estimate": lq["information_gain_avg"],  # Use avg as estimate
                        "source": "learned"
                    })
        
        if not candidate_questions:
            return None
        
        # Apply skip logic to filter
        valid_questions = []
        for q in candidate_questions:
            should_ask, reason = self.should_ask_question(
                q["id"], current_beliefs, processed_input, asked_questions
            )
            if should_ask:
                valid_questions.append(q)
        
        if not valid_questions:
            return None
        
        # Select question with highest information gain estimate
        best_question = max(valid_questions, key=lambda q: q.get("information_gain_estimate", 0.5))
        
        print(f"✅ Selected question ID: '{best_question['id']}' with gain {best_question.get('information_gain_estimate', 0.5):.2f}")
        print(f"   Question text: {best_question.get('text', 'N/A')}")
        
        # Ensure all required fields are present
        if "expected_signal" not in best_question and best_question["id"] in self.base_questions:
            # Fill from base question
            base_q = self.base_questions[best_question["id"]]
            best_question["expected_signal"] = base_q.get("expected_signal", "behavioral")
            best_question["cost_level"] = base_q.get("cost_level", "safe")
        
        return best_question
    
    def get_confidence(self, beliefs: Dict[str, float]) -> float:
        """Get maximum confidence from belief vector"""
        return max(beliefs.values()) if beliefs else 0.0
    
    def generate_text_question(self, current_beliefs: Dict[str, float], asked_questions: List[str]) -> Optional[Dict]:
        """
        Generate open-ended question based on top uncertain causes
        """
        # If no beliefs yet, ask general diagnostic question
        if not current_beliefs or len(current_beliefs) < 2:
            general_id = f"text_general_{len(asked_questions)}"
            if general_id not in asked_questions:
                return {
                    "id": general_id,
                    "text": "Can you describe in detail what's happening with your laptop? Include when the issue started, what you were doing, and any error messages or unusual behavior.",
                    "expected_signal": "text",
                    "cost_level": "safe",
                    "information_gain_estimate": 0.9,
                    "response_type": "text"
                }
            return None
        
        # Get top 3 causes with similar probabilities (uncertain area)
        sorted_beliefs = sorted(current_beliefs.items(), key=lambda x: x[1], reverse=True)
        
        top_cause, top_prob = sorted_beliefs[0]
        second_cause, second_prob = sorted_beliefs[1] if len(sorted_beliefs) > 1 else (None, 0)
        
        # If very confident, no need for more questions
        if top_prob > 0.75:
            return None
        
        # Generate questions based on cause comparison
        question_templates = {
            ("driver_issue", "malware"): "Have you recently installed any new software, drivers, or updates? Or have you noticed any suspicious behavior?",
            ("driver_issue", "hardware_failure"): "Does the issue occur in Safe Mode? And have you checked if any hardware components are loose?",
            ("gpu_overheating", "display_cable_loose"): "Is the screen issue constant or does it come and go? Does the laptop feel hot?",
            ("power_supply_failure", "motherboard_dead"): "When you press the power button, do you see ANY lights or hear ANY sounds at all?",
            ("ram_failure", "os_corruption"): "Do you hear any beeping sounds during startup? And does it show any error messages?",
            ("thermal_throttling", "background_processes"): "Does the slowdown happen immediately or after a few minutes of use? Have you checked Task Manager?",
        }
        
        # Find matching template
        for (cause1, cause2), question in question_templates.items():
            if (top_cause == cause1 and second_cause == cause2) or \
               (top_cause == cause2 and second_cause == cause1):
                question_id = f"text_{cause1}_{cause2}"
                if question_id not in asked_questions:
                    return {
                        "id": question_id,
                        "text": question,
                        "expected_signal": "text",
                        "cost_level": "safe",
                        "information_gain_estimate": 0.85,
                        "response_type": "text"
                    }
        
        # Fallback: general clarification question
        general_id = f"text_general_{len(asked_questions)}"
        if general_id not in asked_questions:
            return {
                "id": general_id,
                "text": f"Can you describe in more detail what happens when the issue occurs? Any specific error messages or behaviors?",
                "expected_signal": "text",
                "cost_level": "safe",
                "information_gain_estimate": 0.7,
                "response_type": "text"
            }
        
        return None
    
    def get_diagnosis(self, beliefs: Dict[str, float]) -> Tuple[str, float]:
        """Get top diagnosis and its confidence"""
        if not beliefs:
            return "unknown", 0.0
        
        top_cause = max(beliefs, key=beliefs.get)
        confidence = beliefs[top_cause]
        
        return top_cause, confidence
