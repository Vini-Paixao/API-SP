"""
Rotas da API de Calendário do SPFC.
"""
from fastapi import APIRouter, Depends, HTTPException, Security, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional

from app.config import get_settings, Settings
from app.models import (
    CalendarioResponse,
    ProximoJogoResponse,
    ErrorResponse,
    CacheInfoResponse,
    MarcarJogoRequest,
)
from app.scraper import (
    scrape_calendario, 
    limpar_cache, 
    obter_info_cache,
    ordenar_jogos,
    filtrar_jogos_futuros,
    filtrar_jogos_semana,
    marcar_jogo_no_calendario,
    desmarcar_jogo_do_calendario,
    obter_jogos_no_calendario,
    obter_jogos_passados_no_calendario,
)

router = APIRouter(prefix="/api", tags=["Calendário SPFC"])

# Security
security = HTTPBearer()


async def verificar_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    settings: Settings = Depends(get_settings)
) -> bool:
    """Verifica se a API key é válida."""
    if not settings.api_key:
        raise HTTPException(
            status_code=500,
            detail="API_KEY não configurada no servidor"
        )
    
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key inválida"
        )
    
    return True


@router.get(
    "/jogos",
    response_model=CalendarioResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        500: {"model": ErrorResponse, "description": "Erro interno"},
    },
    summary="Listar todos os jogos",
    description="""
    Retorna os jogos do calendário do São Paulo FC extraídos da página oficial.
    
    Parâmetros:
    - **apenas_futuros**: Filtra apenas jogos que ainda não aconteceram (recomendado para Google Calendar)
    - **force_refresh**: Ignora o cache e faz nova requisição ao Firecrawl (gasta créditos)
    """
)
async def listar_jogos(
    force_refresh: bool = Query(
        False, 
        description="Se True, ignora o cache e faz novo scraping"
    ),
    apenas_futuros: bool = Query(
        True,
        description="Se True, retorna apenas jogos que ainda não aconteceram"
    ),
    _: bool = Depends(verificar_api_key)
):
    """Lista todos os jogos do calendário do SPFC."""
    try:
        jogos, from_cache = await scrape_calendario(force_refresh=force_refresh)
        
        # Ordenar por data
        jogos = ordenar_jogos(jogos)
        
        # Filtrar apenas futuros se solicitado
        if apenas_futuros:
            jogos = filtrar_jogos_futuros(jogos)
        
        return CalendarioResponse(
            sucesso=True,
            total_jogos=len(jogos),
            jogos=jogos,
            atualizado_em=datetime.now(),
            cache=from_cache
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar jogos: {str(e)}"
        )


@router.get(
    "/proximo-jogo",
    response_model=ProximoJogoResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Nenhum jogo encontrado"},
        500: {"model": ErrorResponse, "description": "Erro interno"},
    },
    summary="Próximo jogo",
    description="Retorna apenas o próximo jogo do São Paulo FC."
)
async def proximo_jogo(
    force_refresh: bool = Query(
        False, 
        description="Se True, ignora o cache e faz novo scraping"
    ),
    _: bool = Depends(verificar_api_key)
):
    """Retorna o próximo jogo do SPFC."""
    try:
        jogos, from_cache = await scrape_calendario(force_refresh=force_refresh)
        
        # Ordenar e filtrar apenas futuros
        jogos = ordenar_jogos(jogos)
        jogos = filtrar_jogos_futuros(jogos)
        
        if not jogos:
            raise HTTPException(
                status_code=404,
                detail="Nenhum jogo futuro encontrado no calendário"
            )
        
        # Retornar o primeiro jogo (já ordenado por data)
        return ProximoJogoResponse(
            sucesso=True,
            jogo=jogos[0],
            atualizado_em=datetime.now(),
            cache=from_cache
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar próximo jogo: {str(e)}"
        )


