"""
Serviço de Scraping usando Firecrawl para extrair jogos do SPFC.

Sistema de cache inteligente:
- Persiste em arquivo JSON para sobreviver restarts
- Só faz requisição ao Firecrawl quando o último jogo do cache já passou
- Economiza créditos do Firecrawl ao máximo
"""
try:
    from firecrawl import Firecrawl
except ImportError:
    from firecrawl import FirecrawlApp as Firecrawl
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import json
import logging

from app.config import get_settings
from app.models import Jogo

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho do arquivo de cache
CACHE_FILE = Path(__file__).parent.parent / "data" / "cache_jogos.json"


def _parse_data_jogo(jogo: Jogo) -> Optional[datetime]:
    """
    Extrai datetime de um objeto Jogo.
    
    Args:
        jogo: Objeto Jogo
        
    Returns:
        datetime ou None se não conseguir parsear
    """
    try:
        if jogo.data_iso:
            # Formato: 2026-02-07T16:00:00-03:00
            data_str = jogo.data_iso.replace("-03:00", "")
            return datetime.fromisoformat(data_str)
        elif jogo.data:
            # Tentar parsear data no formato DD/MM/YYYY
            partes = jogo.data.split("/")
            if len(partes) == 3:
                hora = 0
                minuto = 0
                if jogo.horario:
                    try:
                        h_parts = jogo.horario.replace("h", ":").split(":")
                        hora = int(h_parts[0])
                        minuto = int(h_parts[1]) if len(h_parts) > 1 else 0
                    except:
                        pass
                return datetime(int(partes[2]), int(partes[1]), int(partes[0]), hora, minuto)
    except Exception as e:
        logger.warning(f"Erro ao parsear data do jogo: {e}")
    return None


def ordenar_jogos(jogos: List[Jogo]) -> List[Jogo]:
    """
    Ordena jogos por data em ordem cronológica.
    
    Args:
        jogos: Lista de jogos
        
    Returns:
        Lista de jogos ordenada por data
    """
    def get_sort_key(jogo: Jogo) -> datetime:
        data = _parse_data_jogo(jogo)
        # Se não conseguir parsear, coloca no final
        return data if data else datetime.max
    
    return sorted(jogos, key=get_sort_key)


def filtrar_jogos_futuros(jogos: List[Jogo]) -> List[Jogo]:
    """
    Filtra apenas jogos que ainda não aconteceram.
    
    Args:
        jogos: Lista de jogos
        
    Returns:
        Lista com apenas jogos futuros
    """
    agora = datetime.now()
    jogos_futuros = []
    
    for jogo in jogos:
        data_jogo = _parse_data_jogo(jogo)
        if data_jogo and data_jogo > agora:
            jogos_futuros.append(jogo)
    
    return jogos_futuros


def filtrar_jogos_semana(jogos: List[Jogo], semanas: int = 1) -> List[Jogo]:
    """
    Filtra jogos que acontecem nas próximas N semanas.
    
    Args:
        jogos: Lista de jogos
        semanas: Número de semanas a considerar (padrão: 1)
        
    Returns:
        Lista com jogos da(s) próxima(s) semana(s)
    """
    agora = datetime.now()
    limite = agora + timedelta(weeks=semanas)
    jogos_semana = []
    
    for jogo in jogos:
        data_jogo = _parse_data_jogo(jogo)
        if data_jogo and agora < data_jogo <= limite:
            jogos_semana.append(jogo)
    
    return jogos_semana


