"""
Personal Control Config
Your command brain for the entire system.
"""
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PersonalConfig:
    """Your personal control settings."""
    
    # Mode
    mode: str = "personal"
    
    # Default content settings
    default_persona: str = "fast_explainer"
    default_visual_style: str = "cinematic_dark"
    default_genre: str = "facts"
    default_audience: str = "genz_us"
    
    # Platform priority
    platform_priority: str = "youtube_shorts"
    
    # Output targets
    daily_output_target: int = 5
    batch_size: int = 10
    
    # Risk / creativity
    risk_tolerance: str = "medium"  # low, medium, high
    creativity_level: float = 0.7
    
    # Speed mode
    speed_mode: bool = False
    preview_resolution: str = "low"  # low, medium, high
    
    # Quality thresholds
    min_quality_score: float = 0.70
    auto_reject_below: float = 0.60
    
    # Active playbook
    active_playbook: str = ""


CONFIG_PATH = Path("config/personal_config.yaml")


def load_config() -> PersonalConfig:
    """Load personal config from file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
            return PersonalConfig(**data)
    return PersonalConfig()


def save_config(config: PersonalConfig):
    """Save personal config to file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(asdict(config), f, default_flow_style=False)
    logger.info(f"Saved personal config to {CONFIG_PATH}")


def update_config(**kwargs) -> PersonalConfig:
    """Update specific config values."""
    config = load_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    save_config(config)
    return config


def display_config():
    """Display current config."""
    config = load_config()
    print("\n" + "=" * 50)
    print("  PERSONAL CONTROL CONFIG")
    print("=" * 50)
    for key, value in asdict(config).items():
        print(f"  {key}: {value}")
    print("=" * 50)


# Create default config on import
if not CONFIG_PATH.exists():
    save_config(PersonalConfig())
