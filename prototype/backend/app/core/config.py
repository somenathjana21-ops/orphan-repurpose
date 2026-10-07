from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "OrphanRepurpose API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/orphan_repurpose.db"
    KUZU_DB_PATH: str = "./data/kuzu_db"
    CHROMA_DB_PATH: str = "./data/chroma_db"

    # Data paths
    DATA_DIR: str = "./data"
    RAW_DATA_DIR: str = "./data/raw"
    PROCESSED_DATA_DIR: str = "./data/processed"
    MODELS_DIR: str = "./models"

    # ML Models
    INDICATION_MODEL_PATH: str = "./models/indication_model.pt"
    KG_EMBEDDINGS_PATH: str = "./models/kg_embeddings.pt"
    BIOMISTRAL_MODEL_PATH: str = "./models/bioMistral-7b.Q4_K_M.gguf"

    # External APIs (optional for prototype)
    PUBMED_API_KEY: Optional[str] = None
    CHEMBL_API_KEY: Optional[str] = None

    # Security (prototype - no auth)
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"

    # Disclaimer
    DISCLAIMER: str = "RESEARCH PROTOTYPE — Not for clinical use. Outputs require human expert validation."


settings = Settings()