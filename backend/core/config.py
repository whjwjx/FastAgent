from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAIStack MVP"
    # To run locally without PostgreSQL easily if needed, we can use SQLite for MVP quick test, but PRD specifies PostgreSQL.
    # We will use SQLite for testing if DATABASE_URL is not set, or a default PG URL.
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:15432/fastaistackdb"
    SECRET_KEY: str = "secret-key-for-mvp"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    LLM_MODEL: str = "doubao-1-5-lite-32k-250115"
    
    class Config:
        env_file = ".env"

settings = Settings()