def _garantir_diretorio_cache():
    """Garante que o diretório de cache existe."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


def _carregar_cache_arquivo() -> Optional[Dict[str, Any]]:
    """
    Carrega o cache do arquivo JSON.
    
    Returns:
        Dict com 'jogos' e 'ultima_atualizacao' ou None se não existir
    """
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Cache carregado do arquivo: {len(data.get('jogos', []))} jogos")
                return data
    except Exception as e:
        logger.error(f"Erro ao carregar cache do arquivo: {e}")
    return None


def _salvar_cache_arquivo(jogos: List[Jogo]):
    """
    Salva os jogos no arquivo JSON de cache.
    
    Args:
        jogos: Lista de jogos para salvar
    """
    try:
        _garantir_diretorio_cache()
        
        data = {
            "ultima_atualizacao": datetime.now().isoformat(),
            "jogos": [jogo.model_dump() for jogo in jogos]
        }
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache salvo em arquivo: {len(jogos)} jogos")
        
    except Exception as e:
        logger.error(f"Erro ao salvar cache no arquivo: {e}")


def _obter_data_ultimo_jogo(jogos: List[Jogo]) -> Optional[datetime]:
    """
    Obtém a data do último jogo da lista.
    
    Args:
        jogos: Lista de jogos
        
    Returns:
        datetime do último jogo ou None
    """
    if not jogos:
        return None
    
    ultima_data = None
    
    for jogo in jogos:
        data = _parse_data_jogo(jogo)
        if data and (ultima_data is None or data > ultima_data):
            ultima_data = data
    
    return ultima_data


def _cache_ainda_valido(jogos: List[Jogo]) -> bool:
    """
    Verifica se o cache ainda é válido baseado na data do último jogo.
    
    Lógica: Se o último jogo do cache ainda não aconteceu, o cache é válido.
    Isso significa que só precisamos buscar novos dados quando todos os jogos
    do cache já passaram.
    
    Args:
        jogos: Lista de jogos do cache
        
    Returns:
        True se o cache ainda é válido, False se precisa atualizar
    """
    if not jogos:
        return False
    
    ultimo_jogo_data = _obter_data_ultimo_jogo(jogos)
    
    if ultimo_jogo_data is None:
        logger.warning("Não foi possível determinar data do último jogo, cache inválido")
        return False
    
    agora = datetime.now()
    
    # Cache válido se o último jogo ainda não passou
    # Adicionamos 3 horas para garantir que o jogo terminou
    valido = ultimo_jogo_data + timedelta(hours=3) > agora
    
    logger.info(
        f"Verificação de cache: último jogo em {ultimo_jogo_data.strftime('%d/%m/%Y %H:%M')}, "
        f"agora é {agora.strftime('%d/%m/%Y %H:%M')}, "
        f"cache {'VÁLIDO' if valido else 'EXPIRADO'}"
    )
    
    return valido


def _converter_cache_para_jogos(data: Dict[str, Any]) -> List[Jogo]:
    """
    Converte dados do cache JSON para lista de objetos Jogo.
    
    Args:
        data: Dict do cache com 'jogos'
        
    Returns:
        Lista de objetos Jogo
    """
    jogos = []
    
    for jogo_data in data.get("jogos", []):
        try:
            jogo = Jogo(**jogo_data)
            jogos.append(jogo)
        except Exception as e:
            logger.warning(f"Erro ao converter jogo do cache: {e}")
            continue
    
    return jogos


def parse_data_hora(data_str: str, horario_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    Converte data e horário para formato ISO 8601 (compatível com Google Calendar).
    
    Args:
        data_str: Data no formato DD/MM/YYYY ou similar
        horario_str: Horário no formato HH:MM ou HHhMM
        
    Returns:
        Tupla (data_inicio_iso, data_fim_iso) ou (None, None) se falhar
    """
    try:
        # Limpar e normalizar data
        data_limpa = data_str.strip()
        horario_limpo = horario_str.strip().replace("h", ":").replace("H", ":")
        
        # Tentar diferentes formatos de data
        formatos_data = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m",
        ]
        
        data_parsed = None
        for fmt in formatos_data:
            try:
                if fmt == "%d/%m":
                    # Se não tem ano, assumir ano atual
                    data_parsed = datetime.strptime(data_limpa, fmt).replace(year=datetime.now().year)
                else:
                    data_parsed = datetime.strptime(data_limpa, fmt)
                break
            except ValueError:
                continue
        
        if data_parsed is None:
            logger.warning(f"Não foi possível parsear data: {data_str}")
            return None, None
        
        # Parsear horário
        try:
            hora, minuto = map(int, horario_limpo.split(":"))
            data_inicio = data_parsed.replace(hour=hora, minute=minuto)
        except (ValueError, AttributeError):
            logger.warning(f"Não foi possível parsear horário: {horario_str}")
            # Se não conseguir parsear horário, usar meia-noite
            data_inicio = data_parsed
        
        # Calcular fim (2 horas depois - duração típica de jogo)
        data_fim = data_inicio + timedelta(hours=2)
        
        # Formatar para ISO 8601 com timezone de São Paulo (-03:00)
        data_inicio_iso = data_inicio.strftime("%Y-%m-%dT%H:%M:%S") + "-03:00"
        data_fim_iso = data_fim.strftime("%Y-%m-%dT%H:%M:%S") + "-03:00"
        
        return data_inicio_iso, data_fim_iso
        
    except Exception as e:
        logger.error(f"Erro ao parsear data/hora: {e}")
        return None, None


