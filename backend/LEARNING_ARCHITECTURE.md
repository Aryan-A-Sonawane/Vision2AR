# Self-Learning Diagnostic System Architecture

## System Overview

**Goal**: Build an adaptive laptop troubleshooting system that learns from every interaction, never limited to predefined rules.

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER INPUT                                                 │
│  • Text: "lenovo laptop blue screen"                       │
│  • Image: Photo of BSOD (optional)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  INPUT PROCESSOR (Multi-Modal Analysis)                     │
│                                                             │
│  Text Analysis:                                             │
│    → Keywords: ['blue', 'screen', 'error']                 │
│    → Symptoms: ['blue_screen', 'display_issue']            │
│    → Brand extraction: "lenovo" (confidence: 0.95)         │
│                                                             │
│  Image Analysis (BLIP-2 with text conditioning):            │
│    → Prompt: "What is shown in this photo of a lenovo      │
│       laptop blue screen?"                                  │
│    → Caption: "Blue screen error with code 0x0000007B"     │
│    → Visual symptoms: ['error_code_0x0000007B']            │
│                                                             │
│  Category Routing:                                          │
│    → Device: PC (not Mac)                                   │
│    → Target dataset: PC.json from MyFixit                   │
│                                                             │
│  LOG: 🔍 INPUT_ANALYSIS_COMPLETE                            │
│    brand: lenovo (0.95), category: PC                      │
│    symptoms: ['blue_screen'], visual: ['error_code_...']   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  BELIEF ENGINE (Hybrid: Base Rules + Learned Patterns)      │
│                                                             │
│  Step 1: Load base symptom mappings                         │
│    symptom_mappings.json:                                   │
│      'blue_screen' → {'memory_issue': 0.4,                 │
│                       'driver_issue': 0.3,                 │
│                       'thermal_issue': 0.2}                │
│                                                             │
│  Step 2: Query learned patterns                             │
│    SELECT * FROM learned_patterns                           │
│    WHERE category='PC' AND 'blue_screen' = ANY(symptoms)   │
│                                                             │
│    Found: ['blue_screen', 'error_code_0x0000007B']         │
│            → 'storage_driver_issue': 0.85                  │
│            (learned from 12 successful resolutions)         │
│                                                             │
│  Step 3: Merge beliefs                                      │
│    Combined: {                                              │
│      'storage_driver_issue': 0.85  ← HIGH (learned)        │
│      'memory_issue': 0.40           ← from base            │
│      'driver_issue': 0.30           ← from base            │
│    }                                                        │
│                                                             │
│  LOG: 📊 BELIEF_VECTOR_COMPUTED                             │
│    storage_driver_issue: 0.85, memory_issue: 0.40          │
│    Max confidence: 0.85 → SKIP QUESTIONS!                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  QUESTION ENGINE (Context-Aware + Skip Logic)               │
│                                                             │
│  IF max_confidence >= 0.7:                                  │
│    → SKIP to tutorial matching                              │
│                                                             │
│  ELSE:                                                      │
│    Load questions from:                                     │
│      1. questions.json (base questions)                     │
│      2. learned_questions table (community-generated)       │
│                                                             │
│    For each question:                                       │
│      - Check should_ask_question():                         │
│          ✗ Skip if brand_confidence > 0.8 (already known)  │
│          ✗ Skip if cause probability < 0.1 (irrelevant)    │
│          ✗ Skip if visual symptom answers it               │
│          ✓ Ask if high information gain                    │
│                                                             │
│    Example skip:                                            │
│      Q: "What brand is your laptop?"                        │
│      → SKIPPED (brand: lenovo, confidence: 0.95)           │
│                                                             │
│    LOG: ⏭️  SKIPPING QUESTION                               │
│      reason: Brand already detected from input             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  TUTORIAL MATCHER (MyFixit Dataset + Hybrid Search)         │
│                                                             │
│  Step 1: Route to correct category                          │
│    Category: PC → Load PC.json (6,677 manuals)             │
│    Filter: brand='lenovo', cause='storage_driver_issue'    │
│                                                             │
│  Step 2: Vector search (Weaviate)                           │
│    Query embedding: encode("storage driver blue screen")   │
│    Results: [(guide_89254, score: 0.92),                   │
│              (guide_12345, score: 0.87), ...]              │
│                                                             │
│  Step 3: Keyword search (PostgreSQL)                        │
│    SELECT * FROM tutorials WHERE                            │
│      'storage' = ANY(keywords) AND brand='lenovo'          │
│                                                             │
│  Step 4: Hybrid scoring                                     │
│    final_score = (vector_score * 0.6) +                    │
│                  (keyword_score * 0.4)                     │
│                                                             │
│  Step 5: Re-rank by user feedback history                   │
│    SELECT AVG(solved_problem) FROM user_feedback           │
│    WHERE tutorial_id = X                                    │
│    → Boost tutorials with >80% success rate                │
│                                                             │
│  LOG: 📚 TUTORIALS_FOUND                                    │
│    count: 5, top: "Lenovo ThinkPad SSD Driver Fix"        │
│    score: 0.94, success_rate: 87%                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  USER SELECTS TUTORIAL & PROVIDES FEEDBACK                  │
│                                                             │
│  Tutorial displayed:                                        │
│    - Step-by-step instructions with images                 │
│    - Tools required                                         │
│    - Estimated time                                         │
│                                                             │
│  After completion:                                          │
│    → Did this solve your problem? ✓ Yes / ✗ No            │
│    → Rate clarity: ⭐⭐⭐⭐⭐                                  │
│    → Time spent: 25 minutes                                 │
│                                                             │
│  Store in: user_feedback table                              │
│    session_id, tutorial_id, solved_problem=True,           │
│    clarity_rating=5, time_spent=25                         │
│                                                             │
│  LOG: ⭐ FEEDBACK_RECEIVED                                  │
│    solved: true, rating: 5/5                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEARNING ENGINE (Pattern Discovery - Nightly Batch)        │
│                                                             │
│  Runs daily at 2 AM:                                        │
│                                                             │
│  Task 1: Discover new patterns                              │
│    Query: Sessions with problem_resolved=TRUE              │
│    Analyze: (symptoms → diagnosis) combinations            │
│                                                             │
│    Example found:                                           │
│      ['blue_screen', 'error_code_0x0000007B', 'slow_boot'] │
│      → 'storage_driver_issue'                              │
│      Observed: 12 times, Success: 11 times (92%)           │
│                                                             │
│    Action: INSERT INTO learned_patterns                     │
│      confidence: 0.92, support: 12                         │
│      approved: FALSE (awaiting review)                     │
│                                                             │
│  Task 2: Generate new questions                             │
│    Find: Sessions with low start confidence, high end      │
│    Identify: Which questions led to breakthrough           │
│                                                             │
│    Example:                                                 │
│      Q: "Does error appear only during boot?"              │
│      → Changed belief from 0.4 to 0.8 for storage_issue   │
│      → Asked in 8 successful sessions                      │
│                                                             │
│    Action: INSERT INTO learned_questions                    │
│      information_gain_avg: 0.35                            │
│      times_helpful: 8/10                                    │
│                                                             │
│  Task 3: Update effectiveness metrics                       │
│    For each question:                                       │
│      - How often asked?                                     │
│      - How often skipped?                                   │
│      - Average information gain                             │
│      - Correlation with success                             │
│                                                             │
│  Task 4: Export approved learnings                          │
│    IF confidence > 0.7 AND support > 5:                    │
│      → Merge into symptom_mappings.json                    │
│      → Merge into questions.json                            │
│                                                             │
│  LOG: 🧠 LEARNING_CYCLE_COMPLETE                            │
│    new_patterns: 3, new_questions: 2                       │
│    exported_to_json: 5 patterns, 1 question                │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Learning Schema (schema_learning.sql)

