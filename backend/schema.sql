-- AR Laptop Repair Database Schema
-- PostgreSQL Schema for repair procedures and diagnosis data

-- Drop existing tables if they exist
DROP TABLE IF EXISTS repair_procedures CASCADE;
DROP TABLE IF EXISTS diagnosis_history CASCADE;
DROP TABLE IF EXISTS device_models CASCADE;

-- Device Models Table
CREATE TABLE device_models (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(brand, model)
);

-- Repair Procedures Table (from OEM manuals, iFixit, YouTube)
CREATE TABLE repair_procedures (
    id SERIAL PRIMARY KEY,
    device_model VARCHAR(200) NOT NULL,
    issue VARCHAR(200) NOT NULL,
    symptom_pattern JSONB,
    cause VARCHAR(500) NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    source VARCHAR(50) NOT NULL, -- 'OEM', 'iFixit', 'YouTube'
    steps JSONB NOT NULL,
    images TEXT[],
    risk_level VARCHAR(20) DEFAULT 'safe', -- 'safe', 'medium', 'high'
    tools TEXT[],
    warnings TEXT[],
    recovery TEXT,
    easy_fix TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnosis History Table (for learning system)
CREATE TABLE diagnosis_history (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    device_model VARCHAR(200) NOT NULL,
    symptoms TEXT NOT NULL,
    questions_asked JSONB,
    answers JSONB,
    final_diagnosis VARCHAR(500),
    confidence FLOAT,
    source_contributions JSONB,
    success BOOLEAN DEFAULT NULL,
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX idx_repair_device ON repair_procedures(device_model);
CREATE INDEX idx_repair_issue ON repair_procedures(issue);
CREATE INDEX idx_repair_source ON repair_procedures(source);
CREATE INDEX idx_diagnosis_session ON diagnosis_history(session_id);
CREATE INDEX idx_diagnosis_device ON diagnosis_history(device_model);
CREATE INDEX idx_diagnosis_created ON diagnosis_history(created_at DESC);

-- Insert sample device models
INSERT INTO device_models (brand, model, product_id) VALUES
('Lenovo', 'IdeaPad 5', 'lenovo_ideapad_5'),
('Dell', 'XPS 15', 'dell_xps_15'),
('HP', 'Pavilion', 'hp_pavilion'),
('Lenovo', 'ThinkPad X1', 'lenovo_thinkpad_x1');

-- Insert sample repair procedures (from your ingested data)
INSERT INTO repair_procedures (
    device_model, issue, symptom_pattern, cause, confidence, source,
    steps, images, risk_level, tools, warnings, recovery, easy_fix
) VALUES
(
    'lenovo_ideapad_5',
    'no_boot_power',
    '{"power_led": false, "fan_noise": false, "screen": false}'::jsonb,
    'Battery disconnected or power supply failure',
    0.85,
    'OEM',
    '[
        {"step": 1, "action": "Turn off laptop and unplug power"},
        {"step": 2, "action": "Remove bottom cover (8x Torx-5 screws)"},
        {"step": 3, "action": "Check battery connection cable"},
        {"step": 4, "action": "Reconnect battery if loose"},
        {"step": 5, "action": "Replace battery if swollen/damaged"}
    ]'::jsonb,
    ARRAY['assets/lenovo/ideapad_5/bottom_cover.jpg', 'assets/lenovo/ideapad_5/battery_connector.jpg'],
    'safe',
    ARRAY['Torx-5 screwdriver', 'Plastic spudger'],
    ARRAY['Disconnect power before opening', 'Handle battery carefully'],
    'If problem persists, check motherboard connections',
    'Try unplugging laptop for 30 seconds, then reconnect power and battery'
),
(
    'lenovo_ideapad_5',
    'keyboard_not_working',
    '{"keys_stuck": true, "some_keys_work": false}'::jsonb,
    'Keyboard cable disconnected or keyboard failure',
    0.75,
    'iFixit',
    '[
        {"step": 1, "action": "Power off laptop"},
        {"step": 2, "action": "Remove bottom cover"},
        {"step": 3, "action": "Locate keyboard ribbon cable"},
        {"step": 4, "action": "Disconnect and reconnect cable"},
        {"step": 5, "action": "Test keyboard, replace if needed"}
    ]'::jsonb,
    ARRAY['assets/lenovo/ideapad_5/keyboard_cable.jpg'],
    'medium',
    ARRAY['Torx-5 screwdriver', 'Plastic spudger'],
    ARRAY['Be gentle with ribbon cable', 'Take photo before disconnecting'],
    'Order replacement keyboard if needed',
    'Clean keyboard with compressed air first'
),
(
    'dell_xps_15',
    'overheating',
    '{"fan_loud": true, "hot_bottom": true, "throttling": true}'::jsonb,
    'Dust buildup in cooling system',
    0.90,
    'YouTube',
    '[
        {"step": 1, "action": "Power off and unplug"},
        {"step": 2, "action": "Remove bottom panel (Torx-5)"},
        {"step": 3, "action": "Clean fan with compressed air"},
        {"step": 4, "action": "Replace thermal paste on CPU/GPU"},
        {"step": 5, "action": "Reassemble and test"}
    ]'::jsonb,
    ARRAY['assets/dell/xps_15/fan_cleaning.jpg'],
    'medium',
    ARRAY['Torx-5 screwdriver', 'Compressed air', 'Thermal paste', 'Isopropyl alcohol'],
    ARRAY['Do not spin fan with compressed air', 'Apply thin layer of thermal paste'],
    'If overheating continues, check for BIOS updates',
    'Use laptop on hard flat surface, elevate back slightly'
);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_repair_procedures_updated_at
    BEFORE UPDATE ON repair_procedures
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

COMMENT ON TABLE repair_procedures IS 'Stores repair procedures from OEM manuals, iFixit guides, and YouTube tutorials';
COMMENT ON TABLE diagnosis_history IS 'Stores diagnosis sessions for machine learning and improvement';
COMMENT ON TABLE device_models IS 'Master list of supported laptop models';
