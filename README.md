# Meeting Assistant

Um assistente de reuniões inteligente que automatiza a gravação e transcrição de reuniões do Google Meet e Zoom.

## 🎯 Visão Geral

O Meeting Assistant é uma solução self-hosted que:

- **Sincroniza** automaticamente com seu Google Calendar
- **Entra** automaticamente em reuniões do Google Meet e Zoom
- **Grava** áudio e vídeo das reuniões
- **Transcreve** usando OpenAI Whisper API com identificação de speakers
- **Disponibiliza** gravações e transcrições em um dashboard intuitivo

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                       │
│                              (NextJs 16 + Supabase Auth)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Dashboard  │  │  Calendar   │  │  Recordings │  │  Transcription Viewer   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API (FastAPI)                               │
│                                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Calendar   │  │  Meetings   │  │  Recordings │  │    Transcriptions       │ │
│  │   Routes    │  │   Routes    │  │   Routes    │  │       Routes            │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────────┐
│   SCHEDULER         │    │   BOT ORCHESTRATOR  │    │  TRANSCRIPTION WORKER   │
│                     │    │                     │    │                         │
│ • Calendar Sync     │    │ • Bot Lifecycle     │    │ • OpenAI Whisper API    │
│ • Meeting Detection │    │ • Container Mgmt    │    │ • Speaker Diarization   │
│ • Job Scheduling    │    │ • Health Monitoring │    │ • Post Processing       │
└─────────────────────┘    └─────────────────────┘    └─────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BOT WORKERS (Docker)                                │
│  ┌───────────────────────────────┐    ┌───────────────────────────────────────┐ │
│  │      GOOGLE MEET BOT          │    │           ZOOM BOT                    │ │
│  │  • Playwright + Chrome        │    │  • Zoom Meeting SDK                   │ │
│  │  • FFmpeg Recording           │    │  • Native Recording                   │ │
│  └───────────────────────────────┘    └───────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MESSAGE QUEUE (Redis + BullMQ)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │join_meeting │  │  recording  │  │ transcribe  │  │     notification        │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 DATA LAYER                                       │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐  │
│  │      SUPABASE       │    │   CLOUDFLARE R2     │    │       REDIS         │  │
│  │     PostgreSQL      │    │      Storage        │    │       Cache         │  │
│  │                     │    │                     │    │                     │  │
│  │ • Users & Auth      │    │ • Raw Recordings    │    │ • Session State     │  │
│  │ • Meetings          │    │ • Processed Media   │    │ • Bot Status        │  │
│  │ • Transcriptions    │    │ • Audio Files       │    │ • Job Queues        │  │
│  │ • Calendar Events   │    │ • Thumbnails        │    │                     │  │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📁 Estrutura do Projeto

```
meeting-assistant/
├── apps/
│   ├── web/                    # Frontend NextJs 16
│   │   ├── src/
│   │   │   ├── app/           # App Router
│   │   │   ├── components/    # React Components
│   │   │   ├── lib/           # Utilities
│   │   │   └── hooks/         # Custom Hooks
│   │   └── package.json
│   │
│   └── api/                    # Backend FastAPI
│       ├── src/
│       │   ├── routers/       # API Routes
│       │   ├── services/      # Business Logic
│       │   ├── models/        # Pydantic Models
│       │   └── core/          # Config & Utils
│       └── requirements.txt
│
├── services/
│   ├── scheduler/              # Calendar Sync & Scheduling
│   ├── bot-orchestrator/       # Bot Container Management
│   ├── meet-bot/               # Google Meet Bot
│   ├── zoom-bot/               # Zoom Bot
│   ├── transcription-worker/   # OpenAI Whisper Processing
│   └── media-processor/        # FFmpeg Processing
│
├── packages/
│   └── shared/                 # Shared Types & Utils
│
├── infrastructure/
│   ├── docker/                 # Docker Compose
│   ├── supabase/              # Database Migrations
│   └── scripts/               # Deployment Scripts
│
├── docs/                       # Documentation
├── README.md
├── CLAUDE.md                   # AI Assistant Context
└── .env.example
```

## 🛠️ Tech Stack

