from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Game server settings
    game_server_url: str = Field(..., description="Game server WebSocket URL")
    game_id: str = Field(..., description="Game ID to connect to")
    
    # Bot settings
    initial_bots: int = Field(3, description="Number of bots to start with")
    bot_name_prefix: str = Field("Bot", description="Prefix for bot names")
    bot_move_interval: float = Field(0.1, description="Interval between bot moves in seconds")
    
    # Logging settings
    log_level: str = Field("INFO", description="Logging level")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")