-- PostgreSQL Schema for AR Laptop Troubleshooter
-- Clean, normalized design for tutorial storage

-- Main tutorials table
CREATE TABLE IF NOT EXISTS tutorials (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    issue_type VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    keywords TEXT[] NOT NULL,  -- For vector search matching
    source VARCHAR(20) NOT NULL,  -- 'oem', 'ifixit'
    source_id VARCHAR(100),
    source_url TEXT,
    difficulty VARCHAR(20),  -- 'easy', 'moderate', 'hard'
    estimated_time_minutes INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tutorial steps (ordered)
CREATE TABLE IF NOT EXISTS tutorial_steps (
    id SERIAL PRIMARY KEY,
    tutorial_id INT NOT NULL REFERENCES tutorials(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    title VARCHAR(200),
    description TEXT NOT NULL,
    image_url TEXT,  -- URL to step image
    video_timestamp VARCHAR(50),  -- For YouTube sources: "03:20-03:45"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tutorial_id, step_number)
);

-- Required tools
CREATE TABLE IF NOT EXISTS tutorial_tools (
    id SERIAL PRIMARY KEY,
    tutorial_id INT NOT NULL REFERENCES tutorials(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    tool_type VARCHAR(50),  -- 'screwdriver', 'pry_tool', 'thermal_paste', etc.
    is_optional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warnings and safety notes
CREATE TABLE IF NOT EXISTS tutorial_warnings (
    id SERIAL PRIMARY KEY,
    tutorial_id INT NOT NULL REFERENCES tutorials(id) ON DELETE CASCADE,
    warning_text TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'danger'
    step_number INT,  -- NULL for general warnings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions for user interactions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    user_query TEXT NOT NULL,
    brand VARCHAR(50),
    image_analysis TEXT,  -- BLIP model output
    selected_tutorial_id INT REFERENCES tutorials(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant'
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tutorials_brand ON tutorials(brand);
CREATE INDEX IF NOT EXISTS idx_tutorials_issue ON tutorials(issue_type);
CREATE INDEX IF NOT EXISTS idx_tutorials_keywords ON tutorials USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_steps_tutorial ON tutorial_steps(tutorial_id, step_number);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, created_at);

-- Comments
COMMENT ON TABLE tutorials IS 'Main tutorial repository from OEM manuals and iFixit';
COMMENT ON TABLE tutorial_steps IS 'Step-by-step repair instructions with images';
COMMENT ON TABLE tutorial_tools IS 'Tools required for each tutorial';
COMMENT ON TABLE tutorial_warnings IS 'Safety warnings and important notes';
COMMENT ON TABLE chat_sessions IS 'User diagnostic sessions';
COMMENT ON TABLE chat_messages IS 'Chat conversation history';
