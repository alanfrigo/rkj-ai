# Guia de Deploy em Produção

Este guia cobre o processo de deploy da aplicação completa usando **Easypanel** para gerenciamento de containers Docker.

---

## 📋 Arquitetura de Produção

| Componente | Serviço |
|------------|---------|
| **Banco de Dados** | Supabase Cloud (gerenciado) |
| **Armazenamento** | Cloudflare R2 |
| **Backend Services** | Easypanel (Docker Compose) |
| **Frontend** | Vercel ou Easypanel |

### Serviços Docker (Easypanel)

```
┌─────────────────────────────────────────────────────────────┐
│                       Easypanel                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    Redis     │  │  Orchestrator │  │ Transcription│       │
│  │   (Cache)    │  │   (Bot Mgmt)  │  │   Worker     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                           │                                  │
│                           ▼ (spawns)                         │
│                    ┌──────────────┐                          │
│                    │   Meet Bot   │ ← Containers dinâmicos   │
│                    │  (Chrome)    │                          │
│                    └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Passo 1: Configurar Supabase Cloud

### 1.1 Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com) e crie um projeto
2. Vá em **Project Settings > Database** e copie a Connection String
3. Vá em **Project Settings > API** e copie:
   - `Project URL` (ex: `https://xxxx.supabase.co`)
   - `anon key` (para frontend)
   - `service_role key` (para backend - **NUNCA** exponha no frontend)

### 1.2 Aplicar Migrations

```bash
# No seu ambiente local
cd supabase

# Login e link ao projeto
supabase login
supabase link --project-ref seu-project-ref

# Aplicar migrations
supabase db push
```

### 1.3 Configurar Google OAuth no Supabase

1. No Supabase Dashboard, vá em **Authentication > Providers**
2. Habilite **Google** e configure:
   - Client ID (do Google Cloud Console)
   - Client Secret (do Google Cloud Console)
3. Adicione as URLs de callback:
   ```
   https://seu-dominio.com/callback
   https://seu-dominio.com/api/calendar/callback
   ```

---

## Passo 2: Configurar Cloudflare R2

