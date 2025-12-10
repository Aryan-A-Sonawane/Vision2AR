# Honest Architecture Breakdown & Issues

## Current System Architecture (The Truth)

### What Actually Happens:

```
User Input → Knowledge Engine → If Confidence < 70% → Generate 1 Question → No Further Logic
                                ↓
                           If Confidence ≥ 70% → Return Diagnosis
```

## The Problem You're Seeing

### Issue #1: **Questions Run Out Immediately**

**Why it happens:**
```python
# knowledge_engine.py line 229-235
def generate_question(self, current_understanding, asked_questions):
    # Get questions for this issue type
    questions = questions_by_issue.get(issue_type, [...])
    
    # Return first unasked question
    for q in questions:
        if q not in asked_questions:
            return q  # ❌ RETURNS ONLY 1 QUESTION PER CALL
```

**The reality:**
- The knowledge engine is called **ONCE** at diagnosis start
- It generates **ONE** question (if confidence < 70%)
- When user answers, the `/api/answer` endpoint is called
- **BUT** `/api/answer` doesn't call the knowledge engine again!
- It falls back to the generic ML engine which has no connection to the knowledge base

### Issue #2: **Yes/No Questions are Hardcoded**

**From `ml_engine.py` line ~250:**
```python
def _generate_questions(self, matches, device_model):
    # Generic hardcoded questions
    questions = [
        {
            "id": "power_led_check",
            "text": "Does the power LED light up?",
            "type": "binary",  # ❌ Only yes/no
            ...
        },
        {
            "id": "fan_spin_check",
            "text": "Do you hear the fan spin?",
            "type": "binary",  # ❌ Only yes/no
            ...
        }
    ]
```

**The problem:**
- Questions are **NOT** generated from the OEM manuals
- They are **hardcoded** generic yes/no questions
- They don't adapt based on the manual content
- Binary answers provide minimal information

### Issue #3: **Answer Processing Doesn't Update Knowledge Engine**

**What happens when user answers:**

```python
# main.py line 340-390 (simplified)
@app.post("/api/answer")
async def process_answer(answer):
    session = active_sessions[session_id]
    
    # ❌ PROBLEM: Uses generic ML engine, not knowledge engine
    next_q, result, debug_info = ml_engine.process_answer(
        session_id, question_id, answer, belief_vector, asked_questions
    )
    
    # The knowledge engine is NEVER called here!
    # The manual-based diagnosis is LOST after first question
```

**The truth:**
- After first diagnosis, the knowledge engine is abandoned
- System falls back to generic belief vector updates
- No connection to the OEM manual procedures anymore
- Just updates arbitrary probabilities (battery: 33%, power: 33%, motherboard: 34%)

### Issue #4: **No Text Answer Processing**

**Current flow:**
```
User types: "yes" or "no"
    ↓
Backend: Updates belief vector by ±0.1
    ↓
No semantic understanding of what user actually said
```

**What's missing:**
- No NLP to understand free-text answers
- No extraction of symptoms from text responses
- No re-embedding of combined symptoms
- No re-querying of knowledge base with new information

---

## What the System ACTUALLY Does (Be Honest)

### ✅ What Works Well:

1. **Initial Diagnosis from OEM Manuals**
   - Loads 39 real procedures from PDFs ✓
   - Computes semantic similarity (sentence-transformers) ✓
   - Matches "black screen" → dell.pdf with 68.5% confidence ✓
   - Returns actual repair steps from manuals ✓

2. **Source Attribution**
   - Shows which PDF file ✓
   - Includes raw manual text ✓
   - Not hallucinated content ✓

### ❌ What Doesn't Work:

1. **Iterative Question-Answer Loop**
   - Only asks 1 question from knowledge engine
   - Then disconnects from manual knowledge
   - Falls back to generic hardcoded questions
   - Doesn't refine diagnosis based on answers

2. **Answer Processing**
   - Only handles binary yes/no
   - No free-text understanding
   - Doesn't re-query knowledge base
   - Just updates arbitrary probability numbers

3. **Confidence Refinement**
   - Confidence stays at initial 68% regardless of answers
   - Doesn't increase with more information
   - User answers don't actually help narrow down the issue

---

## What Needs to Be Built (Honest Assessment)

### Critical Missing Pieces:

#### 1. **Iterative Knowledge Engine Loop**
```python
# What we need:
@app.post("/api/answer")
async def process_answer(answer):
    session = active_sessions[session_id]
    
    # ✅ ADD: Combine original symptoms + all answers
    combined_context = f"{session['symptoms']} {' '.join(session['answers'])}"
    
    # ✅ ADD: Re-run knowledge engine with more context
    kb_engine = get_engine()
    best_match, alternatives = kb_engine.diagnose(
        user_symptoms=combined_context,
        user_answers=session['answers']  # Pass answers for confidence boost
    )
    
    # ✅ ADD: Generate next question based on updated understanding
    next_question = kb_engine.generate_question(
        current_understanding=best_match,
        asked_questions=session['questions_asked']
    )
```