**Tables:**
- `diagnostic_sessions` - Complete session history
- `diagnostic_logs` - Step-by-step logs for frontend display
- `belief_snapshots` - Belief vector at each stage
- `question_interactions` - Questions asked + answers
- `tutorial_matches` - Matched tutorials with scores
- `user_feedback` - Resolution outcomes
- `learned_patterns` - Discovered symptom→cause patterns
- `learned_questions` - Community-generated questions
- `pattern_candidates` - Awaiting approval
- `question_analytics` - Effectiveness tracking
- `image_caption_cache` - Avoid re-analyzing images

### 2. Session Manager (session_manager.py)

**Orchestrates:**
- Input processing → Belief engine → Questions → Tutorials
- Generates detailed logs at each stage
- Persists session state to database
- Triggers learning on successful feedback

**Methods:**
- `initialize(user_input)` - Start session
- `answer_question(q_id, answer)` - Process answer
- `record_feedback(tutorial_id, feedback)` - Store outcome
- `get_logs_for_display()` - Formatted logs for frontend

### 3. Learning Engine (learning_engine.py)

**Discovers:**
- New symptom→cause patterns (from successful sessions)
- New diagnostic questions (from ambiguous cases)
- Question effectiveness (which questions help most)

**Methods:**
- `discover_new_patterns(lookback_days)` - Analyze sessions
- `generate_new_questions(lookback_days)` - Find gaps
- `update_question_effectiveness()` - Track metrics
- `approve_pattern(pattern_id)` - Human review
- `export_to_json()` - Merge into base files

### 4. Belief Engine (adaptive)

