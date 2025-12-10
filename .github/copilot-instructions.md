# AR Laptop Troubleshooter - AI Agent Instructions

## Project Overview

This is a web-based diagnostic and repair assistant that uses **adaptive questioning + AR-guided overlays** to help users fix laptop problems. The system combines OEM manuals, iFixit guides, and YouTube tutorials into a single canonical repair path.

**Critical Goal**: Users must complete repairs successfully without device damage.

## Architecture & Data Flow

### Three-Stage Pipeline

1. **Diagnosis Engine** → Dynamic follow-up questions with belief vector tracking
2. **Tutorial Generator** → Merge OEM (spine) + iFixit (details) + YouTube (visuals) 
3. **AR Layer** → WebXR overlays tied to device frame via camera

### Tech Stack

- **Frontend**: Next.js + Tailwind + WebXR API + browser TTS
- **Backend**: Python FastAPI + worker pipeline for ingestion
- **ML Models**: Whisper (STT), YOLOv8/SAM (vision), BLIP2/LLaVA (vision+LLM), XGBoost (classifier)
- **Storage**: PostgreSQL (procedural tutorials), Vector DB (symptom embeddings)

## Critical Safety Rules (NON-NEGOTIABLE)

### Rule 1: Source Priority & Conflict Resolution

**NEVER show multiple conflicting repair methods simultaneously.**

**Source hierarchy:**
1. **OEM manuals FIRST** (safety guaranteed, warranty-safe)
2. **iFixit WHEN** OEM lacks clarity (validated teardowns)
3. **YouTube WHEN** real-world visuals needed (with human validation)

**Merge strategy:**
- Pick OEM as canonical step sequence
- Enhance with iFixit details (screw types, tool names)
- Add YouTube keyframes as visual anchors
- Tag each step with `source_primary` and `source_supporting`

### Rule 2: Agent Behavior Constraints

❌ **NEVER** invent repair steps via LLM hallucination  
❌ **NEVER** guess screw locations or part positions  
❌ **NEVER** provide disassembly steps without source data  
❌ **NEVER** proceed when confidence ≤ 0.4  

✅ **ALWAYS** load procedural entries from PostgreSQL  
✅ **ALWAYS** use local asset paths (`assets/{brand}/{product}/`)  
✅ **ALWAYS** show warnings for high-risk/irreversible steps  

### Rule 3: Risk Level Classification

- **Safe**: RAM, SSD, CMOS reset, bottom panel removal
- **Medium**: Fan replacement, keyboard removal
- **High**: BIOS reflash, motherboard work, hot-air soldering

**Abort high-risk YouTube-only tutorials.** Require OEM or iFixit validation.

## Directory Structure

```
assets/
  {brand}/          # lenovo, dell, hp, etc.
    {product}/      # ideapad_5, xps_15, pavilion, etc.
      *.jpg|png     # Part images with overlay anchors
manuals/
  {brand}/          # OEM service manuals (PDFs)
    *.pdf
backend/
  diagnosis/        # Belief vector engine + question generator
  tutorial/         # Step merger + source resolver
  ar_layer/         # Overlay generator + bounding box logic
frontend/
  components/       # WebXR viewer + step controls
  pages/            # Next.js routes
```

## Key Workflows

### Diagnosis Workflow

1. **Embed user input** (text/image/video) → symptom vector
2. **Query vector DB** filtered by device model → top 3 probable causes
3. **Ask binary follow-up questions** (minimal, high-signal):
   - "Does CapsLock LED toggle?"
   - "Do you hear fan spin for 2 seconds?"
4. **Update belief vector** after each answer
5. **Stop when confidence ≥ 0.6** or next step is high-risk

**Question data structure:**
```python
{
  "id": "q_power_led",
  "intent": "check_power",
  "question_text": "Does the power LED light up?",
  "expected_signal": "visual",
  "cost_level": "safe",
  "confidence_gain_estimate": 0.3,
  "next_if_yes": "q_boot_logo",
  "next_if_no": "q_battery_check"
}
```

