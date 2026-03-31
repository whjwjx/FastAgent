from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAgent MVP"
    # To run locally without PostgreSQL easily if needed, we can use SQLite for MVP quick test, but PRD specifies PostgreSQL.
    # We will use SQLite for testing if DATABASE_URL is not set, or a default PG URL.
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:15432/fastagentdb"
    SECRET_KEY: str = "your-secret-key-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    LLM_MODEL_PRO: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None
    
    # Search API
    TAVILY_API_KEY: Optional[str] = None
    
    def get_routing_model(self, text: str) -> str:
        # 简单的多模型切换架构：
        # 如果文本较长或包含复杂的指令特征，则使用 PRO 模型以保证提取准确率，否则使用 LITE 模型以降低成本。
        complex_keywords = ["总结", "分析", "提取", "提取出", "详细", "翻译"]
        
        # 优先使用配置的模型，如果没有配置则返回空字符串或抛出异常
        model_pro = self.LLM_MODEL_PRO or self.LLM_MODEL or ""
        model_lite = self.LLM_MODEL or ""
        
        if len(text) > 500 or any(kw in text for kw in complex_keywords):
            return model_pro
        return model_lite
    
    class Config:
        env_file = ".env"

settings = Settings()
