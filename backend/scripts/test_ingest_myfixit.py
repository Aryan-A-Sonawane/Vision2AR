"""
Test MyFixit Ingestion - 10 Tutorials Only
Validates the ingestion pipeline before full run
"""
import asyncio
import asyncpg
import weaviate
import json
from pathlib import Path
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MYFIXIT_PATH = Path(__file__).parent.parent / "data" / "myfixit" / "jsons"
TEST_LIMIT = 10  # Only process 10 tutorials

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_KEY = os.getenv("WEAVIATE_API_KEY")

async def test_ingestion():
    """Test ingestion with 10 tutorials from PC.json"""
    print("\n" + "="*70)
    print("TEST INGESTION - 10 Tutorials from PC.json")
    print("="*70 + "\n")
    
    # Connect to databases
    db_pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=2)
    weaviate_client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_KEY)
    )
    print("[OK] Database connections established\n")
    
    # Load 10 guides from PC.json
    filepath = MYFIXIT_PATH / "PC.json"
    guides = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if len(guides) >= TEST_LIMIT:
                break
            line = line.strip()
            if not line:
                continue
            try:
                guide = json.loads(line)
                guides.append(guide)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON error at line {line_num}: {e}")
                continue
    
    print(f"[OK] Loaded {len(guides)} guides for testing\n")
    
    # Process each guide
    success_count = 0
    for idx, guide in enumerate(guides, 1):
        try:
            # Extract metadata
            title = guide.get("Title", "Untitled")
            guideid = guide.get("Guidid", 0)
            category = guide.get("Category", "N/A")
            
            # Get brand from ancestors
            ancestors = guide.get("Ancestors", [])
            brand = ancestors[1] if len(ancestors) > 1 else "general"
            model = category
            
            # Extract issue type from title
            title_lower = title.lower()
            if "keyboard" in title_lower:
                issue_type = "keyboard"
            elif "display" in title_lower or "screen" in title_lower:
                issue_type = "display"
            elif "battery" in title_lower:
                issue_type = "power"
            else:
                issue_type = "general"
            
            # Extract tools
            toolbox = guide.get("Toolbox", [])
            tools = [t.get("Name", "") for t in toolbox if t.get("Name")]
            
            # Keywords from title
            keywords = [word for word in title.lower().split() if len(word) > 3][:10]
            
            print(f"[{idx}/{TEST_LIMIT}] Processing: {title[:60]}...")
            print(f"    Guidid: {guideid} | Brand: {brand} | Model: {model[:30]}")
            print(f"    Issue: {issue_type} | Tools: {len(tools)} | Steps: {len(guide.get('Steps', []))}")
            
            # Insert into PostgreSQL
            async with db_pool.acquire() as conn:
                tutorial_id = await conn.fetchval("""
                    INSERT INTO tutorials 
                    (brand, model, issue_type, title, difficulty, keywords, source, myfixit_guideid)
                    VALUES ($1, $2, $3, $4, 'medium', $5, 'myfixit', $6)
                    ON CONFLICT (myfixit_guideid) DO UPDATE
                    SET title = EXCLUDED.title
                    RETURNING id
                """, brand.lower(), model.lower(), issue_type, title, keywords, guideid)
                
                # Insert steps
                steps = guide.get("Steps", [])
                for step in steps:
                    order = step.get("Order", 0)
                    lines = step.get("Lines", [])
                    instruction = "\n".join([line.get("Text", "") for line in lines])
                    images = step.get("Images", [])
                    image_url = images[0] if images else None
                    
                    await conn.execute("""
                        INSERT INTO tutorial_steps
                        (tutorial_id, step_number, description, image_url)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (tutorial_id, step_number) DO UPDATE
                        SET description = EXCLUDED.description
                    """, tutorial_id, order + 1, instruction, image_url)
                
                # Insert tools
                for tool in tools:
                    await conn.execute("""
                        INSERT INTO tutorial_tools (tutorial_id, tool_name)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, tutorial_id, tool)
            
            # Insert into Weaviate
            embed_text = f"{brand} {model} {issue_type} {title}"
            if len(embed_text) > 5000:
                embed_text = embed_text[:5000]
            
            try:
                weaviate_client.data_object.create(
                    data_object={
                        "tutorial_id": tutorial_id,
                        "brand": brand.lower(),
                        "model": model.lower(),
                        "issue_type": issue_type,
                        "title": title,
                        "keywords": keywords,
                        "source": "myfixit",
                        "difficulty": "medium"
                    },
                    class_name="Tutorial"
                )
                print(f"    [OK] Inserted tutorial_id={tutorial_id} into PostgreSQL + Weaviate")
            except Exception as weaviate_error:
                print(f"    [WARN] Weaviate insert failed: {weaviate_error}")
                print(f"    [OK] Inserted tutorial_id={tutorial_id} into PostgreSQL only")
            
            success_count += 1
            print()
            
        except Exception as e:
            print(f"    [ERROR] Failed to process guide: {e}\n")
            continue
    
    # Summary
    async with db_pool.acquire() as conn:
        total_tutorials = await conn.fetchval("SELECT COUNT(*) FROM tutorials WHERE source='myfixit'")
        total_steps = await conn.fetchval("""
            SELECT COUNT(*) FROM tutorial_steps ts
            JOIN tutorials t ON ts.tutorial_id = t.id
            WHERE t.source='myfixit'
        """)
    
    print("="*70)
    print("TEST INGESTION COMPLETE")
    print("="*70)
    print(f"Successfully ingested: {success_count}/{TEST_LIMIT} tutorials")
    print(f"Total MyFixit tutorials in DB: {total_tutorials}")
    print(f"Total MyFixit steps in DB: {total_steps}")
    print(f"Average steps per tutorial: {total_steps/total_tutorials if total_tutorials > 0 else 0:.1f}")
    print("\n[NEXT STEP] If this looks good, run: python scripts/ingest_myfixit.py")
    print("="*70 + "\n")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(test_ingestion())