@router.get(
    "/jogos/semana",
    response_model=CalendarioResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        500: {"model": ErrorResponse, "description": "Erro interno"},
    },
    summary="Jogos da semana",
    description="""
    Retorna os jogos que acontecem nas próximas semanas.
    
    Perfeito para integração com n8n/Google Calendar em workflows semanais.
    Por padrão retorna jogos da próxima semana (7 dias).
    """
)
async def jogos_da_semana(
    semanas: int = Query(
        1,
        ge=1,
        le=8,
        description="Número de semanas a considerar (1-8)"
    ),
    force_refresh: bool = Query(
        False, 
        description="Se True, ignora o cache e faz novo scraping"
    ),
    _: bool = Depends(verificar_api_key)
):
    """Retorna jogos das próximas N semanas."""
    try:
        jogos, from_cache = await scrape_calendario(force_refresh=force_refresh)
        
        # Ordenar e filtrar jogos da semana
        jogos = ordenar_jogos(jogos)
        jogos = filtrar_jogos_semana(jogos, semanas=semanas)
        
        return CalendarioResponse(
            sucesso=True,
            total_jogos=len(jogos),
            jogos=jogos,
            atualizado_em=datetime.now(),
            cache=from_cache
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar jogos da semana: {str(e)}"
        )


@router.get(
    "/jogos/semana/pendentes",
    response_model=CalendarioResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        500: {"model": ErrorResponse, "description": "Erro interno"},
    },
    summary="Jogos da semana pendentes de criação",
    description="""
    Retorna jogos da semana que ainda NÃO foram adicionados ao Google Calendar.
    
    Combina os filtros de:
    - Jogos das próximas N semanas
    - Jogos ainda não criados no calendário (criado_no_calendario = false)
    
    Perfeito para workflow semanal do n8n:
    1. Chamar este endpoint
    2. Para cada jogo, criar evento no Calendar
    3. Chamar POST /api/jogos/{jogo_id}/marcar-calendario
    """
)
async def jogos_semana_pendentes(
    semanas: int = Query(
        1,
        ge=1,
        le=8,
        description="Número de semanas a considerar (1-8)"
    ),
    force_refresh: bool = Query(
        False, 
        description="Se True, ignora o cache e faz novo scraping"
    ),
    _: bool = Depends(verificar_api_key)
):
    """Retorna jogos da semana que ainda não foram criados no calendário."""
    try:
        jogos, from_cache = await scrape_calendario(force_refresh=force_refresh)
        
        # Ordenar e filtrar jogos da semana
        jogos = ordenar_jogos(jogos)
        jogos = filtrar_jogos_semana(jogos, semanas=semanas)
        
        # Filtrar apenas não criados no calendário
        jogos = [j for j in jogos if not j.criado_no_calendario]
        
        return CalendarioResponse(
            sucesso=True,
            total_jogos=len(jogos),
            jogos=jogos,
            atualizado_em=datetime.now(),
            cache=from_cache
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar jogos da semana pendentes: {str(e)}"
        )


@router.post(
    "/cache/limpar",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
    },
    summary="Limpar cache",
    description="Limpa o cache de jogos, forçando novo scraping na próxima requisição."
)
async def limpar_cache_endpoint(_: bool = Depends(verificar_api_key)):
    """Limpa o cache de jogos."""
    limpar_cache()
    return {
        "sucesso": True,
        "mensagem": "Cache limpo com sucesso",
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/cache/status",
    response_model=CacheInfoResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
    },
    summary="Status do cache",
    description="""
    Retorna informações sobre o estado atual do cache.
    
    O cache é considerado válido enquanto o último jogo armazenado não tiver passado.
    Isso significa que a API só fará nova requisição ao Firecrawl (gastando créditos)
    quando todos os jogos do cache já tiverem acontecido.
    """
)
async def status_cache(_: bool = Depends(verificar_api_key)):
    """Retorna status do cache."""
    info = obter_info_cache()
    return CacheInfoResponse(**info)


# =============================================================================
# Endpoints de Controle do Google Calendar
# =============================================================================

@router.post(
    "/jogos/{jogo_id}/marcar-calendario",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Jogo não encontrado"},
    },
    summary="Marcar jogo como criado no calendário",
    description="""
    Marca um jogo como já adicionado ao Google Calendar.
    
    Use este endpoint após criar o evento no Calendar via n8n.
    O jogo não será retornado novamente em requisições com filtro de não-criados.
    """
)
async def marcar_jogo_calendario(
    jogo_id: str = Path(..., description="ID único do jogo (campo jogo_id)"),
    request: Optional[MarcarJogoRequest] = None,
    _: bool = Depends(verificar_api_key)
):
    """Marca jogo como criado no calendário."""
    google_event_id = request.google_event_id if request else None
    
    sucesso = marcar_jogo_no_calendario(jogo_id, google_event_id)
    
    if not sucesso:
        raise HTTPException(
            status_code=404,
            detail=f"Jogo com ID '{jogo_id}' não encontrado"
        )
    
    return {
        "sucesso": True,
        "mensagem": f"Jogo {jogo_id} marcado como criado no calendário",
        "google_event_id": google_event_id,
        "timestamp": datetime.now().isoformat()
    }


