-- Learning and Feedback Schema for Self-Improving System
-- Tracks user interactions, outcomes, and discovered patterns

-- User diagnostic sessions (conversation state)
CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    user_id VARCHAR(100),  -- Optional user identification
    device_category VARCHAR(50),  -- 'PC', 'Mac', 'Phone', etc.
    brand VARCHAR(50),
    brand_confidence FLOAT,
    model VARCHAR(100),
    initial_input_text TEXT,
    initial_input_image_url TEXT,  -- Stored image path
    initial_symptoms TEXT[],  -- From text analysis
    visual_symptoms TEXT[],  -- From BLIP
    final_diagnosis VARCHAR(100),  -- Top cause after questions
    final_confidence FLOAT,
    questions_asked INT DEFAULT 0,
    tutorial_selected_id INT REFERENCES tutorials(id),
    problem_resolved BOOLEAN,  -- Did tutorial solve the issue?
    resolution_time_minutes INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Detailed log of each diagnostic step (for frontend display)
CREATE TABLE IF NOT EXISTS diagnostic_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE,
    log_order INT NOT NULL,
    stage VARCHAR(50) NOT NULL,  -- 'input_processing', 'belief_update', 'question_asked', etc.
    action VARCHAR(100) NOT NULL,
    data JSONB,  -- Flexible storage for any log data
    confidence FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, log_order)
);

-- Belief vector updates during session
CREATE TABLE IF NOT EXISTS belief_snapshots (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE,
    snapshot_order INT NOT NULL,
    belief_vector JSONB NOT NULL,  -- {"thermal_issue": 0.75, "memory_issue": 0.45, ...}
    trigger_event VARCHAR(100),  -- 'initial', 'question_answered', 'image_analyzed'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, snapshot_order)
);

-- Questions asked and answers received
CREATE TABLE IF NOT EXISTS question_interactions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE,
    question_id VARCHAR(100) NOT NULL,  -- From questions.json or learned_questions
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL,  -- 'binary', 'choice', 'text_input'
    answer TEXT,  -- User's response
    answer_timestamp TIMESTAMP,
    belief_change JSONB,  -- Before/after belief vector
    information_gain FLOAT,  -- How much did this question help?
    was_skipped BOOLEAN DEFAULT FALSE,
    skip_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tutorial matches and rankings
CREATE TABLE IF NOT EXISTS tutorial_matches (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE,
    tutorial_id INT NOT NULL REFERENCES tutorials(id),
    match_rank INT NOT NULL,  -- 1st, 2nd, 3rd match
    vector_score FLOAT,  -- Weaviate similarity score
    keyword_score FLOAT,  -- PostgreSQL keyword match score
    combined_score FLOAT,  -- Final weighted score
    match_reasoning JSONB,  -- Why this was matched
    was_selected BOOLEAN DEFAULT FALSE,
    was_helpful BOOLEAN,  -- User feedback
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, tutorial_id)
);

-- User feedback on tutorials
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(session_id),
    tutorial_id INT NOT NULL REFERENCES tutorials(id),
    solved_problem BOOLEAN NOT NULL,
    clarity_rating INT CHECK (clarity_rating BETWEEN 1 AND 5),
    accuracy_rating INT CHECK (accuracy_rating BETWEEN 1 AND 5),
    completion_percentage INT CHECK (completion_percentage BETWEEN 0 AND 100),
    time_spent_minutes INT,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learned symptom-to-cause patterns (discovered from successful resolutions)
CREATE TABLE IF NOT EXISTS learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'PC', 'Mac', 'Phone'
    symptom_combination TEXT[],  -- ['blue_screen', 'fan_noise', 'high_performance']
    cause VARCHAR(100) NOT NULL,  -- 'thermal_issue'
    confidence FLOAT NOT NULL,  -- 0.0 - 1.0
    support_count INT DEFAULT 1,  -- How many times seen
    success_rate FLOAT,  -- % of times tutorial solved the problem
    average_resolution_time INT,  -- Minutes
    source VARCHAR(20) DEFAULT 'learned',  -- 'base', 'learned'
    first_discovered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT FALSE  -- Human review flag
);

