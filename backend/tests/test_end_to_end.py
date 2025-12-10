"""
End-to-end test of the diagnostic system
Tests the complete flow: Input → Belief Engine → Questions → Tutorials → Feedback
"""
import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Simulated components (will be replaced with real implementations)
class MockDiagnosticSystem:
    """Simulates the diagnostic flow"""
    
    def __init__(self):
        # Load base knowledge
        self.symptom_mappings = self._load_json("diagnosis/symptom_mappings.json")
        self.questions = self._load_json("diagnosis/questions.json")
        print("✅ Loaded base knowledge files")
        print(f"   - {len(self.symptom_mappings['patterns'])} symptom patterns")
        print(f"   - {len(self.questions['questions'])} diagnostic questions")
    
    def _load_json(self, relative_path):
        """Load JSON file"""
        file_path = Path(__file__).parent.parent / relative_path
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def process_user_input(self, text_input, image_path=None):
        """Stage 1: Process user input"""
        print("\n" + "="*60)
        print("STAGE 1: INPUT PROCESSING")
        print("="*60)
        
        # Extract keywords
        keywords = [word.lower() for word in text_input.split() 
                   if len(word) > 3 and word.isalpha()]
        print(f"📝 Text input: {text_input}")
        print(f"🔑 Keywords extracted: {keywords[:5]}")
        
        # Brand detection
        brands = ["lenovo", "dell", "hp", "apple", "asus", "acer"]
        detected_brand = next((b for b in brands if b in text_input.lower()), None)
        brand_confidence = 0.95 if detected_brand else 0.0
        
        print(f"🏢 Brand detected: {detected_brand or 'None'} (confidence: {brand_confidence})")
        
        # Symptom extraction
        symptoms = []
        symptom_keywords = {
            "blue_screen": ["blue", "screen", "bsod"],
            "no_boot": ["won't", "boot", "start", "turn", "on"],
            "overheating": ["hot", "overheat", "thermal"],
            "screen_flickering": ["flicker", "display", "artifacts"],
            "battery_not_charging": ["battery", "charging", "charge"]
        }
        
        for symptom, kw_list in symptom_keywords.items():
            if any(kw in text_input.lower() for kw in kw_list):
                symptoms.append(symptom)
        
        print(f"🔍 Symptoms detected: {symptoms}")
        
        # Visual symptoms (simulated)
        visual_symptoms = []
        if image_path:
            print(f"📷 Image provided: {image_path}")
            # Simulate BLIP-2 analysis
            if "blue" in text_input.lower():
                visual_symptoms.append("error_0x007B")
            print(f"👁️ Visual symptoms: {visual_symptoms}")
        
        return {
            "keywords": keywords,
            "brand": detected_brand,
            "brand_confidence": brand_confidence,
            "symptoms": symptoms,
            "visual_symptoms": visual_symptoms,
            "category": "PC"  # Simplified
        }
    
    def initialize_beliefs(self, processed_input):
        """Stage 2: Initialize belief vector"""
        print("\n" + "="*60)
        print("STAGE 2: BELIEF INITIALIZATION")
        print("="*60)
        
        symptoms = processed_input["symptoms"] + processed_input["visual_symptoms"]
        beliefs = {}
        
        # Match symptoms to patterns
        for pattern in self.symptom_mappings["patterns"]:
            overlap = set(pattern["symptoms"]) & set(symptoms)
            if overlap:
                for cause, prob in pattern["causes"].items():
                    if cause not in beliefs:
                        beliefs[cause] = 0.0
                    beliefs[cause] += prob * (len(overlap) / len(pattern["symptoms"]))
        
        # Normalize
        total = sum(beliefs.values())
        if total > 0:
            beliefs = {k: round(v/total, 3) for k, v in beliefs.items()}
        
        # Sort by confidence
        beliefs = dict(sorted(beliefs.items(), key=lambda x: x[1], reverse=True))
        
        print("🧠 Initial belief vector:")
        for cause, confidence in list(beliefs.items())[:5]:
            print(f"   {cause}: {confidence:.3f}")
        
        max_confidence = max(beliefs.values()) if beliefs else 0.0
        print(f"\n📊 Max confidence: {max_confidence:.3f}")
        
        return beliefs, max_confidence
    
    def select_next_question(self, beliefs, processed_input, asked_questions):
        """Stage 3: Select next question"""
        print("\n" + "="*60)
        print("STAGE 3: QUESTION SELECTION")
        print("="*60)
        
        category = processed_input["category"]
        candidate_questions = [
            q for q in self.questions["questions"] 
            if q["category"] == category and q["id"] not in asked_questions
        ]
        
        print(f"📋 Candidate questions: {len(candidate_questions)}")
        
        # Apply skip logic
        filtered_questions = []
        for q in candidate_questions:
            skip_conditions = q.get("skip_if", {})
            should_skip = False
            
            # Check brand confidence skip
            if "brand_confidence" in skip_conditions:
                threshold = float(skip_conditions["brand_confidence"].replace(">", ""))
                if processed_input["brand_confidence"] > threshold:
                    print(f"⏭️ Skipping {q['id']}: Brand already known")
                    should_skip = True
            
            # Check symptom presence skip
            if "symptom_present" in skip_conditions:
                required = skip_conditions["symptom_present"]
                if any(s in processed_input["symptoms"] for s in required):
                    print(f"⏭️ Skipping {q['id']}: Symptom already detected")
                    should_skip = True
            
            if not should_skip:
                filtered_questions.append(q)
        
        print(f"✅ After skip logic: {len(filtered_questions)} questions")
        
        if not filtered_questions:
            return None
        
        # Select highest information gain
        best_question = max(filtered_questions, key=lambda q: q["information_gain_estimate"])
        
        print(f"\n❓ Selected question:")
        print(f"   ID: {best_question['id']}")
        print(f"   Text: {best_question['text']}")
        print(f"   Expected IG: {best_question['information_gain_estimate']:.2f}")
        
        return best_question
    
    def update_beliefs(self, beliefs, question, answer):
        """Stage 4: Update beliefs based on answer"""
        print("\n" + "="*60)
        print("STAGE 4: BELIEF UPDATE")
        print("="*60)
        
        print(f"💬 User answer: {answer}")
        
        updates = question["belief_updates"].get(answer, {})
        
        for cause, multiplier in updates.items():
            if cause in beliefs:
                old_value = beliefs[cause]
                if isinstance(multiplier, str) and multiplier.startswith("*"):
                    factor = float(multiplier[1:])
                    beliefs[cause] *= factor
                    print(f"   {cause}: {old_value:.3f} → {beliefs[cause]:.3f}")
        
        # Normalize
        total = sum(beliefs.values())
        if total > 0:
            beliefs = {k: v/total for k, v in beliefs.items()}
        
        # Sort
        beliefs = dict(sorted(beliefs.items(), key=lambda x: x[1], reverse=True))
        
        print("\n🧠 Updated belief vector:")
        for cause, confidence in list(beliefs.items())[:5]:
            print(f"   {cause}: {confidence:.3f}")
        
        max_confidence = max(beliefs.values()) if beliefs else 0.0
        print(f"\n📊 Max confidence: {max_confidence:.3f}")
        
        return beliefs, max_confidence
    
    async def match_tutorials(self, beliefs, processed_input):
        """Stage 5: Match tutorials"""
        print("\n" + "="*60)
        print("STAGE 5: TUTORIAL MATCHING")
        print("="*60)
        
        top_cause = max(beliefs, key=beliefs.get)
        confidence = beliefs[top_cause]
        
        print(f"🎯 Diagnosis: {top_cause} (confidence: {confidence:.3f})")
        
        # Simulate tutorial search
        print("\n🔎 Searching tutorials...")
        print(f"   Category: {processed_input['category']}")
        print(f"   Brand: {processed_input['brand']}")
        print(f"   Keywords: {processed_input['keywords'][:3]}")
        
        # Mock results
        tutorials = [
            {"id": 1, "title": f"Fix {top_cause.replace('_', ' ').title()}", "score": 0.94},
            {"id": 2, "title": "General troubleshooting guide", "score": 0.87},
            {"id": 3, "title": "Component replacement", "score": 0.79}
        ]
        
        print("\n📚 Matched tutorials:")
        for t in tutorials:
            print(f"   {t['id']}. {t['title']} (score: {t['score']:.2f})")
        
        return tutorials
    
    def record_feedback(self, session_id, tutorial_id, resolved):
        """Stage 6: Record user feedback"""
        print("\n" + "="*60)
        print("STAGE 6: FEEDBACK COLLECTION")
        print("="*60)
        
        print(f"⭐ Tutorial {tutorial_id} used")
        print(f"✅ Problem resolved: {resolved}")
        print(f"💾 Feedback saved to database")
        print(f"🔄 Learning cycle will process this session")
        
        return True

