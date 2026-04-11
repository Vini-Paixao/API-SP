# 🏟️ API Calendário SPFC

API de Web Scraping para extrair jogos do calendário do São Paulo FC usando [Firecrawl](https://firecrawl.dev).

## 📋 Funcionalidades

- **GET /api/jogos** - Lista todos os jogos do calendário (apenas futuros por padrão)
- **GET /api/jogos/semana** - Retorna jogos das próximas N semanas
- **GET /api/jogos/semana/pendentes** - Jogos da semana não sincronizados (ideal para n8n)
- **GET /api/proximo-jogo** - Retorna apenas o próximo jogo
- **GET /api/jogos/hoje/ao-vivo** - Retorna jogo do dia com status (planejado, ao_vivo ou finalizado)
- **GET /api/jogos/pendentes** - Jogos não sincronizados com Google Calendar
- **GET /api/jogos/calendario** - Jogos já sincronizados
- **POST /api/jogos/{id}/marcar-calendario** - Marca jogo como sincronizado
- **DELETE /api/jogos/{id}/calendario** - Desmarca jogo
- **GET /api/cache/status** - Status do cache
- **POST /api/cache/limpar** - Limpa o cache manualmente
- **GET /health** - Health check (sem autenticação)

## 🔒 Segurança

- Rate limiting: 30 requisições/minuto por IP
- Headers de segurança (XSS, Clickjacking, MIME sniffing)
- CORS configurável
- Compatível com Cloudflare Proxy

## 🚀 Quick Start

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Suporta múltiplas API keys para load-balance (separadas por vírgula)
FIRECRAWL_API_KEYS=fc-key1,fc-key2,fc-key3
API_KEY=sua-api-key-segura

# CORS - seus domínios
CORS_ORIGINS=https://seudominio.com,https://n8n.seudominio.com

# Hosts permitidos
ALLOWED_HOSTS=api.seudominio.com,localhost
```

### 2. Rodar com Docker

```bash
docker-compose up -d
```

A API estará disponível em `http://localhost:8001`

### 3. Rodar localmente (desenvolvimento)

```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Rodar
uvicorn app.main:app --reload
```

## 📖 Documentação

Acesse a documentação interativa:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- Documentação técnica: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

## 🔐 Autenticação

Todas as rotas (exceto `/health`) requerem autenticação via Bearer Token.

```bash
curl -X GET "http://localhost:8001/api/jogos" \
  -H "Authorization: Bearer SUA_API_KEY"
```

## 📦 Response Example

```json
{
  "sucesso": true,
  "total_jogos": 5,
  "jogos": [
    {
      "competicao": "Campeonato Paulista",
      "adversario": "Corinthians",
      "adversario_logo": "https://cdn.saopaulofc.net/...",
      "data": "08/02/2026",
      "dia_semana": "Domingo",
      "horario": "16:00",
      "local": "Morumbi",
      "mandante": true,
      "data_iso": "2026-02-08T16:00:00-03:00",
      "data_fim_iso": "2026-02-08T18:00:00-03:00"
    }
  ],
  "atualizado_em": "2026-02-04T10:30:00",
  "cache": false
}
```

## 🔄 Integração n8n

Esta API foi projetada para ser chamada por um workflow n8n que:

1. Faz requisição GET para `/api/jogos` semanalmente
2. Processa a lista de jogos
3. Cria eventos no Google Calendar usando `data_iso` e `data_fim_iso`

### Exemplo de configuração no n8n:

**HTTP Request Node:**
- Method: GET
- URL: `https://sua-api.com/api/jogos`
- Headers: `Authorization: Bearer SUA_API_KEY`

## 🐳 Deploy com Nginx (HTTPS)

Exemplo de configuração nginx:

```nginx
server {
    listen 443 ssl;
    server_name api-spfc.seudominio.com;
    
    ssl_certificate /etc/letsencrypt/live/api-spfc.seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-spfc.seudominio.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## ⚙️ Configurações

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `FIRECRAWL_API_KEY` | Chave da API Firecrawl | - |
| `API_KEY` | Chave para autenticação | - |
| `CORS_ORIGINS` | Origins CORS permitidas (vírgula) | * |
| `ALLOWED_HOSTS` | Hosts permitidos (vírgula) | * |
| `RATE_LIMIT_REQUESTS` | Requisições por janela | 30 |
| `RATE_LIMIT_WINDOW` | Janela em segundos | 60 |

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
