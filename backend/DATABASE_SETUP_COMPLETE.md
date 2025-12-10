# Database Setup Complete ✓

## Summary

Successfully set up **PostgreSQL** and **Weaviate** cloud instances for the AR Laptop Troubleshooter system.

---

## PostgreSQL Setup

**Database:** `ar_laptop_repair`  
**Host:** localhost:5432  
**Status:** ✓ Connected  

### Created Tables (9)

1. **tutorials** - Main tutorial repository
   - Fields: id, brand, model, issue_type, title, keywords[], source, difficulty, estimated_time_minutes
   - Indexes: GIN on keywords[], brand, issue_type

2. **tutorial_steps** - Step-by-step instructions
   - Fields: id, tutorial_id, step_number, description, image_url, video_timestamp
   - Index: UNIQUE(tutorial_id, step_number)

3. **tutorial_tools** - Required tools
   - Fields: id, tutorial_id, tool_name, tool_type, is_optional

4. **tutorial_warnings** - Safety warnings
   - Fields: id, tutorial_id, warning_text, severity, step_number

5. **chat_sessions** - User interaction sessions
   - Fields: session_id (UUID), user_query, image_analysis, selected_tutorial_id

6. **chat_messages** - Chat history
   - Fields: id, session_id, role, message, timestamp

7-9. **Legacy tables** (device_models, diagnosis_history, repair_procedures)

### Database Utilities

Created `database/db_utils.py` with functions:
- `create_tutorial()` - Add new tutorial
- `add_tutorial_step()` - Add step with image_url
- `add_tutorial_tool()` - Add required tool
- `add_tutorial_warning()` - Add safety warning
- `get_tutorial()` - Get full tutorial with steps/tools/warnings
- `search_tutorials_by_keywords()` - GIN array search
- `create_chat_session()` - Start user session
- `add_chat_message()` - Track conversation
- `get_stats()` - Database statistics

---

## Weaviate Cloud Setup

**URL:** https://4bih5mbfsjw1gbtt9o6nw.c0.asia-southeast1.gcp.weaviate.cloud  
**Version:** 1.34.2  
**Status:** ✓ Connected  

### Schema

**Class:** `Tutorial`  
**Vectorizer:** None (manual embeddings from sentence-transformers)  

**Properties:**
- tutorial_id (INT) - PostgreSQL foreign key
- brand (TEXT) - Laptop brand
- model (TEXT) - Laptop model
- issue_type (TEXT) - Problem category
- title (TEXT) - Tutorial title
- keywords (TEXT[]) - Extracted keywords
- source (TEXT) - 'oem' or 'ifixit'
- difficulty (TEXT) - 'easy', 'medium', 'hard'

### Weaviate Utilities

Created `database/weaviate_utils.py` with functions:
- `add_tutorial_to_weaviate()` - Store tutorial with 384-dim embedding
- `search_similar_tutorials()` - Vector similarity search
- `search_by_keywords_and_vector()` - Hybrid search (60% vector + 40% keyword)
- `delete_tutorial_from_weaviate()` - Remove by tutorial_id
- `get_weaviate_stats()` - Vector DB statistics

---

## Current Data Status

| Database | Tutorials | Steps | Tools | Sessions |
|----------|-----------|-------|-------|----------|
| PostgreSQL | 0 | 0 | 0 | 0 |
| Weaviate | 0 | - | - | - |

**Ready for data seeding!**

---

## Next Steps

### 1. Seed iFixit Data (90 tutorials)
```bash
python backend/database/seed_ifixit.py
```
- Fetch 30 problems × 3 brands (Dell, Lenovo, HP)
- Extract keywords with TextAnalyzer
- Store in PostgreSQL + Weaviate

### 2. Migrate OEM Manuals (39 procedures)
```bash
python backend/database/seed_oem.py
```
- Read knowledge_base_v2.json
- Extract keywords with TextAnalyzer
- Store with source='oem'

### 3. Build Tutorial Matcher
- Combine text + image analysis
- Query Weaviate for similar tutorials
- Fetch full details from PostgreSQL
- Return step-by-step with images

---

## Verification

Run verification script to check connections:
```bash
python backend/verify_setup.py
```

**Status:** ✓ All systems operational

---

## Files Created

1. `backend/database/schema_v2.sql` - PostgreSQL schema (94 lines)
2. `backend/database/setup_postgres.py` - Database creation script
3. `backend/database/setup_weaviate.py` - Weaviate schema setup
4. `backend/database/db_utils.py` - PostgreSQL utilities (330 lines)
5. `backend/database/weaviate_utils.py` - Weaviate utilities (260 lines)
6. `backend/verify_setup.py` - Connection verification

---

## Architecture Flow

```
User Query (text + image)
    ↓
TextAnalyzer → keywords + embedding (384-dim)
ImageAnalyzer (BLIP) → description + visual symptoms
    ↓
Combined keywords + embedding
    ↓
Weaviate → Hybrid search (60% vector + 40% keyword)
    ↓
Get tutorial_ids with similarity scores
    ↓
PostgreSQL → Fetch full tutorials with steps/images/tools/warnings
    ↓
Return to user (step-by-step display)
```

---

## Configuration (.env)

```ini
# PostgreSQL
DATABASE_URL=postgresql://postgres:****@localhost:5432/ar_laptop_repair

# Weaviate Cloud
WEAVIATE_URL=https://4bih5mbfsjw1gbtt9o6nw.c0.asia-southeast1.gcp.weaviate.cloud
WEAVIATE_API_KEY=****

# ML Models
TRANSFORMERS_CACHE=E:/z.code/arvr/.cache/huggingface
HF_HOME=E:/z.code/arvr/.cache/huggingface
```

---

## Ready to Proceed!

✓ PostgreSQL database created  
✓ Weaviate cloud connected  
✓ Database utilities implemented  
✓ Vector search utilities implemented  
✓ Connections verified  

**Next:** Data seeding (iFixit + OEM) to populate the system.
