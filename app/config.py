"""
Configurações da aplicação.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""
    
    # Firecrawl - Suporta múltiplas API keys separadas por vírgula para load-balance
    firecrawl_api_keys: str = ""  # Múltiplas keys separadas por vírgula
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
    
    @property
    def firecrawl_api_key_list(self) -> List[str]:
        """Retorna lista de API keys do Firecrawl."""
        if not self.firecrawl_api_keys:
            return []
        return [key.strip() for key in self.firecrawl_api_keys.split(",") if key.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
