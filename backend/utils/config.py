"""Configuration settings for the LectureAI application."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings."""
    
    def __init__(self):
        # API Keys
        self.OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        
        # Database
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/lectureai.db")
        
        # Vector Store
        self.FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./data/embeddings/faiss_index")
        
        # Directories
        self.UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
        self.CHUNKS_DIR: str = os.getenv("CHUNKS_DIR", "./data/chunks")
        
        # Models
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
        
        # OpenRouter API Configuration
        self.OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
        self.APP_URL: str = os.getenv("APP_URL", "http://localhost:8501")
        
        # Chunking Configuration
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        # RAG Configuration
        self.MAX_RETRIEVED_DOCS: int = int(os.getenv("MAX_RETRIEVED_DOCS", "5"))
        self.TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
        
        # Validate critical settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate critical configuration settings."""
        warnings = []
        
        # Check OpenRouter API key
        if not self.OPENROUTER_API_KEY or self.OPENROUTER_API_KEY == "your_openrouter_api_key_here":
            warnings.append("OPENROUTER_API_KEY is not configured. RAG functionality will not work.")
        
        # Check directories exist or can be created
        for dir_path in [self.UPLOAD_DIR, self.CHUNKS_DIR, os.path.dirname(self.FAISS_INDEX_PATH)]:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                warnings.append(f"Cannot create directory {dir_path}: {e}")
        
        # Log warnings
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)
    
    def is_rag_enabled(self) -> bool:
        """Check if RAG functionality is properly configured."""
        return bool(self.OPENROUTER_API_KEY and self.OPENROUTER_API_KEY != "your_openrouter_api_key_here")
    
    def get_status(self) -> dict:
        """Get configuration status."""
        return {
            "openrouter_configured": self.is_rag_enabled(),
            "embedding_model": self.EMBEDDING_MODEL,
            "llm_model": self.LLM_MODEL,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "max_retrieved_docs": self.MAX_RETRIEVED_DOCS,
            "temperature": self.TEMPERATURE
        }

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings
