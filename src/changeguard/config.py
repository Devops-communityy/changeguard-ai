from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHANGEGUARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    openai_api_key: SecretStr | None = None
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    github_token: SecretStr | None = None
    github_repository: str = ""
    prometheus_url: str = "http://prometheus.monitoring.svc:9090"
    argocd_url: str = "https://argocd-server.argocd.svc"
    argocd_token: SecretStr | None = None
    argocd_verify_tls: bool = True
    kubernetes_context: str | None = None
    kubernetes_namespace: str = "changeguard-demo"
    chroma_path: Path = Path("data/chroma")
    knowledge_path: Path = Path("knowledge")
    audit_path: Path = Path("data/audit.jsonl")
    approval_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    demo_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
