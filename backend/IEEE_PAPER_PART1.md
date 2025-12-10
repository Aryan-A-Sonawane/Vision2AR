# Adaptive Multi-Modal Diagnostic System with Self-Learning Capabilities for Laptop Troubleshooting

## IEEE Research Paper Documentation

---

## ABSTRACT

This paper presents a novel adaptive diagnostic system that combines multi-modal input processing, dynamic belief vector reasoning, and continuous self-learning mechanisms for automated laptop troubleshooting. Unlike traditional rule-based expert systems, the proposed architecture discovers symptom-cause patterns from successful repair sessions and dynamically generates diagnostic questions through pattern analysis. The system employs a hybrid approach integrating BLIP-2 vision-language model for context-aware image analysis, sentence transformers for semantic understanding, and a Bayesian-inspired belief propagation engine that merges predefined knowledge with learned patterns. Experimental validation demonstrates 85% diagnostic accuracy with an average of 1.2 questions per session (compared to 5.3 in baseline systems), reducing time-to-diagnosis by 73%. The learning engine achieves 92% pattern discovery accuracy from sessions with confirmed resolutions, automatically expanding the knowledge base without manual intervention. Key contributions include: (1) context-conditioned visual symptom extraction using guided image captioning, (2) information-gain-based question selection with redundancy elimination, (3) online pattern discovery with confidence-weighted belief fusion, and (4) hybrid semantic-lexical tutorial matching with user feedback integration. The system architecture supports transparent logging for each diagnostic stage, enabling explainability and performance analysis. Results indicate significant improvements in diagnostic efficiency, user satisfaction (4.6/5.0 average rating), and knowledge base evolution (147% growth over 90 days) compared to static expert systems.

**Keywords**: Adaptive diagnostics, self-learning systems, multi-modal reasoning, belief propagation, pattern discovery, vision-language models, knowledge base evolution

---

## I. INTRODUCTION

### A. Background and Motivation

Technical troubleshooting of complex devices represents a fundamental challenge in human-computer interaction and knowledge management systems. Traditional diagnostic approaches rely on static decision trees or rule-based expert systems, which suffer from knowledge obsolescence and inability to adapt to emerging failure patterns [1][2]. The proliferation of diverse laptop models (estimated 12,000+ active SKUs globally) and evolving software ecosystems necessitates diagnostic systems capable of continuous learning and adaptation.

Existing commercial solutions exhibit three critical limitations: (1) exhaustive interrogation requiring 5-8 questions per diagnosis regardless of symptom clarity, (2) inability to leverage visual information from user-provided photographs, and (3) static knowledge bases requiring manual curation by domain experts. These constraints result in suboptimal user experience, with average time-to-diagnosis ranging from 8-15 minutes for simple issues [3].

### B. Problem Formulation

Let S = {s₁, s₂, ..., sₙ} represent the set of observable symptoms, C = {c₁, c₂, ..., cₘ} the set of possible root causes, and Q = {q₁, q₂, ..., qₖ} the set of diagnostic questions. The objective is to construct a mapping function f: S → C that:

1. Minimizes the expected number of questions E[|Q|] required to reach confidence threshold τ
2. Maximizes diagnostic accuracy P(ĉ = c*) where ĉ is predicted cause and c* is ground truth
3. Adapts continuously such that P(ĉ = c* | t + Δt) ≥ P(ĉ = c* | t) for time t

Traditional approaches model f as a static decision tree with fixed branching logic. This work proposes a dynamic Bayesian network that evolves through reinforcement from successful diagnostic sessions.

### C. Research Contributions

This paper makes the following novel contributions to adaptive diagnostic systems:

**1. Context-Conditioned Visual Symptom Extraction**: A methodology for guiding vision-language models using textual context to extract structured symptom representations from unstructured images. Unlike unconditional image captioning, the proposed approach conditions BLIP-2 on user-provided text descriptions, improving error code detection accuracy by 34% and symptom classification F1-score by 0.27 points.

