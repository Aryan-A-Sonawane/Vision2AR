"""
MyFixit Dataset Ingestion Script
Loads 31,601 repair tutorials from JSONL files into PostgreSQL + Weaviate
"""
import asyncio
import asyncpg
import weaviate
import json
from pathlib import Path
from typing import List, Dict
import hashlib
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer

load_dotenv()

# Configuration
# Path relative to backend directory (not backend/scripts)
MYFIXIT_PATH = Path(__file__).parent.parent / "data" / "myfixit" / "jsons"
BATCH_SIZE = 100  # Process in batches to avoid memory issues

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_KEY = os.getenv("WEAVIATE_API_KEY")

# Category mapping for device types
CATEGORY_FILES = {
    "PC": "PC.json",
    "Mac": "Mac.json",
    "Phone": "Phone.json",
    "Tablet": "Tablet.json",
    "Computer Hardware": "Computer Hardware.json",
    "Camera": "Camera.json",
    "Game Console": "Game Console.json",
    "Household": "Household.json",
    "Vehicle": "Vehicle.json",
    "Skill": "Skills.json",
    "Media Player": "Media Player.json",
    "Electronics": "Electronics.json",
    "Appliance": "Appliance.json",
    "Tool": "Tools.json"
}

class MyFixitIngestion:
    """Ingest MyFixit dataset into PostgreSQL and Weaviate"""
    
    def __init__(self):
        self.db_pool = None
        self.weaviate_client = None
        self.text_encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("[OK] Text encoder loaded")
    
    async def connect_databases(self):
        """Connect to PostgreSQL and Weaviate"""
        # PostgreSQL
        self.db_pool = await asyncpg.create_pool(DB_URL, min_size=2, max_size=10)
        print("[OK] PostgreSQL connected")
        
        # Weaviate
        self.weaviate_client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_KEY)
        )
        print("[OK] Weaviate connected")
    
    async def close_databases(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
        print("[OK] Databases closed")
    
    def load_myfixit_category(self, category: str) -> List[Dict]:
        """Load MyFixit JSONL file for a category"""
        filename = CATEGORY_FILES.get(category)
        if not filename:
            print(f"[WARN] Unknown category: {category}")
            return []
        
        filepath = MYFIXIT_PATH / filename
        if not filepath.exists():
            print(f"[WARN] File not found: {filepath}")
            return []
        
        guides = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    guide = json.loads(line)
                    guides.append(guide)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON error at line {line_num}: {e}")
                    continue
        
        print(f"[OK] Loaded {len(guides)} guides from {filename}")
        return guides
    
    def parse_difficulty(self, guide: Dict) -> str:
        """Extract difficulty level from guide"""
        # MyFixit doesn't have difficulty in dataset, default to medium
        return "medium"
    
    def extract_brand_model(self, guide: Dict) -> tuple:
        """Extract brand and model from guide metadata"""
        # Use capital-first keys: Ancestors, Category
        ancestors = guide.get("Ancestors", [])
        if ancestors and len(ancestors) >= 2:
            # Second ancestor is usually the specific device model
            brand = ancestors[1] if len(ancestors) > 1 else ancestors[0]
            category = guide.get("Category", "general")
            return brand.lower(), category.lower()
        
        # Fallback to category
        category = guide.get("Category", "general")
        if category and category != "Root":
            parts = category.split()
            if len(parts) >= 2:
                return parts[0].lower(), " ".join(parts[1:]).lower()
            return category.lower(), "general"
        
        return "general", "general"
    
    def extract_issue_type(self, guide: Dict) -> str:
        """Extract issue type from guide title"""
        # Use capital-first Title key
        title = guide.get("Title", "").lower()
        
        # Map keywords to issue types
        if any(word in title for word in ["replace", "replacement", "install"]):
            return "replacement"
        elif any(word in title for word in ["repair", "fix", "broken"]):
            return "repair"
        elif any(word in title for word in ["clean", "cleaning"]):
            return "maintenance"
        elif any(word in title for word in ["upgrade", "install"]):
            return "upgrade"
        elif any(word in title for word in ["battery", "power", "charging"]):
            return "power"
        elif any(word in title for word in ["screen", "display"]):
            return "display"
        elif any(word in title for word in ["keyboard", "key"]):
            return "keyboard"
        elif any(word in title for word in ["fan", "cooling", "thermal"]):
            return "thermal"
        else:
            return "general"
    
    async def ingest_guide(self, guide: Dict, category: str) -> tuple:
        """
        Ingest a single guide into PostgreSQL and Weaviate
        Returns (tutorial_id, success)
        """
        try:
            # Extract metadata - use capital-first keys
            brand, model = self.extract_brand_model(guide)
            issue_type = self.extract_issue_type(guide)
            difficulty = self.parse_difficulty(guide)
            title = guide.get("Title", "Untitled")
            guideid = guide.get("Guidid", 0)
            
            # Extract tools - use capital-first Toolbox key
            tools = []
            toolbox = guide.get("Toolbox", [])
            for tool in toolbox:
                tool_name = tool.get("Name", "")  # Name, not text
                if tool_name:
                    tools.append(tool_name)
            
            # Extract keywords from title and category
            keywords = title.lower().split() + [category.lower(), brand, model, issue_type]
            keywords = list(set([k for k in keywords if len(k) > 2]))[:10]  # Top 10 unique
            
            # Insert tutorial into PostgreSQL
            async with self.db_pool.acquire() as conn:
                tutorial_id = await conn.fetchval("""
                    INSERT INTO tutorials 
                    (brand, model, issue_type, title, difficulty, keywords, source, myfixit_guideid, category)
                    VALUES ($1, $2, $3, $4, $5, $6, 'myfixit', $7, $8)
                    ON CONFLICT (myfixit_guideid) DO UPDATE
                    SET title = EXCLUDED.title, category = EXCLUDED.category
                    RETURNING id
                """, brand, model, issue_type, title, difficulty, keywords, guideid, category)
                
                # Insert steps - use capital-first Steps key
                steps = guide.get("Steps", [])
                for step_idx, step in enumerate(steps, 1):
                    # Steps have Order number, use Text_raw for instruction
                    step_order = step.get("Order", step_idx - 1)
                    
                    # Use Lines array for instruction text
                    lines = step.get("Lines", [])
                    instruction = "\n".join([line.get("Text", "") for line in lines])
                    
                    # Get first image from Images array
                    image_url = None
                    images = step.get("Images", [])
                    if images:
                        image_url = images[0]  # First image URL
                    
                    await conn.execute("""
                        INSERT INTO tutorial_steps
                        (tutorial_id, step_number, description, image_url)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (tutorial_id, step_number) DO UPDATE
                        SET description = EXCLUDED.description
                    """, tutorial_id, step_order + 1, instruction, image_url)  # Use Order + 1 for step_number
                
                # Insert tools
                for tool in tools:
                    await conn.execute("""
                        INSERT INTO tutorial_tools (tutorial_id, tool_name)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, tutorial_id, tool)
            
            # Insert into Weaviate for vector search
            # Create text for embedding
            embed_text = f"{brand} {model} {issue_type} {title} {' '.join(keywords)}"
            
            # Check length before inserting
            if len(embed_text) > 5000:
                embed_text = embed_text[:5000]
            
            try:
                self.weaviate_client.data_object.create(
                    data_object={
                        "tutorial_id": tutorial_id,
                        "brand": brand,
                        "model": model,
                        "issue_type": issue_type,
                        "title": title,
                        "keywords": keywords,
                        "source": "myfixit",
                        "difficulty": difficulty,
                        "category": category
                    },
                    class_name="Tutorial"
                )
            except Exception as weaviate_error:
                print(f"[WARN] Weaviate insert failed for {title}: {weaviate_error}")
                # Continue even if Weaviate fails
            
            return tutorial_id, True
            
        except Exception as e:
            print(f"[ERROR] Failed to ingest guide '{guide.get('title', 'unknown')}': {e}")
            return None, False
    
    async def ingest_category(self, category: str):
        """Ingest all guides for a category"""
        print(f"\n{'='*70}")
        print(f"INGESTING CATEGORY: {category}")
        print(f"{'='*70}")
        
        guides = self.load_myfixit_category(category)
        if not guides:
            return
        
        total = len(guides)
        success_count = 0
        failed_count = 0
        
        # Process in batches
        for batch_start in range(0, total, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total)
            batch = guides[batch_start:batch_end]
            
            print(f"[BATCH] Processing {batch_start+1}-{batch_end} of {total}...")
            
            for guide in batch:
                tutorial_id, success = await self.ingest_guide(guide, category)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            
            print(f"[PROGRESS] {success_count}/{total} succeeded, {failed_count} failed")
        
        print(f"\n[OK] Category '{category}' complete: {success_count} tutorials ingested")
    
    async def ingest_all(self):
        """Ingest all MyFixit categories"""
        print("\n" + "#"*70)
        print("# MyFixit Dataset Ingestion")
        print("# Total: 31,601 repair tutorials")
        print("#"*70 + "\n")
        
        await self.connect_databases()
        
        try:
            # Priority categories (most relevant for laptop repair)
            priority_categories = ["PC", "Mac", "Computer Hardware"]
            
            for category in priority_categories:
                await self.ingest_category(category)
            
            # Optional: Ingest remaining categories
            print("\n[INFO] Priority categories complete!")
            print("[INFO] To ingest remaining categories (Phone, Tablet, etc.),")
            print("[INFO] uncomment the loop below and re-run.")
            
            # Uncomment to ingest all categories:
            # for category in CATEGORY_FILES.keys():
            #     if category not in priority_categories:
            #         await self.ingest_category(category)
            
            # Summary
            async with self.db_pool.acquire() as conn:
                total_tutorials = await conn.fetchval("SELECT COUNT(*) FROM tutorials WHERE source='myfixit'")
                total_steps = await conn.fetchval("SELECT COUNT(*) FROM tutorial_steps")
                
            print(f"\n{'='*70}")
            print(f"INGESTION COMPLETE")
            print(f"{'='*70}")
            print(f"Total tutorials ingested: {total_tutorials}")
            print(f"Total steps: {total_steps}")
            print(f"Average steps per tutorial: {total_steps/total_tutorials if total_tutorials > 0 else 0:.1f}")
            
        finally:
            await self.close_databases()


async def main():
    """Run the ingestion pipeline"""
    ingestion = MyFixitIngestion()
    await ingestion.ingest_all()


if __name__ == "__main__":
    asyncio.run(main())
