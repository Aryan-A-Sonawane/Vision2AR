# Mathematical Equations for IEEE Paper
## AR-Guided Device Repair System - Key Algorithms

---

## A. MULTI-MODAL INPUT PROCESSING

### Equation 1: Semantic Symptom Embedding
```
v_symptom = Encoder(T_input) ∈ ℝ^384
```
**Where:** T_input is the tokenized symptom text, v_symptom is the 384-dimensional embedding vector from sentence-transformers (all-MiniLM-L6-v2).

---

### Equation 2: Visual Context Extraction (BLIP-2)
```
T_visual = BLIP-2(I_input, P_prompt)
```
**Where:** I_input is the input image, P_prompt is the guided prompt for hardware symptom description.

---

### Equation 3: Multi-Modal Fusion
```
v_fused = α · v_symptom + (1-α) · Encoder(T_visual)
```
**Where:** α ∈ [0,1] is the text-visual balance weight (default: α = 0.7 for text priority).

---

## B. BAYESIAN BELIEF INITIALIZATION

### Equation 4: Cosine Similarity (Vector Search)
```
sim(v_fused, v_i) = (v_fused · v_i) / (||v_fused|| ||v_i||)
```
**Where:** v_i represents stored symptom embeddings in the vector database.

---

### Equation 5: Initial Belief Distribution
```
                  Σ (sim(v_fused, v_i) · I[cause_i = c_j])
                  i∈N_k
P(c_j | v_fused) = ───────────────────────────────────────
                  Σ sim(v_fused, v_i)
                  i∈N_k
```
**Where:** N_k is the set of top-k nearest neighbors, I[·] is the indicator function, c_j is a candidate cause.

---

### Equation 6: Uniform Prior Fallback
```
P(c_j) = 1/|C|,  ∀ c_j ∈ C
```
**Used when:** max_j P(c_j) < θ_min (no strong semantic matches found).

---

## C. INFORMATION GAIN MAXIMIZATION

### Equation 7: Shannon Entropy
```
H(P) = -Σ P(c_j) log₂ P(c_j)
       j=1 to |C|
```
**Purpose:** Measures current diagnostic uncertainty in the belief distribution.

---

### Equation 8: Expected Information Gain
```
IG(q_i) = H(P_current) - E[H(P | q_i = a)]
                          a~q_i
```
**Where:** a represents possible answers (yes/no/uncertain), E[·] is expectation over answer distribution.

---

### Equation 9: Conditional Entropy After Answer
```
H(P | q_i = a) = -Σ P(c_j | q_i = a) log₂ P(c_j | q_i = a)
                  j=1 to |C|
```
**Purpose:** Calculate expected uncertainty after receiving answer a to question q_i.

---

### Equation 10: Question Selection Policy
```
q* = argmax [IG(q_i) - λ · Redundancy(q_i)]
     q_i ∈ Q\Q_asked
```
**Where:** λ is redundancy penalty weight, Q_asked is set of previously asked questions.

---

## D. BAYESIAN BELIEF PROPAGATION

### Equation 11: Bayes' Theorem Update Rule
```
P(c_j | q=a) = P(a | c_j, q) · P(c_j) / Σ P(a | c_k, q) · P(c_k)
                                        k=1 to |C|
```
**Purpose:** Update belief distribution after receiving answer a to question q.

---

### Equation 12: Likelihood Function
```
P(a | c_j, q) = { μ⁺_(q,c_j)  if a = yes
                { μ⁻_(q,c_j)  if a = no
                { 0.5         if a = uncertain
```
**Where:** μ⁺ and μ⁻ are learned evidence multipliers from historical repair data.

---

### Equation 13: Multiplicative Update (Simplified)
```
P_new(c_j) ∝ P_old(c_j) · LikelihoodRatio(a, c_j, q)
```
**Purpose:** Efficient log-space belief update without full Bayesian computation.

---

### Equation 14: Normalization
```
P_norm(c_j) = P_new(c_j) / Σ P_new(c_k)
                           k=1 to |C|
```
**Purpose:** Maintain valid probability distribution (sum to 1.0).

---

## E. DIAGNOSTIC CONVERGENCE CRITERIA

### Equation 15: Confidence Threshold
```
max P(c_j) ≥ θ_conf    where θ_conf = 0.70
 j
```
**Purpose:** Stop questioning when diagnosis confidence reaches 70%.

