"""
Application settings and configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "Marketing Strategy Recommender API"
    debug: bool = False
    
    # Supabase Configuration
    supabase_url: str
    supabase_service_role_key: str  # Service role key for backend operations
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # External Services Configuration
    strategy_generator_url: str = "http://localhost:8002"
    trend_agent_url: str = "http://localhost:8001"
    
    # Strategy Generation Settings
    enable_auto_strategy_generation: bool = True  # Generate strategy on form submit
    strategy_relevance_threshold: float = 60.0
    
    class Config:
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        env_file_encoding = "utf-8"

_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings