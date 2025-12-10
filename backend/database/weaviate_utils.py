"""
Weaviate utilities for vector search
"""
import os
import weaviate
from typing import List, Dict, Any, Optional
import numpy as np
from dotenv import load_dotenv

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

class WeaviateConnection:
    """Singleton Weaviate connection"""
    _client: Optional[weaviate.WeaviateClient] = None
    
    @classmethod
    def get_client(cls) -> weaviate.WeaviateClient:
        """Get or create Weaviate client"""
        if cls._client is None:
            cls._client = weaviate.connect_to_wcs(
                cluster_url=WEAVIATE_URL,
                auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
            )
        return cls._client
    
    @classmethod
    def close_client(cls):
        """Close Weaviate client"""
        if cls._client:
            cls._client.close()
            cls._client = None

def add_tutorial_to_weaviate(
    tutorial_id: int,
    brand: str,
    model: str,
    issue_type: str,
    title: str,
    keywords: List[str],
    source: str,
    difficulty: str,
    embedding: np.ndarray
) -> str:
    """Add tutorial to Weaviate with embedding"""
    client = WeaviateConnection.get_client()
    
    try:
        collection = client.collections.get("Tutorial")
        
        # Convert numpy array to list
        vector = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        
        # Add object with vector
        uuid = collection.data.insert(
            properties={
                "tutorial_id": tutorial_id,
                "brand": brand,
                "model": model,
                "issue_type": issue_type,
                "title": title,
                "keywords": keywords,
                "source": source,
                "difficulty": difficulty
            },
            vector=vector
        )
        
        return str(uuid)
        
    except Exception as e:
        print(f"Error adding tutorial to Weaviate: {e}")
        raise

def search_similar_tutorials(
    query_embedding: np.ndarray,
    brand: Optional[str] = None,
    limit: int = 10,
    distance_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Search for similar tutorials using vector similarity"""
    client = WeaviateConnection.get_client()
    
    try:
        collection = client.collections.get("Tutorial")
        
        # Convert numpy array to list
        vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        
        # Build query
        query = collection.query.near_vector(
            near_vector=vector,
            limit=limit,
            return_metadata=["distance"]
        )
        
        # Add brand filter if provided
        if brand:
            query = query.where_filter({
                "path": ["brand"],
                "operator": "Equal",
                "valueText": brand
            })
        
        # Execute query
        results = query.objects
        
        # Format results
        formatted_results = []
        for item in results:
            if item.metadata.distance <= distance_threshold:
                formatted_results.append({
                    "tutorial_id": item.properties["tutorial_id"],
                    "brand": item.properties["brand"],
                    "model": item.properties["model"],
                    "issue_type": item.properties["issue_type"],
                    "title": item.properties["title"],
                    "keywords": item.properties["keywords"],
                    "source": item.properties["source"],
                    "difficulty": item.properties["difficulty"],
                    "distance": item.metadata.distance,
                    "similarity": 1 - item.metadata.distance  # Convert distance to similarity score
                })
        
        return formatted_results
        
    except Exception as e:
        print(f"Error searching Weaviate: {e}")
        raise

def search_by_keywords_and_vector(
    query_embedding: np.ndarray,
    keywords: List[str],
    brand: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Hybrid search using both keywords and vector similarity"""
    client = WeaviateConnection.get_client()
    
    try:
        collection = client.collections.get("Tutorial")
        
        # Convert numpy array to list
        vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        
        # Start with vector search
        query = collection.query.near_vector(
            near_vector=vector,
            limit=limit * 2,  # Get more results for filtering
            return_metadata=["distance"]
        )
        
        # Execute query
        results = query.objects
        
        # Score results based on keyword matches
        scored_results = []
        for item in results:
            tutorial_keywords = item.properties.get("keywords", [])
            
            # Count keyword matches
            keyword_matches = sum(1 for kw in keywords if kw in tutorial_keywords)
            keyword_score = keyword_matches / len(keywords) if keywords else 0
            
            # Calculate combined score (60% vector, 40% keyword)
            vector_score = 1 - item.metadata.distance
            combined_score = 0.6 * vector_score + 0.4 * keyword_score
            
            # Filter by brand if provided
            if brand and item.properties["brand"] != brand:
                continue
            
            scored_results.append({
                "tutorial_id": item.properties["tutorial_id"],
                "brand": item.properties["brand"],
                "model": item.properties["model"],
                "issue_type": item.properties["issue_type"],
                "title": item.properties["title"],
                "keywords": item.properties["keywords"],
                "source": item.properties["source"],
                "difficulty": item.properties["difficulty"],
                "distance": item.metadata.distance,
                "vector_score": vector_score,
                "keyword_score": keyword_score,
                "combined_score": combined_score,
                "keyword_matches": keyword_matches
            })
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Return top results
        return scored_results[:limit]
        
    except Exception as e:
        print(f"Error in hybrid search: {e}")
        raise

def delete_tutorial_from_weaviate(tutorial_id: int) -> bool:
    """Delete tutorial from Weaviate by tutorial_id"""
    client = WeaviateConnection.get_client()
    
    try:
        collection = client.collections.get("Tutorial")
        
        # Find objects with matching tutorial_id
        results = collection.query.fetch_objects(
            filters={
                "path": ["tutorial_id"],
                "operator": "Equal",
                "valueInt": tutorial_id
            }
        )
        
        # Delete each matching object
        deleted_count = 0
        for item in results.objects:
            collection.data.delete_by_id(item.uuid)
            deleted_count += 1
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"Error deleting from Weaviate: {e}")
        return False

def get_weaviate_stats() -> Dict[str, Any]:
    """Get Weaviate statistics"""
    client = WeaviateConnection.get_client()
    
    try:
        collection = client.collections.get("Tutorial")
        
        # Get total count
        response = collection.aggregate.over_all(total_count=True)
        total_count = response.total_count
        
        return {
            "total_tutorials": total_count,
            "status": "connected"
        }
        
    except Exception as e:
        return {
            "total_tutorials": 0,
            "status": f"error: {e}"
        }

def test_weaviate_connection() -> bool:
    """Test Weaviate connection"""
    try:
        client = WeaviateConnection.get_client()
        return client.is_ready()
    except Exception as e:
        print(f"Weaviate connection test failed: {e}")
        return False
