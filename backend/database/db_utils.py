"""
PostgreSQL database utilities and connection management
"""
import os
import asyncpg
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class DatabaseConnection:
    """Singleton database connection pool"""
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get or create connection pool"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
        return cls._pool
    
    @classmethod
    async def close_pool(cls):
        """Close connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

# Tutorial CRUD operations
async def create_tutorial(
    brand: str,
    model: str,
    issue_type: str,
    title: str,
    keywords: List[str],
    source: str = "ifixit",
    difficulty: str = "medium",
    estimated_time_minutes: int = 30
) -> int:
    """Create a new tutorial and return its ID"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    INSERT INTO tutorials (brand, model, issue_type, title, keywords, source, difficulty, estimated_time_minutes)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    RETURNING id
    """
    
    async with pool.acquire() as conn:
        tutorial_id = await conn.fetchval(
            query, brand, model, issue_type, title, keywords, source, difficulty, estimated_time_minutes
        )
    
    return tutorial_id

async def add_tutorial_step(
    tutorial_id: int,
    step_number: int,
    description: str,
    image_url: Optional[str] = None,
    video_timestamp: Optional[str] = None
) -> int:
    """Add a step to a tutorial"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    INSERT INTO tutorial_steps (tutorial_id, step_number, description, image_url, video_timestamp)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id
    """
    
    async with pool.acquire() as conn:
        step_id = await conn.fetchval(
            query, tutorial_id, step_number, description, image_url, video_timestamp
        )
    
    return step_id

async def add_tutorial_tool(
    tutorial_id: int,
    tool_name: str,
    tool_type: str = "manual",
    is_optional: bool = False
) -> int:
    """Add a required tool to a tutorial"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    INSERT INTO tutorial_tools (tutorial_id, tool_name, tool_type, is_optional)
    VALUES ($1, $2, $3, $4)
    RETURNING id
    """
    
    async with pool.acquire() as conn:
        tool_id = await conn.fetchval(query, tutorial_id, tool_name, tool_type, is_optional)
    
    return tool_id

async def add_tutorial_warning(
    tutorial_id: int,
    warning_text: str,
    severity: str = "warning",
    step_number: Optional[int] = None
) -> int:
    """Add a warning to a tutorial"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    INSERT INTO tutorial_warnings (tutorial_id, warning_text, severity, step_number)
    VALUES ($1, $2, $3, $4)
    RETURNING id
    """
    
    async with pool.acquire() as conn:
        warning_id = await conn.fetchval(query, tutorial_id, warning_text, severity, step_number)
    
    return warning_id

async def get_tutorial(tutorial_id: int) -> Optional[Dict[str, Any]]:
    """Get full tutorial with steps, tools, and warnings"""
    pool = await DatabaseConnection.get_pool()
    
    async with pool.acquire() as conn:
        # Get tutorial details
        tutorial = await conn.fetchrow(
            "SELECT * FROM tutorials WHERE id = $1",
            tutorial_id
        )
        
        if not tutorial:
            return None
        
        # Get steps
        steps = await conn.fetch(
            "SELECT * FROM tutorial_steps WHERE tutorial_id = $1 ORDER BY step_number",
            tutorial_id
        )
        
        # Get tools
        tools = await conn.fetch(
            "SELECT * FROM tutorial_tools WHERE tutorial_id = $1",
            tutorial_id
        )
        
        # Get warnings
        warnings = await conn.fetch(
            "SELECT * FROM tutorial_warnings WHERE tutorial_id = $1 ORDER BY step_number NULLS LAST",
            tutorial_id
        )
        
        return {
            "id": tutorial["id"],
            "brand": tutorial["brand"],
            "model": tutorial["model"],
            "issue_type": tutorial["issue_type"],
            "title": tutorial["title"],
            "keywords": tutorial["keywords"],
            "source": tutorial["source"],
            "difficulty": tutorial["difficulty"],
            "estimated_time_minutes": tutorial["estimated_time_minutes"],
            "created_at": tutorial["created_at"],
            "steps": [dict(step) for step in steps],
            "tools": [dict(tool) for tool in tools],
            "warnings": [dict(warning) for warning in warnings]
        }

async def search_tutorials_by_keywords(
    keywords: List[str],
    brand: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search tutorials by keywords using GIN index"""
    pool = await DatabaseConnection.get_pool()
    
    # Build query
    if brand:
        query = """
        SELECT id, brand, model, issue_type, title, keywords, source, difficulty, estimated_time_minutes
        FROM tutorials
        WHERE keywords && $1 AND brand = $2
        ORDER BY array_length(
            (SELECT array_agg(k) FROM unnest(keywords) k WHERE k = ANY($1)), 
            1
        ) DESC NULLS LAST
        LIMIT $3
        """
        params = (keywords, brand, limit)
    else:
        query = """
        SELECT id, brand, model, issue_type, title, keywords, source, difficulty, estimated_time_minutes
        FROM tutorials
        WHERE keywords && $1
        ORDER BY array_length(
            (SELECT array_agg(k) FROM unnest(keywords) k WHERE k = ANY($1)), 
            1
        ) DESC NULLS LAST
        LIMIT $2
        """
        params = (keywords, limit)
    
    async with pool.acquire() as conn:
        results = await conn.fetch(query, *params)
    
    return [dict(row) for row in results]

