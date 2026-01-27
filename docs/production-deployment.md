# Guia de Deploy em Produção: Vercel + VPS

Este guia cobre o deploy da aplicação usando **Vercel** para o frontend e uma **VPS** para o backend e serviços.

> [!NOTE]
> **Arquitetura:**
> - Frontend (Next.js) → **Vercel** (CDN global, Edge Functions)
> - Backend (FastAPI, Redis, Workers) → **VPS** (Hetzner, DigitalOcean)

---

## 📋 Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────┐
│                          USUÁRIO                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
    ┌───────────────────────┴───────────────────────┐
    │                                               │
    ▼                                               ▼
┌─────────────────────┐                 ┌─────────────────────────┐
│      VERCEL         │                 │         VPS             │
├─────────────────────┤                 ├─────────────────────────┤
│ • Next.js Frontend  │ ──────────────► │ • Traefik (SSL)         │
│ • CDN Global        │     HTTPS       │ • FastAPI (API)         │
│ • rkj.ai            │                 │ • Redis (Queue)         │
└─────────────────────┘                 │ • Bot Orchestrator      │
                                        │ • Transcription Worker  │
                                        │ • api.rkj.ai            │
                                        └─────────────────────────┘
```

---

## Passo 1: Deploy do Backend (VPS)

### 1.1 Pré-requisitos VPS

- **OS**: Ubuntu 22.04 ou 24.04 LTS
- **RAM**: Mínimo 8GB (32GB+ para múltiplos bots)
- **DNS**: Configure `api.seudominio.com` → IP da VPS

### 1.2 Configurar `.env`

Crie o arquivo `.env` na raiz do projeto:

```env
# Domínio da API (obrigatório)
API_DOMAIN=api.seudominio.com
ACME_EMAIL=seu-email@dominio.com

# Supabase Cloud
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co

# Cloudflare R2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=meeting-assistant
R2_PUBLIC_URL=https://pub-xxx.r2.dev

# APIs
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### 1.3 Executar Deploy

```bash
# Clonar repositório
git clone https://github.com/seu-repo/meeting-assistant.git
cd meeting-assistant

# Copiar .env
cp .env.production.example .env
# Editar .env com seus valores

# Executar deploy
chmod +x deploy.sh
sudo ./deploy.sh
```

O script irá:
1. Instalar Docker (se necessário)
2. Configurar firewall (portas 22, 80, 443)
3. Build e deploy dos containers
4. Verificar se está rodando

---

## Passo 2: Deploy do Frontend (Vercel)

### 2.1 Conectar Repositório

1. Acesse [vercel.com](https://vercel.com) e conecte seu repositório
2. Configure o projeto:
   - **Framework Preset**: Next.js
   - **Root Directory**: `apps/web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 2.2 Variáveis de Ambiente (Vercel)

No painel do Vercel, adicione estas variáveis:

| Variável | Valor |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbG...` |
| `NEXT_PUBLIC_APP_URL` | `https://rkj.ai` |
| `NEXT_PUBLIC_API_URL` | `https://api.rkj.ai` |

### 2.3 Domínio Customizado

1. Vá em **Settings → Domains**
2. Adicione seu domínio (ex: `rkj.ai`)
3. Configure DNS conforme instruções da Vercel

---

## 3. Verificação

```bash
# Verificar API na VPS
curl https://api.seudominio.com/health

# Verificar containers
docker ps

# Ver logs
docker logs -f rkj-api
docker logs -f rkj-traefik
```

---

## 4. Manutenção

### Atualizar Backend

```bash
cd meeting-assistant
git pull origin main
sudo ./deploy.sh
```

### Atualizar Frontend

Push para a branch `main` → Vercel faz deploy automático.

### Logs Úteis

```bash
# API
docker logs -f rkj-api

# Traefik (SSL/Roteamento)
docker logs -f rkj-traefik

# Bot Orchestrator
docker logs -f rkj-bot-orchestrator

# Transcription Worker
docker logs -f rkj-transcription-worker
```

---

## 5. Troubleshooting

| Problema | Solução |
|----------|---------|
| SSL não funciona | Verificar se DNS propagou: `dig api.seudominio.com` |
| API retorna 502 | Ver logs: `docker logs rkj-api` |
| Frontend não conecta na API | Verificar `NEXT_PUBLIC_API_URL` no Vercel |
| Bots não entram na reunião | Checar logs: `docker logs rkj-bot-orchestrator` |