#### 2. **Free-Text Answer Support**
```python
# Current: question_type = "binary" (only yes/no)
# Need: question_type = "open_ended" (text responses)

# What we need:
def process_text_answer(answer_text: str, current_match: Dict):
    # Extract symptoms from answer
    answer_embedding = model.encode(answer_text)
    
    # Check if answer mentions specific keywords
    keywords_found = extract_keywords(answer_text)
    
    # Boost confidence if answer confirms diagnosis
    if any(keyword in current_match['issue_type'] for keyword in keywords_found):
        confidence += 0.15
    
    # Re-embed combined symptoms + answer
    combined = f"{original_symptoms} {answer_text}"
    new_matches = find_matches(combined)
    
    return new_matches
```

#### 3. **Smart Question Generation from Manuals**
```python
# Instead of hardcoded questions, extract from manual context:
def generate_contextual_questions(manual_procedure: Dict):
    # Look at the manual's diagnostic section
    diagnostic_text = manual_procedure['raw_text']
    
    # Extract questions using patterns:
    # - "Check if..."
    # - "Verify that..."
    # - "Test..."
    # - "Measure..."
    
    # Or use LLM to generate questions based on manual content
    questions = extract_diagnostic_steps_from_manual(diagnostic_text)
    
    return questions
```

#### 4. **Confidence Evolution**
```python
def calculate_updated_confidence(
    initial_match: Dict,
    user_answers: List[str],
    asked_questions: List[str]
):
    confidence = initial_match['similarity_score'] * 0.6
    
    # Boost for each answer that confirms diagnosis
    for answer in user_answers:
        if confirms_hypothesis(answer, initial_match['issue_type']):
            confidence += 0.1
        else:
            confidence -= 0.05  # Penalty for contradicting answers
    
    # Boost for depth of investigation
    if len(user_answers) >= 3:
        confidence += 0.05
    
    return min(confidence, 0.95)
```

---

## The Real Architecture (Current State)

```
┌─────────────────────────────────────────────────────────────┐
│ FIRST CALL: /api/diagnose                                   │
├─────────────────────────────────────────────────────────────┤
│ 1. User input → Knowledge Engine                            │
│ 2. Semantic match → Find procedure in manual                │
│ 3. Confidence 68% → Generate 1 question                     │
│ 4. Return question to user                                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ SUBSEQUENT CALLS: /api/answer                               │
├─────────────────────────────────────────────────────────────┤
│ 1. User answers → ❌ IGNORES knowledge engine               │
│ 2. Falls back to generic ML engine                          │
│ 3. Updates belief vector (arbitrary numbers)                │
│ 4. Tries to find "next question" → NONE AVAILABLE           │
│ 5. Returns "no more questions"                              │
│ 6. Forces diagnosis with same 68% confidence                │
└─────────────────────────────────────────────────────────────┘
```

## What Should Happen (Proper Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│ EVERY CALL: Knowledge Engine Loop                           │
├─────────────────────────────────────────────────────────────┤
│ 1. Combine symptoms + all previous answers                  │
│ 2. Re-embed combined text                                   │
│ 3. Re-query knowledge base                                  │
│ 4. Calculate updated confidence                             │
│ 5. If confidence < 80%:                                     │
│    - Extract diagnostic questions from manual               │
│    - Ask next most informative question                     │
│ 6. If confidence ≥ 80%:                                     │
│    - Return diagnosis from manual                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary: What You Actually Have

### ✅ Strengths:
- Real OEM manual extraction (39 procedures)
- Good initial semantic matching (68% for black screen)
- Source attribution and raw text
- NOT hallucinated responses

### ❌ Critical Gaps:
- Question generation disconnected after first call
- No iterative refinement with user answers
- Only binary yes/no questions (not text-based)
- Confidence doesn't improve with more information
- Knowledge engine only used once, then abandoned

### 🎯 What Makes It Feel Broken:
- User answers questions but system doesn't "learn"
- Confidence stays at 68% no matter what user says
- Runs out of questions immediately
- Feels like questions are pointless since diagnosis doesn't change

---

## Priority Fixes (In Order):

1. **Make `/api/answer` use knowledge engine** (30 min)
   - Pass accumulated context to knowledge engine
   - Re-run diagnosis with more information

2. **Support text-based answers** (1 hour)
   - Change question type from "binary" to "open_ended"
   - Process text answers with NLP
   - Extract keywords and boost confidence

3. **Extract questions from manuals** (2 hours)
   - Parse diagnostic sections from PDFs
   - Generate questions based on manual procedures
   - Not hardcoded generic questions

4. **Implement confidence evolution** (1 hour)
   - Update confidence based on answers
   - Show user that system is learning
   - Stop asking when confidence > 80%

Without these fixes, the system is essentially a **one-shot diagnosis tool** that asks meaningless follow-up questions.
