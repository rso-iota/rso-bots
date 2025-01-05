from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    game_port: int = Field(8080, description="Game server port")
    
    # Logging settings
    log_level: str = Field("INFO", description="Logging level")
    
    grpc_port: int = Field(50051, description="gRPC server port")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
