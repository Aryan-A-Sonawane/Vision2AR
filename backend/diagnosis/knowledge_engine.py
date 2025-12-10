"""
Knowledge-Based ML Diagnosis Engine
Learns from extracted manual data and provides real solutions
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
from pathlib import Path
from .smart_question_generator import SmartQuestionGenerator


class KnowledgeBasedDiagnosisEngine:
    """
    ML engine that learns from OEM manuals
    - Embeds manual procedures
    - Matches user symptoms to known issues
    - Provides actual repair solutions from manuals
    """
    
    def __init__(self, knowledge_base_path: str = "knowledge_base_v2.json"):
        print("🤖 Initializing Knowledge-Based ML Engine...")
        
        # Load sentence transformer for semantic matching
        print("  Loading sentence transformer model...")
        import os
        cache_dir = os.getenv("TRANSFORMERS_CACHE", "E:\\z.code\\arvr\\.cache")
        self.model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
        print("  ✓ Model loaded")
        
        # Initialize smart question generator
        self.question_generator = SmartQuestionGenerator(self.model)
        print("  ✓ Smart question generator initialized")
        
        # Load knowledge base from extracted manuals
        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)
        print(f"  ✓ Loaded {len(self.knowledge_base)} procedures from manuals")
        
        # Pre-compute embeddings for all procedures
        print("  Computing embeddings for procedures...")
        self._build_procedure_embeddings()
        print("  ✓ Embeddings ready")
        
        print("✓ Engine ready!")
    
    def _load_knowledge_base(self, path: str) -> List[Dict]:
        """Load extracted knowledge from JSON"""
        
        kb_path = Path(path)
        if not kb_path.exists():
            print(f"⚠ Knowledge base not found: {path}")
            print("  Run manual_extractor.py first to extract data from PDFs")
            return []
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_procedure_embeddings(self):
        """Pre-compute embeddings for all procedures"""
        
        self.procedure_embeddings = []
        
        for proc in self.knowledge_base:
            # Combine symptoms and issue type for embedding
            text_to_embed = f"{proc['issue_type']} {' '.join(proc.get('symptoms', []))}"
            
            embedding = self.model.encode(text_to_embed)
            self.procedure_embeddings.append(embedding)
        
        if self.procedure_embeddings:
            self.procedure_embeddings = np.array(self.procedure_embeddings)
    
    def diagnose(
        self,
        user_symptoms: str,
        user_answers: List[Dict] = None
    ) -> Tuple[Dict, List[Dict]]:
        """
        Main diagnosis function
        
        Args:
            user_symptoms: Initial symptom description
            user_answers: List of Q&A pairs from conversation
        
        Returns:
            (best_match_procedure, top_3_alternatives)
        """
        
        print("\n" + "="*70)
        print("🔍 DIAGNOSING FROM OEM MANUALS")
        print("="*70)
        print(f"User Symptoms: {user_symptoms}")
        
        # Embed user symptoms
        symptom_embedding = self.model.encode(user_symptoms)
        print(f"✓ Symptom embedding generated ({len(symptom_embedding)} dimensions)")
        
        # Find similar procedures from knowledge base
        similarities = self._compute_similarities(symptom_embedding)
        print(f"✓ Computed similarities with {len(self.knowledge_base)} procedures")
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:5]
        print(f"\n📊 Top 5 matches:")
        
        matches = []
        for idx in top_indices:
            if idx < len(self.knowledge_base):
                proc = self.knowledge_base[idx].copy()
                proc['similarity_score'] = float(similarities[idx])
                proc['confidence'] = self._calculate_confidence(
                    similarities[idx],
                    user_symptoms,
                    proc,
                    user_answers
                )
                matches.append(proc)
                
                # Print match info
                print(f"  {len(matches)}. {proc['issue_type']:20s} | Similarity: {similarities[idx]:.3f} | Confidence: {proc['confidence']:.3f} | Source: {proc['source_file']}")
        
        # Return best match + alternatives
        best_match = matches[0] if matches else None
        alternatives = matches[1:4] if len(matches) > 1 else []
        
        if best_match:
            print(f"\n✓ BEST MATCH: {best_match['issue_type']} (Confidence: {best_match['confidence']:.2%})")
            print(f"  Source: {best_match['source_file']}")
            print(f"  Solution steps: {len(best_match['solution_steps'])}")
            print(f"  Tools needed: {len(best_match['tools_needed'])}")
        else:
            print("\n⚠ No matches found in knowledge base")
        
        print("="*70 + "\n")
        
        return best_match, alternatives
    
    def _compute_similarities(self, query_embedding: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all procedures"""
        
        if len(self.procedure_embeddings) == 0:
            return np.array([])
        
        # Cosine similarity
        similarities = np.dot(
            self.procedure_embeddings,
            query_embedding
        ) / (
            np.linalg.norm(self.procedure_embeddings, axis=1) *
            np.linalg.norm(query_embedding)
        )
        
        return similarities
    
    def _calculate_confidence(
        self,
        similarity_score: float,
        user_symptoms: str,
        procedure: Dict,
        user_answers: List[Dict]
    ) -> float:
        """Calculate confidence based on multiple factors"""
        
        # Start with higher base confidence (75% of similarity instead of 60%)
        confidence = similarity_score * 0.75
        
        # Boost if user symptoms mention specific keywords from procedure
        symptoms_lower = user_symptoms.lower()
        issue_keywords = procedure['issue_type'].split('_')
        
        keyword_matches = 0
        for keyword in issue_keywords:
            if keyword in symptoms_lower:
                keyword_matches += 1
        
        # More aggressive keyword bonus (0.08 per match, up to 0.24)
        confidence += min(keyword_matches * 0.08, 0.24)
        
        # Progressive bonus for each answer (not just >2)
        # 1 answer: +5%, 2 answers: +10%, 3+ answers: +15%
        if user_answers:
            answer_count = len(user_answers)
            if answer_count == 1:
                confidence += 0.05
            elif answer_count == 2:
                confidence += 0.10
            elif answer_count >= 3:
                confidence += 0.15
            
            # Extra bonus for detailed answers (>20 words)
            detailed_count = sum(1 for a in user_answers 
                               if isinstance(a, dict) and len(a.get('answer', '').split()) > 20)
            if detailed_count > 0:
                confidence += 0.05 * detailed_count  # +5% per detailed answer
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def generate_question(
        self,
        current_understanding: Dict,
        asked_questions: List[str] = None,
        conversation_history: List[Dict] = None,
        user_symptoms: str = ""
    ) -> Optional[Dict]:
        """
        Generate next diagnostic question using smart question generator
        
        Returns question object with reasoning, or None if no more questions needed
        """
        
        if asked_questions is None:
            asked_questions = []
        if conversation_history is None:
            conversation_history = []
        
        issue_type = current_understanding.get('issue_type', 'unknown')
        confidence = current_understanding.get('confidence', 0.0)
        manual_text = current_understanding.get('raw_text', '')
        
        # If confidence already high, don't ask more (lowered from 80% to 75%)
        if confidence > 0.75:
            print(f"  Confidence {confidence:.2%} is high enough, stopping questions")
            return None
        
        # Use smart question generator
        questions = self.question_generator.generate_contextual_questions(
            manual_text=manual_text,
            issue_type=issue_type,
            user_symptoms=user_symptoms,
            conversation_history=conversation_history,
            confidence=confidence,
            max_questions=1  # Generate one question at a time
        )
        
        if questions:
            return questions[0]
        
        # Fallback if generator returns nothing
        return {
            "id": "fallback_q",
            "text": "Can you provide any additional details about the issue?",
            "type": "open_ended",
            "source": "fallback",
            "reasoning": "Gathering more information to improve diagnosis",
            "expected_info": "Additional symptoms"
        }
    
    def format_solution(self, procedure: Dict) -> Dict:
        """Format procedure into user-friendly solution"""
        
        return {
            "diagnosis": procedure['issue_type'].replace('_', ' ').title(),
            "confidence": procedure.get('confidence', 0.7),
            "source": f"{procedure['brand'].title()} {procedure['manual_type'].replace('_', ' ').title()}",
            "source_file": procedure['source_file'],
            
            "solution_steps": procedure.get('solution_steps', []),
            "tools_needed": procedure.get('tools_needed', []),
            "warnings": procedure.get('warnings', []),
            
            "raw_manual_text": procedure.get('raw_text', ''),
            
            "alternative_causes": [],  # Will be filled with alternatives
            
            "recommendation": self._generate_recommendation(procedure)
        }
    
    def update_diagnosis_with_answer(
        self,
        current_diagnosis: Dict,
        user_symptoms: str,
        answer: str,
        question_asked: str,
        all_answers: List[Dict]
    ) -> Tuple[Dict, float]:
        """
        Update diagnosis based on user answer
        
        Returns:
            (updated_diagnosis, confidence_delta)
        """
        # Analyze answer for confidence adjustment
        confidence_delta, keywords = self.question_generator.analyze_answer_for_confidence_update(
            answer=answer,
            current_diagnosis=current_diagnosis,
            question_asked=question_asked
        )
        
        # Re-run diagnosis with accumulated context
        combined_symptoms = f"{user_symptoms} {answer}"
        
        # Re-embed and find matches
        symptom_embedding = self.model.encode(combined_symptoms)
        similarities = self._compute_similarities(symptom_embedding)
        
        # Check if answer changed the top match
        top_index = np.argmax(similarities)
        new_match = self.knowledge_base[top_index].copy()
        new_match['similarity_score'] = float(similarities[top_index])
        
        # Calculate updated confidence
        old_confidence = current_diagnosis.get('confidence', 0.5)
        new_base_confidence = self._calculate_confidence(
            new_match['similarity_score'],
            combined_symptoms,
            new_match,
            all_answers
        )
        
        # Apply confidence delta from answer analysis
        updated_confidence = min(new_base_confidence + confidence_delta, 0.95)
        new_match['confidence'] = updated_confidence
        
        print(f"\n📊 Confidence Update:")
        print(f"  Previous: {old_confidence:.2%}")
        print(f"  Base (re-match): {new_base_confidence:.2%}")
        print(f"  Answer delta: {confidence_delta:+.2%}")
        print(f"  Updated: {updated_confidence:.2%}")
        print(f"  Keywords extracted: {keywords}")
        
        return new_match, confidence_delta
    
    def _generate_recommendation(self, procedure: Dict) -> str:
        """Generate recommendation text"""
        
        confidence = procedure.get('confidence', 0.7)
        
        if confidence > 0.8:
            return "High confidence diagnosis based on OEM manual procedures."
        elif confidence > 0.6:
            return "Likely diagnosis. Follow the steps carefully and check alternatives if this doesn't resolve the issue."
        else:
            return "Possible diagnosis. Consider checking alternative causes listed below."


# Global instance
_engine = None

def get_engine() -> KnowledgeBasedDiagnosisEngine:
    """Get or create global engine instance"""
    global _engine
    if _engine is None:
        _engine = KnowledgeBasedDiagnosisEngine()
    return _engine
