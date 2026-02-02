"""Application configuration using Pydantic settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Twilio Configuration
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Application
    app_name: str = "Texter"
    debug: bool = False
    
    # Warp Configuration
    warp_api_key: str = ""
    warp_environment_id: str = ""
    warp_model_id: str = "claude-sonnet-4"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