async def test_diagnostic_flow():
    """Test complete diagnostic flow"""
    
    print("\n" + "🚀 "*30)
    print("END-TO-END DIAGNOSTIC SYSTEM TEST")
    print("🚀 "*30)
    
    # Initialize system
    system = MockDiagnosticSystem()
    
    # Test Case 1: Blue screen with error code
    print("\n\n" + "="*60)
    print("TEST CASE 1: Lenovo laptop blue screen")
    print("="*60)
    
    # User input
    user_input = "My Lenovo IdeaPad 5 shows blue screen with error 0x007B after update"
    image_path = None
    
    # Stage 1: Process input
    processed = system.process_user_input(user_input, image_path)
    
    # Stage 2: Initialize beliefs
    beliefs, confidence = system.initialize_beliefs(processed)
    
    # Stage 3-4: Question loop
    asked_questions = []
    confidence_threshold = 0.75
    max_questions = 3
    
    while confidence < confidence_threshold and len(asked_questions) < max_questions:
        question = system.select_next_question(beliefs, processed, asked_questions)
        
        if question is None:
            print("\n⚠️ No more questions to ask")
            break
        
        asked_questions.append(question["id"])
        
        # Simulate user answer
        if question["id"] == "q_safe_mode_boot":
            answer = "no"
        elif question["id"] == "q_boot_logo":
            answer = "no"
        else:
            answer = "yes"
        
        beliefs, confidence = system.update_beliefs(beliefs, question, answer)
        
        if confidence >= confidence_threshold:
            print(f"\n✅ Confidence threshold reached: {confidence:.3f} >= {confidence_threshold}")
            break
    
    print(f"\n📊 Total questions asked: {len(asked_questions)}")
    
    # Stage 5: Match tutorials
    tutorials = await system.match_tutorials(beliefs, processed)
    
    # Stage 6: Feedback
    system.record_feedback(
        session_id="test-001",
        tutorial_id=tutorials[0]["id"],
        resolved=True
    )
    
    print("\n\n" + "✅ "*30)
    print("TEST COMPLETED SUCCESSFULLY")
    print("✅ "*30)
    
    print("\n📋 Summary:")
    print(f"   - Questions asked: {len(asked_questions)}")
    print(f"   - Final confidence: {confidence:.3f}")
    print(f"   - Diagnosis: {max(beliefs, key=beliefs.get)}")
    print(f"   - Tutorials found: {len(tutorials)}")
    print(f"   - Resolved: Yes")
    
    print("\n🔄 Next Steps:")
    print("   1. Implement real belief_engine.py")
    print("   2. Implement real input_processor.py with BLIP-2")
    print("   3. Implement tutorial_matcher.py with MyFixit integration")
    print("   4. Create API endpoints")
    print("   5. Setup learning cron job")

if __name__ == "__main__":
    asyncio.run(test_diagnostic_flow())
