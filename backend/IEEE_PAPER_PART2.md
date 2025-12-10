# Adaptive Multi-Modal Diagnostic System - Part 2

## IV. SYSTEM ARCHITECTURE

### A. Architectural Overview

The system comprises six primary subsystems operating in a pipelined architecture with feedback loops for continuous learning. Figure 1 illustrates the complete system architecture.

```
┌────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Text Input   │  │ Image Upload │  │ Log Display  │        │
│  │ Component    │  │ Component    │  │ (Terminal)   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘        │
│         │                  │                  │                 │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          ▼                  ▼                  │
┌────────────────────────────────────────────────────────────────┐
│              API GATEWAY & SESSION ORCHESTRATION               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  DiagnosticSession (session_manager.py)                  │ │
│  │  • State persistence (PostgreSQL)                        │ │
│  │  • Log generation (diagnostic_logs table)                │ │
│  │  • Workflow coordination                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
          │                                          │
          ▼                                          │
┌────────────────────────────────────────────────────────────────┐
│               MULTI-MODAL INPUT PROCESSING LAYER               │
│  ┌──────────────────────┐    ┌─────────────────────────────┐ │
│  │  Text Analyzer       │    │  Vision Analyzer            │ │
│  │  • Keyword extract   │    │  • BLIP-2 captioning        │ │
│  │  • Brand detection   │    │  • Context conditioning     │ │
│  │  • Sentence-BERT     │    │  • Error code extraction    │ │
│  │  embedding           │    │  • Image cache (SHA-256)    │ │
│  └──────────┬───────────┘    └─────────┬───────────────────┘ │
│             │                           │                      │
│             └───────────┬───────────────┘                      │
└─────────────────────────┼──────────────────────────────────────┘
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                 BELIEF PROPAGATION ENGINE                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  BeliefVectorEngine (belief_engine.py)                   │ │
│  │                                                           │ │
│  │  Knowledge Sources:                                       │ │
│  │  ┌─────────────────┐  ┌───────────────────────────┐    │ │
│  │  │ Base Rules      │  │ Learned Patterns          │    │ │
│  │  │ (JSON files)    │  │ (learned_patterns table)  │    │ │
│  │  │ • symptom_      │  │ • Support: n              │    │ │
│  │  │   mappings.json │  │ • Success rate: r         │    │ │
│  │  │ • Confidence: α │  │ • Confidence: w = r·f(n)  │    │ │
│  │  └────────┬────────┘  └─────────┬─────────────────┘    │ │
│  │           │                      │                       │ │
│  │           └───────┬──────────────┘                       │ │
│  │                   ▼                                       │ │
│  │          Belief Fusion:                                   │ │
│  │          B₀(c) = α·P_base(c|S) + (1-α)·P_learned(c|S)   │ │
│  │                                                           │ │
│  │  Output: B ∈ [0,1]^m  (belief vector over m causes)     │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│            ADAPTIVE QUESTION SELECTION ENGINE                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Question Database:                                       │ │
│  │  ┌────────────────┐  ┌──────────────────────────────┐   │ │
│  │  │ Base Questions │  │ Learned Questions            │   │ │
│  │  │ (questions.json)  │ (learned_questions table)    │   │ │
│  │  └────────┬───────┘  └──────────┬───────────────────┘   │ │
│  │           │                      │                        │ │
│  │           └──────────┬───────────┘                        │ │
│  │                      ▼                                     │ │
│  │           Question Filtering:                             │ │
│  │           • Redundancy check (brand known?)               │ │
│  │           • Relevance check (P(c) > τ_cause?)            │ │
│  │           • Information gain (IG(q) > τ_IG?)             │ │
│  │                      │                                     │ │
│  │                      ▼                                     │ │
│  │           IF max(B) >= 0.7:                               │ │
│  │               → SKIP to Tutorial Matching                 │ │
│  │           ELSE:                                            │ │
│  │               → SELECT question with max IG(q)            │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│              HYBRID TUTORIAL RETRIEVAL ENGINE                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Stage 1: Category Routing                               │ │
│  │    category → {Mac.json, PC.json, Phone.json, ...}      │ │
│  │                      │                                     │ │
│  │                      ▼                                     │ │
│  │  Stage 2: Dense Retrieval (Weaviate Vector DB)           │ │
│  │    score_vec(t) = cos(φ(S), φ(t))                       │ │
│  │    Top-K: K=50                                            │ │
│  │                      │                                     │ │
│  │                      ▼                                     │ │
│  │  Stage 3: Sparse Retrieval (PostgreSQL)                  │ │
│  │    score_lex(t) = Jaccard(keywords, t.keywords)         │ │
│  │                      │                                     │ │
│  │                      ▼                                     │ │
│  │  Stage 4: Hybrid Fusion                                   │ │
│  │    score = 0.6·score_vec + 0.4·score_lex                │ │
│  │                      │                                     │ │
│  │                      ▼                                     │ │
│  │  Stage 5: Feedback Re-ranking                             │ │
│  │    score_final = score · (1 + γ·feedback_score)         │ │
│  │    γ = 0.3 (empirically tuned)                           │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                  USER FEEDBACK COLLECTION                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Explicit Feedback:                                       │ │
│  │  • Problem solved? (Boolean)                              │ │
│  │  • Clarity rating (1-5 scale)                             │ │
│  │  • Accuracy rating (1-5 scale)                            │ │
│  │  • Time spent (minutes)                                   │ │
│  │                                                           │ │
│  │  Implicit Feedback:                                       │ │
│  │  • Completion percentage                                  │ │
│  │  • Steps viewed                                           │ │
│  │  • Tutorial selection rank                                │ │
│  │                                                           │ │
│  │  Storage: user_feedback table                             │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│            ONLINE LEARNING ENGINE (Nightly Batch)              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LearningEngine (learning_engine.py)                     │ │
│  │                                                           │ │
│  │  Task 1: Pattern Discovery                                │ │
│  │    Input: Sessions with solved=true (last 7 days)        │ │
│  │    Process:                                               │ │
│  │      FOR each (symptom_combo, cause, category):          │ │
│  │        n = count(sessions)                                │ │
│  │        r = successes / n                                  │ │
│  │        w = r · (1 - exp(-n/5))                           │ │
│  │        IF n >= 3 AND r >= 0.7 AND w >= 0.65:            │ │
│  │          CREATE pattern_candidate                         │ │
│  │    Output: pattern_candidates table                       │ │
│  │                                                           │ │
│  │  Task 2: Question Generation                              │ │
│  │    Input: Sessions with H(C|Ψ₀) > 1.5 & solved=true     │ │
│  │    Process:                                               │ │
│  │      FOR each session:                                    │ │
│  │        Find q* = argmax_q ΔH(q)  (breakthrough Q)        │ │
│  │      Cluster similar q* across sessions                   │ │
│  │      Generate generalized question templates              │ │
│  │    Output: learned_questions table                        │ │
│  │                                                           │ │
│  │  Task 3: Effectiveness Analysis                           │ │
│  │    Metrics computed:                                      │ │
│  │      • Question skip rate                                 │ │
│  │      • Average information gain                           │ │
│  │      • Correlation with resolution                        │ │
│  │    Action: Prune questions with low effectiveness         │ │
│  │                                                           │ │
│  │  Task 4: Knowledge Export                                 │ │
│  │    IF pattern approved (human review):                    │ │
│  │      MERGE into symptom_mappings.json                     │ │
│  │      MERGE into questions.json                            │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          └──────────┐
                                     ▼
┌────────────────────────────────────────────────────────────────┐
│                   PERSISTENT STORAGE LAYER                     │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │  PostgreSQL          │  │  Weaviate Vector DB          │  │
│  │  • Tutorials (41)    │  │  • Tutorial embeddings (384d)│  │
│  │  • Steps (294)       │  │  • Semantic search           │  │
│  │  • Sessions          │  │  • Cosine similarity         │  │
│  │  • Feedback          │  │                              │  │
│  │  • Learned patterns  │  │                              │  │
│  │  • Question analytics│  │                              │  │
│  └──────────────────────┘  └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Fig. 1. Complete System Architecture Diagram**. The architecture comprises six layers: (1) User Interface for input collection and log display, (2) Session Orchestration for state management, (3) Multi-Modal Processing for text and image analysis, (4) Belief Propagation Engine combining base knowledge with learned patterns, (5) Adaptive Question Selection with redundancy elimination, (6) Hybrid Tutorial Retrieval with feedback-based re-ranking. Feedback loops enable continuous learning through pattern discovery and question generation.

---

### B. Data Flow Sequence

**TABLE I: COMPLETE DIAGNOSTIC SESSION DATA FLOW**

| Stage | Input | Processing | Output | Storage |
|-------|-------|------------|--------|---------|
| 1. Input Reception | User text, Optional image | UTF-8 parsing, Image validation | Raw input data | diagnostic_sessions |
| 2. Text Analysis | Raw text | Keyword extraction (TF-IDF), Brand detection (regex), Symptom classification (Sentence-BERT) | S^text, brand, confidence | diagnostic_logs |
| 3. Image Analysis | Image bytes | BLIP-2 captioning conditioned on text, Error code extraction (regex), Visual symptom mapping | S^vis, error_codes | image_caption_cache |
| 4. Belief Initialization | S^text, S^vis, category | Load base rules (JSON), Query learned patterns (SQL), Weighted fusion | B_0 ∈ [0,1]^m | belief_snapshots |
| 5. Question Selection | B_t, Θ_t, Q_history | Filter redundant questions, Compute IG(q), Select max IG | Next question or DONE | question_interactions |
| 6. Belief Update | Question answer | Bayesian update, Normalize | B_t+1 | belief_snapshots |
| 7. Tutorial Matching | B_final, category, brand | Vector search (Weaviate), Keyword search (PostgreSQL), Hybrid scoring, Feedback re-rank | Ranked tutorial list | tutorial_matches |
| 8. Feedback Collection | Tutorial ID, User ratings | Validation, Aggregation | Feedback record | user_feedback |
| 9. Pattern Discovery | Feedback corpus (7 days) | Frequency analysis, Success rate calc, Confidence scoring | Pattern candidates | pattern_candidates |
| 10. Knowledge Update | Approved patterns | JSON merge, Database insert | Updated knowledge base | learned_patterns |

---

### C. Component Interactions

**Algorithm 1: Main Diagnostic Loop**
```
INPUT: user_text, user_image (optional)
OUTPUT: tutorial_list, diagnostic_logs

