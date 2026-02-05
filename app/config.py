"""
Configurações da aplicação.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""
    
    # Firecrawl
    firecrawl_api_key: str = ""
    firecrawl_max_retries: int = 3
    firecrawl_retry_delay: int = 5  # segundos
    
    # API Security
    api_key: str = ""
    
    # Rate Limiting
    rate_limit_requests: int = 30  # requisições
    rate_limit_window: int = 60  # segundos (janela de tempo)
    
    # CORS
    cors_origins: str = "*"  # Origins permitidas (separadas por vírgula)
    
    # Security Headers
    allowed_hosts: str = "*"  # Hosts permitidos (separados por vírgula)
    
    # SPFC
    spfc_calendario_url: str = "https://www.saopaulofc.net/calendario-de-jogos/"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