---

### Equation 16: Maximum Questions Limit
```
|Q_asked| ≥ N_max    where N_max = 5
```
**Purpose:** Prevent excessive questioning (fallback to best guess after 5 questions).

---

### Equation 17: Entropy Convergence Rate
```
[H(P_(t-1)) - H(P_t)] / H(P_(t-1)) < ε_conv
```
**Where:** ε_conv = 0.05 (stop if entropy reduction < 5% per question).

---

## F. SEMANTIC TUTORIAL RETRIEVAL

### Equation 18: Diagnosis-Tutorial Matching Score
```
Score(t, d) = β · sim_sem(t, d) + (1-β) · sim_struct(t, d)
```
**Where:** β = 0.6 (semantic weight), t is tutorial, d is diagnosis.

---

### Equation 19: Semantic Similarity
```
sim_sem(t, d) = (v_tutorial · v_diagnosis) / (||v_tutorial|| ||v_diagnosis||)
```
**Purpose:** Cosine similarity between tutorial and diagnosis embeddings.

---

### Equation 20: Structural Similarity (Jaccard)
```
sim_struct(t, d) = |Keywords_t ∩ Keywords_d| / |Keywords_t ∪ Keywords_d|
```
**Purpose:** Keyword overlap ratio for exact matching validation.

---

## G. YOLOv8 AR COMPONENT DETECTION

### Equation 21: Detection Output Format
```
Detection_i = ([x_i, y_i, w_i, h_i], c_i, p_i)
```
**Where:** (x_i, y_i) is center coordinate, (w_i, h_i) is bounding box dimensions, c_i is class label, p_i is confidence score.

---

### Equation 22: Non-Maximum Suppression (IoU)
```
IoU(b_i, b_j) = Area(b_i ∩ b_j) / Area(b_i ∪ b_j)
```
**Rule:** Suppress box b_j if IoU(b_i, b_j) > θ_NMS and p_j < p_i, where θ_NMS = 0.45.

---

### Equation 23: Spatial Distance for Anchor Matching
```
dist(d_i, a_j) = √[(x_d_i - x_a_j)² + (y_d_i - y_a_j)²]
```
**Purpose:** Measure Euclidean distance between live detection d_i and reference anchor a_j.

---

### Equation 24: Optimal Anchor Assignment
```
a*_j = argmin dist(d_i, a_j),  subject to dist(d_i, a*_j) < δ_max
       a_j∈A
```
**Where:** δ_max = 100 pixels (matching tolerance threshold).

---

## H. CONTINUOUS LEARNING SYSTEM

### Equation 25: Question Effectiveness Scoring
```
                  Σ I[q_i ∈ s] · IG_s(q_i)
                  s∈S_success
Effectiveness(q_i) = ────────────────────────
                  Σ I[q_i ∈ s]
                  s∈S_all
```
**Where:** S_success is successful diagnostic sessions, IG_s(q_i) is measured information gain.

---

### Equation 26: Belief Update Learning (Multiplier Refinement)
```
μ⁺_(q,c)_new = (1-γ) · μ⁺_(q,c)_old + γ · [Σ I[q=yes, outcome=c] / Σ I[q asked]]
                                           s∈S_c                    s∈S_c
```
**Where:** γ = 0.1 is learning rate, S_c is sessions with true cause c.

---

### Equation 27: Contrastive Embedding Loss (Optional Fine-tuning)
```
L_contrastive = Σ [y_ij ||v_i - v_j||² + (1-y_ij) max(0, m - ||v_i - v_j||)²]
                i,j
```
**Where:** y_ij = 1 if symptoms i,j share same root cause, m = 1.0 is margin.

---

## ALGORITHM PSEUDOCODE

### Algorithm 1: Adaptive Belief-Driven Diagnosis
```
Input: User symptom T_input, optional image I_input
Output: Diagnosis c*, Tutorial set T

1. v_fused ← Embed(T_input, I_input)              // Eq. 1-3
2. P ← InitializeBeliefs(v_fused)                 // Eq. 5-6
3. Q_asked ← ∅

4. while max_j P(c_j) < θ_conf AND |Q_asked| < N_max do
5.     q* ← argmax_i IG(q_i)                      // Eq. 8-10
6.     a ← AskUser(q*)
7.     P ← UpdateBelief(P, q*, a)                 // Eq. 11-14
8.     Q_asked ← Q_asked ∪ {q*}
9. end while

10. c* ← argmax_j P(c_j)
11. T ← RetrieveTutorials(c*, v_fused)            // Eq. 18-20
12. return c*, T
```