### Repair Workflow

1. **Load OEM procedural tutorial** from PostgreSQL (device-specific)
2. **Load matching images** from `assets/{brand}/{product}/`
3. **Load overlay.json** with bounding box coordinates
4. **Render AR overlay** (step-by-step):
   - Overlay visual (highlight/arrow)
   - Text instruction
   - TTS voice guidance
5. **Controls**: Next Step | Previous | Repeat | Manual View (fallback)

### Tutorial Merge Example

**OEM Manual Step 6:** "Remove bottom cover"  
**iFixit Enhancement:** "Unscrew 8 screws (Torx-5)"  
**YouTube Visual:** Shows screw positions at 03:20–03:40  

**Merged Output:**
```
Step 6: Remove bottom cover
- Use Torx-5 screwdriver (×8 screws)
- Reference video: 03:20–03:40
- Image overlay: screw_positions.jpg
- Source: OEM + iFixit + YouTube
```

## Code Patterns & Conventions

### Asset Path Convention

```python
# Always use this pattern
asset_path = f"assets/{brand}/{product}/{image_name}.jpg"
# Example: assets/lenovo/ideapad_5/bottom_cover_screws.jpg
```

### Step Locking (Canonical Order)

Once a tutorial is merged, **step numbering cannot change per source**. Use this structure:

```json
{
  "step_id": 6,
  "action": "Remove bottom cover",
  "source_primary": "OEM",
  "source_supporting": ["iFixit", "YouTube"],
  "tools": ["Torx-5"],
  "risk_level": "safe",
  "image": "assets/lenovo/ideapad_5/step6_cover.jpg",
  "overlay_anchors": [{"x": 120, "y": 340, "type": "screw"}],
  "video_timestamp": "03:20-03:40",
  "warnings": []
}
```

### Belief Vector Update

```python
# After each question response
belief_vector[cause_id] *= (
    confidence_gain if answer == expected_signal 
    else confidence_penalty
)

# Stop condition
if max(belief_vector.values()) >= 0.6:
    present_repair_path()
```

## Dataset Schema

PostgreSQL table: `repair_procedures`

| Column | Type | Description |
|--------|------|-------------|
| device_model | varchar | e.g., "lenovo_ideapad_5" |
| issue | varchar | e.g., "no_boot" |
| symptom_pattern | json | Binary signals array |
| cause | varchar | Root cause identifier |
| confidence | float | 0.0-1.0 |
| source | varchar | OEM/iFixit/YouTube |
| steps | jsonb | Ordered step array |
| images | text[] | Asset paths |
| risk_level | varchar | safe/medium/high |
| tools | text[] | Required tools |
| warnings | text[] | Safety alerts |
| recovery | text | Rollback instructions |

## When Adding New Features

1. **New device model?** → Create `assets/{brand}/{new_product}/` + add PDF to `manuals/{brand}/`
2. **New diagnosis pattern?** → Add question to belief engine with confidence gain estimate
3. **New repair step?** → Ensure OEM source exists first, then enhance with community sources
4. **New ML model?** → Update ingestion pipeline in `backend/tutorial/` worker

## Testing Checklist

- [ ] Diagnosis stops at confidence ≥ 0.6
- [ ] No conflicting steps shown simultaneously
- [ ] High-risk steps show warnings
- [ ] Asset paths resolve correctly (`assets/{brand}/{product}/`)
- [ ] AR overlays anchor to correct image regions
- [ ] TTS speaks each step clearly
- [ ] Fallback to manual view works offline

## Common Pitfalls to Avoid

- ❌ Using YouTube as primary source for risky repairs
- ❌ Mixing step sequences from different sources without merging
- ❌ Hardcoding device-specific logic (use database queries)
- ❌ Generating repair steps via LLM without source validation
- ❌ Ignoring risk level classifications