async def get_tutorials_by_brand(brand: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get all tutorials for a specific brand"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    SELECT id, brand, model, issue_type, title, keywords, source, difficulty, estimated_time_minutes
    FROM tutorials
    WHERE brand = $1
    ORDER BY created_at DESC
    LIMIT $2
    """
    
    async with pool.acquire() as conn:
        results = await conn.fetch(query, brand, limit)
    
    return [dict(row) for row in results]

async def create_chat_session(
    user_query: str,
    image_analysis: Optional[str] = None,
    selected_tutorial_id: Optional[int] = None
) -> str:
    """Create a new chat session"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    INSERT INTO chat_sessions (user_query, image_analysis, selected_tutorial_id)
    VALUES ($1, $2, $3)
    RETURNING session_id
    """
    
    async with pool.acquire() as conn:
        session_id = await conn.fetchval(query, user_query, image_analysis, selected_tutorial_id)
    
    return str(session_id)

async def add_chat_message(
    session_id: str,
    role: str,
    message: str
) -> int:
    """Add a message to chat session"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    INSERT INTO chat_messages (session_id, role, message)
    VALUES ($1, $2, $3)
    RETURNING id
    """
    
    async with pool.acquire() as conn:
        message_id = await conn.fetchval(query, session_id, role, message)
    
    return message_id

async def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """Get chat history for a session"""
    pool = await DatabaseConnection.get_pool()
    
    query = """
    SELECT role, message, timestamp
    FROM chat_messages
    WHERE session_id = $1
    ORDER BY timestamp ASC
    """
    
    async with pool.acquire() as conn:
        results = await conn.fetch(query, session_id)
    
    return [dict(row) for row in results]

# Statistics
async def get_stats() -> Dict[str, int]:
    """Get database statistics"""
    pool = await DatabaseConnection.get_pool()
    
    async with pool.acquire() as conn:
        total_tutorials = await conn.fetchval("SELECT COUNT(*) FROM tutorials")
        total_steps = await conn.fetchval("SELECT COUNT(*) FROM tutorial_steps")
        total_tools = await conn.fetchval("SELECT COUNT(DISTINCT tool_name) FROM tutorial_tools")
        total_sessions = await conn.fetchval("SELECT COUNT(*) FROM chat_sessions")
        
        # Count by brand
        by_brand = await conn.fetch("""
            SELECT brand, COUNT(*) as count
            FROM tutorials
            GROUP BY brand
            ORDER BY count DESC
        """)
        
        # Count by source
        by_source = await conn.fetch("""
            SELECT source, COUNT(*) as count
            FROM tutorials
            GROUP BY source
        """)
    
    return {
        "total_tutorials": total_tutorials,
        "total_steps": total_steps,
        "total_tools": total_tools,
        "total_sessions": total_sessions,
        "by_brand": [dict(row) for row in by_brand],
        "by_source": [dict(row) for row in by_source]
    }