**2. Information-Theoretic Question Selection with Redundancy Elimination**: An algorithm that computes expected information gain for candidate questions while eliminating redundant queries based on already-known information with quantified confidence. The approach reduces average questions-per-diagnosis from 5.3 (baseline) to 1.2 (proposed) while maintaining diagnostic accuracy above 85%.

**3. Online Pattern Discovery with Confidence-Weighted Belief Fusion**: A learning mechanism that discovers symptom-cause patterns from user feedback and integrates them with base knowledge through confidence-weighted averaging. The system demonstrates 92% pattern discovery precision and 147% knowledge base growth over 90-day deployment.

**4. Hybrid Semantic-Lexical Tutorial Matching**: A retrieval system combining dense vector similarity (sentence transformers) with sparse keyword matching, re-ranked by historical user feedback. Achieves NDCG@5 of 0.847 compared to 0.623 for keyword-only baseline.

### D. Paper Organization

The remainder of this paper is organized as follows: Section II reviews related work in expert systems, multi-modal reasoning, and continual learning. Section III presents the mathematical formulation and system architecture. Section IV details the implementation of core components. Section V presents experimental results and comparative analysis. Section VI discusses limitations and future directions, and Section VII concludes.

---

## II. RELATED WORK

### A. Rule-Based Expert Systems

Traditional diagnostic expert systems employ forward or backward chaining over predefined rule sets [4]. MYCIN, one of the earliest medical diagnostic systems, achieved expert-level performance using ~600 hand-crafted rules [5]. However, such systems suffer from the knowledge acquisition bottleneck and brittleness when encountering novel scenarios. More recent systems like Apple Diagnostics and Dell SupportAssist maintain rule bases of 10,000+ entries, requiring continuous manual updates [6].

### B. Multi-Modal Diagnostic Systems

Recent advances in vision-language models enable joint reasoning over text and images. CLIP [7] and BLIP [8] demonstrate strong zero-shot capabilities for image-text matching. However, these models are typically applied to classification tasks rather than structured information extraction. This work extends BLIP-2 [9] through prompt conditioning to extract symptom-specific visual features.

### C. Active Learning and Question Selection

Active learning frameworks select informative samples to query for labels [10]. In diagnostic contexts, this translates to asking questions that maximally reduce uncertainty over possible causes. Entropy-based question selection [11] and expected information gain [12] provide theoretical foundations. However, existing approaches do not account for partial information already known with varying confidence levels.

### D. Continual Learning and Knowledge Base Evolution

Continual learning systems accumulate knowledge over time without catastrophic forgetting [13]. In expert systems, this manifests as case-based reasoning [14] and inductive logic programming [15]. This work differs by learning structured patterns (symptom combinations → causes) rather than individual cases, enabling generalization while maintaining interpretability.

### E. Retrieval-Augmented Generation

Recent work combines dense retrieval with language models for knowledge-intensive tasks [16]. This paper applies similar principles to tutorial retrieval, but incorporates user feedback as an additional signal for re-ranking.

---

## III. METHODOLOGY

### A. Problem Formalization

#### 1) State Space Definition

The diagnostic session state at time t is represented as:

**State Representation:**
```
Ψₜ = (Sₜᵗᵉˣᵗ, Sₜᵛⁱˢ, Bₜ, Qₜ, Θₜ)
```

Where:
- Sₜᵗᵉˣᵗ ∈ ℝᵈ: Symptom embedding from textual input
- Sₜᵛⁱˢ ∈ ℝᵈ: Visual symptom embedding from image
- Bₜ ∈ [0,1]ᵐ: Belief vector over m possible causes
- Qₜ ⊆ Q: Set of questions already asked
- Θₜ: Known metadata (brand, model) with confidence scores

#### 2) Belief Vector Dynamics

The belief vector B evolves according to Bayesian update rules:

**Initial Belief Computation:**
```
B₀(cᵢ) = σ(Σⱼ P(cᵢ|sⱼ) · 𝟙[sⱼ ∈ S₀])
```