def extrair_jogos_do_resultado(resultado: Any) -> List[Jogo]:
    """
    Extrai lista de jogos do resultado do Firecrawl.
    
    Args:
        resultado: Resposta da API do Firecrawl (pode ser objeto ou dict)
        
    Returns:
        Lista de objetos Jogo
    """
    jogos = []
    
    try:
        # Converter para dict se for objeto
        if hasattr(resultado, '__dict__'):
            dados = vars(resultado)
        elif hasattr(resultado, 'data'):
            dados = resultado.data if isinstance(resultado.data, dict) else {"jogos": []}
        elif isinstance(resultado, dict):
            dados = resultado
        else:
            logger.warning(f"Tipo de resultado inesperado: {type(resultado)}")
            dados = {}
        
        logger.info(f"Dados extraídos: {dados}")
        
        # Tentar diferentes estruturas de resposta
        lista_jogos: List[Dict[str, Any]] = []
        
        # Estrutura 1: {jogos: [...]}
        if isinstance(dados, dict) and "jogos" in dados:
            lista_jogos = dados["jogos"]
        # Estrutura 2: dados é uma lista diretamente
        elif isinstance(dados, list):
            lista_jogos = dados
        # Estrutura 3: {data: {jogos: [...]}}
        elif isinstance(dados, dict) and "data" in dados:
            data_content = dados["data"]
            if isinstance(data_content, dict) and "jogos" in data_content:
                lista_jogos = data_content["jogos"]
        # Estrutura 4: {extract: {jogos: [...]}}
        elif isinstance(dados, dict) and "extract" in dados:
            extract_data = dados["extract"]
            if isinstance(extract_data, dict) and "jogos" in extract_data:
                lista_jogos = extract_data["jogos"]
            elif isinstance(extract_data, list):
                lista_jogos = extract_data
        
        if not lista_jogos:
            logger.warning("Nenhum jogo encontrado na resposta")
            return jogos
        
        for jogo_data in lista_jogos:
            try:
                # Extrair campos com fallbacks
                data = jogo_data.get("data", "")
                horario = jogo_data.get("horario", "")
                
                # Converter para ISO 8601
                data_iso, data_fim_iso = parse_data_hora(data, horario)
                
                jogo = Jogo(
                    competicao=jogo_data.get("competicao", "Não informada"),
                    adversario=jogo_data.get("adversario", "Não informado"),
                    adversario_logo=jogo_data.get("adversario_logo") or jogo_data.get("logo"),
                    data=data,
                    dia_semana=jogo_data.get("dia_semana"),
                    horario=horario,
                    local=jogo_data.get("local") or jogo_data.get("estadio"),
                    mandante=jogo_data.get("mandante"),
                    data_iso=data_iso,
                    data_fim_iso=data_fim_iso,
                    criado_no_calendario=False,
                    google_event_id=None,
                )
                jogos.append(jogo)
                
            except Exception as e:
                logger.error(f"Erro ao processar jogo: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Erro ao extrair jogos: {e}")
    
    return jogos