1:  session ← CreateSession()
2:  S_text ← AnalyzeText(user_text)
3:  IF user_image ≠ NULL THEN
4:      S_vis ← AnalyzeImage(user_image, user_text)
5:  ELSE
6:      S_vis ← ∅
7:  END IF
8:  
9:  symptoms ← S_text ∪ S_vis
10: B ← InitializeBelief(symptoms, category, brand)
11: session.LogBelief(B, "initial")
12: 
13: WHILE max(B) < τ_conf DO
14:     q ← SelectNextQuestion(B, session.asked_questions)
15:     IF q = NULL THEN
16:         BREAK  // No more useful questions
17:     END IF
18:     
19:     session.Log("QUESTION_SELECTED", q)
20:     answer ← AskUser(q)
21:     session.Log("QUESTION_ANSWERED", answer)
22:     
23:     B ← UpdateBelief(B, q, answer)
24:     session.LogBelief(B, "question_" + q.id)
25: END WHILE
26: 
27: cause ← argmax(B)
28: session.Log("DIAGNOSIS", cause)
29: 
30: tutorials ← MatchTutorials(symptoms, cause, category, brand)
31: session.Log("TUTORIALS_FOUND", tutorials)
32: 
33: RETURN tutorials, session.logs
```

---

**Algorithm 2: Pattern Discovery (Learning Engine)**
```
INPUT: session_history (last N days)
OUTPUT: pattern_candidates

