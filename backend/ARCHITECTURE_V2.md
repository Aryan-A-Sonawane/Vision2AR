# New Architecture Implementation Plan

## Overview
Clean, production-ready architecture with proper separation of concerns.

## Components

### 1. Vector DB (Weaviate)
- Store tutorial embeddings with keywords
- Fast semantic search for symptom matching
- Schema: Tutorial (id, brand, issue, keywords, embedding)

### 2. PostgreSQL Database
```sql
-- Main tutorial table
tutorials (
  id SERIAL PRIMARY KEY,
  brand VARCHAR(50),
  issue_type VARCHAR(100),
  title TEXT,
  keywords TEXT[],
  source VARCHAR(20), -- 'oem', 'ifixit'
  source_id VARCHAR(100),
  difficulty VARCHAR(20),
  estimated_time INT,
  created_at TIMESTAMP
)

-- Step-by-step instructions
tutorial_steps (
  id SERIAL PRIMARY KEY,
  tutorial_id INT REFERENCES tutorials(id),
  step_number INT,
  description TEXT,
  image_url TEXT,
  video_timestamp TEXT,
  created_at TIMESTAMP
)

-- Tools and warnings
tutorial_tools (
  id SERIAL PRIMARY KEY,
  tutorial_id INT REFERENCES tutorials(id),
  tool_name VARCHAR(100)
)

tutorial_warnings (
  id SERIAL PRIMARY KEY,
  tutorial_id INT REFERENCES tutorials(id),
  warning_text TEXT,
  severity VARCHAR(20)
)
```

### 3. Processing Pipeline

```
User Input (Text + Optional Image)
         ↓
┌────────────────────────────────────┐
│ 1. Text Analysis                   │
│    - Tokenize query                │
│    - Extract keywords              │
│    - Generate embedding            │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│ 2. Image Analysis (if provided)    │
│    - BLIP model → text description │
│    - Extract visual symptoms       │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│ 3. Combined Analysis               │
│    - Merge text + image keywords   │
│    - Query Weaviate vector DB      │
│    - Get top 5 similar tutorials   │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│ 4. Fetch Tutorial Details          │
│    - Query PostgreSQL              │
│    - Get steps with images         │
│    - Get tools, warnings           │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│ 5. Return to User                  │
│    - List of tutorials             │
│    - Step-by-step with images      │
│    - Chat for clarifications       │
└────────────────────────────────────┘
```

### 4. Data Seeding Strategy

**Phase 1: iFixit (30 problems × 3 brands = 90 tutorials)**
- Dell: Common issues (black screen, no boot, overheating, etc.)
- Lenovo: ThinkPad specific + common
- HP: Pavilion/Elitebook specific + common

**Phase 2: OEM Manuals (from existing knowledge_base_v2.json)**
- Already have 39 procedures
- Tag with keywords
- Store in PostgreSQL

### 5. API Endpoints

```python
POST /api/analyze
{
  "text": "laptop screen is black",
  "image": "base64_image_data",  # optional
  "brand": "dell"  # optional filter
}
→ Returns: List of matching tutorials

GET /api/tutorial/{id}
→ Returns: Full tutorial with steps, images, tools

POST /api/chat
{
  "session_id": "...",
  "message": "yes, I tried that",
  "tutorial_id": 123
}
→ Returns: Next clarification or confirmation
```

## Implementation Order

1. ✅ Setup PostgreSQL schema
2. ✅ Install Weaviate (local Docker or cloud)
3. ✅ Create text analysis module (tokenization, keywords)
4. ✅ Integrate BLIP for image analysis
5. ✅ Build data seeding pipeline (iFixit API)
6. ✅ Migrate existing OEM data to new schema
7. ✅ Build tutorial matching engine
8. ✅ Create chat interface (backend)
9. ✅ Update frontend for chat + step display
10. ✅ Test end-to-end

## File Structure

```
backend/
  database/
    schema.sql              # PostgreSQL schema
    seed_ifixit.py         # Seed from iFixit API
    seed_oem.py            # Migrate knowledge_base_v2.json
  analysis/
    text_analyzer.py       # Tokenization, keyword extraction
    image_analyzer.py      # BLIP model integration
    tutorial_matcher.py    # Weaviate + PostgreSQL query
  api/
    endpoints.py           # FastAPI routes
  models/
    schemas.py             # Pydantic models
```

## Next Steps

1. Update requirements.txt with BLIP
2. Create PostgreSQL schema
3. Setup Weaviate connection
4. Build text analyzer
5. Integrate BLIP
6. Seed database
7. Build matching engine
8. Update API endpoints
9. Create chat interface
10. Update frontend
