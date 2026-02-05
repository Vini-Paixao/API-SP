"""
Models Pydantic para a API de Calendário do SPFC.
"""
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime
import hashlib


class Jogo(BaseModel):
    """Representa um jogo do São Paulo FC."""
    
    competicao: str = Field(..., description="Nome da competição (ex: Brasileirão 2026)")
    adversario: str = Field(..., description="Nome do time adversário")
    adversario_logo: Optional[str] = Field(None, description="URL do logo do adversário")
    data: str = Field(..., description="Data do jogo no formato DD/MM/YYYY")
    dia_semana: Optional[str] = Field(None, description="Dia da semana (ex: Quarta)")
    horario: str = Field(..., description="Horário do jogo no formato HH:MM")
    local: Optional[str] = Field(None, description="Estádio/local do jogo")
    mandante: Optional[bool] = Field(None, description="True se SPFC é mandante")
    
    # Campos formatados para Google Calendar
    data_iso: Optional[str] = Field(None, description="Data/hora em formato ISO 8601")
    data_fim_iso: Optional[str] = Field(None, description="Data/hora de fim estimada (2h após início)")
    
    # Controle de sincronização com calendário
    criado_no_calendario: bool = Field(False, description="Se o jogo já foi adicionado ao Google Calendar")
    google_event_id: Optional[str] = Field(None, description="ID do evento no Google Calendar (para remoção)")
    
    @computed_field
    @property
    def jogo_id(self) -> str:
        """ID único do jogo baseado em data + adversário + competição."""
        unique_str = f"{self.data}_{self.horario}_{self.adversario}_{self.competicao}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]


class MarcarJogoRequest(BaseModel):
    """Request para marcar jogo como criado no calendário."""
    
    jogo_id: str = Field(..., description="ID único do jogo")
    google_event_id: Optional[str] = Field(None, description="ID do evento criado no Google Calendar")


class CalendarioResponse(BaseModel):
    """Response do endpoint de calendário."""
    
    sucesso: bool = Field(..., description="Indica se a requisição foi bem sucedida")
    total_jogos: int = Field(..., description="Quantidade total de jogos retornados")
    jogos: List[Jogo] = Field(..., description="Lista de jogos")
    atualizado_em: datetime = Field(..., description="Timestamp da última atualização")
    cache: bool = Field(False, description="Indica se os dados vieram do cache")


class ProximoJogoResponse(BaseModel):
    """Response do endpoint de próximo jogo."""
    
    sucesso: bool = Field(..., description="Indica se a requisição foi bem sucedida")
    jogo: Optional[Jogo] = Field(None, description="Próximo jogo do SPFC")
    atualizado_em: datetime = Field(..., description="Timestamp da última atualização")
    cache: bool = Field(False, description="Indica se os dados vieram do cache")


class ErrorResponse(BaseModel):
    """Response de erro."""
    
    sucesso: bool = Field(False, description="Sempre False para erros")
    erro: str = Field(..., description="Mensagem de erro")
    detalhes: Optional[str] = Field(None, description="Detalhes adicionais do erro")


class HealthResponse(BaseModel):
    """Response do health check."""
    
    status: str = Field(..., description="Status da API")
    versao: str = Field(..., description="Versão da API")
    timestamp: datetime = Field(..., description="Timestamp atual")


class CacheInfoResponse(BaseModel):
    """Informações sobre o estado do cache."""
    
    existe: bool = Field(..., description="Se existe cache salvo")
    ultima_atualizacao: Optional[str] = Field(None, description="Quando o cache foi atualizado")
    total_jogos: Optional[int] = Field(None, description="Quantidade de jogos no cache")
    ultimo_jogo_data: Optional[str] = Field(None, description="Data do último jogo no cache")
    cache_valido: Optional[bool] = Field(None, description="Se o cache ainda é válido")
    proxima_atualizacao: Optional[str] = Field(None, description="Quando será necessário atualizar")
    arquivo: Optional[str] = Field(None, description="Caminho do arquivo de cache")
    mensagem: Optional[str] = Field(None, description="Mensagem informativa")
