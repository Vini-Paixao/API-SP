"""
API de Web Scraping - Calendário do São Paulo FC

Extrai informações de jogos da página oficial do SPFC
para integração com Google Calendar via n8n.

Segurança:
- Rate limiting por IP
- Headers de segurança
- Autenticação via Bearer Token
- Compatível com Cloudflare Proxy
"""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import logging

from app.routes.calendario import router as calendario_router
from app.models import HealthResponse
from app.config import get_settings
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware, TrustedHostMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Versão da API
API_VERSION = "1.1.0"


class UTF8JSONResponse(JSONResponse):
    """JSONResponse com encoding UTF-8 garantido."""
    media_type = "application/json; charset=utf-8"
    
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")


# Carregar configurações
settings = get_settings()

# Criar app FastAPI
app = FastAPI(
    title="API Calendário SPFC",
    description="""
    API de Web Scraping para extrair jogos do calendário do São Paulo FC.
    
    ## Funcionalidades
    
    * **Listar Jogos** - Retorna todos os jogos futuros (ordenados por data)
    * **Jogos da Semana** - Retorna jogos das próximas N semanas
    * **Próximo Jogo** - Retorna apenas o próximo jogo
    * **Marcar no Calendário** - Marca jogos como já adicionados ao Google Calendar
    * **Cache Inteligente** - Cache persiste até o último jogo passar
    
    ## Segurança
    
    * Rate limiting: 30 requisições por minuto por IP
    * Headers de segurança (XSS, Clickjacking, MIME sniffing)
    * Compatível com Cloudflare Proxy
    
    ## Autenticação
    
    Todas as rotas (exceto health check) requerem autenticação via Bearer Token.
    
    Adicione o header: `Authorization: Bearer SUA_API_KEY`
    
    ## Integração n8n
    
    Esta API foi projetada para ser chamada semanalmente por um workflow n8n
    que salva os jogos no Google Calendar automaticamente.
    
    Workflow sugerido:
    1. Chamar GET /api/jogos/semana
    2. Para cada jogo com criado_no_calendario=false, criar evento no Calendar
    3. Chamar POST /api/jogos/{jogo_id}/marcar-calendario com o google_event_id
    4. Opcionalmente, chamar DELETE para remover jogos antigos do Calendar
    """,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=UTF8JSONResponse,
)

# Middlewares de segurança (ordem importa: primeiro a ser adicionado é o último a executar)
# 1. Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window
)

# 2. Headers de Segurança
app.add_middleware(SecurityHeadersMiddleware)

# 3. Validação de Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# 4. CORS - Origins permitidas (configurar via CORS_ORIGINS no .env)
cors_origins = (
    [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if settings.cors_origins != "*"
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Incluir rotas
app.include_router(calendario_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Verifica se a API está funcionando. Não requer autenticação."
)
async def health_check():
    """Endpoint de health check."""
    return HealthResponse(
        status="healthy",
        versao=API_VERSION,
        timestamp=datetime.now()
    )


@app.get(
    "/",
    tags=["Root"],
    summary="Root",
    description="Redireciona para a documentação."
)
async def root():
    """Endpoint root com informações básicas."""
    return {
        "nome": "API Calendário SPFC",
        "versao": API_VERSION,
        "documentacao": "/docs",
        "health": "/health"
    }