async def scrape_calendario(force_refresh: bool = False) -> tuple[List[Jogo], bool]:
    """
    Faz scraping do calendário do SPFC usando Firecrawl com cache inteligente.
    
    Sistema de cache:
    1. Primeiro tenta carregar do arquivo JSON
    2. Verifica se o último jogo do cache ainda não passou
    3. Se ainda não passou, usa o cache (economiza créditos!)
    4. Se já passou, busca novos dados do Firecrawl
    
    Args:
        force_refresh: Se True, ignora o cache e força nova requisição
        
    Returns:
        Tupla (lista de jogos, from_cache)
    """
    settings = get_settings()
    
    # Tentar carregar cache do arquivo
    cache_data = _carregar_cache_arquivo()
    
    if cache_data and not force_refresh:
        jogos_cache = _converter_cache_para_jogos(cache_data)
        
        if jogos_cache and _cache_ainda_valido(jogos_cache):
            logger.info(
                f"✅ Usando cache (último jogo ainda não passou). "
                f"Economia de créditos Firecrawl!"
            )
            return jogos_cache, True
        else:
            logger.info("📅 Cache expirado (último jogo já passou), buscando novos dados...")
    
    elif force_refresh:
        logger.info("🔄 Force refresh solicitado, ignorando cache...")
    
    else:
        logger.info("📭 Nenhum cache encontrado, buscando dados...")
    
    logger.info(f"🌐 Fazendo scraping de: {settings.spfc_calendario_url}")
    
    # Obter lista de API keys para load-balance
    api_keys = settings.firecrawl_api_key_list
    if not api_keys:
        raise Exception("Nenhuma API key do Firecrawl configurada. Configure FIRECRAWL_API_KEYS no .env")
    
    logger.info(f"🔑 {len(api_keys)} API key(s) disponível(is) para load-balance")
    
    # Retry automático com rotação de API keys
    max_retries = settings.firecrawl_max_retries
    retry_delay = settings.firecrawl_retry_delay
    last_error = None
    
    # Total de tentativas = retries por key * número de keys
    total_attempts = max_retries * len(api_keys)
    attempt = 0
    
    for key_index, api_key in enumerate(api_keys):
        key_label = f"Key {key_index + 1}/{len(api_keys)}"
        
        for retry in range(1, max_retries + 1):
            attempt += 1
            try:
                logger.info(f"🔑 Usando {key_label} (tentativa {retry}/{max_retries})")
                
                # Inicializar Firecrawl com a key atual
                app = Firecrawl(api_key=api_key)
            
            # Schema para extração estruturada
            schema = {
                "type": "object",
                "properties": {
                    "jogos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "competicao": {"type": "string", "description": "Nome da competição ou campeonato"},
                                "adversario": {"type": "string", "description": "Nome do time adversário"},
                                "adversario_logo": {"type": "string", "description": "URL da imagem/logo do adversário"},
                                "data": {"type": "string", "description": "Data do jogo no formato DD/MM/YYYY"},
                                "dia_semana": {"type": "string", "description": "Dia da semana"},
                                "horario": {"type": "string", "description": "Horário do jogo no formato HH:MM"},
                                "local": {"type": "string", "description": "Estádio ou local do jogo"},
                                "mandante": {"type": "boolean", "description": "True se o São Paulo é o mandante/time da casa"}
                            },
                            "required": ["competicao", "adversario", "data", "horario"]
                        }
                    }
                }
            }
            
            # Prompt para extração
            prompt = """
            Extraia TODOS os jogos do calendário do São Paulo FC que aparecem na página.
            Para cada jogo, extraia:
            - competicao: nome do campeonato/competição
            - adversario: nome do time adversário (não incluir 'x' ou 'vs')
            - adversario_logo: URL completa da imagem do escudo do adversário se disponível
            - data: data do jogo no formato DD/MM/YYYY
            - dia_semana: dia da semana (Segunda, Terça, etc)
            - horario: horário no formato HH:MM
            - local: nome do estádio
            - mandante: true se São Paulo joga em casa, false se joga fora
            
            Inclua jogos futuros e próximos. Retorne uma lista completa de jogos.
            """
            
            # Fazer extração estruturada usando o método extract
            resultado = app.extract(
                urls=[settings.spfc_calendario_url],
                schema=schema,
                prompt=prompt
            )
            
            logger.info(f"✅ Extração concluída com {key_label}! Resultado: {resultado}")
            
            # Extrair jogos do resultado
            jogos = extrair_jogos_do_resultado(resultado)
            
            # Preservar status de criado_no_calendario do cache anterior
            if cache_data:
                jogos = _preservar_status_calendario(jogos, cache_data)
            
            # Salvar no arquivo de cache
            if jogos:
                _salvar_cache_arquivo(jogos)
                logger.info(f"✅ Cache atualizado com {len(jogos)} jogos")
            
            return jogos, False
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Detectar erro de créditos insuficientes
            is_credit_error = any(x in error_str for x in [
                "payment required", 
                "insufficient credits",
                "credit",
                "402"
            ])
            
            if is_credit_error:
                logger.warning(f"⚠️ {key_label} sem créditos: {e}")
                # Se tem mais keys, pula para a próxima key imediatamente
                if key_index < len(api_keys) - 1:
                    logger.info(f"🔄 Alternando para próxima API key...")
                    break  # Sai do loop de retry para ir para próxima key
                else:
                    logger.warning(f"⚠️ Todas as API keys estão sem créditos!")
            else:
                logger.warning(f"⚠️ {key_label} tentativa {retry}/{max_retries} falhou: {e}")
            
            if retry < max_retries and not is_credit_error:
                import time
                logger.info(f"⏳ Aguardando {retry_delay}s antes de tentar novamente...")
                time.sleep(retry_delay)
    
    # Todas as tentativas e keys falharam
    logger.error(f"❌ Todas as {len(api_keys)} API key(s) falharam. Último erro: {last_error}")
    
    # Se falhar mas tiver cache, retornar cache mesmo expirado
    if cache_data:
        jogos_cache = _converter_cache_para_jogos(cache_data)
        if jogos_cache:
            logger.info("⚠️ Retornando cache após erro (melhor que nada)")
            return jogos_cache, True
    
    if last_error:
        raise last_error
    raise Exception("Falha ao buscar dados do Firecrawl após múltiplas tentativas")


