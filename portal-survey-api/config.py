import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required — no defaults; app will raise ValidationError on startup if missing
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str

    # Optional with safe defaults
    DB_PORT: int = 3306
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    # App Configuration
    APP_NAME: str = "portal-survey-api"
    APP_DEBUG: str = "false"
    APP_PORT: int = 8000
    APP_LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Database Pool Settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "CHANGE_ME"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Initialize settings with error handling
try:
    settings = Settings()
    print(f"✓ Configuration loaded successfully")
    print(f"  - DB_HOST: {settings.DB_HOST}")
    print(f"  - DB_PORT: {settings.DB_PORT}")
    print(f"  - DB_NAME: {settings.DB_NAME}")
    print(f"  - DB_USER: {settings.DB_USER}")
    print(f"  - APP_ENV: {settings.APP_ENV}")
except Exception as e:
    print(f"✗ Configuration error: {e}", file=sys.stderr)
    sys.exit(1)