| Componente | Tecnologia |
|------------|------------|
| Frontend | NextJs 16, TypeScript, Tailwind CSS, shadcn/ui |
| Backend API | FastAPI, Python 3.11+ |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth + Google OAuth |
| Storage | Cloudflare R2 |
| Queue | Redis + BullMQ |
| Transcription | OpenAI Whisper API |
| Bot Runtime | Playwright, Docker |
| Containers | Docker, Docker Compose |

## 🚀 Quick Start

### Pré-requisitos

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Conta Supabase
- Conta Cloudflare (R2)
- Conta OpenAI (API Key)
- Google Cloud Console (OAuth + Calendar API)

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/meeting-assistant.git
cd meeting-assistant
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 3. Inicie os serviços

```bash
# Desenvolvimento
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Ou use o script
./scripts/dev.sh
```

### 4. Execute as migrations

```bash
cd infrastructure/supabase
supabase db push
```

### 5. Inicie o frontend

```bash
cd apps/web
pnpm install
pnpm dev
```

## ⚙️ Configuração

### Google Cloud Console

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com)
2. Ative as APIs:
   - Google Calendar API
   - Google People API
3. Configure OAuth 2.0:
   - Tipo: Web Application
   - Redirect URIs: `http://localhost:3000/api/auth/callback/google`
4. Copie Client ID e Client Secret para `.env`

### Supabase

1. Crie um projeto no [Supabase](https://supabase.com)
2. Copie URL e API Keys para `.env`
3. Execute as migrations em `infrastructure/supabase/`

### Cloudflare R2

1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Crie um bucket R2 chamado `meeting-assistant`
3. Gere API Token com permissões R2
4. Copie Account ID, Access Key e Secret Key para `.env`

### OpenAI

1. Acesse [OpenAI Platform](https://platform.openai.com)
2. Gere uma API Key
3. Copie para `.env`

## 📋 Variáveis de Ambiente

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Cloudflare R2
R2_ACCOUNT_ID=xxx
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=meeting-assistant
R2_PUBLIC_URL=https://pub-xxx.r2.dev

# OpenAI
OPENAI_API_KEY=sk-xxx

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Redis
REDIS_URL=redis://localhost:6379

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
API_URL=http://localhost:8000
```

## 🔄 Fluxo de Funcionamento

1. **Usuário conecta Google Calendar** → OAuth flow salva refresh token
2. **Scheduler sincroniza eventos** → A cada 5 minutos, busca eventos com links de reunião
3. **2 minutos antes da reunião** → Job é enfileirado para o bot entrar
4. **Bot Orchestrator** → Inicia container Docker com o bot apropriado
5. **Bot entra na reunião** → Playwright navega e entra no Google Meet
6. **Gravação inicia** → FFmpeg captura tela + áudio
7. **Reunião termina** → Bot detecta e finaliza gravação
8. **Upload para R2** → Arquivo é enviado para Cloudflare R2
9. **Transcrição** → OpenAI Whisper API processa o áudio
10. **Disponibilização** → Usuário acessa gravação e transcrição no dashboard

## 📖 API Documentation

Após iniciar o backend, acesse:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testes

```bash
# Backend
cd apps/api
pytest

# Frontend
cd apps/web
pnpm test
```

## 🚢 Deploy

### Docker (Recomendado)

```bash
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d
```

### Kubernetes

```bash
kubectl apply -f infrastructure/k8s/
```

## 📝 Roadmap

- [x] Arquitetura base
- [ ] MVP - Google Calendar Sync
- [ ] MVP - Google Meet Bot
- [ ] MVP - Gravação básica
- [ ] MVP - Transcrição OpenAI
- [ ] Dashboard básico
- [ ] Zoom Bot
- [ ] Speaker Diarization
- [ ] Resumos com IA
- [ ] Integrações (Slack, Notion)

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia nosso guia de contribuição antes de enviar PRs.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Disclaimer

Este projeto usa browser automation para entrar em reuniões. Certifique-se de:
- Ter permissão para gravar as reuniões
- Informar os participantes sobre a gravação
- Cumprir com as leis de privacidade locais (LGPD, GDPR, etc.)
