"""
Tutorial Matcher with MyFixit Integration
Implements hybrid search (60% vector + 40% keyword) with feedback re-ranking
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import asyncpg
import weaviate
from sentence_transformers import SentenceTransformer
import os

class TutorialMatcher:
    """Matches diagnostic results to repair tutorials using hybrid search"""
    
    def __init__(self, db_pool: asyncpg.Pool, weaviate_client: weaviate.Client):
        self.db_pool = db_pool
        self.weaviate_client = weaviate_client
        
        # Load sentence transformer for vector search
        self.text_encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("[OK] Loaded text encoder for tutorial matching")
        
        # MyFixit dataset paths
        self.myfixit_path = Path(__file__).parent.parent / "data" / "myfixit" / "jsons"
        self.myfixit_cache = {}  # In-memory cache for loaded JSON files
        
        # Hybrid search weights
        self.beta = 0.6  # Vector weight
        self.gamma = 0.3  # Feedback re-ranking weight
    
    def _load_myfixit_category(self, category: str) -> List[Dict]:
        """
        Load MyFixit JSON file for specific category
        Cache in memory to avoid repeated file I/O
        """
        if category in self.myfixit_cache:
            return self.myfixit_cache[category]
        
        # Map category to file
        category_files = {
            "PC": "PC.json",
            "Mac": "Mac.json",
            "Phone": "Phone.json",
            "Tablet": "Tablet.json",
            "Computer Hardware": "Computer Hardware.json"
        }
        
        filename = category_files.get(category, "PC.json")
        filepath = self.myfixit_path / filename
        
        if not filepath.exists():
            print(f"[WARN] MyFixit file not found: {filepath}")
            return []
        
        try:
            # Load JSONL format (one JSON object per line)
            guides = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        guides.append(json.loads(line))
            
            self.myfixit_cache[category] = guides
            print(f"[OK] Loaded {len(guides)} guides from {filename}")
            return guides
            
        except Exception as e:
            print(f"[ERROR] Error loading {filename}: {e}")
            return []
    
    async def search_tutorials_hybrid(
        self,
        diagnosis: str,
        symptoms: List[str],
        keywords: List[str],
        category: str,
        brand: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        5-stage hybrid search pipeline:
        1. Category routing
        2. Dense retrieval (Weaviate vector search)
        3. Sparse retrieval (PostgreSQL keyword search)
        4. Hybrid scoring (β*vector + (1-β)*keyword)
        5. Feedback re-ranking
        """
        # Stage 1: Category routing
        print(f"\n[SEARCH] Stage 1: Category routing -> {category}")
        
        # Construct search query
        search_text = f"{diagnosis} {' '.join(symptoms)} {' '.join(keywords)}"
        if brand:
            search_text = f"{brand} {search_text}"
        
        print(f"[QUERY] Search query: {search_text[:100]}...")
        
        # Stage 2: Dense retrieval (Vector search)
        print("[SEARCH] Stage 2: Dense retrieval (Weaviate)")
        vector_results = await self._vector_search(search_text, category, brand, k=50)
        
        # Stage 3: Sparse retrieval (Keyword search)
        print("[SEARCH] Stage 3: Sparse retrieval (PostgreSQL)")
        keyword_results = await self._keyword_search(keywords, category, brand, limit=50)
        
        # Stage 4: Hybrid scoring
        print("[SEARCH] Stage 4: Hybrid scoring")
        hybrid_results = self._hybrid_scoring(vector_results, keyword_results)
        
        # Stage 5: Feedback re-ranking
        print("[SEARCH] Stage 5: Feedback re-ranking")
        final_results = await self._feedback_reranking(hybrid_results)
        
        # Limit results
        final_results = final_results[:limit]
        
        print(f"[OK] Matched {len(final_results)} tutorials")
        
        return final_results
    
    async def _vector_search(
        self,
        search_text: str,
        category: str,
        brand: Optional[str],
        k: int = 50
    ) -> List[Dict]:
        """Vector similarity search using Weaviate"""
        try:
            # Build where filter
            where_filter = None
            
            if brand:
                where_filter = {
                    "operator": "And",
                    "operands": [
                        {"path": ["brand"], "operator": "Equal", "valueText": brand}
                    ]
                }
            
            # Query Weaviate
            query_builder = self.weaviate_client.query.get(
                "Tutorial",
                ["tutorial_id", "brand", "model", "issue_type", "title", "keywords", "source", "difficulty"]
            ).with_near_text({
                "concepts": [search_text]
            }).with_limit(k)
            
            if where_filter:
                query_builder = query_builder.with_where(where_filter)
            
            results = query_builder.with_additional(["distance"]).do()
            
            if 'data' not in results or 'Get' not in results['data']:
                return []
            
            tutorials = results['data']['Get']['Tutorial']
            
            # Convert to standard format with scores
            vector_results = []
            for t in tutorials:
                distance = t.get('_additional', {}).get('distance', 1.0)
                score = 1.0 - distance  # Convert distance to similarity
                
                vector_results.append({
                    "tutorial_id": t.get("tutorial_id"),
                    "brand": t.get("brand"),
                    "model": t.get("model"),
                    "issue_type": t.get("issue_type"),
                    "title": t.get("title"),
                    "keywords": t.get("keywords", []),
                    "source": t.get("source"),
                    "difficulty": t.get("difficulty"),
                    "vector_score": max(0.0, score)
                })
            
            return vector_results
            
        except Exception as e:
            print(f"[ERROR] Vector search error: {e}")
            return []
    
    async def _keyword_search(
        self,
        keywords: List[str],
        category: str,
        brand: Optional[str],
        limit: int = 50
    ) -> List[Dict]:
        """Keyword-based search using PostgreSQL"""
        try:
            async with self.db_pool.acquire() as conn:
                # Build query
                query = """
                    SELECT 
                        id as tutorial_id,
                        brand,
                        model,
                        issue_type,
                        title,
                        keywords,
                        source,
                        difficulty
                    FROM tutorials
                    WHERE 1=1
                """
                params = []
                param_count = 1
                
                if brand:
                    query += f" AND brand = ${param_count}"
                    params.append(brand)
                    param_count += 1
                
                if keywords:
                    # Use GIN index for array overlap
                    query += f" AND keywords && ${param_count}"
                    params.append(keywords)
                    param_count += 1
                
                query += f" LIMIT {limit}"
                
                results = await conn.fetch(query, *params)
                
                # Calculate keyword scores
                keyword_results = []
                for r in results:
                    tutorial_keywords = set(r["keywords"])
                    search_keywords = set(keywords)
                    
                    # Jaccard similarity
                    intersection = len(tutorial_keywords & search_keywords)
                    union = len(tutorial_keywords | search_keywords)
                    jaccard = intersection / union if union > 0 else 0.0
                    
                    keyword_results.append({
                        "tutorial_id": r["tutorial_id"],
                        "brand": r["brand"],
                        "model": r["model"],
                        "issue_type": r["issue_type"],
                        "title": r["title"],
                        "keywords": r["keywords"],
                        "source": r["source"],
                        "difficulty": r["difficulty"],
                        "keyword_score": jaccard
                    })
                
                return keyword_results
                
        except Exception as e:
            print(f"[ERROR] Keyword search error: {e}")
            return []
    
    def _hybrid_scoring(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict]
    ) -> List[Dict]:
        """
        Combine vector and keyword scores
        score = β*score_vec + (1-β)*score_lex
        """
        # Create lookup for both result sets
        vector_lookup = {r["tutorial_id"]: r for r in vector_results}
        keyword_lookup = {r["tutorial_id"]: r for r in keyword_results}
        
        # Get all unique tutorial IDs
        all_ids = set(vector_lookup.keys()) | set(keyword_lookup.keys())
        
        hybrid_results = []
        for tid in all_ids:
            vec = vector_lookup.get(tid, {})
            kw = keyword_lookup.get(tid, {})
            
            # Get scores (default to 0 if not in one of the sets)
            vec_score = vec.get("vector_score", 0.0)
            kw_score = kw.get("keyword_score", 0.0)
            
            # Hybrid score
            hybrid_score = self.beta * vec_score + (1 - self.beta) * kw_score
            
            # Use data from whichever source has it
            result = vec if vec else kw
            result["vector_score"] = vec_score
            result["keyword_score"] = kw_score
            result["hybrid_score"] = hybrid_score
            
            # Ensure 'id' field exists for frontend compatibility
            if "tutorial_id" in result and "id" not in result:
                result["id"] = result["tutorial_id"]
            
            hybrid_results.append(result)
        
        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return hybrid_results
    
    async def _feedback_reranking(self, results: List[Dict]) -> List[Dict]:
        """
        Re-rank results based on user feedback
        score_final = score_hybrid * (1 + γ*feedback_score)
        """
        try:
            async with self.db_pool.acquire() as conn:
                for result in results:
                    tid = result["tutorial_id"]
                    
                    # Get feedback statistics
                    feedback = await conn.fetchrow("""
                        SELECT 
                            COUNT(*) as feedback_count,
                            AVG(CASE WHEN solved_problem THEN 1.0 ELSE 0.0 END) as success_rate,
                            AVG((clarity_rating + accuracy_rating) / 10.0) as avg_rating
                        FROM user_feedback
                        WHERE tutorial_id = $1
                    """, tid)
                    
                    if feedback and feedback["feedback_count"] > 0:
                        # Normalize feedback score (0 to 1)
                        success_rate = feedback["success_rate"] or 0.0
                        avg_rating = feedback["avg_rating"] or 0.5
                        feedback_score = (success_rate + avg_rating) / 2.0
                        
                        # Re-rank
                        original_score = result["hybrid_score"]
                        result["feedback_score"] = feedback_score
                        result["final_score"] = original_score * (1 + self.gamma * feedback_score)
                        result["feedback_count"] = feedback["feedback_count"]
                    else:
                        result["feedback_score"] = 0.5  # Neutral default
                        result["final_score"] = result["hybrid_score"]
                        result["feedback_count"] = 0
            
            # Re-sort by final score
            results.sort(key=lambda x: x["final_score"], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Feedback re-ranking error: {e}")
            # Return results with original scores
            for r in results:
                r["final_score"] = r["hybrid_score"]
            return results
    
    async def get_tutorial_details(self, tutorial_id: int) -> Optional[Dict]:
        """Get complete tutorial details including steps"""
        try:
            async with self.db_pool.acquire() as conn:
                tutorial = await conn.fetchrow("""
                    SELECT * FROM tutorials WHERE id = $1
                """, tutorial_id)
                
                if not tutorial:
                    return None
                
                # Get steps
                steps = await conn.fetch("""
                    SELECT step_number, instruction, image_url, warnings
                    FROM tutorial_steps
                    WHERE tutorial_id = $1
                    ORDER BY step_number
                """, tutorial_id)
                
                # Get tools
                tools = await conn.fetch("""
                    SELECT tool_name FROM tutorial_tools
                    WHERE tutorial_id = $1
                """, tutorial_id)
                
                # Get warnings
                warnings = await conn.fetch("""
                    SELECT warning_text FROM tutorial_warnings
                    WHERE tutorial_id = $1
                """, tutorial_id)
                
                return {
                    **dict(tutorial),
                    "steps": [dict(s) for s in steps],
                    "tools": [t["tool_name"] for t in tools],
                    "warnings": [w["warning_text"] for w in warnings]
                }
                
        except Exception as e:
            print(f"[ERROR] Error fetching tutorial details: {e}")
            return None
