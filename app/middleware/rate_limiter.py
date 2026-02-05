"""
Middleware de Rate Limiting para proteção da API.
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para limitar requisições por IP.
    
    Implementa rate limiting baseado em janela deslizante.
    """
    
    def __init__(self, app, requests_limit: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests: dict = defaultdict(list)
        self._lock = asyncio.Lock()
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtém o IP real do cliente, considerando proxies (Cloudflare, nginx).
        """
        # Cloudflare
        cf_connecting_ip = request.headers.get("CF-Connecting-IP")
        if cf_connecting_ip:
            return cf_connecting_ip
        
        # Proxy padrão
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Pega o primeiro IP da lista (IP original do cliente)
            return x_forwarded_for.split(",")[0].strip()
        
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip
        
        # IP direto
        return request.client.host if request.client else "unknown"
    
    async def _cleanup_old_requests(self, client_ip: str):
        """Remove requisições antigas fora da janela de tempo."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Não aplicar rate limit em health check
        if request.url.path == "/health":
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        async with self._lock:
            await self._cleanup_old_requests(client_ip)
            
            # Verificar limite
            if len(self.requests[client_ip]) >= self.requests_limit:
                logger.warning(f"Rate limit excedido para IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "erro": "Rate limit excedido",
                        "limite": f"{self.requests_limit} requisições por {self.window_seconds} segundos",
                        "retry_after": self.window_seconds
                    }
                )
            
            # Registrar requisição
            self.requests[client_ip].append(datetime.now())
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        remaining = self.requests_limit - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        
        return response