1:  patterns ← empty dictionary
2:  
3:  FOR each session s IN session_history WHERE s.resolved = TRUE DO
4:      key ← (s.symptoms, s.diagnosis, s.category)
5:      
6:      IF key NOT IN patterns THEN
7:          patterns[key] ← {count: 0, successes: 0, sessions: []}
8:      END IF
9:      
10:     patterns[key].count += 1
11:     patterns[key].successes += (s.feedback.solved ? 1 : 0)
12:     patterns[key].sessions.append(s.id)
13: END FOR
14: 
15: candidates ← []
16: FOR each (key, stats) IN patterns DO
17:     n ← stats.count
18:     r ← stats.successes / n
19:     w ← r × (1 - exp(-n / n₀))  // n₀ = 5
20:     
21:     IF n >= n_min AND r >= r_min AND w >= w_min THEN
22:         candidate ← CreatePattern(key, n, r, w)
23:         candidates.append(candidate)
24:     END IF
25: END FOR
26: 
27: RETURN candidates
```

---

### D. Database Schema Design

**TABLE II: KEY DATABASE TABLES FOR LEARNING**

| Table Name | Purpose | Key Fields | Indices |
|------------|---------|------------|---------|
| diagnostic_sessions | Session state tracking | session_id (UUID), brand, symptoms[], diagnosis, resolved (Boolean) | (brand), (created_at), (resolved) |
| diagnostic_logs | Step-by-step logging | session_id, stage, action, data (JSONB), timestamp | (session_id, log_order) |
| belief_snapshots | Belief evolution tracking | session_id, belief_vector (JSONB), trigger_event | (session_id, snapshot_order) |
| question_interactions | Question-answer history | session_id, question_id, answer, belief_change (JSONB) | (session_id), (question_id) |
| tutorial_matches | Retrieved tutorials | session_id, tutorial_id, rank, vector_score, keyword_score, combined_score | (session_id), (tutorial_id) |
| user_feedback | Resolution outcomes | session_id, tutorial_id, solved (Boolean), clarity_rating (1-5), time_spent | (tutorial_id), (solved) |
| learned_patterns | Discovered patterns | symptom_combination[], cause, confidence, support_count, success_rate, approved (Boolean) | GIN(symptom_combination), (category), (approved) |
| learned_questions | Generated questions | question_id, question_text, information_gain_avg, times_helpful, approved (Boolean) | (category), (approved) |
| pattern_candidates | Pending approval | symptom_combination[], cause, observed_count, success_count, confidence | GIN(symptom_combination) |
| question_analytics | Question effectiveness | question_id, times_asked, avg_information_gain, correlation_with_success | (question_id) |
| image_caption_cache | Cached BLIP results | image_hash (SHA-256), blip_caption, visual_symptoms[], context_text | (image_hash) |

---

### E. Scalability Considerations

**Computational Complexity Analysis:**

**TABLE III: TIME COMPLEXITY OF KEY OPERATIONS**

| Operation | Complexity | Bottleneck | Mitigation |
|-----------|------------|------------|------------|
| Text Analysis | O(n log n) | TF-IDF computation | Pre-computed IDF weights |
| Image Captioning | O(1) w/ cache, O(T) w/o | BLIP-2 inference | SHA-256 caching, GPU acceleration |
| Belief Initialization | O(m × s) | Pattern matching | Indexed symptom lookup |
| Question Selection | O(k × m) | IG computation for k questions | Pre-filter by relevance |
| Vector Search (Weaviate) | O(log N) | ANN indexing | HNSW algorithm [18] |
| Keyword Search (PostgreSQL) | O(log N) | GIN index lookup | PostgreSQL GIN index |
| Pattern Discovery | O(n × m) | Session aggregation | Batch processing, time windowing |
| Knowledge Export | O(p) | JSON serialization | Incremental updates |

Where:
- n: Input text length
- m: Number of possible causes
- s: Number of symptoms
- k: Number of candidate questions
- N: Number of tutorials in database
- T: BLIP-2 inference steps
- p: Number of learned patterns

**Storage Requirements:**

| Component | Storage per Entity | Estimated Total (90 days) |
|-----------|-------------------|---------------------------|
| Sessions | ~2 KB | 180 KB (100 sessions) |
| Logs | ~1 KB per log | 500 KB (5 logs/session × 100) |
| Belief Snapshots | ~500 bytes | 150 KB (3 snapshots/session × 100) |
| Feedback | ~300 bytes | 30 KB |
| Learned Patterns | ~1 KB | 150 KB (150 patterns) |
| Image Cache | ~100 KB per image | 5 MB (50 unique images) |
| **Total** | | **~6 MB** |

The system demonstrates linear scalability with respect to session count.

---

*[Continue to Part 3 for Implementation, Results, and Discussion]*