Where:
- P(cᵢ|sⱼ): Conditional probability of cause cᵢ given symptom sⱼ
- σ(·): Softmax normalization
- 𝟙[·]: Indicator function

**Update After Question Answer:**
```
Bₜ₊₁(cᵢ) = Bₜ(cᵢ) · P(aₜ₊₁|cᵢ) / P(aₜ₊₁)
```

Where:
- aₜ₊₁: Answer to question qₜ₊₁
- P(aₜ₊₁|cᵢ): Likelihood of answer given cause
- P(aₜ₊₁): Marginal probability of answer

### B. Multi-Modal Input Processing

#### 1) Text Analysis Pipeline

Textual input undergoes the following transformations:

**Keyword Extraction:**
```
K = {k ∈ V : TF-IDF(k, D) > θₖ}
```

Where:
- V: Vocabulary
- D: Input document
- θₖ: Threshold for relevance

**Symptom Classification:**
```
Sᵗᵉˣᵗ = {s : cos(φ(D), φ(s)) > θₛ}
```

Where:
- φ(·): Sentence-BERT embedding [17]
- θₛ: Similarity threshold

**Brand Extraction:**
```
b* = argmax_{b∈B} max_{w∈K} sim(w, lexicon(b))
```

Where:
- B: Set of known brands
- lexicon(b): Brand-specific keywords

#### 2) Context-Conditioned Visual Analysis

The proposed visual analysis conditions image captioning on textual context:

**Conditional Captioning:**
```
p(y|x, c) = Π_{t=1}^T p(yₜ | y₁:ₜ₋₁, x, c; θ)
```

Where:
- x: Image features
- c: Contextual text
- y: Generated caption
- θ: BLIP-2 parameters

**Visual Symptom Extraction:**
```
Sᵛⁱˢ = extract_symptoms(y) ∪ detect_error_codes(y)
```

Error codes are detected via regex patterns:
```
error_code = match(y, "0x[0-9A-F]{8}|[A-Z_]+_ERROR")
```

#### 3) Image Caption Caching

To avoid redundant computation:

**Hash-Based Caching:**
```
h = SHA256(x)
if h ∈ cache:
    return cache[h]
else:
    y = generate_caption(x, c)
    cache[h] ← (y, Sᵛⁱˢ, timestamp)
    return y
```

### C. Adaptive Belief Engine

#### 1) Hybrid Knowledge Integration

The system integrates base knowledge K_base with learned patterns K_learned:

**Pattern Representation:**
```
π = (S_pattern, c, w, n, r)
```

Where:
- S_pattern: Symptom combination
- c: Associated cause
- w ∈ [0,1]: Confidence weight
- n: Support count (observations)
- r ∈ [0,1]: Success rate

**Belief Initialization with Learning:**
```
B₀(cᵢ) = α · P_base(cᵢ|S) + (1-α) · P_learned(cᵢ|S)
```

Where:
```
P_learned(cᵢ|S) = Σ_{π: π.c=cᵢ} w_π · 𝟙[S_π ⊆ S] / Z
```

And:
```
α = exp(-λt)  (decay factor for base knowledge)
```

#### 2) Information-Theoretic Question Selection

Expected information gain for question q:

**Information Gain Computation:**
```
IG(q) = H(C|Ψₜ) - Σ_{a∈A(q)} P(a|Ψₜ) · H(C|Ψₜ, q=a)
```

Where:
```
H(C|Ψ) = -Σᵢ Bₜ(cᵢ) log Bₜ(cᵢ)  (entropy)
```

**Question Filtering:**

A question q is skipped if any condition holds:

1. **Redundancy**: Information already known with high confidence
   ```
   skip(q) ← ∃θ ∈ Θₜ : relevant(q, θ) ∧ conf(θ) > τ_conf
   ```

2. **Low Expected Gain**: Question unlikely to reduce uncertainty
   ```
   skip(q) ← IG(q) < τ_IG
   ```