---

### Algorithm 2: AR-Guided Repair Execution
```
Input: Tutorial t, Camera stream F
Output: Repair completion status

1. Load category-specific YOLOv8 model M_category
2. A_ref ← ProcessReferenceImage(t.step_images)   // Eq. 21-22

3. for each frame f ∈ F do
4.     D_live ← M_category(f)                     // Live detection
5.     M ← MatchAnchors(D_live, A_ref)            // Eq. 23-24
6.     f_overlay ← DrawOverlay(f, M)
7.     Display f_overlay in WebXR viewer
8.     if all critical components matched then
9.         Proceed to next step
10.    end if
11. end for
```

---

## NOTATION REFERENCE TABLE

| Symbol | Description |
|--------|-------------|
| v_symptom | Symptom embedding vector (384-dim) |
| T_input | User input text |
| I_input | User input image |
| P | Belief distribution over causes |
| C = {c₁, ..., cₙ} | Set of possible causes |
| P(cⱼ) | Probability of cause cⱼ |
| H(P) | Shannon entropy of belief distribution |
| IG(qᵢ) | Information gain of question qᵢ |
| Q_asked | Set of previously asked questions |
| θ_conf | Confidence threshold (0.70) |
| N_max | Maximum questions allowed (5) |
| μ⁺, μ⁻ | Likelihood multipliers for yes/no answers |
| A_ref | Reference anchor set from tutorial images |
| D_live | Live detection set from camera |
| IoU | Intersection over Union (overlap metric) |
| α | Text-visual fusion weight (0.7) |
| β | Semantic-structural matching weight (0.6) |
| γ | Learning rate (0.1) |
| δ_max | Anchor matching tolerance (100 pixels) |
| θ_NMS | Non-Maximum Suppression threshold (0.45) |
| ε_conv | Entropy convergence threshold (0.05) |

---

## KEY HYPERPARAMETERS

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Embedding dimension | 384 | Sentence-transformer output size |
| Confidence threshold (θ_conf) | 0.70 | Minimum belief to stop questioning |
| Max questions (N_max) | 5 | Question budget per session |
| Text weight (α) | 0.7 | Text priority in multi-modal fusion |
| Semantic weight (β) | 0.6 | Embedding priority in tutorial matching |
| Learning rate (γ) | 0.1 | Belief multiplier update rate |
| NMS threshold (θ_NMS) | 0.45 | IoU threshold for duplicate detection |
| Matching tolerance (δ_max) | 100 px | Max distance for anchor matching |
| Entropy threshold (ε_conv) | 0.05 | Min entropy reduction to continue |
| Top-k neighbors | 5 | Vector DB retrieval count |

---

## USAGE IN IEEE PAPER

### For LaTeX:
Use the file: `paper_equations.tex`
- Copy equations directly into your IEEE LaTeX template
- Requires packages: `amsmath`, `amssymb`, `algorithm`, `algorithmic`

### For Microsoft Word:
- Use Word's built-in equation editor (Insert → Equation)
- Copy the mathematical notation from this file
- Use italic for variables, bold for vectors
- Use subscripts/superscripts appropriately

### For Google Docs:
- Use "Insert → Equation" or MathType add-on
- Convert symbols: ∈ (element of), ∀ (for all), ∃ (exists), ∑ (sum), ∏ (product)

---

## EQUATION CITATION EXAMPLES

In your paper text, reference equations like this:

> "The belief distribution is updated using Bayes' theorem (Equation 11), where likelihood multipliers are learned from historical repair outcomes (Equation 12)."

> "Question selection maximizes information gain (Equation 8) while penalizing redundancy (Equation 10), reducing average diagnostic session length."

> "Component detection confidence is computed using the IoU metric (Equation 22), ensuring accurate anchor-to-detection matching in the AR overlay system."

---

**Generated:** December 8, 2025  
**Project:** AR-Guided Device Repair with Belief-Driven Diagnosis  
**For:** IEEE Conference Paper Submission
