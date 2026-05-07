"""Production-ready configuration with mandatory validation"""

import os
import sys
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import requests


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    app_name: str = Field(default="CivicScheme AI")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Mistral AI
    mistral_api_key: str = Field(default=None)
    
    # AI Models
    embedding_model: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embedding_dimension: int = Field(default=384)
    llm_model: str = Field(default="mistral-tiny")
    
    # Web Search
    tavily_api_key: Optional[str] = Field(default=None)
    
    database_url: str = Field(default="sqlite:///./data/app.db")
    
    # Auth
    secret_key: str = Field(default="v8r9p2-civicscheme-secret-key-3n4m5")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440) # 24 hours
    
    # Supported languages
    supported_languages: list = Field(default=["en", "hi", "ta", "te", "kn", "ml", "bn", "gu", "mr", "pa", "or"])
    default_language: str = Field(default="en")
    
    @field_validator('mistral_api_key')
    @classmethod
    def validate_mistral_key(cls, v: str) -> str:
        """Validate Mistral API key presence"""
        if not v:
            raise ValueError("Mistral API key is required")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with validation"""
    try:
        return Settings()
    except Exception as e:
        print(f"\n[ERROR] Configuration Error: {str(e)}\n")
        print("Please ensure you have a .env file with required variables:")
        print("  - MISTRAL_API_KEY (required)")
        print("\nSee .env.example for template\n")
        sys.exit(1)


def validate_mistral_api_connection(api_key: str) -> bool:
    # Validate key using the models endpoint
    test_url = "https://api.mistral.ai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(
            test_url,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            print(f"\n[ERROR] Mistral API Key is INVALID")
            print(f"Response: {response.text}")
            return False
        elif response.status_code == 200:
            print(f"[SUCCESS] Mistral API connection validated")
            return True
        else:
            print(f"[WARNING] Unexpected response from Mistral API: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("[WARNING] Mistral API timeout (check internet connection)")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to validate Mistral API: {str(e)}")
        return False


settings = get_settings()
