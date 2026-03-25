import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_streamlit_secrets() -> None:
    try:
        import streamlit as st
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ.setdefault(key.upper(), value)
    except Exception:
        pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "CyberMind"
    app_version: str = "1.0.0"
    app_description: str = "AI-Powered Threat Intelligence & Security Analytics Platform"
    debug: bool = False
    log_level: str = "INFO"

    groq_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "cybermind-threats"

    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.2

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    faiss_index_path: str = "data/gold/faiss_index"
    use_pinecone: bool = False

    rag_top_k: int = 5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64

    mitre_attack_url: str = (
        "https://raw.githubusercontent.com/mitre/cti/master/"
        "enterprise-attack/enterprise-attack.json"
    )
    mitre_bronze_path: str = "data/bronze/mitre_attack_raw.json"
    mitre_silver_path: str = "data/silver/mitre_threats_normalized.json"
    mitre_gold_path: str = "data/gold/mitre_threats_enriched.json"

    nvd_cve_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    cve_bronze_path: str = "data/bronze/cve_raw.json"
    cve_silver_path: str = "data/silver/cve_normalized.json"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    risk_score_critical: float = 0.85
    risk_score_high: float = 0.65
    risk_score_medium: float = 0.40


@lru_cache
def get_settings() -> Settings:
    _load_streamlit_secrets()
    return Settings()


settings = get_settings()