"""
Diagnostic Session Manager - Orchestrates entire diagnostic flow with logging

Manages:
- Session state persistence
- Log generation for frontend display
- Integration of belief engine, questions, tutorial matching
- Feedback collection and learning trigger
"""

import uuid
import json
import asyncpg
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class DiagnosticSession:
    """
    Represents a single user diagnostic session
    Tracks all interactions and generates detailed logs
    """
    
    def __init__(self, db_pool: asyncpg.Pool, session_id: str = None):
        self.db = db_pool
        self.session_id = session_id or str(uuid.uuid4())
        self.logs = []
        self.log_order = 0
        self.snapshot_order = 0
        
        # Session state
        self.state = {
            "brand": None,
            "brand_confidence": 0.0,
            "model": None,
            "category": None,
            "symptoms": [],
            "visual_symptoms": [],
            "belief_vector": {},
            "questions_asked": [],
            "current_question": None,
            "final_diagnosis": None,
            "matched_tutorials": []
        }
    
    async def initialize(self, user_input: Dict) -> Dict:
        """
        Start new session with user input
        
        Args:
            user_input: {
                "text": str,
                "image": Optional[file],
                "user_id": Optional[str]
            }
        
        Returns:
            {
                "session_id": str,
                "logs": List[Dict],
                "next_action": "ask_question" | "show_tutorials",
                "question": Optional[Dict],
                "tutorials": Optional[List]
            }
        """
        self._log("SESSION_START", "Starting new diagnostic session", {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process input
        from analysis.input_processor import InputProcessor
        processor = InputProcessor()
        
        self._log("INPUT_PROCESSING", "Analyzing user input", {
            "text_length": len(user_input.get('text', '')),
            "has_image": user_input.get('image') is not None
        })
        
        result = await processor.process_async(user_input)
        
        # Update state
        self.state.update({
            "brand": result.get('brand'),
            "brand_confidence": result.get('brand_confidence', 0.0),
            "category": result.get('device_category'),
            "symptoms": result.get('symptoms', []),
            "visual_symptoms": result.get('visual_symptoms', [])
        })
        
        self._log("INPUT_ANALYSIS_COMPLETE", "Input analysis complete", {
            "brand": self.state['brand'],
            "brand_confidence": f"{self.state['brand_confidence']:.2f}",
            "category": self.state['category'],
            "symptoms": self.state['symptoms'],
            "visual_symptoms": self.state['visual_symptoms']
        })
        
        # Store in database
        await self._save_session_to_db(user_input)
        
        # Initialize belief engine
        from diagnosis.belief_engine import BeliefVectorEngine
        engine = BeliefVectorEngine(self.db)
        
        self._log("BELIEF_ENGINE_INIT", "Initializing belief vector", {
            "symptoms": self.state['symptoms'] + self.state['visual_symptoms'],
            "category": self.state['category']
        })
        
        beliefs = await engine.initialize_with_learning(
            symptoms=self.state['symptoms'] + self.state['visual_symptoms'],
            category=self.state['category'],
            brand=self.state['brand']
        )
        
        self.state['belief_vector'] = beliefs
        
        self._log("BELIEF_VECTOR_COMPUTED", "Initial belief vector", {
            "top_causes": dict(sorted(beliefs.items(), key=lambda x: x[1], reverse=True)[:5]),
            "max_confidence": f"{max(beliefs.values()):.2f}" if beliefs else "0.00"
        })
        
        await self._save_belief_snapshot(beliefs, "initial")
        
        # Get next question or show tutorials
        max_confidence = max(beliefs.values()) if beliefs else 0
        
        if max_confidence >= 0.7:
            self._log("CONFIDENCE_SUFFICIENT", "High confidence reached, skipping questions", {
                "confidence": f"{max_confidence:.2f}",
                "diagnosis": max(beliefs.items(), key=lambda x: x[1])[0]
            })
            
            return await self._match_and_return_tutorials()
        else:
            self._log("CONFIDENCE_LOW", "Requesting clarifying questions", {
                "confidence": f"{max_confidence:.2f}",
                "threshold": "0.70"
            })
            
            question = await engine.get_next_question(self.state)
            
            if question:
                self.state['current_question'] = question
                await self._save_question(question)
                
                self._log("QUESTION_SELECTED", "Asking clarifying question", {
                    "question_id": question['id'],
                    "question": question['question'],
                    "type": question['type'],
                    "reason": "To discriminate between top causes"
                })
                
                return {
                    "session_id": self.session_id,
                    "logs": self.logs,
                    "next_action": "ask_question",
                    "question": question,
                    "current_beliefs": dict(sorted(beliefs.items(), key=lambda x: x[1], reverse=True)[:3])
                }
            else:
                return await self._match_and_return_tutorials()
    
    async def answer_question(self, question_id: str, answer: Any) -> Dict:
        """
        Process user's answer to question
        
        Returns: Next question or tutorials
        """
        self._log("QUESTION_ANSWERED", "User provided answer", {
            "question_id": question_id,
            "answer": str(answer)
        })
        
        # Update belief vector
        from diagnosis.belief_engine import BeliefVectorEngine
        engine = BeliefVectorEngine(self.db)
        engine.state = self.state
        
        old_beliefs = self.state['belief_vector'].copy()
        
        new_beliefs = await engine.update_belief(question_id, answer)
        
        self.state['belief_vector'] = new_beliefs
        self.state['questions_asked'].append(question_id)
        
        # Calculate belief change
        belief_changes = {}
        for cause in set(old_beliefs.keys()) | set(new_beliefs.keys()):
            old_val = old_beliefs.get(cause, 0)
            new_val = new_beliefs.get(cause, 0)
            if abs(new_val - old_val) > 0.01:
                belief_changes[cause] = {
                    "before": f"{old_val:.2f}",
                    "after": f"{new_val:.2f}",
                    "change": f"{new_val - old_val:+.2f}"
                }
        
        self._log("BELIEF_VECTOR_UPDATED", "Beliefs updated based on answer", {
            "changes": belief_changes,
            "top_causes_now": dict(sorted(new_beliefs.items(), key=lambda x: x[1], reverse=True)[:3])
        })
        
        await self._save_belief_snapshot(new_beliefs, f"question_{question_id}")
        await self._save_question_interaction(question_id, answer, belief_changes)
        
        # Check confidence
        max_confidence = max(new_beliefs.values()) if new_beliefs else 0
        
        if max_confidence >= 0.7:
            self._log("CONFIDENCE_THRESHOLD_REACHED", "Sufficient confidence achieved", {
                "confidence": f"{max_confidence:.2f}",
                "diagnosis": max(new_beliefs.items(), key=lambda x: x[1])[0],
                "questions_asked": len(self.state['questions_asked'])
            })
            
            return await self._match_and_return_tutorials()
        else:
            # Get next question
            next_question = await engine.get_next_question(self.state)
            
            if next_question:
                self.state['current_question'] = next_question
                await self._save_question(next_question)
                
                self._log("NEXT_QUESTION", "Asking follow-up question", {
                    "question_id": next_question['id'],
                    "question": next_question['question'],
                    "current_confidence": f"{max_confidence:.2f}"
                })
                
                return {
                    "session_id": self.session_id,
                    "logs": self.logs,
                    "next_action": "ask_question",
                    "question": next_question,
                    "current_beliefs": dict(sorted(new_beliefs.items(), key=lambda x: x[1], reverse=True)[:3])
                }
            else:
                # No more questions, show tutorials anyway
                self._log("NO_MORE_QUESTIONS", "No additional questions available", {
                    "confidence": f"{max_confidence:.2f}",
                    "proceeding_with": "best guess"
                })
                
                return await self._match_and_return_tutorials()
    
    async def _match_and_return_tutorials(self) -> Dict:
        """
        Match tutorials based on current belief vector
        """
        from analysis.tutorial_matcher import TutorialMatcher
        matcher = TutorialMatcher(self.db)
        
        top_cause = max(self.state['belief_vector'].items(), key=lambda x: x[1])
        self.state['final_diagnosis'] = top_cause[0]
        
        self._log("TUTORIAL_MATCHING", "Searching for relevant tutorials", {
            "diagnosis": self.state['final_diagnosis'],
            "confidence": f"{top_cause[1]:.2f}",
            "category": self.state['category'],
            "brand": self.state['brand']
        })
        
        tutorials = await matcher.match_tutorials(
            symptoms=self.state['symptoms'] + self.state['visual_symptoms'],
            cause=self.state['final_diagnosis'],
            category=self.state['category'],
            brand=self.state['brand']
        )
        
        self.state['matched_tutorials'] = tutorials
        
        self._log("TUTORIALS_FOUND", f"Found {len(tutorials)} matching tutorials", {
            "count": len(tutorials),
            "top_match": tutorials[0]['title'] if tutorials else "None",
            "top_score": f"{tutorials[0]['combined_score']:.2f}" if tutorials else "0.00"
        })
        
        # Save matches to DB
        await self._save_tutorial_matches(tutorials)
        
        # Update session in DB
        await self.db.execute("""
            UPDATE diagnostic_sessions
            SET final_diagnosis = $1,
                final_confidence = $2,
                questions_asked = $3
            WHERE session_id = $4
        """, self.state['final_diagnosis'], top_cause[1], 
            len(self.state['questions_asked']), self.session_id)
        
        return {
            "session_id": self.session_id,
            "logs": self.logs,
            "next_action": "show_tutorials",
            "diagnosis": {
                "cause": self.state['final_diagnosis'],
                "confidence": top_cause[1],
                "questions_asked": len(self.state['questions_asked'])
            },
            "tutorials": tutorials[:5]  # Top 5
        }
    
    async def record_feedback(self, tutorial_id: int, feedback: Dict):
        """
        Record user feedback after tutorial completion
        
        Triggers learning engine to analyze patterns
        """
        self._log("FEEDBACK_RECEIVED", "User provided feedback", {
            "tutorial_id": tutorial_id,
            "solved_problem": feedback.get('solved_problem'),
            "rating": feedback.get('clarity_rating')
        })
        
        await self.db.execute("""
            INSERT INTO user_feedback
            (session_id, tutorial_id, solved_problem, clarity_rating,
             accuracy_rating, completion_percentage, time_spent_minutes, comments)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, self.session_id, tutorial_id, feedback.get('solved_problem'),
            feedback.get('clarity_rating'), feedback.get('accuracy_rating'),
            feedback.get('completion_percentage'), feedback.get('time_spent_minutes'),
            feedback.get('comments'))
        
        # Update session
        await self.db.execute("""
            UPDATE diagnostic_sessions
            SET problem_resolved = $1,
                tutorial_selected_id = $2,
                completed_at = CURRENT_TIMESTAMP
            WHERE session_id = $3
        """, feedback.get('solved_problem'), tutorial_id, self.session_id)
        
        # Trigger learning if successful
        if feedback.get('solved_problem'):
            self._log("LEARNING_TRIGGER", "Successful resolution - triggering learning", {
                "pattern": f"{self.state['symptoms']} → {self.state['final_diagnosis']}",
                "confidence": f"{max(self.state['belief_vector'].values()):.2f}"
            })
    
    def _log(self, stage: str, action: str, data: Dict):
        """Add log entry for frontend display"""
        log_entry = {
            "order": self.log_order,
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "action": action,
            "data": data
        }
        self.logs.append(log_entry)
        self.log_order += 1
    
    async def _save_session_to_db(self, user_input: Dict):
        """Create session record in database"""
        await self.db.execute("""
            INSERT INTO diagnostic_sessions
            (session_id, user_id, device_category, brand, brand_confidence,
             initial_input_text, initial_symptoms, visual_symptoms)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, self.session_id, user_input.get('user_id'), self.state['category'],
            self.state['brand'], self.state['brand_confidence'],
            user_input.get('text'), self.state['symptoms'], self.state['visual_symptoms'])
    
    async def _save_belief_snapshot(self, beliefs: Dict, trigger: str):
        """Save belief vector snapshot"""
        await self.db.execute("""
            INSERT INTO belief_snapshots
            (session_id, snapshot_order, belief_vector, trigger_event)
            VALUES ($1, $2, $3, $4)
        """, self.session_id, self.snapshot_order, json.dumps(beliefs), trigger)
        self.snapshot_order += 1
    
    async def _save_question(self, question: Dict):
        """Record question being asked"""
        await self.db.execute("""
            INSERT INTO question_interactions
            (session_id, question_id, question_text, question_type)
            VALUES ($1, $2, $3, $4)
        """, self.session_id, question['id'], question['question'], question['type'])
    
    async def _save_question_interaction(self, question_id: str, answer: Any, 
                                         belief_change: Dict):
        """Update question with answer and belief changes"""
        await self.db.execute("""
            UPDATE question_interactions
            SET answer = $1,
                answer_timestamp = CURRENT_TIMESTAMP,
                belief_change = $2
            WHERE session_id = $3 AND question_id = $4
        """, str(answer), json.dumps(belief_change), self.session_id, question_id)
    
    async def _save_tutorial_matches(self, tutorials: List[Dict]):
        """Save matched tutorials with scores"""
        for rank, tutorial in enumerate(tutorials[:10], 1):
            await self.db.execute("""
                INSERT INTO tutorial_matches
                (session_id, tutorial_id, match_rank, vector_score,
                 keyword_score, combined_score, match_reasoning)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, self.session_id, tutorial['id'], rank,
                tutorial.get('vector_score', 0), tutorial.get('keyword_score', 0),
                tutorial.get('combined_score', 0), json.dumps(tutorial.get('reasoning', {})))
    
    async def get_logs_for_display(self) -> List[Dict]:
        """
        Get all logs formatted for frontend terminal display
        
        Returns: List of log entries with color coding
        """
        formatted_logs = []
        
        for log in self.logs:
            # Add color coding based on stage
            color = self._get_log_color(log['stage'])
            icon = self._get_log_icon(log['stage'])
            
            formatted_logs.append({
                **log,
                "color": color,
                "icon": icon,
                "formatted_data": self._format_log_data(log['data'])
            })
        
        return formatted_logs
    
    def _get_log_color(self, stage: str) -> str:
        """Get terminal color for log stage"""
        colors = {
            "SESSION_START": "cyan",
            "INPUT_PROCESSING": "yellow",
            "INPUT_ANALYSIS_COMPLETE": "green",
            "BELIEF_ENGINE_INIT": "blue",
            "BELIEF_VECTOR_COMPUTED": "magenta",
            "QUESTION_SELECTED": "yellow",
            "QUESTION_ANSWERED": "green",
            "BELIEF_VECTOR_UPDATED": "magenta",
            "CONFIDENCE_THRESHOLD_REACHED": "green",
            "TUTORIAL_MATCHING": "blue",
            "TUTORIALS_FOUND": "green",
            "FEEDBACK_RECEIVED": "cyan"
        }
        return colors.get(stage, "white")
    
    def _get_log_icon(self, stage: str) -> str:
        """Get emoji icon for log stage"""
        icons = {
            "SESSION_START": "🚀",
            "INPUT_PROCESSING": "🔍",
            "INPUT_ANALYSIS_COMPLETE": "✅",
            "BELIEF_ENGINE_INIT": "🧠",
            "BELIEF_VECTOR_COMPUTED": "📊",
            "QUESTION_SELECTED": "❓",
            "QUESTION_ANSWERED": "💬",
            "BELIEF_VECTOR_UPDATED": "📈",
            "CONFIDENCE_THRESHOLD_REACHED": "✅",
            "TUTORIAL_MATCHING": "🔎",
            "TUTORIALS_FOUND": "📚",
            "FEEDBACK_RECEIVED": "⭐"
        }
        return icons.get(stage, "•")
    
    def _format_log_data(self, data: Dict) -> str:
        """Format log data for readable display"""
        lines = []
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value, indent=2)
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
