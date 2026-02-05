"""
Middleware de Segurança para proteção da API.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para adicionar headers de segurança.
    
    Protege contra:
    - XSS (Cross-Site Scripting)
    - Clickjacking
    - MIME sniffing
    - Vazamento de informações do servidor
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevenir XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevenir MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Política de referência
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Remover header que expõe tecnologia do servidor
        if "server" in response.headers:
            del response.headers["server"]
        
        # Não expor versão do Python/FastAPI
        response.headers["X-Powered-By"] = "SPFC-API"
        
        # Cache control para dados sensíveis
        if "/api/" in str(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Middleware para validar hosts permitidos.
    
    Protege contra ataques de Host header injection.
    """
    
    def __init__(self, app, allowed_hosts: str = "*"):
        super().__init__(app)
        if allowed_hosts == "*":
            self.allowed_hosts = None  # Permite todos
        else:
            self.allowed_hosts = [h.strip().lower() for h in allowed_hosts.split(",")]
    
    async def dispatch(self, request: Request, call_next):
        if self.allowed_hosts is None:
            return await call_next(request)
        
        host = request.headers.get("host", "").split(":")[0].lower()
        
        if host not in self.allowed_hosts:
            logger.warning(f"Host não permitido: {host}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"erro": "Host não permitido"}
            )
        
        return await call_next(request)
