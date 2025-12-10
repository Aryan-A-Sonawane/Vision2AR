"""
Learning Engine - Pattern Discovery and Knowledge Base Evolution

Discovers new symptom-cause patterns from successful resolutions
Generates new diagnostic questions from unclear cases
Updates confidence scores based on outcomes
"""

import json
import asyncpg
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path


class LearningEngine:
    """
    Analyzes diagnostic sessions to discover patterns and improve the system
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        self.base_path = Path(__file__).parent
        
        # Thresholds for pattern validation
        self.MIN_SUPPORT = 3  # Minimum occurrences to consider pattern
        self.MIN_SUCCESS_RATE = 0.7  # 70% success rate to approve
        self.MIN_INFO_GAIN = 0.15  # Minimum information gain for questions
    
    async def discover_new_patterns(self, lookback_days: int = 7) -> List[Dict]:
        """
        Analyze recent successful sessions to find new symptom→cause patterns
        
        Process:
        1. Get sessions with problem_resolved=True from last N days
        2. Group by (symptom_combination, final_diagnosis)
        3. Calculate success rate and confidence
        4. Create pattern_candidates if support >= MIN_SUPPORT
        
        Returns: List of discovered patterns
        """
        since = datetime.now() - timedelta(days=lookback_days)
        
        query = """
        SELECT 
            ds.initial_symptoms || ds.visual_symptoms as symptoms,
            ds.final_diagnosis as cause,
            ds.device_category as category,
            ds.problem_resolved,
            ds.session_id
        FROM diagnostic_sessions ds
        WHERE ds.created_at >= $1
            AND ds.final_diagnosis IS NOT NULL
            AND ds.tutorial_selected_id IS NOT NULL
        ORDER BY ds.created_at DESC
        """
        
        rows = await self.db.fetch(query, since)
        
        # Group by (category, symptoms, cause)
        pattern_groups = defaultdict(lambda: {"success": 0, "total": 0, "sessions": []})
        
        for row in rows:
            # Sort symptoms for consistent key
            symptoms = tuple(sorted(set(row['symptoms'])))
            key = (row['category'], symptoms, row['cause'])
            
            pattern_groups[key]['total'] += 1
            if row['problem_resolved']:
                pattern_groups[key]['success'] += 1
            pattern_groups[key]['sessions'].append(str(row['session_id']))
        
        # Filter and create candidates
        new_patterns = []
        
        for (category, symptoms, cause), stats in pattern_groups.items():
            if stats['total'] < self.MIN_SUPPORT:
                continue
            
            success_rate = stats['success'] / stats['total']
            
            if success_rate >= self.MIN_SUCCESS_RATE:
                # Check if pattern already exists
                existing = await self._check_existing_pattern(category, symptoms, cause)
                
                if existing:
                    # Update existing pattern
                    await self._update_pattern_stats(
                        existing['id'],
                        stats['total'],
                        success_rate
                    )
                else:
                    # Create new candidate
                    pattern = await self._create_pattern_candidate(
                        category=category,
                        symptoms=list(symptoms),
                        cause=cause,
                        support=stats['total'],
                        success_rate=success_rate,
                        sessions=stats['sessions']
                    )
                    new_patterns.append(pattern)
        
        return new_patterns
    
    async def _check_existing_pattern(self, category: str, symptoms: Tuple, cause: str):
        """Check if pattern already exists in learned_patterns or candidates"""
        query = """
        SELECT id, confidence, support_count
        FROM learned_patterns
        WHERE category = $1 
            AND symptom_combination = $2 
            AND cause = $3
        """
        return await self.db.fetchrow(query, category, list(symptoms), cause)
    
    async def _create_pattern_candidate(self, category: str, symptoms: List[str], 
                                       cause: str, support: int, 
                                       success_rate: float, sessions: List[str]) -> Dict:
        """Create new pattern candidate awaiting review"""
        confidence = self._calculate_pattern_confidence(support, success_rate)
        
        query = """
        INSERT INTO pattern_candidates 
        (symptom_combination, cause, category, observed_count, 
         success_count, confidence, supporting_session_ids)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        
        pattern_id = await self.db.fetchval(
            query,
            symptoms,
            cause,
            category,
            support,
            int(support * success_rate),
            confidence,
            sessions
        )
        
        return {
            "id": pattern_id,
            "category": category,
            "symptoms": symptoms,
            "cause": cause,
            "confidence": confidence,
            "support": support,
            "success_rate": success_rate
        }
    
    def _calculate_pattern_confidence(self, support: int, success_rate: float) -> float:
        """
        Calculate confidence score for pattern
        
        Factors:
        - Success rate (primary)
        - Support count (secondary, with diminishing returns)
        """
        # Base confidence from success rate
        base = success_rate
        
        # Boost from support count (logarithmic)
        support_boost = min(0.2, np.log(support) / 20)
        
        return min(1.0, base + support_boost)
    
    async def _update_pattern_stats(self, pattern_id: int, new_support: int, 
                                    new_success_rate: float):
        """Update existing pattern with new observations"""
        query = """
        UPDATE learned_patterns
        SET support_count = support_count + $1,
            success_rate = (success_rate + $2) / 2.0,
            confidence = $3,
            last_updated = CURRENT_TIMESTAMP
        WHERE id = $4
        """
        
        new_confidence = self._calculate_pattern_confidence(new_support, new_success_rate)
        await self.db.execute(query, new_support, new_success_rate, new_confidence, pattern_id)
    
    async def generate_new_questions(self, lookback_days: int = 14) -> List[Dict]:
        """
        Generate new diagnostic questions from ambiguous cases
        
        Strategy:
        1. Find sessions with low initial confidence (<0.5) that succeeded
        2. Identify which questions led to breakthrough
        3. Analyze what information was missing
        4. Generate question to get that info earlier
        
        Returns: List of candidate questions
        """
        since = datetime.now() - timedelta(days=lookback_days)
        
        # Get sessions with low start confidence, high end confidence
        query = """
        SELECT 
            ds.session_id,
            ds.device_category,
            ds.initial_symptoms,
            ds.final_diagnosis,
            bs_start.belief_vector as initial_beliefs,
            bs_end.belief_vector as final_beliefs
        FROM diagnostic_sessions ds
        JOIN belief_snapshots bs_start 
            ON bs_start.session_id = ds.session_id 
            AND bs_start.snapshot_order = 0
        JOIN belief_snapshots bs_end 
            ON bs_end.session_id = ds.session_id 
            AND bs_end.snapshot_order = (
                SELECT MAX(snapshot_order) 
                FROM belief_snapshots 
                WHERE session_id = ds.session_id
            )
        WHERE ds.created_at >= $1
            AND ds.problem_resolved = TRUE
            AND ds.questions_asked >= 2
        """
        
        rows = await self.db.fetch(query, since)
        
        question_candidates = []
        
        for row in rows:
            initial_beliefs = row['initial_beliefs']
            final_beliefs = row['final_beliefs']
            
            # Find belief with biggest gain
            max_gain_cause = None
            max_gain = 0
            
            for cause in final_beliefs.keys():
                gain = final_beliefs.get(cause, 0) - initial_beliefs.get(cause, 0)
                if gain > max_gain:
                    max_gain = gain
                    max_gain_cause = cause
            
            if max_gain > 0.3:  # Significant belief change
                # Find which questions caused this
                breakthrough_questions = await self._find_breakthrough_questions(
                    row['session_id'],
                    max_gain_cause
                )
                
                if breakthrough_questions:
                    question_candidates.append({
                        "category": row['device_category'],
                        "cause": max_gain_cause,
                        "symptoms": row['initial_symptoms'],
                        "breakthrough_questions": breakthrough_questions,
                        "gain": max_gain
                    })
        
        # Cluster similar candidates and generate new questions
        new_questions = await self._cluster_and_generate_questions(question_candidates)
        
        return new_questions
    
    async def _find_breakthrough_questions(self, session_id: str, cause: str) -> List[Dict]:
        """Find questions that significantly increased belief in this cause"""
        query = """
        SELECT 
            question_id,
            question_text,
            answer,
            belief_change
        FROM question_interactions
        WHERE session_id = $1
            AND belief_change IS NOT NULL
        ORDER BY answer_timestamp
        """
        
        rows = await self.db.fetch(query, session_id)
        
        breakthrough = []
        for row in rows:
            if row['belief_change']:
                # Check if this question boosted the cause
                change = row['belief_change'].get(cause, {})
                if change.get('after', 0) - change.get('before', 0) > 0.2:
                    breakthrough.append({
                        "question_id": row['question_id'],
                        "question": row['question_text'],
                        "answer": row['answer']
                    })
        
        return breakthrough
    
    async def _cluster_and_generate_questions(self, candidates: List[Dict]) -> List[Dict]:
        """
        Cluster similar situations and generate generalized questions
        
        For now, just returns promising candidates
        Future: Use clustering to generalize patterns
        """
        # Group by (category, cause)
        grouped = defaultdict(list)
        for c in candidates:
            key = (c['category'], c['cause'])
            grouped[key].append(c)
        
        new_questions = []
        
        for (category, cause), group in grouped.items():
            if len(group) < 3:  # Need multiple examples
                continue
            
            # Find common breakthrough question patterns
            question_counter = Counter()
            for item in group:
                for q in item['breakthrough_questions']:
                    question_counter[q['question_id']] += 1
            
            # Most common breakthrough question
            if question_counter:
                most_common_q_id = question_counter.most_common(1)[0][0]
                
                new_questions.append({
                    "category": category,
                    "cause": cause,
                    "based_on_question": most_common_q_id,
                    "observed_count": len(group),
                    "avg_gain": np.mean([item['gain'] for item in group])
                })
        
        return new_questions
    
    async def update_question_effectiveness(self):
        """
        Update analytics for all questions based on recent usage
        
        Calculates:
        - Average information gain
        - Correlation with successful resolution
        - Skip rate
        """
        query = """
        SELECT 
            qi.question_id,
            AVG(qi.information_gain) as avg_gain,
            COUNT(*) as times_asked,
            SUM(CASE WHEN qi.was_skipped THEN 1 ELSE 0 END) as times_skipped,
            AVG(CASE WHEN ds.problem_resolved THEN 1.0 ELSE 0.0 END) as success_rate
        FROM question_interactions qi
        JOIN diagnostic_sessions ds ON ds.session_id = qi.session_id
        WHERE qi.answer_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
        GROUP BY qi.question_id
        """
        
        rows = await self.db.fetch(query)
        
        for row in rows:
            await self.db.execute("""
                INSERT INTO question_analytics 
                (question_id, category, times_asked, times_skipped, 
                 avg_information_gain, correlation_with_success, last_asked)
                VALUES ($1, 'PC', $2, $3, $4, $5, CURRENT_TIMESTAMP)
                ON CONFLICT (question_id) DO UPDATE SET
                    times_asked = question_analytics.times_asked + $2,
                    times_skipped = question_analytics.times_skipped + $3,
                    avg_information_gain = $4,
                    correlation_with_success = $5,
                    last_asked = CURRENT_TIMESTAMP
            """, row['question_id'], row['times_asked'], row['times_skipped'],
                row['avg_gain'] or 0.0, row['success_rate'] or 0.0)
    
    async def approve_pattern(self, pattern_id: int) -> bool:
        """
        Move pattern from candidates to learned_patterns (human review)
        """
        # Get candidate
        candidate = await self.db.fetchrow("""
            SELECT * FROM pattern_candidates WHERE id = $1
        """, pattern_id)
        
        if not candidate:
            return False
        
        # Create pattern
        pattern_id = f"{candidate['category']}_{candidate['cause']}_{hash(tuple(candidate['symptom_combination']))}"
        
        await self.db.execute("""
            INSERT INTO learned_patterns
            (pattern_id, category, symptom_combination, cause, confidence,
             support_count, success_rate, source, approved)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'learned', TRUE)
        """, pattern_id, candidate['category'], candidate['symptom_combination'],
            candidate['cause'], candidate['confidence'], candidate['observed_count'],
            candidate['success_count'] / candidate['observed_count'] if candidate['observed_count'] > 0 else 0)
        
        # Mark as reviewed
        await self.db.execute("""
            UPDATE pattern_candidates SET reviewed = TRUE WHERE id = $1
        """, pattern_id)
        
        return True
    
    async def export_to_json(self, output_path: str = None):
        """
        Export approved learned patterns to symptom_mappings.json
        Export approved questions to questions.json
        
        Merges with existing base rules
        """
        if output_path is None:
            output_path = self.base_path
        
        # Load existing mappings
        mappings_file = Path(output_path) / "symptom_mappings.json"
        if mappings_file.exists():
            with open(mappings_file) as f:
                mappings = json.load(f)
        else:
            mappings = {}
        
        # Get approved patterns
        patterns = await self.db.fetch("""
            SELECT category, symptom_combination, cause, confidence
            FROM learned_patterns
            WHERE approved = TRUE AND confidence >= 0.7
        """)
        
        # Merge into mappings
        for p in patterns:
            category = p['category']
            if category not in mappings:
                mappings[category] = {}
            
            # Create symptom key (concatenated sorted symptoms)
            symptom_key = "_".join(sorted(p['symptom_combination']))
            
            if symptom_key not in mappings[category]:
                mappings[category][symptom_key] = {}
            
            mappings[category][symptom_key][p['cause']] = p['confidence']
        
        # Write back
        with open(mappings_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        
        print(f"✅ Exported learned patterns to {mappings_file}")
        
        # Export questions (similar process)
        questions_file = Path(output_path) / "questions.json"
        if questions_file.exists():
            with open(questions_file) as f:
                questions = json.load(f)
        else:
            questions = {}
        
        learned_q = await self.db.fetch("""
            SELECT * FROM learned_questions
            WHERE approved = TRUE AND information_gain_avg >= $1
        """, self.MIN_INFO_GAIN)
        
        for q in learned_q:
            category = q['category']
            context = q['issue_context']
            
            if category not in questions:
                questions[category] = {}
            if context not in questions[category]:
                questions[category][context] = {}
            
            questions[category][context][q['question_id']] = {
                "question": q['question_text'],
                "type": q['question_type'],
                "intent": q['intent'],
                "affects_causes": q['affects_causes'],
                "yes_updates": q['yes_updates'],
                "no_updates": q['no_updates'],
                "source": "learned"
            }
        
        with open(questions_file, 'w') as f:
            json.dump(questions, f, indent=2)
        
        print(f"✅ Exported learned questions to {questions_file}")
        
        return {
            "patterns_exported": len(patterns),
            "questions_exported": len(learned_q)
        }


async def run_learning_cycle(db_pool: asyncpg.Pool):
    """
    Main learning cycle - run daily as cron job
    
    Steps:
    1. Discover new patterns from recent sessions
    2. Generate new questions from ambiguous cases
    3. Update question effectiveness metrics
    4. Export high-confidence learnings to JSON files
    """
    engine = LearningEngine(db_pool)
    
    print("🧠 Starting learning cycle...")
    
    # Discover patterns
    print("\n[1/4] Discovering new patterns...")
    patterns = await engine.discover_new_patterns(lookback_days=7)
    print(f"   Found {len(patterns)} new pattern candidates")
    
    # Generate questions
    print("\n[2/4] Generating new questions...")
    questions = await engine.generate_new_questions(lookback_days=14)
    print(f"   Generated {len(questions)} question candidates")
    
    # Update analytics
    print("\n[3/4] Updating question effectiveness...")
    await engine.update_question_effectiveness()
    print(f"   ✓ Analytics updated")
    
    # Export approved learnings
    print("\n[4/4] Exporting approved patterns...")
    result = await engine.export_to_json()
    print(f"   ✓ Exported {result['patterns_exported']} patterns")
    print(f"   ✓ Exported {result['questions_exported']} questions")
    
    print("\n✅ Learning cycle complete!")


if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def main():
        # Connect to database
        conn = await asyncpg.create_pool(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB')
        )
        
        await run_learning_cycle(conn)
        
        await conn.close()
    
    asyncio.run(main())