**Loads:**
1. Base rules from `symptom_mappings.json`
2. Learned patterns from `learned_patterns` table
3. Merges with weighted confidence

**Smart Skip Logic:**
- Don't ask brand if brand_confidence > 0.8
- Don't ask if visual symptom answers it
- Don't ask if cause probability < 0.1

### 5. Input Processor (BLIP-2 conditioning)

**Text Analysis:**
- Extract keywords, symptoms, brand/model
- Map to device category (PC vs Mac vs Phone)

**Image Analysis:**
- Condition BLIP on user's text:
  ```python
  prompt = f"What is shown in this photo of a {user_text}?"
  caption = blip.generate(image, prompt)
  ```
- Extract visual symptoms: error codes, LED colors
- Cache by image hash (avoid re-analysis)

### 6. Tutorial Matcher (MyFixit integration)

**Process:**
1. Route to correct JSON (PC.json for Dell/Lenovo/HP)
2. Filter by brand, cause
3. Vector search (semantic)
4. Keyword search (exact)
5. Hybrid scoring (60% vector + 40% keyword)
6. Re-rank by user feedback history

## Frontend Display (Terminal-Style Logs)

```javascript
// Example log display
[10:23:45] 🔍 INPUT_ANALYSIS_COMPLETE
  brand: lenovo (0.95)
  symptoms: ['blue_screen']
  visual: ['error_code_0x0000007B']

[10:23:46] 📊 BELIEF_VECTOR_COMPUTED
  storage_driver_issue: 0.85 ✓ HIGH
  memory_issue: 0.40
  driver_issue: 0.30

[10:23:46] ⏭️  SKIPPING QUESTION
  question: "What brand is your laptop?"
  reason: Brand already detected (lenovo, 0.95)

[10:23:46] ✅ CONFIDENCE_THRESHOLD_REACHED
  confidence: 0.85 (threshold: 0.70)
  diagnosis: storage_driver_issue

[10:23:47] 📚 TUTORIALS_FOUND
  count: 5
  top: "Lenovo ThinkPad SSD Driver Fix"
  score: 0.94, success_rate: 87%
```

## Why This Works

### 1. Not Rule-Based
- Base rules are just **seed data**
- System discovers patterns from real usage
- Confidence scores update dynamically
- New questions generated automatically

### 2. Handles Ambiguity
- Low confidence → Ask clarifying questions
- High confidence → Skip directly to tutorials
- Visual symptoms can answer questions

### 3. Learns Continuously
- Every feedback updates patterns
- Nightly batch job consolidates learnings
- Approved patterns merge into base knowledge
- Questions proven useful become permanent

### 4. Transparent for Evaluators
- Every decision logged with reasoning
- Confidence scores shown at each stage
- Question skip reasons explained
- Tutorial match scores displayed

### 5. Efficient Architecture
- Image caption cache (no re-analysis)
- Question analytics (prune low-value questions)
- Pattern candidates (human review before approval)
- Incremental learning (not full retrain)

## Next Steps

1. **Run schema_learning.sql** - Create learning tables
2. **Download MyFixit dataset** - 31,601 repair manuals
3. **Create base symptom_mappings.json** - Initial seed patterns
4. **Create base questions.json** - Initial diagnostic questions
5. **Test end-to-end flow** - Input → Questions → Tutorials → Feedback
6. **Setup learning cron job** - Run daily pattern discovery
7. **Build API endpoints** - `/api/diagnose/*` with logging
8. **Frontend terminal display** - Show diagnostic_logs in real-time

## API Endpoints

```
POST /api/diagnose/start
  Body: {text, image?, user_id?}
  Returns: {session_id, logs[], next_action, question?}

POST /api/diagnose/answer
  Body: {session_id, question_id, answer}
  Returns: {logs[], next_action, question? | tutorials?}

GET /api/diagnose/logs/{session_id}
  Returns: {logs[]} - Formatted for terminal display

POST /api/feedback
  Body: {session_id, tutorial_id, solved_problem, ratings, comments}
  Returns: {success: true}

GET /api/admin/patterns/pending
  Returns: {pattern_candidates[]} - Awaiting approval

POST /api/admin/patterns/approve/{pattern_id}
  Returns: {success: true}
```

## Human-in-the-Loop

**Pattern approval workflow:**
1. Learning engine discovers candidate pattern
2. Stored in `pattern_candidates` with `approved=FALSE`
3. Admin reviews: support count, success rate, symptoms
4. If valid → `approve_pattern()` → moves to `learned_patterns`
5. Next export → merged into `symptom_mappings.json`

**Question approval workflow:**
1. System generates candidate question from ambiguous cases
2. Stored in `learned_questions` with `approved=FALSE`
3. Admin reviews: information gain, usefulness
4. If valid → approved → merged into `questions.json`

This ensures quality while enabling continuous learning!