1. Acesse [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Crie um bucket R2 chamado `meeting-assistant`
3. Em **R2 > Manage R2 API Tokens**, crie um token com permissão **Admin Read & Write**
4. Anote:
   - `Account ID`
   - `Access Key ID`
   - `Secret Access Key`

---

## Passo 3: Configurar Easypanel

### 3.1 Criar Projeto no Easypanel

1. Acesse seu painel Easypanel
2. Crie um novo projeto: `meeting-assistant`

### 3.2 Configurar Variáveis de Ambiente

No Easypanel, vá em **Settings > Environment** e adicione:

```env
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...

# Cloudflare R2
R2_ACCOUNT_ID=xxxx
R2_ACCESS_KEY_ID=xxxx
R2_SECRET_ACCESS_KEY=xxxx
R2_BUCKET_NAME=meeting-assistant
R2_PUBLIC_URL=https://pub-xxx.r2.dev

# OpenAI
OPENAI_API_KEY=sk-xxxx

# Google OAuth (para sincronização de calendário)
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx

# Bot Configuration
BOT_DISPLAY_NAME=Meeting Assistant Bot 🤖
BOT_JOIN_BEFORE_MINUTES=2
BOT_MAX_DURATION_HOURS=4

# Docker (interno ao Easypanel)
BOT_IMAGE=docker-meet-bot:latest
DOCKER_NETWORK=meeting-assistant-network
RECORDINGS_VOLUME=recordings

# Logging
LOG_LEVEL=INFO
```

### 3.3 Criar docker-compose.prod.yml

Crie um arquivo `docker-compose.prod.yml` para Easypanel:

```yaml
version: '3.8'

services:
  # Redis (Cache e Message Queue)
  redis:
    image: redis:7-alpine
    container_name: rkj-redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rkj-ai

  # Bot Orchestrator
  bot-orchestrator:
    build:
      context: ./services/bot-orchestrator
    container_name: rkj-bot-orchestrator
    restart: always
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_URL=redis://redis:6379
      - R2_ACCOUNT_ID=${R2_ACCOUNT_ID}
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_BUCKET_NAME=${R2_BUCKET_NAME}
      - R2_PUBLIC_URL=${R2_PUBLIC_URL}
      - BOT_DISPLAY_NAME=${BOT_DISPLAY_NAME}
      - BOT_MAX_DURATION_HOURS=${BOT_MAX_DURATION_HOURS}
      - BOT_IMAGE=${BOT_IMAGE}
      - DOCKER_NETWORK=${DOCKER_NETWORK}
      - RECORDINGS_VOLUME=${RECORDINGS_VOLUME}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - recordings:/recordings
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - rkj-ai

  # Transcription Worker
  transcription-worker:
    build:
      context: ./services/transcription-worker
    container_name: rkj-transcription-worker
    restart: always
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_URL=redis://redis:6379
      - R2_ACCOUNT_ID=${R2_ACCOUNT_ID}
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_BUCKET_NAME=${R2_BUCKET_NAME}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - recordings:/recordings:ro
      - temp_audio:/tmp/audio
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - rkj-ai

  # Meet Bot (BUILD ONLY - spawned dynamically)
  meet-bot:
    build:
      context: ./services/meet-bot
    image: docker-meet-bot:latest
    profiles:
      - build-only

volumes:
  redis_data:
  recordings:
  temp_audio:

networks:
  rkj-ai:
    driver: bridge
    name: rkj-ai-network
```

---

## Passo 4: Build e Deploy no Easypanel

### 4.1 Conectar Repositório

1. No Easypanel, conecte seu repositório GitHub
2. Configure o branch de produção (ex: `main`)

### 4.2 Build das Imagens

> [!IMPORTANT]
> O `meet-bot` usa `profiles: [build-only]` porque é **inicializado dinamicamente** pelo `bot-orchestrator` quando um usuário agenda uma reunião. A imagem precisa ser construída antes do deploy.

```bash
# No servidor ou via Easypanel terminal
docker compose -f docker-compose.prod.yml build

# Verificar se a imagem meet-bot foi criada
docker images | grep meet-bot
```

### 4.3 Iniciar Serviços

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4.4 Verificar Deploy

```bash
# Logs do orchestrator
docker logs -f rkj-bot-orchestrator

# Status dos containers
docker ps

# Verificar se meet-bot image existe
docker images | grep docker-meet-bot
```

---

## Passo 5: Deploy do Frontend (Vercel)

### Opção A: Vercel (Recomendado)

1. Importe o projeto `apps/web` na Vercel
2. Configure as variáveis de ambiente:

| Variável | Valor |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | URL do projeto Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key do Supabase |
| `SUPABASE_SERVICE_KEY` | Service role key |
| `ORCHESTRATOR_URL` | URL do orchestrator no Easypanel |

### Opção B: Frontend no Easypanel

Adicione o serviço `web` ao docker-compose:

```yaml
web:
  build:
    context: ./apps/web
    args:
      - NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
  container_name: rkj-web
  restart: always
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
    - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    - SUPABASE_URL=${SUPABASE_URL}
    - ORCHESTRATOR_URL=http://bot-orchestrator:8002
  depends_on:
    - bot-orchestrator
  networks:
    - meeting-assistant
```

---

## Passo 6: Configurar Domínio e SSL

### No Easypanel

1. Vá em **Domains**
2. Adicione seu domínio (ex: `api.seusite.com`)
3. Configure SSL automático via Let's Encrypt

### Configurar Proxy Reverso

Para expor o orchestrator externamente (se necessário para webhooks):

```yaml
# No Easypanel, configure o serviço com:
ports:
  - "8002:8002"
```

---

## 📋 Checklist de Produção

### Segurança
- [ ] Redis com autenticação (se exposto)
- [ ] Secrets armazenados no Easypanel (nunca em código)
- [ ] HTTPS habilitado em todos os endpoints
- [ ] `SUPABASE_SERVICE_KEY` apenas no backend

### Bot Configuration
- [ ] Imagem `docker-meet-bot:latest` construída
- [ ] Docker socket montado no orchestrator
- [ ] Network `meeting-assistant-network` criada
- [ ] Volume `recordings` criado

### Monitoramento
- [ ] Logs configurados (Easypanel tem integração)
- [ ] Alertas de health check
- [ ] Limpeza automática de containers meet-bot antigos

### Manutenção
```bash
# Limpeza de containers antigos (cronjob recomendado)
docker container prune -f --filter "label=meeting_id"
docker system prune -f
```

---

## Troubleshooting

### Bot não entra na reunião

1. Verifique se a imagem existe:
   ```bash
   docker images | grep meet-bot
   ```

2. Verifique logs do orchestrator:
   ```bash
   docker logs rkj-bot-orchestrator
   ```

3. Verifique se o Docker socket está montado:
   ```bash
   docker exec rkj-bot-orchestrator ls -la /var/run/docker.sock
   ```

### Erro "ImageNotFound"

A imagem `docker-meet-bot:latest` precisa ser construída:

```bash
docker compose -f docker-compose.prod.yml build meet-bot
```

### Containers meet-bot ficam presos

Limpe containers órfãos:

```bash
docker ps -a | grep meet-bot | awk '{print $1}' | xargs docker rm -f
```

---

## Atualização

Para atualizar a aplicação:

```bash
# Pull do código
git pull origin main

# Rebuild das imagens
docker compose -f docker-compose.prod.yml build

# Restart dos serviços
docker compose -f docker-compose.prod.yml up -d

# Verificar
docker ps
docker logs -f rkj-bot-orchestrator
```
