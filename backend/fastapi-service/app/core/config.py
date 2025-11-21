"""
Configuration settings for Fitmealor FastAPI service
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "Fitmealor AI Service"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fitmealor_user:fitmealor_pass@localhost:5432/fitmealor"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_CACHE_EXPIRY: int = 3600  # 1 hour
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
    ]
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # CLOVA OCR
    CLOVA_OCR_SECRET: str = os.getenv("CLOVA_OCR_SECRET", "")
    CLOVA_OCR_URL: str = os.getenv("CLOVA_OCR_URL", "")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # AI Model Settings
    AI_MODEL_PATH: str = "./models"
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Nutrition Expert Prompt
    NUTRITION_EXPERT_PROMPT: str = """당신은 영양학 전문가입니다.
사용자의 건강 상태와 증상을 분석하여 부족한 영양소를 추론하고, 
해당 영양소가 풍부한 음식을 추천해주세요.
알레르기와 식이 제한 사항을 반드시 고려해야 합니다."""
    
    # Allergen Detection
    ALLERGEN_SIMILARITY_THRESHOLD: float = 0.85
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