-- Learned questions (generated from common unclear cases)
CREATE TABLE IF NOT EXISTS learned_questions (
    id SERIAL PRIMARY KEY,
    question_id VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    issue_context VARCHAR(100) NOT NULL,  -- 'display_issues', 'thermal_issues'
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL,
    intent VARCHAR(100),
    affects_causes TEXT[],  -- Which causes this question helps discriminate
    yes_updates JSONB,  -- Belief updates for 'yes' answer
    no_updates JSONB,  -- Belief updates for 'no' answer
    information_gain_avg FLOAT,  -- Average usefulness
    times_asked INT DEFAULT 0,
    times_helpful INT DEFAULT 0,  -- When answer led to successful resolution
    source VARCHAR(20) DEFAULT 'learned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT FALSE
);

-- Pattern discovery candidates (potential new patterns awaiting validation)
CREATE TABLE IF NOT EXISTS pattern_candidates (
    id SERIAL PRIMARY KEY,
    symptom_combination TEXT[],
    cause VARCHAR(100),
    category VARCHAR(50),
    observed_count INT DEFAULT 1,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    confidence FLOAT,
    supporting_session_ids UUID[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT FALSE
);

-- Question effectiveness tracking (for pruning low-value questions)
CREATE TABLE IF NOT EXISTS question_analytics (
    question_id VARCHAR(100) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    times_asked INT DEFAULT 0,
    times_skipped INT DEFAULT 0,
    avg_information_gain FLOAT,
    avg_belief_change FLOAT,  -- How much it changed beliefs
    correlation_with_success FLOAT,  -- Does asking this lead to resolution?
    last_asked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Image caption cache (avoid re-analyzing same images)
CREATE TABLE IF NOT EXISTS image_caption_cache (
    id SERIAL PRIMARY KEY,
    image_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 of image
    image_url TEXT,
    blip_caption TEXT NOT NULL,
    visual_symptoms TEXT[],
    context_text TEXT,  -- User's text that conditioned BLIP
    model_version VARCHAR(50),  -- Track BLIP model version
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES for performance
CREATE INDEX idx_diagnostic_sessions_brand ON diagnostic_sessions(brand);
CREATE INDEX idx_diagnostic_sessions_category ON diagnostic_sessions(device_category);
CREATE INDEX idx_diagnostic_sessions_created ON diagnostic_sessions(created_at);
CREATE INDEX idx_diagnostic_sessions_resolved ON diagnostic_sessions(problem_resolved);

CREATE INDEX idx_diagnostic_logs_session ON diagnostic_logs(session_id, log_order);
CREATE INDEX idx_diagnostic_logs_stage ON diagnostic_logs(stage);

CREATE INDEX idx_belief_snapshots_session ON belief_snapshots(session_id, snapshot_order);

CREATE INDEX idx_question_interactions_session ON question_interactions(session_id);
CREATE INDEX idx_question_interactions_question ON question_interactions(question_id);

CREATE INDEX idx_tutorial_matches_session ON tutorial_matches(session_id);
CREATE INDEX idx_tutorial_matches_tutorial ON tutorial_matches(tutorial_id);
CREATE INDEX idx_tutorial_matches_selected ON tutorial_matches(was_selected);

CREATE INDEX idx_user_feedback_tutorial ON user_feedback(tutorial_id);
CREATE INDEX idx_user_feedback_solved ON user_feedback(solved_problem);

CREATE INDEX idx_learned_patterns_category ON learned_patterns(category);
CREATE INDEX idx_learned_patterns_cause ON learned_patterns(cause);
CREATE INDEX idx_learned_patterns_confidence ON learned_patterns(confidence);
CREATE INDEX idx_learned_patterns_approved ON learned_patterns(approved);

CREATE INDEX idx_learned_questions_category ON learned_questions(category);
CREATE INDEX idx_learned_questions_context ON learned_questions(issue_context);
CREATE INDEX idx_learned_questions_approved ON learned_questions(approved);

CREATE INDEX idx_pattern_candidates_category ON pattern_candidates(category);
CREATE INDEX idx_pattern_candidates_reviewed ON pattern_candidates(reviewed);

CREATE INDEX idx_image_caption_hash ON image_caption_cache(image_hash);

-- GIN indexes for array columns
CREATE INDEX idx_learned_patterns_symptoms ON learned_patterns USING GIN(symptom_combination);
CREATE INDEX idx_pattern_candidates_symptoms ON pattern_candidates USING GIN(symptom_combination);
CREATE INDEX idx_diagnostic_sessions_symptoms ON diagnostic_sessions USING GIN(initial_symptoms);