def limpar_cache():
    """Limpa o cache de jogos (arquivo JSON)."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            logger.info("🗑️ Cache removido (arquivo deletado)")
        else:
            logger.info("📭 Nenhum cache para limpar")
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")


def obter_info_cache() -> Dict[str, Any]:
    """
    Retorna informações sobre o estado atual do cache.
    
    Returns:
        Dict com informações do cache
    """
    cache_data = _carregar_cache_arquivo()
    
    if not cache_data:
        return {
            "existe": False,
            "mensagem": "Nenhum cache encontrado"
        }
    
    jogos = _converter_cache_para_jogos(cache_data)
    ultimo_jogo_data = _obter_data_ultimo_jogo(jogos)
    valido = _cache_ainda_valido(jogos)
    
    return {
        "existe": True,
        "ultima_atualizacao": cache_data.get("ultima_atualizacao"),
        "total_jogos": len(jogos),
        "ultimo_jogo_data": ultimo_jogo_data.strftime("%d/%m/%Y %H:%M") if ultimo_jogo_data else None,
        "cache_valido": valido,
        "proxima_atualizacao": "Quando o último jogo passar" if valido else "Na próxima requisição",
        "arquivo": str(CACHE_FILE)
    }


def _preservar_status_calendario(jogos_novos: List[Jogo], cache_data: Dict[str, Any]) -> List[Jogo]:
    """
    Preserva o status de criado_no_calendario ao atualizar o cache.
    
    Quando novos dados são buscados do Firecrawl, precisamos manter
    o status dos jogos que já foram adicionados ao calendário.
    
    Args:
        jogos_novos: Lista de jogos recém-extraídos
        cache_data: Dados do cache anterior
        
    Returns:
        Lista de jogos com status preservado
    """
    # Criar mapa de jogos antigos por jogo_id
    jogos_antigos = _converter_cache_para_jogos(cache_data)
    status_map = {}
    
    for jogo in jogos_antigos:
        status_map[jogo.jogo_id] = {
            "criado_no_calendario": jogo.criado_no_calendario,
            "google_event_id": jogo.google_event_id
        }
    
    # Aplicar status aos jogos novos
    for jogo in jogos_novos:
        if jogo.jogo_id in status_map:
            jogo.criado_no_calendario = status_map[jogo.jogo_id]["criado_no_calendario"]
            jogo.google_event_id = status_map[jogo.jogo_id]["google_event_id"]
    
    return jogos_novos


def marcar_jogo_no_calendario(jogo_id: str, google_event_id: Optional[str] = None) -> bool:
    """
    Marca um jogo como criado no Google Calendar.
    
    Args:
        jogo_id: ID único do jogo
        google_event_id: ID do evento criado no Google Calendar
        
    Returns:
        True se marcou com sucesso, False se jogo não encontrado
    """
    cache_data = _carregar_cache_arquivo()
    if not cache_data:
        return False
    
    jogos = _converter_cache_para_jogos(cache_data)
    encontrado = False
    
    for jogo in jogos:
        if jogo.jogo_id == jogo_id:
            jogo.criado_no_calendario = True
            jogo.google_event_id = google_event_id
            encontrado = True
            logger.info(f"✅ Jogo {jogo_id} marcado como criado no calendário")
            break
    
    if encontrado:
        _salvar_cache_arquivo(jogos)
    
    return encontrado


def desmarcar_jogo_do_calendario(jogo_id: str) -> Optional[str]:
    """
    Desmarca um jogo do calendário (para quando o evento for removido).
    
    Args:
        jogo_id: ID único do jogo
        
    Returns:
        google_event_id do jogo (para remover do Calendar) ou None
    """
    cache_data = _carregar_cache_arquivo()
    if not cache_data:
        return None
    
    jogos = _converter_cache_para_jogos(cache_data)
    google_event_id = None
    
    for jogo in jogos:
        if jogo.jogo_id == jogo_id:
            google_event_id = jogo.google_event_id
            jogo.criado_no_calendario = False
            jogo.google_event_id = None
            logger.info(f"🗑️ Jogo {jogo_id} desmarcado do calendário")
            break
    
    if google_event_id:
        _salvar_cache_arquivo(jogos)
    
    return google_event_id


def obter_jogos_no_calendario() -> List[Jogo]:
    """
    Retorna todos os jogos que estão marcados como criados no calendário.
    
    Útil para limpar eventos antigos do Google Calendar.
    
    Returns:
        Lista de jogos que estão no calendário
    """
    cache_data = _carregar_cache_arquivo()
    if not cache_data:
        return []
    
    jogos = _converter_cache_para_jogos(cache_data)
    return [jogo for jogo in jogos if jogo.criado_no_calendario]


def obter_jogos_passados_no_calendario() -> List[Jogo]:
    """
    Retorna jogos que já passaram mas ainda estão marcados no calendário.
    
    Perfeito para workflow de limpeza: remover eventos antigos.
    
    Returns:
        Lista de jogos passados que estão no calendário
    """
    jogos_calendario = obter_jogos_no_calendario()
    agora = datetime.now()
    
    jogos_passados = []
    for jogo in jogos_calendario:
        data_jogo = _parse_data_jogo(jogo)
        # Considerar passado se já faz 3 horas que o jogo terminou
        if data_jogo and data_jogo + timedelta(hours=5) < agora:
            jogos_passados.append(jogo)
    
    return jogos_passados
