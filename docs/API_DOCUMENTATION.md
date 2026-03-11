# Documentação Técnica - API Calendário SPFC

> API de Web Scraping para extração automática de jogos do São Paulo FC com integração Google Calendar via n8n.

**Versão:** 1.1.0
**Base URL:** `http://seudominio:8001`
**Última atualização:** Março 2026

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Autenticação](#autenticação)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Listar Jogos](#listar-jogos)
   - [Jogos da Semana](#jogos-da-semana)
   - [Jogos da Semana Pendentes](#jogos-da-semana-pendentes)
   - [Próximo Jogo](#próximo-jogo)
   - [Jogos Pendentes](#jogos-pendentes)
   - [Jogos no Calendário](#jogos-no-calendário)
   - [Jogos para Limpar](#jogos-para-limpar)
   - [Marcar Jogo no Calendário](#marcar-jogo-no-calendário)
   - [Desmarcar Jogo do Calendário](#desmarcar-jogo-do-calendário)
   - [Status do Cache](#status-do-cache)
   - [Limpar Cache](#limpar-cache)
6. [Modelos de Dados](#modelos-de-dados)
7. [Sistema de Cache](#sistema-de-cache)
8. [Segurança](#segurança)
9. [Integração n8n](#integração-n8n)
10. [Exemplos de Uso](#exemplos-de-uso)
11. [Troubleshooting](#troubleshooting)

---

## Visão Geral

Esta API foi desenvolvida para:

- **Extrair automaticamente** jogos do calendário oficial do São Paulo FC
- **Cachear dados inteligentemente** para economizar créditos do Firecrawl
- **Integrar com n8n** para sincronização automática com Google Calendar
- **Controlar sincronização** marcando jogos já adicionados ao calendário

### Fluxo de Funcionamento

```
+-------------------+     +-------------------+     +-------------------+
|   Site SPFC       |---->|   Firecrawl       |---->|   API SPFC        |
|   (calendário)    |     |   (scraping)      |     |   (cache JSON)    |
+-------------------+     +-------------------+     +---------+---------+
                                                              |
                          +-------------------+               |
                          |  Google Calendar  |<--------------+
                          +-------------------+               |
                                   ^                          |
                                   |              +-----------v---------+
                                   +--------------+       n8n           |
                                                  |    (workflow)       |
                                                  +---------------------+
```

---

## Arquitetura

### Stack Tecnológica

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| Framework | FastAPI | >= 0.128.0 |
| Runtime | Python | 3.11 |
| Scraping | Firecrawl | >= 4.14.0 |
| Validação | Pydantic | >= 2.12.5 |
| Container | Docker | - |
| Proxy | Cloudflare + nginx | - |

### Estrutura de Diretórios

```
API-SP/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI principal
│   ├── config.py            # Configurações (env vars)
│   ├── models.py            # Modelos Pydantic
│   ├── scraper.py           # Lógica de scraping + cache
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py  # Rate limiting por IP
│   │   └── security.py      # Headers de segurança
│   └── routes/
│       └── calendario.py    # Endpoints da API
├── data/
│   └── cache_jogos.json     # Cache persistente
├── docs/
│   └── API_DOCUMENTATION.md # Esta documentação
├── .env                     # Variáveis de ambiente
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Autenticação

A API utiliza **Bearer Token** para autenticação.

### Header Necessário

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

### Respostas de Erro de Autenticação

| Código | Descrição |
|--------|-----------|
| 401 | API Key inválida ou ausente |
| 500 | API_KEY não configurada no servidor |

---

## Rate Limiting

A API implementa rate limiting para proteção contra abuso.

### Limites Padrão

| Parâmetro | Valor | Configurável |
|-----------|-------|--------------|
| Requisições | 30 | `RATE_LIMIT_REQUESTS` |
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
  "limite": "30 requisições por 60 segundos",
  "retry_after": 60
}
```

**HTTP Status:** 429 Too Many Requests

---

## Endpoints

### Health Check

Verifica se a API está funcionando. **Não requer autenticação.**

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

Retorna todos os jogos do calendário do SPFC.

```http
GET /api/jogos
```

#### Parâmetros Query

| Parâmetro | Tipo | Padrão | Descrição |
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
      "competicao": "Brasileirão 2026",
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

Retorna jogos das próximas N semanas. **Ideal para workflow semanal.**

```http
GET /api/jogos/semana
```

#### Parâmetros Query

| Parâmetro | Tipo | Padrão | Range | Descrição |
|-----------|------|--------|-------|-----------|
| `semanas` | integer | `1` | 1-8 | Número de semanas |
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

### Jogos da Semana Pendentes

Retorna jogos das próximas N semanas que **NÃO** foram adicionados ao Google Calendar.

**Ideal para workflow semanal do n8n** - combina filtro de semana + pendentes.

```http
GET /api/jogos/semana/pendentes
```

#### Parâmetros Query

| Parâmetro | Tipo | Padrão | Range | Descrição |
|-----------|------|--------|-------|-----------|
| `semanas` | integer | `1` | 1-8 | Número de semanas |
| `force_refresh` | boolean | `false` | - | Ignorar cache |

#### Exemplo

```http
GET /api/jogos/semana/pendentes?semanas=1
```

#### Uso no n8n (Recomendado)

Este endpoint é o **ponto de entrada ideal** para workflows semanais:

1. Trigger semanal (ex: toda segunda-feira)
2. Chamar `/api/jogos/semana/pendentes`
3. Para cada jogo, criar evento no Calendar
4. Marcar jogo com `POST /api/jogos/{jogo_id}/marcar-calendario`

#### Resposta

```json
{
  "sucesso": true,
  "total_jogos": 2,
  "jogos": [
    {
      "jogo_id": "c144182ca543",
      "adversario": "Primavera SAF",
      "competicao": "Campeonato Paulista 2026",
      "data": "07/02/2026",
      "horario": "20:30",
      "criado_no_calendario": false,
      "google_event_id": null
    }
  ],
  "atualizado_em": "2026-02-06T12:00:00.000000",
  "cache": true
}
```

---

### Próximo Jogo

Retorna apenas o próximo jogo futuro do SPFC.

```http
GET /api/proximo-jogo
```

#### Parâmetros Query

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `force_refresh` | boolean | `false` | Ignorar cache |

#### Resposta

```json
{
  "sucesso": true,
  "jogo": {
    "competicao": "Brasileirão 2026",
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

Retorna jogos futuros que **NÃO** foram adicionados ao Google Calendar.

```http
GET /api/jogos/pendentes
```

#### Parâmetros Query

| Parâmetro | Tipo | Padrão | Range | Descrição |
|-----------|------|--------|-------|-----------|
| `semanas` | integer | `4` | 1-8 | Semanas a considerar |

#### Uso no n8n

Este endpoint é o **ponto de entrada principal** para o workflow de criação de eventos.

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
      "google_event_id": null
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Jogos no Calendário

Retorna jogos que estão marcados como sincronizados com o Google Calendar.

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
      "google_event_id": "abc123googleevent"
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Jogos para Limpar

Retorna jogos **passados** que ainda estão no calendário (para remoção).

```http
GET /api/jogos/calendario/limpar
```

#### Uso no n8n

Este endpoint é usado para **limpar eventos antigos** do Google Calendar.

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
      "google_event_id": "googleevent456"
    }
  ],
  "atualizado_em": "2026-02-04T15:00:00.000000",
  "cache": true
}
```

---

### Marcar Jogo no Calendário

Marca um jogo como adicionado ao Google Calendar.

```http
POST /api/jogos/{jogo_id}/marcar-calendario
```

#### Parâmetros Path

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `jogo_id` | string | ID único do jogo (campo `jogo_id`) |

#### Body (JSON)

```json
{
  "google_event_id": "abc123googlecalendar"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `google_event_id` | string | Não | ID do evento no Google Calendar |

#### Resposta Sucesso

```json
{
  "sucesso": true,
  "mensagem": "Jogo b22420564665 marcado como criado no calendário",
  "google_event_id": "abc123googlecalendar",
  "timestamp": "2026-02-04T15:00:00.000000"
}
```

#### Resposta Erro (404)

```json
{
  "detail": "Jogo com ID 'xyz' não encontrado"
}
```

---

### Desmarcar Jogo do Calendário

Remove a marcação de um jogo (quando o evento é deletado do Calendar).

```http
DELETE /api/jogos/{jogo_id}/calendario
```

#### Parâmetros Path

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `jogo_id` | string | ID único do jogo |

#### Resposta Sucesso

```json
{
  "sucesso": true,
  "mensagem": "Jogo b22420564665 desmarcado do calendário",
  "google_event_id": "abc123googlecalendar",
  "timestamp": "2026-02-04T15:00:00.000000"
}
```

> **Nota:** O `google_event_id` é retornado para que você possa deletar o evento do Google Calendar.

---

### Status do Cache

Retorna informações sobre o estado do cache.

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
  "proxima_atualizacao": "Quando o último jogo passar",
  "arquivo": "/app/data/cache_jogos.json"
}
```

#### Campos Importantes

| Campo | Descrição |
|-------|-----------|
| `cache_valido` | `true` se ainda há jogos futuros no cache |
| `ultimo_jogo_data` | Data do último jogo - cache válido até esta data |
| `proxima_atualizacao` | Indica quando o cache será renovado |

---

### Limpar Cache

Força limpeza do cache. Próxima requisição buscará dados novos.

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

> **Cuidado:** Limpar o cache vai consumir créditos do Firecrawl na próxima requisição.

---

## Modelos de Dados

### Jogo

O modelo principal que representa um jogo do SPFC.

```typescript
interface Jogo {
  // Identificação
  jogo_id: string;           // ID único (hash MD5 de data+hora+adversário+competição)

  // Informações do jogo
  competicao: string;        // Ex: "Brasileirão 2026", "Campeonato Paulista 2026"
  adversario: string;        // Nome do time adversário
  adversario_logo?: string;  // URL do escudo do adversário
  data: string;              // Formato DD/MM/YYYY
  dia_semana?: string;       // Ex: "Quarta", "Sábado"
  horario: string;           // Formato HH:MM
  local?: string;            // Nome do estádio
  mandante?: boolean;        // true = SPFC joga em casa

  // Campos para Google Calendar
  data_iso?: string;         // ISO 8601: "2026-02-04T20:00:00-03:00"
  data_fim_iso?: string;     // ISO 8601: "2026-02-04T22:00:00-03:00" (2h depois)

  // Controle de sincronização
  criado_no_calendario: boolean;  // Se já foi adicionado ao Calendar
  google_event_id?: string;       // ID do evento no Google Calendar
}
```

### CalendarioResponse

Resposta padrão para endpoints que retornam lista de jogos.

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

Informações sobre o estado do cache.

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

O cache inteligente economiza créditos do Firecrawl:

1. **Primeira requisição**: Busca dados do Firecrawl -> Salva em JSON
2. **Requisições seguintes**: Verifica se último jogo já passou
   - Se NÃO passou -> Usa cache (0 créditos)
   - Se passou -> Busca novos dados

### Lógica de Validação

```
Cache VÁLIDO se:
  último_jogo_data + 3 horas > agora

Cache EXPIRADO se:
  último_jogo_data + 3 horas < agora
```

### Arquivo de Cache

Localização: `/app/data/cache_jogos.json`

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

### Economia de Créditos

| Cenário | Créditos Usados |
|---------|-----------------|
| Cache válido | 0 |
| Cache expirado | ~87 |
| `force_refresh=true` | ~87 |
| Limpar cache + requisição | ~87 |

---

## Segurança

### Headers de Segurança

Todas as respostas incluem:

| Header | Valor | Proteção |
|--------|-------|----------|
| `X-XSS-Protection` | `1; mode=block` | Cross-Site Scripting |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Vazamento de referrer |
| `Content-Security-Policy` | `default-src 'self'` | Injeção de conteúdo |
| `Cache-Control` | `no-store, no-cache` | Cache de dados sensíveis |
| `X-Powered-By` | `SPFC-API` | Oculta tecnologia real |

### Compatibilidade com Cloudflare

A API detecta automaticamente IPs reais através de:

1. `CF-Connecting-IP` (Cloudflare)
2. `X-Forwarded-For` (Proxies)
3. `X-Real-IP` (nginx)

### Retry Automático

Se o Firecrawl falhar:

- **Tentativas:** 3 (configurável via `FIRECRAWL_MAX_RETRIES`)
- **Intervalo:** 5 segundos (configurável via `FIRECRAWL_RETRY_DELAY`)
- **Fallback:** Retorna cache antigo se disponível

---

## Integração n8n

### Workflow 1: Criar Eventos (Semanal)

```
+-----------+     +-------------+     +-------------+     +-------------+
|  Trigger  |---->| GET jogos/  |---->| Loop: cada  |---->|   Criar     |
|  Semanal  |     | pendentes   |     |    jogo     |     | evento GCal |
+-----------+     +-------------+     +------+------+     +------+------+
                                             |                    |
                                             |    +---------------+
                                             v    v
                                      +-------------+
                                      | POST marcar |
                                      | -calendário |
                                      +-------------+
```

#### Nodes n8n

1. **Schedule Trigger**
   - Intervalo: Toda segunda-feira às 08:00

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
   Calendar: Seu Calendário
   Title: SPFC x {{$json.adversario}} - {{$json.competicao}}
   Start: {{$json.data_iso}}
   End: {{$json.data_fim_iso}}
   Location: {{$json.local}}
   Description: {{$json.mandante ? "Jogo em casa" : "Jogo fora"}}
   ```

5. **HTTP Request - Marcar Calendário**
   ```
   Method: POST
   URL: http://sua-api:8001/api/jogos/{{$json.jogo_id}}/marcar-calendario
   Headers:
     Authorization: Bearer {{$env.SPFC_API_KEY}}
     Content-Type: application/json
   Body:
     {
       "google_event_id": "{{$node["Google Calendar"].json.id}}"
     }
   ```

---

### Workflow 2: Limpar Eventos Antigos (Semanal)

```
+-----------+     +-------------+     +-------------+     +-------------+
|  Trigger  |---->| GET jogos/  |---->| Loop: cada  |---->|   Deletar   |
|  Semanal  |     | calendário/ |     |    jogo     |     | evento GCal |
|           |     | limpar      |     +------+------+     +------+------+
+-----------+     +-------------+            |                    |
                                             |    +---------------+
                                             v    v
                                      +-------------+
                                      |   DELETE    |
                                      | /calendário |
                                      +-------------+
```

#### Nodes n8n

1. **Schedule Trigger**
   - Intervalo: Toda segunda-feira às 09:00

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
   Calendar: Seu Calendário
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

#### Jogos da semana pendentes (recomendado para n8n)
```bash
curl -X GET "http://localhost:8001/api/jogos/semana/pendentes?semanas=1" \
  -H "Authorization: Bearer SUA_API_KEY_AQUI"
```

#### Marcar jogo no calendário
```bash
curl -X POST "http://localhost:8001/api/jogos/b22420564665/marcar-calendario" \
  -H "Authorization: Bearer SUA_API_KEY_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"google_event_id": "abc123"}'
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
        json={"google_event_id": google_event_id}
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

// Marcar jogo no calendário
async function marcarCalendario(jogoId, googleEventId) {
  await fetch(`${API_URL}/api/jogos/${jogoId}/marcar-calendario`, {
    method: "POST",
    headers,
    body: JSON.stringify({ google_event_id: googleEventId })
  });
}
```

---

## Troubleshooting

### Erro 401 - API Key inválida

**Causa:** Header de autorização ausente ou incorreto.

**Solução:**
```bash
# Verificar header
curl -v -H "Authorization: Bearer SUA_KEY_AQUI" http://localhost:8001/api/jogos
```

### Erro 429 - Rate Limit

**Causa:** Muitas requisições em pouco tempo.

**Solução:** Aguardar 60 segundos ou ajustar `RATE_LIMIT_REQUESTS` no `.env`.

### Erro 500 - Firecrawl

**Causa:** Falha na comunicação com Firecrawl.

**Soluções:**
1. Verificar `FIRECRAWL_API_KEYS` no `.env`
2. Verificar créditos disponíveis nas contas Firecrawl
3. API tentará automaticamente com todas as keys configuradas
4. Adicionar mais API keys para load-balance

### Cache não atualiza

**Causa:** Cache ainda é válido (último jogo não passou).

**Soluções:**
1. Usar `force_refresh=true`
2. Chamar `POST /api/cache/limpar`
3. Verificar status com `GET /api/cache/status`

### Jogos duplicados no Calendar

**Causa:** Workflow n8n rodou sem verificar `criado_no_calendario`.

**Solução:** Usar endpoint `/api/jogos/pendentes` que já filtra jogos não-criados.

### Container não inicia

**Verificar logs:**
```bash
docker logs api-spfc-calendario
```

**Causas comuns:**
- `.env` não existe ou está incompleto
- Porta 8001 já em uso
- Volume com permissões incorretas

---

## Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `FIRECRAWL_API_KEYS` | Sim | - | Chaves da API Firecrawl (separadas por vírgula para load-balance) |
| `API_KEY` | Sim | - | Chave para autenticação da API |
| `RATE_LIMIT_REQUESTS` | Não | 30 | Requisições por janela |
| `RATE_LIMIT_WINDOW` | Não | 60 | Janela em segundos |
| `FIRECRAWL_MAX_RETRIES` | Não | 3 | Tentativas em caso de erro |
| `FIRECRAWL_RETRY_DELAY` | Não | 5 | Segundos entre tentativas |
| `CORS_ORIGINS` | Não | * | Origins CORS permitidas (separadas por vírgula) |
| `ALLOWED_HOSTS` | Não | * | Hosts permitidos (separados por vírgula) |

### Exemplo `.env`

```env
# Firecrawl - Múltiplas keys para load-balance (quando uma fica sem créditos, usa a próxima)
FIRECRAWL_API_KEYS=fc-key1-aqui,fc-key2-aqui,fc-key3-aqui
FIRECRAWL_MAX_RETRIES=3
FIRECRAWL_RETRY_DELAY=5

# API Security
API_KEY=sua-api-key-segura-aqui

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60

# CORS (domínios do frontend/n8n)
CORS_ORIGINS=https://seudominio.com.br

# Hosts (para produção)
ALLOWED_HOSTS=api.seudominio.com.br,localhost
```

> **IMPORTANTE:** Nunca commite o arquivo `.env` no git! Use `.env.example` como template.

---

## Contato & Suporte

- **Swagger UI:** http://seudominio:8001/docs
- **ReDoc:** http://seudominio:8001/redoc
- **Health Check:** http://seudominio:8001/health

---

*Documentação atualizada em Março 2026*
