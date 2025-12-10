"""
Database schema for repair procedures.

PostgreSQL table structure following the PRD specification.
"""

from sqlalchemy import (
    Column, Integer, String, Float, JSON, ARRAY, 
    Text, Enum as SQLEnum, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import enum

Base = declarative_base()


class RiskLevel(enum.Enum):
    """Risk classification for repair procedures"""
    safe = "safe"
    medium = "medium"
    high = "high"


class SourceType(enum.Enum):
    """Tutorial source types"""
    OEM = "OEM"
    iFixit = "iFixit"
    YouTube = "YouTube"


class RepairProcedure(Base):
    """
    Core table for storing merged repair procedures.
    
    Schema follows PRD specification:
    | DeviceModel | Issue | SymptomPattern | Cause | Confidence | 
    | Source | Steps | Images | RiskLevel | Tools | Warnings | Recovery |
    """
    __tablename__ = "repair_procedures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Device identification
    device_model = Column(String(100), nullable=False, index=True)
    # Examples: "lenovo_ideapad_5", "dell_xps_15"
    
    # Problem identification
    issue = Column(String(100), nullable=False, index=True)
    # Examples: "no_boot", "screen_flicker", "keyboard_malfunction"
    
    symptom_pattern = Column(JSON, nullable=False)
    # Binary signals array: {"power_led": true, "caps_lock_toggle": false}
    
    # Diagnosis
    cause = Column(String(200), nullable=False)
    # Root cause identifier: "no_boot_power", "keyboard_ribbon_loose"
    
    confidence = Column(Float, nullable=False)
    # Confidence level 0.0-1.0
    
    # Source attribution
    source = Column(String(50), nullable=False)
    # Primary source: "OEM", "iFixit", "YouTube"
    
    # Repair steps (canonical merged sequence)
    steps = Column(JSONB, nullable=False)
    # Array of step objects with full metadata
    # Example: [{"step_id": 1, "action": "...", "tools": [...], ...}]
    
    # Asset paths
    images = Column(ARRAY(Text), nullable=True)
    # Local paths: ["assets/lenovo/ideapad_5/step1.jpg", ...]
    
    # Safety classification
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.safe)
    
    # Required tools
    tools = Column(ARRAY(Text), nullable=True)
    # ["Torx-5", "Plastic spudger", "Anti-static wrist strap"]
    
    # Safety alerts
    warnings = Column(ARRAY(Text), nullable=True)
    # ["Disconnect battery before proceeding", "Avoid ESD damage"]
    
    # Recovery instructions
    recovery = Column(Text, nullable=True)
    # Rollback steps if procedure fails
    
    def __repr__(self):
        return (
            f"<RepairProcedure(model={self.device_model}, "
            f"issue={self.issue}, confidence={self.confidence})>"
        )


class DiagnosticQuestion(Base):
    """
    Questions for adaptive diagnosis workflow.
    
    Used by belief vector engine to narrow down root cause.
    """
    __tablename__ = "diagnostic_questions"
    
    id = Column(String(50), primary_key=True)
    # Example: "q_power_led", "q_caps_lock"
    
    intent = Column(String(100), nullable=False)
    # "check_power", "check_keyboard", "check_display"
    
    question_text = Column(Text, nullable=False)
    # "Does the power LED light up?"
    
    expected_signal = Column(String(50), nullable=False)
    # "yes", "no", "visual", "audio"
    
    cost_level = Column(SQLEnum(RiskLevel), nullable=False)
    # safe, medium, high
    
    confidence_gain_estimate = Column(Float, nullable=False)
    # Expected confidence gain: 0.0-1.0
    
    next_if_yes = Column(String(50), nullable=True)
    # Next question ID if answer is yes
    
    next_if_no = Column(String(50), nullable=True)
    # Next question ID if answer is no
    
    related_causes = Column(ARRAY(Text), nullable=True)
    # Causes this question helps identify
    
    def __repr__(self):
        return f"<DiagnosticQuestion(id={self.id}, intent={self.intent})>"


# Database initialization
def init_db(database_url: str):
    """
    Initialize database schema.
    
    Usage:
        init_db("postgresql://user:pass@localhost:5432/ar_laptop_repair")
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


# Example seed data
SEED_PROCEDURES = [
    {
        "device_model": "lenovo_ideapad_5",
        "issue": "no_boot",
        "symptom_pattern": {
            "power_led": False,
            "fan_spin": False,
            "caps_lock_toggle": False
        },
        "cause": "no_boot_power",
        "confidence": 0.85,
        "source": "OEM",
        "steps": [
            {
                "step_id": 1,
                "action": "Disconnect AC adapter",
                "tools": [],
                "risk_level": "safe",
                "image": "assets/lenovo/ideapad_5/step1_adapter.jpg",
                "warnings": []
            },
            {
                "step_id": 2,
                "action": "Remove battery",
                "tools": ["Torx-5"],
                "risk_level": "safe",
                "image": "assets/lenovo/ideapad_5/step2_battery.jpg",
                "warnings": ["Disconnect power first"]
            }
        ],
        "images": [
            "assets/lenovo/ideapad_5/step1_adapter.jpg",
            "assets/lenovo/ideapad_5/step2_battery.jpg"
        ],
        "risk_level": "safe",
        "tools": ["Torx-5"],
        "warnings": ["Disconnect power before battery removal"],
        "recovery": "Reconnect battery, plug in AC adapter"
    }
]

SEED_QUESTIONS = [
    {
        "id": "q_power_led",
        "intent": "check_power",
        "question_text": "Does the power LED light up when you press the power button?",
        "expected_signal": "yes",
        "cost_level": "safe",
        "confidence_gain_estimate": 0.4,
        "next_if_yes": "q_fan_spin",
        "next_if_no": "q_battery_check",
        "related_causes": ["no_boot_power", "no_boot_motherboard"]
    },
    {
        "id": "q_caps_lock",
        "intent": "check_keyboard",
        "question_text": "Does the CapsLock LED toggle when you press the key?",
        "expected_signal": "yes",
        "cost_level": "safe",
        "confidence_gain_estimate": 0.3,
        "next_if_yes": "q_boot_logo",
        "next_if_no": "q_ram_reseat",
        "related_causes": ["no_boot_display", "no_boot_bios"]
    }
]


if __name__ == "__main__":
    # Example usage
    print("Database schema defined.")
    print(f"Tables: {Base.metadata.tables.keys()}")