@router.delete(
    "/jogos/{jogo_id}/calendario",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
        404: {"model": ErrorResponse, "description": "Jogo não encontrado ou não está no calendário"},
    },
    summary="Desmarcar jogo do calendário",
    description="""
    Desmarca um jogo do calendário (para quando o evento for removido do Google Calendar).
    
    Retorna o google_event_id para que o n8n possa remover o evento do Calendar.
    """
)
async def desmarcar_jogo_calendario(
    jogo_id: str = Path(..., description="ID único do jogo"),
    _: bool = Depends(verificar_api_key)
):
    """Desmarca jogo do calendário."""
    google_event_id = desmarcar_jogo_do_calendario(jogo_id)
    
    if not google_event_id:
        raise HTTPException(
            status_code=404,
            detail=f"Jogo com ID '{jogo_id}' não encontrado ou não está no calendário"
        )
    
    return {
        "sucesso": True,
        "mensagem": f"Jogo {jogo_id} desmarcado do calendário",
        "google_event_id": google_event_id,
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/jogos/calendario",
    response_model=CalendarioResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
    },
    summary="Jogos no calendário",
    description="""
    Retorna todos os jogos que estão marcados como criados no Google Calendar.
    
    Útil para verificar quais jogos já foram sincronizados.
    """
)
async def listar_jogos_calendario(_: bool = Depends(verificar_api_key)):
    """Lista jogos que estão no calendário."""
    jogos = obter_jogos_no_calendario()
    jogos = ordenar_jogos(jogos)
    
    return CalendarioResponse(
        sucesso=True,
        total_jogos=len(jogos),
        jogos=jogos,
        atualizado_em=datetime.now(),
        cache=True
    )


@router.get(
    "/jogos/calendario/limpar",
    response_model=CalendarioResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
    },
    summary="Jogos passados para limpar do calendário",
    description="""
    Retorna jogos que já passaram mas ainda estão marcados no calendário.
    
    Perfeito para workflow de limpeza:
    1. Chamar este endpoint
    2. Para cada jogo, usar o google_event_id para deletar do Calendar
    3. Chamar DELETE /api/jogos/{jogo_id}/calendario para desmarcar
    
    Isso mantém seu calendário limpo, removendo jogos antigos automaticamente.
    """
)
async def listar_jogos_para_limpar(_: bool = Depends(verificar_api_key)):
    """Lista jogos passados que precisam ser removidos do calendário."""
    jogos = obter_jogos_passados_no_calendario()
    jogos = ordenar_jogos(jogos)
    
    return CalendarioResponse(
        sucesso=True,
        total_jogos=len(jogos),
        jogos=jogos,
        atualizado_em=datetime.now(),
        cache=True
    )


@router.get(
    "/jogos/pendentes",
    response_model=CalendarioResponse,
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida"},
    },
    summary="Jogos pendentes (não estão no calendário)",
    description="""
    Retorna jogos futuros que ainda NÃO foram adicionados ao Google Calendar.
    
    Perfeito para workflow de criação:
    1. Chamar este endpoint
    2. Para cada jogo, criar evento no Calendar
    3. Chamar POST /api/jogos/{jogo_id}/marcar-calendario
    """
)
async def listar_jogos_pendentes(
    semanas: int = Query(
        4,
        ge=1,
        le=8,
        description="Número de semanas a considerar (1-8)"
    ),
    _: bool = Depends(verificar_api_key)
):
    """Lista jogos futuros que não estão no calendário."""
    jogos, _ = await scrape_calendario()
    
    # Ordenar, filtrar futuros e da semana
    jogos = ordenar_jogos(jogos)
    jogos = filtrar_jogos_semana(jogos, semanas=semanas)
    
    # Filtrar apenas os que NÃO estão no calendário
    jogos_pendentes = [j for j in jogos if not j.criado_no_calendario]
    
    return CalendarioResponse(
        sucesso=True,
        total_jogos=len(jogos_pendentes),
        jogos=jogos_pendentes,
        atualizado_em=datetime.now(),
        cache=True
    )