3. **Irrelevance**: Target causes have negligible probability
   ```
   skip(q) ← max_{cᵢ ∈ affects(q)} Bₜ(cᵢ) < τ_cause
   ```

### D. Online Pattern Discovery

#### 1) Pattern Candidate Generation

After each successful resolution (feedback indicates problem solved):

**Candidate Extraction:**
```
For session ψ with resolution=true:
    Extract: (S_session, c_diagnosed, tutorial_id)
    
    If (S_session, c_diagnosed) ∉ existing_patterns:
        Create candidate: π_new
        π_new.n ← 1
        π_new.successes ← 1
    Else:
        π_existing.n ← π_existing.n + 1
        π_existing.successes ← π_existing.successes + 1
```

**Confidence Calculation:**
```
w(π) = r(π) · (1 - exp(-n(π)/n₀))
```

Where:
- r(π) = successes(π) / n(π): Success rate
- n₀: Confidence saturation constant (typically 5)

#### 2) Pattern Approval and Integration

Patterns meeting quality thresholds are promoted:

**Approval Criteria:**
```
approve(π) ← (n(π) ≥ n_min) ∧ (r(π) ≥ r_min) ∧ (w(π) ≥ w_min)
```

Typical values: n_min = 3, r_min = 0.7, w_min = 0.65

**Knowledge Base Update:**
```
K_learned ← K_learned ∪ {π : approve(π)}
```

#### 3) Question Generation from Ambiguity

New questions are generated from sessions with high initial uncertainty but successful outcomes:

**Candidate Session Selection:**
```
C_ambiguous = {ψ : H(C|Ψ₀) > τ_H ∧ resolution(ψ) = true}
```

**Breakthrough Question Identification:**

For each ψ ∈ C_ambiguous:
```
q* = argmax_{q∈Qᵩ} ΔH(q)
```

Where:
```
ΔH(q) = H(C|Ψ_before(q)) - H(C|Ψ_after(q))
```

Questions appearing frequently as breakthroughs are added to Q.

### E. Hybrid Tutorial Retrieval

#### 1) Multi-Stage Retrieval Pipeline

**Stage 1 - Category Routing:**
```
dataset = route(Θₜ.category)
```

Mapping: {Mac → Mac.json, Dell|HP|Lenovo → PC.json, ...}

**Stage 2 - Dense Retrieval (Vector Search):**
```
score_vec(t) = cos(φ(S), φ(t.description))
```

Where φ(·) is sentence-BERT embedding.

**Stage 3 - Sparse Retrieval (Keyword Matching):**
```
score_lex(t) = |K ∩ t.keywords| / |K ∪ t.keywords|
```

**Stage 4 - Hybrid Scoring:**
```
score_hybrid(t) = β · score_vec(t) + (1-β) · score_lex(t)
```

Empirically, β = 0.6 provides optimal performance.

**Stage 5 - Feedback Re-ranking:**
```
score_final(t) = score_hybrid(t) · (1 + γ · feedback_score(t))
```

Where:
```
feedback_score(t) = Σ_{f∈F(t)} [solved(f) · rating(f)] / |F(t)|
```

#### 2) Matching Explanation Generation

For transparency, the system generates match reasoning:

**Reasoning Structure:**
```
R(t) = {
    "vector_match": top_k_similar_symptoms(t),
    "keyword_match": K ∩ t.keywords,
    "cause_alignment": cos(B, t.cause_vector),
    "historical_performance": feedback_score(t)
}
```

---

## Mathematical Notation Summary

| Symbol | Definition |
|--------|------------|
| S | Set of symptoms |
| C | Set of possible causes |
| Q | Set of diagnostic questions |
| B_t | Belief vector at time t |
| Ψ_t | Session state at time t |
| φ(·) | Sentence embedding function |
| π | Learned pattern |
| w | Confidence weight |
| H(·) | Entropy function |
| IG(q) | Information gain for question q |
| τ | Threshold parameter |
| α | Mixing coefficient |
| β | Hybrid retrieval weight |

---

*[Continue to Part 2 for System Architecture, Implementation, and Results]*
