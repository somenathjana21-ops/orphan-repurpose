from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_PROTOTYPE_DIR = _BACKEND_DIR.parent
_DEFAULT_DATA_DIR = _PROTOTYPE_DIR / "data"
_DEFAULT_MODELS_DIR = _PROTOTYPE_DIR / "models"


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
    DATABASE_URL: str = (
        f"sqlite+aiosqlite:///{(_BACKEND_DIR / 'data' / 'orphan_repurpose.db').as_posix()}"
    )
    KUZU_DB_PATH: str = str(_DEFAULT_DATA_DIR / "kuzu_db")
    CHROMA_DB_PATH: str = str(_DEFAULT_DATA_DIR / "chroma_db")

    # Data paths
    DATA_DIR: str = str(_DEFAULT_DATA_DIR)
    RAW_DATA_DIR: str = str(_DEFAULT_DATA_DIR / "raw")
    PROCESSED_DATA_DIR: str = str(_DEFAULT_DATA_DIR / "processed")
    MODELS_DIR: str = str(_DEFAULT_MODELS_DIR)

    # ML Models
    INDICATION_MODEL_PATH: str = str(_DEFAULT_MODELS_DIR / "indication_model.pt")
    KG_EMBEDDINGS_PATH: str = str(_DEFAULT_MODELS_DIR / "kg_embeddings.pkl")
    BIOMISTRAL_MODEL_PATH: str = str(_DEFAULT_MODELS_DIR / "bioMistral-7b.Q4_K_M.gguf")

    # External APIs (optional for prototype)
    PUBMED_API_KEY: str | None = None
    CHEMBL_API_KEY: str | None = None

    # Security (prototype - no auth)
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"

    # Disclaimer
    DISCLAIMER: str = (
        "RESEARCH PROTOTYPE — Not for clinical use. Outputs require human expert validation."
    )


settings = Settings()
