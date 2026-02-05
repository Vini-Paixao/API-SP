# ðŸ“š DocumentaÃ§Ã£o TÃ©cnica - API CalendÃ¡rio SPFC

> API de Web Scraping para extraÃ§Ã£o automÃ¡tica de jogos do SÃ£o Paulo FC com integraÃ§Ã£o Google Calendar via n8n.

**VersÃ£o:** 1.1.0  
**Base URL:** `http://seu-servidor:8001`  
**Ãšltima atualizaÃ§Ã£o:** Fevereiro 2026

---

## ðŸ“‹ Ãndice

1. [VisÃ£o Geral](#visÃ£o-geral)
2. [Arquitetura](#arquitetura)
3. [AutenticaÃ§Ã£o](#autenticaÃ§Ã£o)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Listar Jogos](#listar-jogos)
   - [Jogos da Semana](#jogos-da-semana)
   - [PrÃ³ximo Jogo](#prÃ³ximo-jogo)
   - [Jogos Pendentes](#jogos-pendentes)
   - [Jogos no CalendÃ¡rio](#jogos-no-calendÃ¡rio)
   - [Jogos para Limpar](#jogos-para-limpar)
   - [Marcar Jogo no CalendÃ¡rio](#marcar-jogo-no-calendÃ¡rio)
   - [Desmarcar Jogo do CalendÃ¡rio](#desmarcar-jogo-do-calendÃ¡rio)
   - [Status do Cache](#status-do-cache)
   - [Limpar Cache](#limpar-cache)
6. [Modelos de Dados](#modelos-de-dados)
7. [Sistema de Cache](#sistema-de-cache)
8. [SeguranÃ§a](#seguranÃ§a)
9. [IntegraÃ§Ã£o n8n](#integraÃ§Ã£o-n8n)
10. [Exemplos de Uso](#exemplos-de-uso)
11. [Troubleshooting](#troubleshooting)

---

## VisÃ£o Geral

Esta API foi desenvolvida para:

- **Extrair automaticamente** jogos do calendÃ¡rio oficial do SÃ£o Paulo FC
- **Cachear dados inteligentemente** para economizar crÃ©ditos do Firecrawl
- **Integrar com n8n** para sincronizaÃ§Ã£o automÃ¡tica com Google Calendar
- **Controlar sincronizaÃ§Ã£o** marcando jogos jÃ¡ adicionados ao calendÃ¡rio

### Fluxo de Funcionamento

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Site SPFC     â”‚â”€â”€â”€â”€â–¶â”‚   Firecrawl     â”‚â”€â”€â”€â”€â–¶â”‚   API SPFC      â”‚
â”‚ (calendario)    â”‚     â”‚   (scraping)    â”‚     â”‚   (cache JSON)  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                                         â”‚
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”              â”‚
                        â”‚  Google Calendar â”‚â—€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜              â”‚
                                 â–²                       â”‚
                                 â”‚              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”
                                 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”‚      n8n        â”‚
                                                â”‚   (workflow)    â”‚
                                                â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Arquitetura

### Stack TecnolÃ³gica

| Componente | Tecnologia | VersÃ£o |
|------------|------------|--------|
| Framework | FastAPI | >= 0.128.0 |
| Runtime | Python | 3.11 |
| Scraping | Firecrawl | >= 4.14.0 |
| ValidaÃ§Ã£o | Pydantic | >= 2.12.5 |
| Container | Docker | - |
| Proxy | Cloudflare + nginx | - |

### Estrutura de DiretÃ³rios

```
API-SP/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ main.py              # AplicaÃ§Ã£o FastAPI principal
â”‚   â”œâ”€â”€ config.py            # ConfiguraÃ§Ãµes (env vars)
â”‚   â”œâ”€â”€ models.py            # Modelos Pydantic
â”‚   â”œâ”€â”€ scraper.py           # LÃ³gica de scraping + cache
â”‚   â”œâ”€â”€ middleware/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ rate_limiter.py  # Rate limiting por IP
â”‚   â”‚   â””â”€â”€ security.py      # Headers de seguranÃ§a
â”‚   â””â”€â”€ routes/
â”‚       â””â”€â”€ calendario.py    # Endpoints da API
â”œâ”€â”€ data/
â”‚   â””â”€â”€ cache_jogos.json     # Cache persistente
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ API_DOCUMENTATION.md # Esta documentaÃ§Ã£o
â”œâ”€â”€ .env                     # VariÃ¡veis de ambiente
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ docker-compose.yml
â””â”€â”€ requirements.txt
```

---

## AutenticaÃ§Ã£o

A API utiliza **Bearer Token** para autenticaÃ§Ã£o.

### Header NecessÃ¡rio

```http
Authorization: Bearer SUA_API_KEY
```

### Exemplo cURL

```bash
curl -H "Authorization: Bearer SUA_API_KEY_AQUI" \
     http://localhost:8001/api/jogos
```

### Exemplo JavaScript/n8n

```javascript
const headers = {
  "Authorization": "Bearer SUA_API_KEY_AQUI",
  "Content-Type": "application/json"
};
```

### Respostas de Erro de AutenticaÃ§Ã£o

| CÃ³digo | DescriÃ§Ã£o |
|--------|-----------|
| 401 | API Key invÃ¡lida ou ausente |
| 500 | API_KEY nÃ£o configurada no servidor |

---

## Rate Limiting

A API implementa rate limiting para proteÃ§Ã£o contra abuso.

### Limites PadrÃ£o

| ParÃ¢metro | Valor | ConfigurÃ¡vel |
|-----------|-------|--------------|
| RequisiÃ§Ãµes | 30 | `RATE_LIMIT_REQUESTS` |
| Janela | 60 segundos | `RATE_LIMIT_WINDOW` |

### Headers de Resposta

Toda resposta inclui:

```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
X-RateLimit-Window: 60
```

### Resposta ao Exceder Limite

```json
{
  "erro": "Rate limit excedido",
  "limite": "30 requisiÃ§Ãµes por 60 segundos",
  "retry_after": 60
}
```

**HTTP Status:** 429 Too Many Requests

---

## Endpoints

### Health Check

Verifica se a API estÃ¡ funcionando. **NÃ£o requer autenticaÃ§Ã£o.**

```http
GET /health
```

#### Resposta

```json
{
  "status": "healthy",
  "versao": "1.1.0",
  "timestamp": "2026-02-04T15:00:00.000000"
}
```

---

### Listar Jogos

Retorna todos os jogos do calendÃ¡rio do SPFC.

```http
GET /api/jogos
```

#### ParÃ¢metros Query

| ParÃ¢metro | Tipo | PadrÃ£o | DescriÃ§Ã£o |
|-----------|------|--------|-----------|
| `apenas_futuros` | boolean | `true` | Filtrar apenas jogos futuros |
| `force_refresh` | boolean | `false` | Ignorar cache e buscar novos dados |

#### Exemplo

```http
GET /api/jogos?apenas_futuros=true&force_refresh=false
```

#### Resposta

```json
{
  "sucesso": true,
  "total_jogos": 9,
  "jogos": [
    {
      "competicao": "BrasileirÃ£o 2026",
      "adversario": "Santos",
      "adversario_logo": "https://cdn.saopaulofc.net/...",
      "data": "04/02/2026",
      "dia_semana": "Quarta",
      "horario": "20:00",
      "local": "Vila Belmiro",
      "mandante": false,
      "data_iso": "2026-02-04T20:00:00-03:00",
      "data_fim_iso": "2026-02-04T22:00:00-03:00",
      "criado_no_calendario": false,
      "google_event_id": null,
      "jogo_id": "b22420564665"
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Jogos da Semana

Retorna jogos das prÃ³ximas N semanas. **Ideal para workflow semanal.**

```http
GET /api/jogos/semana
```

#### ParÃ¢metros Query

| ParÃ¢metro | Tipo | PadrÃ£o | Range | DescriÃ§Ã£o |
|-----------|------|--------|-------|-----------|
| `semanas` | integer | `1` | 1-8 | NÃºmero de semanas |
| `force_refresh` | boolean | `false` | - | Ignorar cache |

#### Exemplo

```http
GET /api/jogos/semana?semanas=2
```

#### Resposta

```json
{
  "sucesso": true,
  "total_jogos": 4,
  "jogos": [...],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### PrÃ³ximo Jogo

Retorna apenas o prÃ³ximo jogo futuro do SPFC.

```http
GET /api/proximo-jogo
```

#### ParÃ¢metros Query

| ParÃ¢metro | Tipo | PadrÃ£o | DescriÃ§Ã£o |
|-----------|------|--------|-----------|
| `force_refresh` | boolean | `false` | Ignorar cache |

#### Resposta

```json
{
  "sucesso": true,
  "jogo": {
    "competicao": "BrasileirÃ£o 2026",
    "adversario": "Santos",
    "data": "04/02/2026",
    "horario": "20:00",
    "local": "Vila Belmiro",
    "mandante": false,
    "data_iso": "2026-02-04T20:00:00-03:00",
    "data_fim_iso": "2026-02-04T22:00:00-03:00",
    "jogo_id": "b22420564665"
  },
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Jogos Pendentes

Retorna jogos futuros que **NÃƒO** foram adicionados ao Google Calendar.

```http
GET /api/jogos/pendentes
```

#### ParÃ¢metros Query

| ParÃ¢metro | Tipo | PadrÃ£o | Range | DescriÃ§Ã£o |
|-----------|------|--------|-------|-----------|
| `semanas` | integer | `4` | 1-8 | Semanas a considerar |

#### Uso no n8n

Este endpoint Ã© o **ponto de entrada principal** para o workflow de criaÃ§Ã£o de eventos.

#### Resposta

```json
{
  "sucesso": true,
  "total_jogos": 5,
  "jogos": [
    {
      "jogo_id": "9bf2fc96bbe6",
      "adversario": "Primavera SAF",
      "criado_no_calendario": false,
      "google_event_id": null,
      ...
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Jogos no CalendÃ¡rio

Retorna jogos que estÃ£o marcados como sincronizados com o Google Calendar.

```http
GET /api/jogos/calendario
```

#### Resposta

```json
{
  "sucesso": true,
  "total_jogos": 1,
  "jogos": [
    {
      "jogo_id": "b22420564665",
      "adversario": "Santos",
      "criado_no_calendario": true,
      "google_event_id": "abc123googleevent",
      ...
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Jogos para Limpar

Retorna jogos **passados** que ainda estÃ£o no calendÃ¡rio (para remoÃ§Ã£o).

```http
GET /api/jogos/calendario/limpar
```

#### Uso no n8n

Este endpoint Ã© usado para **limpar eventos antigos** do Google Calendar.

#### Resposta

```json
{
  "sucesso": true,
  "total_jogos": 2,
  "jogos": [
    {
      "jogo_id": "abc123",
      "adversario": "Corinthians",
      "data": "18/01/2026",
      "criado_no_calendario": true,
      "google_event_id": "googleevent456",
      ...
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Marcar Jogo no CalendÃ¡rio

Marca um jogo como adicionado ao Google Calendar.

```http
POST /api/jogos/{jogo_id}/marcar-calendario
```

#### ParÃ¢metros Path

| ParÃ¢metro | Tipo | DescriÃ§Ã£o |
|-----------|------|-----------|
| `jogo_id` | string | ID Ãºnico do jogo (campo `jogo_id`) |

#### Body (JSON)

```json
{
  "jogo_id": "b22420564665",
  "google_event_id": "abc123googlecalendar"
}
```

| Campo | Tipo | ObrigatÃ³rio | DescriÃ§Ã£o |
|-------|------|-------------|-----------|
| `jogo_id` | string | Sim | ID do jogo |
| `google_event_id` | string | NÃ£o | ID do evento no Google Calendar |

#### Resposta Sucesso

```json
{
  "sucesso": true,
  "mensagem": "Jogo b22420564665 marcado como criado no calendÃ¡rio",
  "google_event_id": "abc123googlecalendar",
  "timestamp": "2026-02-04T15:00:00.000000"
}
```

#### Resposta Erro (404)

```json
{
  "detail": "Jogo com ID 'xyz' nÃ£o encontrado"
}
```

---

### Desmarcar Jogo do CalendÃ¡rio

Remove a marcaÃ§Ã£o de um jogo (quando o evento Ã© deletado do Calendar).

```http
DELETE /api/jogos/{jogo_id}/calendario
```

#### ParÃ¢metros Path

| ParÃ¢metro | Tipo | DescriÃ§Ã£o |
|-----------|------|-----------|
| `jogo_id` | string | ID Ãºnico do jogo |

#### Resposta Sucesso

```json
{
  "sucesso": true,
  "mensagem": "Jogo b22420564665 desmarcado do calendÃ¡rio",
  "google_event_id": "abc123googlecalendar",
  "timestamp": "2026-02-04T15:00:00.000000"
}
```

> âš ï¸ O `google_event_id` Ã© retornado para que vocÃª possa deletar o evento do Google Calendar.

---

### Status do Cache

Retorna informaÃ§Ãµes sobre o estado do cache.

```http
GET /api/cache/status
```

#### Resposta

```json
{
  "existe": true,
  "ultima_atualizacao": "2026-02-04T14:38:46.564521",
  "total_jogos": 16,
  "ultimo_jogo_data": "21/03/2026 21:00",
  "cache_valido": true,
  "proxima_atualizacao": "Quando o Ãºltimo jogo passar",
  "arquivo": "/app/data/cache_jogos.json"
}
```

#### Campos Importantes

| Campo | DescriÃ§Ã£o |
|-------|-----------|
| `cache_valido` | `true` se ainda hÃ¡ jogos futuros no cache |
| `ultimo_jogo_data` | Data do Ãºltimo jogo - cache vÃ¡lido atÃ© esta data |
| `proxima_atualizacao` | Indica quando o cache serÃ¡ renovado |

---

### Limpar Cache

ForÃ§a limpeza do cache. PrÃ³xima requisiÃ§Ã£o buscarÃ¡ dados novos.

```http
POST /api/cache/limpar
```

#### Resposta

```json
{
  "sucesso": true,
  "mensagem": "Cache limpo com sucesso",
  "timestamp": "2026-02-04T15:00:00.000000"
}
```

> âš ï¸ **Cuidado:** Limpar o cache vai consumir crÃ©ditos do Firecrawl na prÃ³xima requisiÃ§Ã£o.

---

## Modelos de Dados

### Jogo

O modelo principal que representa um jogo do SPFC.

```typescript
interface Jogo {
  // IdentificaÃ§Ã£o
  jogo_id: string;           // ID Ãºnico (hash MD5 de data+hora+adversÃ¡rio+competiÃ§Ã£o)
  
  // InformaÃ§Ãµes do jogo
  competicao: string;        // Ex: "BrasileirÃ£o 2026", "Campeonato Paulista 2026"
  adversario: string;        // Nome do time adversÃ¡rio
  adversario_logo?: string;  // URL do escudo do adversÃ¡rio
  data: string;              // Formato DD/MM/YYYY
  dia_semana?: string;       // Ex: "Quarta", "SÃ¡bado"
  horario: string;           // Formato HH:MM
  local?: string;            // Nome do estÃ¡dio
  mandante?: boolean;        // true = SPFC joga em casa
  
  // Campos para Google Calendar
  data_iso?: string;         // ISO 8601: "2026-02-04T20:00:00-03:00"
  data_fim_iso?: string;     // ISO 8601: "2026-02-04T22:00:00-03:00" (2h depois)
  
  // Controle de sincronizaÃ§Ã£o
  criado_no_calendario: boolean;  // Se jÃ¡ foi adicionado ao Calendar
  google_event_id?: string;       // ID do evento no Google Calendar
}
```

### CalendarioResponse

Resposta padrÃ£o para endpoints que retornam lista de jogos.

```typescript
interface CalendarioResponse {
  sucesso: boolean;
  total_jogos: number;
  jogos: Jogo[];
  atualizado_em: string;     // ISO datetime
  cache: boolean;            // true = dados vieram do cache
}
```

### CacheInfoResponse

InformaÃ§Ãµes sobre o estado do cache.

```typescript
interface CacheInfoResponse {
  existe: boolean;
  ultima_atualizacao?: string;
  total_jogos?: number;
  ultimo_jogo_data?: string;
  cache_valido?: boolean;
  proxima_atualizacao?: string;
  arquivo?: string;
  mensagem?: string;
}
```

---

## Sistema de Cache

### Como Funciona

O cache inteligente economiza crÃ©ditos do Firecrawl:

1. **Primeira requisiÃ§Ã£o**: Busca dados do Firecrawl â†’ Salva em JSON
2. **RequisiÃ§Ãµes seguintes**: Verifica se Ãºltimo jogo jÃ¡ passou
   - Se NÃƒO passou â†’ Usa cache (0 crÃ©ditos)
   - Se passou â†’ Busca novos dados

### LÃ³gica de ValidaÃ§Ã£o

```
Cache VÃLIDO se:
  Ãºltimo_jogo_data + 3 horas > agora

Cache EXPIRADO se:
  Ãºltimo_jogo_data + 3 horas < agora
```

### Arquivo de Cache

LocalizaÃ§Ã£o: `/app/data/cache_jogos.json`

Estrutura:
```json
{
  "ultima_atualizacao": "2026-02-04T14:38:46.564521",
  "jogos": [...]
}
```

### Volume Docker

O cache persiste entre restarts via volume:
```yaml
volumes:
  - cache_data:/app/data
```

### Economia de CrÃ©ditos

| CenÃ¡rio | CrÃ©ditos Usados |
|---------|-----------------|
| Cache vÃ¡lido | 0 |
| Cache expirado | ~87 |
| `force_refresh=true` | ~87 |
| Limpar cache + requisiÃ§Ã£o | ~87 |

---

## SeguranÃ§a

### Headers de SeguranÃ§a

Todas as respostas incluem:

| Header | Valor | ProteÃ§Ã£o |
|--------|-------|----------|
| `X-XSS-Protection` | `1; mode=block` | Cross-Site Scripting |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Vazamento de referrer |
| `Content-Security-Policy` | `default-src 'self'` | InjeÃ§Ã£o de conteÃºdo |
| `Cache-Control` | `no-store, no-cache` | Cache de dados sensÃ­veis |
| `X-Powered-By` | `SPFC-API` | Oculta tecnologia real |

### Compatibilidade com Cloudflare

A API detecta automaticamente IPs reais atravÃ©s de:

1. `CF-Connecting-IP` (Cloudflare)
2. `X-Forwarded-For` (Proxies)
3. `X-Real-IP` (nginx)

### Retry AutomÃ¡tico

Se o Firecrawl falhar:

- **Tentativas:** 3 (configurÃ¡vel via `FIRECRAWL_MAX_RETRIES`)
- **Intervalo:** 5 segundos (configurÃ¡vel via `FIRECRAWL_RETRY_DELAY`)
- **Fallback:** Retorna cache antigo se disponÃ­vel

---

## IntegraÃ§Ã£o n8n

### Workflow 1: Criar Eventos (Semanal)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Trigger   â”‚â”€â”€â”€â”€â–¶â”‚ GET jogos/  â”‚â”€â”€â”€â”€â–¶â”‚ Loop: cada  â”‚â”€â”€â”€â”€â–¶â”‚ Criar       â”‚
â”‚   Semanal   â”‚     â”‚ pendentes   â”‚     â”‚    jogo     â”‚     â”‚ evento GCal â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                                               â”‚                   â”‚
                                               â”‚    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                               â–¼    â–¼
                                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                        â”‚ POST marcar â”‚
                                        â”‚ -calendario â”‚
                                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Nodes n8n

1. **Schedule Trigger**
   - Intervalo: Toda segunda-feira Ã s 08:00

2. **HTTP Request - Buscar Pendentes**
   ```
   Method: GET
   URL: http://sua-api:8001/api/jogos/pendentes?semanas=2
   Headers:
     Authorization: Bearer {{$env.SPFC_API_KEY}}
   ```

3. **Loop Over Items**
   - Itera sobre `$json.jogos`

4. **Google Calendar - Create Event**
   ```
   Calendar: Seu CalendÃ¡rio
   Title: SPFC x {{$json.adversario}} - {{$json.competicao}}
   Start: {{$json.data_iso}}
   End: {{$json.data_fim_iso}}
   Location: {{$json.local}}
   Description: {{$json.mandante ? "Jogo em casa" : "Jogo fora"}}
   ```

5. **HTTP Request - Marcar CalendÃ¡rio**
   ```
   Method: POST
   URL: http://sua-api:8001/api/jogos/{{$json.jogo_id}}/marcar-calendario
   Headers:
     Authorization: Bearer {{$env.SPFC_API_KEY}}
     Content-Type: application/json
   Body:
     {
       "jogo_id": "{{$json.jogo_id}}",
       "google_event_id": "{{$node["Google Calendar"].json.id}}"
     }
   ```

---

### Workflow 2: Limpar Eventos Antigos (Semanal)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Trigger   â”‚â”€â”€â”€â”€â–¶â”‚ GET jogos/  â”‚â”€â”€â”€â”€â–¶â”‚ Loop: cada  â”‚â”€â”€â”€â”€â–¶â”‚ Deletar     â”‚
â”‚   Semanal   â”‚     â”‚ calendario/ â”‚     â”‚    jogo     â”‚     â”‚ evento GCal â”‚
â”‚             â”‚     â”‚ limpar      â”‚     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚                   â”‚
                                               â”‚    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                               â–¼    â–¼
                                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                        â”‚ DELETE      â”‚
                                        â”‚ /calendario â”‚
                                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Nodes n8n

1. **Schedule Trigger**
   - Intervalo: Toda segunda-feira Ã s 09:00

2. **HTTP Request - Buscar Para Limpar**
   ```
   Method: GET
   URL: http://sua-api:8001/api/jogos/calendario/limpar
   Headers:
     Authorization: Bearer {{$env.SPFC_API_KEY}}
   ```

3. **IF - Tem jogos para limpar?**
   ```
   Condition: {{$json.total_jogos}} > 0
   ```

4. **Loop Over Items**
   - Itera sobre `$json.jogos`

5. **Google Calendar - Delete Event**
   ```
   Calendar: Seu CalendÃ¡rio
   Event ID: {{$json.google_event_id}}
   ```

6. **HTTP Request - Desmarcar**
   ```
   Method: DELETE
   URL: http://sua-api:8001/api/jogos/{{$json.jogo_id}}/calendario
   Headers:
     Authorization: Bearer {{$env.SPFC_API_KEY}}
   ```

---

## Exemplos de Uso

### cURL

#### Listar jogos futuros
```bash
curl -X GET "http://localhost:8001/api/jogos" \
  -H "Authorization: Bearer SUA_API_KEY_AQUI"
```

#### Jogos da semana
```bash
curl -X GET "http://localhost:8001/api/jogos/semana?semanas=2" \
  -H "Authorization: Bearer SUA_API_KEY_AQUI"
```

#### Marcar jogo no calendÃ¡rio
```bash
curl -X POST "http://localhost:8001/api/jogos/b22420564665/marcar-calendario" \
  -H "Authorization: Bearer SUA_API_KEY_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"jogo_id": "b22420564665", "google_event_id": "abc123"}'
```

#### Desmarcar jogo
```bash
curl -X DELETE "http://localhost:8001/api/jogos/b22420564665/calendario" \
  -H "Authorization: Bearer SUA_API_KEY_AQUI"
```

### PowerShell

```powershell
$headers = @{
    "Authorization" = "Bearer SUA_API_KEY_AQUI"
}

# Buscar jogos pendentes
$response = Invoke-WebRequest -Uri "http://localhost:8001/api/jogos/pendentes" `
    -Method Get -Headers $headers
$jogos = ($response.Content | ConvertFrom-Json).jogos

# Marcar jogo
$body = @{
    jogo_id = "b22420564665"
    google_event_id = "abc123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/jogos/b22420564665/marcar-calendario" `
    -Method Post -Headers $headers -Body $body -ContentType "application/json"
```

### Python

```python
import requests

API_URL = "http://localhost:8001"
API_KEY = "SUA_API_KEY_AQUI"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Buscar jogos pendentes
response = requests.get(f"{API_URL}/api/jogos/pendentes", headers=headers)
jogos = response.json()["jogos"]

for jogo in jogos:
    print(f"Pendente: {jogo['adversario']} - {jogo['data']}")
    
    # Criar evento no Google Calendar (exemplo)
    google_event_id = criar_evento_google(jogo)
    
    # Marcar como criado
    requests.post(
        f"{API_URL}/api/jogos/{jogo['jogo_id']}/marcar-calendario",
        headers=headers,
        json={
            "jogo_id": jogo["jogo_id"],
            "google_event_id": google_event_id
        }
    )
```

### JavaScript/Node.js

```javascript
const API_URL = "http://localhost:8001";
const API_KEY = "SUA_API_KEY_AQUI";

const headers = {
  "Authorization": `Bearer ${API_KEY}`,
  "Content-Type": "application/json"
};

// Buscar jogos pendentes
async function buscarPendentes() {
  const response = await fetch(`${API_URL}/api/jogos/pendentes`, { headers });
  const data = await response.json();
  return data.jogos;
}

// Marcar jogo no calendÃ¡rio
async function marcarCalendario(jogoId, googleEventId) {
  await fetch(`${API_URL}/api/jogos/${jogoId}/marcar-calendario`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      jogo_id: jogoId,
      google_event_id: googleEventId
    })
  });
}
```

---

## Troubleshooting

### Erro 401 - API Key invÃ¡lida

**Causa:** Header de autorizaÃ§Ã£o ausente ou incorreto.

**SoluÃ§Ã£o:**
```bash
# Verificar header
curl -v -H "Authorization: Bearer SUA_KEY_AQUI" http://localhost:8001/api/jogos
```

### Erro 429 - Rate Limit

**Causa:** Muitas requisiÃ§Ãµes em pouco tempo.

**SoluÃ§Ã£o:** Aguardar 60 segundos ou ajustar `RATE_LIMIT_REQUESTS` no `.env`.

### Erro 500 - Firecrawl

**Causa:** Falha na comunicaÃ§Ã£o com Firecrawl.

**SoluÃ§Ãµes:**
1. Verificar `FIRECRAWL_API_KEY` no `.env`
2. Verificar crÃ©ditos disponÃ­veis na conta Firecrawl
3. API tentarÃ¡ 3x automaticamente com retry

### Cache nÃ£o atualiza

**Causa:** Cache ainda Ã© vÃ¡lido (Ãºltimo jogo nÃ£o passou).

**SoluÃ§Ãµes:**
1. Usar `force_refresh=true`
2. Chamar `POST /api/cache/limpar`
3. Verificar status com `GET /api/cache/status`

### Jogos duplicados no Calendar

**Causa:** Workflow n8n rodou sem verificar `criado_no_calendario`.

**SoluÃ§Ã£o:** Usar endpoint `/api/jogos/pendentes` que jÃ¡ filtra jogos nÃ£o-criados.

### Container nÃ£o inicia

**Verificar logs:**
```bash
docker logs api-spfc-calendario
```

**Causas comuns:**
- `.env` nÃ£o existe ou estÃ¡ incompleto
- Porta 8001 jÃ¡ em uso
- Volume com permissÃµes incorretas

---

## VariÃ¡veis de Ambiente

| VariÃ¡vel | ObrigatÃ³ria | PadrÃ£o | DescriÃ§Ã£o |
|----------|-------------|--------|-----------|
| `FIRECRAWL_API_KEY` | Sim | - | Chave da API Firecrawl |
| `API_KEY` | Sim | - | Chave para autenticaÃ§Ã£o da API |
| `RATE_LIMIT_REQUESTS` | NÃ£o | 30 | RequisiÃ§Ãµes por janela |
| `RATE_LIMIT_WINDOW` | NÃ£o | 60 | Janela em segundos |
| `FIRECRAWL_MAX_RETRIES` | NÃ£o | 3 | Tentativas em caso de erro |
| `FIRECRAWL_RETRY_DELAY` | NÃ£o | 5 | Segundos entre tentativas |
| `CORS_ORIGINS` | NÃ£o | * | Origins CORS permitidas (separadas por vÃ­rgula) |
| `ALLOWED_HOSTS` | NÃ£o | * | Hosts permitidos (separados por vÃ­rgula) |

### Exemplo `.env`

```env
# Firecrawl
FIRECRAWL_API_KEY=fc-sua-chave-aqui
FIRECRAWL_MAX_RETRIES=3
FIRECRAWL_RETRY_DELAY=5

# API Security
API_KEY=sua-api-key-segura-aqui

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60

# CORS (domÃ­nios do frontend/n8n)
CORS_ORIGINS=https://marcuspaixao.com.br,https://n8n.marcuspaixao.com.br

# Hosts (para produÃ§Ã£o)
ALLOWED_HOSTS=api.marcuspaixao.com.br,localhost
```

> âš ï¸ **IMPORTANTE:** Nunca commite o arquivo `.env` no git! Use `.env.example` como template.

---

## Contato & Suporte

- **Swagger UI:** http://seu-servidor:8001/docs
- **ReDoc:** http://seu-servidor:8001/redoc
- **Health Check:** http://seu-servidor:8001/health

---

*DocumentaÃ§Ã£o gerada em Fevereiro 2026*

