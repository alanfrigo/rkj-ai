# CLAUDE.md - AI Assistant Context

> Este arquivo fornece contexto para LLMs que auxiliam no desenvolvimento do Meeting Assistant.

## 📋 Visão Geral do Projeto

**Meeting Assistant** é um clone do TLDV - um assistente de reuniões que automaticamente entra em reuniões do Google Meet e Zoom, grava, e transcreve o conteúdo.

### Objetivo Principal
Criar um sistema self-hosted que:
1. Sincroniza com Google Calendar do usuário
2. Detecta reuniões com links de Google Meet ou Zoom
3. Entra automaticamente na reunião via bot
4. Grava áudio/vídeo da reunião
5. Transcreve usando OpenAI Whisper API
6. Disponibiliza gravações e transcrições em um dashboard

## 🏗️ Arquitetura Técnica

### Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| Frontend | NextJS 16 (App Router) | SSR, React Server Components, TypeScript nativo |
| UI Components | shadcn/ui + Tailwind | Componentes acessíveis, customizáveis |
| Backend API | FastAPI (Python) | Async nativo, tipagem forte, ótimo para ML/AI |
| Database | Supabase PostgreSQL | Auth integrado, RLS, Realtime |
| Auth | Supabase Auth + Google OAuth | Simplifica fluxo OAuth com Calendar |
| Storage | Cloudflare R2 | S3-compatible, sem egress fees, global |
| Queue | Redis + BullMQ | Filas confiáveis, retry automático |
| Transcription | OpenAI Whisper API | Alta qualidade, múltiplos idiomas |
| Bot Runtime | Playwright + Docker | Browser automation confiável |
| Containerização | Docker Compose | Desenvolvimento e deploy simplificado |

### Decisões Arquiteturais Importantes

1. **Por que Playwright ao invés de Puppeteer?**
   - Melhor suporte a múltiplos browsers
   - API mais moderna e tipada
   - Melhor handling de eventos async

2. **Por que Redis + BullMQ?**
   - Persistência de jobs
   - Retry automático com backoff
   - Dashboard de monitoramento
   - Suporte a jobs atrasados (scheduling)

3. **Por que Cloudflare R2?**
   - Compatível com S3 API
   - Zero egress fees (crítico para vídeos)
   - CDN integrado
   - Mais barato que S3 para nosso caso de uso

4. **Por que OpenAI Whisper API ao invés de self-hosted?**
   - Sem necessidade de GPU
   - Escalabilidade automática
   - Custo previsível por minuto de áudio
   - Manutenção zero

## 📁 Estrutura Detalhada

```
meeting-assistant/
├── apps/
│   ├── web/                          # Frontend NextJS 16
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/page.tsx
│   │   │   │   │   ├── signup/page.tsx
│   │   │   │   │   └── callback/route.ts      # OAuth callback
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── layout.tsx             # Dashboard layout com sidebar
│   │   │   │   │   ├── page.tsx               # Home/Overview
│   │   │   │   │   ├── meetings/
│   │   │   │   │   │   ├── page.tsx           # Lista de reuniões
│   │   │   │   │   │   └── [id]/page.tsx      # Detalhe com player + transcrição
│   │   │   │   │   ├── calendar/page.tsx      # Visualização do calendário
│   │   │   │   │   └── settings/
│   │   │   │   │       ├── page.tsx
│   │   │   │   │       ├── calendars/page.tsx # Gerenciar calendários
│   │   │   │   │       └── integrations/page.tsx
│   │   │   │   ├── api/
│   │   │   │   │   ├── webhooks/
│   │   │   │   │   │   └── google-calendar/route.ts
│   │   │   │   │   └── auth/[...nextauth]/route.ts
│   │   │   │   └── layout.tsx
│   │   │   ├── components/
│   │   │   │   ├── ui/                        # shadcn components
│   │   │   │   ├── meetings/
│   │   │   │   │   ├── meeting-card.tsx
│   │   │   │   │   ├── meeting-list.tsx
│   │   │   │   │   └── video-player.tsx
│   │   │   │   ├── transcription/
│   │   │   │   │   ├── transcription-viewer.tsx
│   │   │   │   │   ├── segment-item.tsx
│   │   │   │   │   └── search-bar.tsx
│   │   │   │   └── layout/
│   │   │   │       ├── sidebar.tsx
│   │   │   │       ├── header.tsx
│   │   │   │       └── nav-items.tsx
│   │   │   ├── lib/
│   │   │   │   ├── supabase/
│   │   │   │   │   ├── client.ts              # Browser client
│   │   │   │   │   ├── server.ts              # Server client
│   │   │   │   │   └── middleware.ts
│   │   │   │   ├── r2/
│   │   │   │   │   └── client.ts              # R2/S3 client
│   │   │   │   └── utils/
│   │   │   │       ├── format.ts
│   │   │   │       └── date.ts
│   │   │   ├── hooks/
│   │   │   │   ├── use-meetings.ts
│   │   │   │   ├── use-transcription.ts
│   │   │   │   └── use-realtime.ts
│   │   │   └── types/
│   │   │       └── database.ts                # Generated from Supabase
│   │   ├── package.json
│   │   ├── tailwind.config.ts
│   │   ├── next.config.js
│   │   └── tsconfig.json
│   │
│   └── api/                                   # Backend FastAPI
│       ├── src/
│       │   ├── main.py                        # FastAPI app entry
│       │   ├── config.py                      # Settings with Pydantic
│       │   ├── dependencies.py                # Dependency injection
│       │   ├── routers/
│       │   │   ├── __init__.py
│       │   │   ├── auth.py                    # Auth endpoints
│       │   │   ├── calendar.py                # Calendar sync endpoints
│       │   │   ├── meetings.py                # Meetings CRUD
│       │   │   ├── recordings.py              # Recording management
│       │   │   └── transcriptions.py          # Transcription endpoints
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── calendar_service.py        # Google Calendar integration
│       │   │   ├── meeting_service.py         # Meeting business logic
│       │   │   ├── recording_service.py       # R2 upload/download
│       │   │   ├── transcription_service.py   # OpenAI Whisper integration
│       │   │   └── queue_service.py           # Redis/BullMQ integration
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── user.py
│       │   │   ├── meeting.py
│       │   │   ├── recording.py
│       │   │   └── transcription.py
│       │   ├── schemas/
│       │   │   ├── __init__.py
│       │   │   ├── meeting.py                 # Pydantic schemas
│       │   │   ├── recording.py
│       │   │   └── transcription.py
│       │   └── core/
│       │       ├── __init__.py
│       │       ├── security.py                # JWT validation
│       │       ├── r2.py                      # R2 client
│       │       ├── supabase.py                # Supabase client
│       │       └── redis.py                   # Redis client
│       ├── tests/
│       │   ├── conftest.py
│       │   ├── test_meetings.py
│       │   └── test_transcriptions.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── pyproject.toml
│
├── services/
│   ├── scheduler/                             # Serviço de agendamento
│   │   ├── src/
│   │   │   ├── main.py                        # Entry point
│   │   │   ├── calendar_sync.py               # Google Calendar polling
│   │   │   ├── meeting_scheduler.py           # Job scheduling logic
│   │   │   └── config.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── bot-orchestrator/                      # Gerenciador de bots
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── orchestrator.py                # Main orchestration logic
│   │   │   ├── container_manager.py           # Docker container lifecycle
│   │   │   ├── health_checker.py              # Bot health monitoring
│   │   │   └── config.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── meet-bot/                              # Google Meet Bot
│   │   ├── src/
│   │   │   ├── main.py                        # Entry point
│   │   │   ├── bot.py                         # Main bot class
│   │   │   ├── meeting_handler.py             # Join/leave logic
│   │   │   ├── recorder.py                    # FFmpeg recording
│   │   │   ├── audio_capture.py               # PulseAudio setup
│   │   │   ├── upload.py                      # R2 upload
│   │   │   └── config.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── entrypoint.sh                      # Xvfb + PulseAudio setup
│   │
│   ├── zoom-bot/                              # Zoom Bot (futuro)
│   │   └── ...
│   │
│   ├── transcription-worker/                  # Worker de transcrição
│   │   ├── src/
│   │   │   ├── main.py                        # Queue consumer
│   │   │   ├── transcriber.py                 # OpenAI Whisper integration
│   │   │   ├── diarization.py                 # Speaker identification
│   │   │   ├── processor.py                   # Post-processing
│   │   │   └── config.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── media-processor/                       # Processamento de mídia
│       ├── src/
│       │   ├── main.py
│       │   ├── video_processor.py             # Video compression
│       │   ├── audio_extractor.py             # Audio extraction
│       │   ├── thumbnail.py                   # Thumbnail generation
│       │   └── config.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/
│   └── shared/                                # Código compartilhado
│       ├── types/
│       │   └── index.ts
│       └── utils/
│           └── index.ts
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml                 # Development
│   │   └── docker-compose.prod.yml            # Production
│   ├── supabase/
│   │   └── migrations/
│   │       ├── 00001_initial_schema.sql
│   │       └── 00002_add_indexes.sql
│   └── scripts/
│       ├── dev.sh
│       ├── deploy.sh
│       └── backup.sh
│
└── docs/
    ├── architecture.md
    ├── api.md
    └── deployment.md
```

## 🗄️ Schema do Banco de Dados

### Tabelas Principais

```sql
-- Usuários (extensão do Supabase Auth)
public.users
  - id: UUID (PK, FK auth.users)
  - email: TEXT
  - full_name: TEXT
  - google_refresh_token: TEXT (encrypted)
  - settings: JSONB
  - created_at, updated_at: TIMESTAMPTZ

-- Calendários conectados
public.connected_calendars
  - id: UUID (PK)
  - user_id: UUID (FK users)
  - provider: TEXT ('google', 'outlook')
  - calendar_id: TEXT
  - calendar_name: TEXT
  - is_active: BOOLEAN
  - sync_token: TEXT
  - last_synced_at: TIMESTAMPTZ

-- Eventos de calendário
public.calendar_events
  - id: UUID (PK)
  - user_id: UUID (FK users)
  - calendar_id: UUID (FK connected_calendars)
  - external_event_id: TEXT
  - title, description: TEXT
  - start_time, end_time: TIMESTAMPTZ
  - meeting_url: TEXT
  - meeting_provider: TEXT ('google_meet', 'zoom')
  - attendees: JSONB
  - should_record: BOOLEAN

-- Reuniões gravadas
public.meetings
  - id: UUID (PK)
  - user_id: UUID (FK users)
  - calendar_event_id: UUID (FK calendar_events)
  - title: TEXT
  - meeting_url: TEXT
  - meeting_provider: TEXT
  - status: TEXT (scheduled/joining/recording/processing/transcribing/completed/failed)
  - bot_session_id: TEXT
  - started_at, ended_at: TIMESTAMPTZ
  - duration_seconds: INTEGER
  - error_message: TEXT
  - metadata: JSONB

-- Gravações
public.recordings
  - id: UUID (PK)
  - meeting_id: UUID (FK meetings)
  - file_type: TEXT ('video', 'audio')
  - storage_path: TEXT (R2 path)
  - storage_url: TEXT (public URL)
  - file_size_bytes: BIGINT
  - duration_seconds: INTEGER
  - format: TEXT
  - is_processed: BOOLEAN
  - thumbnail_path: TEXT

-- Transcrições
public.transcriptions
  - id: UUID (PK)
  - meeting_id: UUID (FK meetings)
  - language: TEXT
  - status: TEXT (pending/processing/completed/failed)
  - full_text: TEXT
  - word_count: INTEGER
  - model_used: TEXT ('whisper-1')
  - processing_time_seconds: INTEGER
  - cost_cents: INTEGER

-- Segmentos de transcrição
public.transcription_segments
  - id: UUID (PK)
  - transcription_id: UUID (FK transcriptions)
  - segment_index: INTEGER
  - speaker_id: TEXT
  - speaker_name: TEXT
  - start_time_ms: INTEGER
  - end_time_ms: INTEGER
  - text: TEXT

-- Jobs de processamento
public.processing_jobs
  - id: UUID (PK)
  - meeting_id: UUID (FK meetings)
  - job_type: TEXT
  - status: TEXT
  - worker_id: TEXT
  - started_at, completed_at: TIMESTAMPTZ
  - error_message: TEXT
  - retry_count: INTEGER
  - metadata: JSONB
```

### RLS Policies

Todas as tabelas usam Row Level Security:
- Usuários só podem ver/editar seus próprios dados
- Service role (backend) tem acesso total

## 🔌 Integrações Externas

### Google Calendar API
- **Scopes necessários:**
  - `https://www.googleapis.com/auth/calendar.readonly`
  - `https://www.googleapis.com/auth/calendar.events.readonly`
- **Webhook:** Push notifications para eventos novos/alterados
- **Polling fallback:** A cada 5 minutos como backup

### OpenAI Whisper API
- **Endpoint:** `POST https://api.openai.com/v1/audio/transcriptions`
- **Model:** `whisper-1`
- **Formato aceito:** mp3, mp4, mpeg, mpga, m4a, wav, webm
- **Limite:** 25MB por arquivo (dividir áudios longos)
- **Custo:** $0.006 por minuto

### Cloudflare R2
- **API:** S3-compatible
- **Bucket structure:**
  ```
  meeting-assistant/
  ├── recordings/
  │   ├── {user_id}/
  │   │   ├── {meeting_id}/
  │   │   │   ├── video.mp4
  │   │   │   ├── audio.mp3
  │   │   │   └── thumbnail.jpg
  ├── temp/
  │   └── {upload_id}/
  ```
- **Lifecycle rules:** Limpar /temp após 24h

## 🤖 Lógica dos Bots

### Google Meet Bot

1. **Inicialização:**
   - Inicia Xvfb (display virtual) em :99
   - Inicia PulseAudio com sink virtual
   - Lança Chrome via Playwright

2. **Entrada na reunião:**
   - Navega para o link do Meet
   - Desativa câmera e microfone
   - Define nome como "RKJ.AI"
   - Clica em "Participar agora"
   - Aguarda confirmação de entrada

3. **Gravação:**
   - FFmpeg captura X11 display + PulseAudio
   - Formato: MP4 (H.264 + AAC)
   - Resolução: 1920x1080
   - Framerate: 30fps

4. **Detecção de fim:**
   - Monitora elementos do DOM
   - Detecta "You left the meeting"
   - Detecta quando único participante
   - Timeout após 4 horas

5. **Finalização:**
   - Para FFmpeg gracefully
   - Upload para R2
   - Notifica queue de transcrição
   - Cleanup do container

### Códigos de Saída do Bot
- `0`: Sucesso
- `1`: Erro genérico
- `2`: Falha ao entrar na reunião
- `3`: Timeout
- `4`: Erro de gravação
- `5`: Erro de upload

## 🔄 Fluxos de Dados

### Fluxo: Sync do Calendário
```
User conecta Google Account
  → OAuth flow (Supabase Auth)
  → Salva refresh_token (encrypted)
  → Scheduler inicia sync
  → Busca eventos das próximas 24h
  → Extrai links de reunião (Meet/Zoom)
  → Upsert em calendar_events
  → Eventos com meeting_url → should_record = true
```

### Fluxo: Gravação de Reunião
```
Scheduler detecta reunião em 2min
  → Cria registro em meetings (status: scheduled)
  → Enfileira job em join_meeting_queue
  → Orchestrator consume job
  → Spawna container do meet-bot
  → Bot entra na reunião
  → Atualiza status: recording
  → FFmpeg grava
  → Reunião termina
  → Bot para gravação
  → Upload para R2
  → Atualiza recordings com storage_path
  → Enfileira job em transcribe_queue
  → Container termina
```

### Fluxo: Transcrição
```
transcription-worker consume job
  → Download áudio do R2
  → Divide em chunks se > 25MB
  → Envia para OpenAI Whisper API
  → Recebe transcrição com timestamps
  → (Opcional) Diarização de speakers
  → Salva em transcriptions
  → Salva segmentos em transcription_segments
  → Atualiza meeting status: completed
  → Notifica usuário (opcional)
```

## 🧩 Padrões de Código

### Python (Backend/Services)

```python
# Use type hints sempre
async def get_meeting(meeting_id: str, user_id: str) -> Meeting | None:
    ...

# Pydantic para validação
class MeetingCreate(BaseModel):
    title: str
    meeting_url: HttpUrl
    scheduled_start: datetime
    
    model_config = ConfigDict(str_strip_whitespace=True)

# Dependency injection com FastAPI
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase: Client = Depends(get_supabase)
) -> User:
    ...

# Async context managers para recursos
async with get_r2_client() as r2:
    await r2.upload_file(...)
```

### TypeScript (Frontend)

```typescript
// Types gerados do Supabase
import { Database } from '@/types/database'
type Meeting = Database['public']['Tables']['meetings']['Row']

// Server Components por padrão
// app/meetings/page.tsx
export default async function MeetingsPage() {
  const supabase = createServerClient()
  const meetings = await supabase.from('meetings').select('*')
  return <MeetingList meetings={meetings.data} />
}

// Client Components quando necessário
'use client'
export function VideoPlayer({ url }: { url: string }) {
  const [playing, setPlaying] = useState(false)
  // ...
}

// Hooks para lógica reutilizável
export function useMeetings() {
  return useQuery({
    queryKey: ['meetings'],
    queryFn: () => supabase.from('meetings').select('*')
  })
}
```

## 🚨 Pontos de Atenção

### Segurança
- **Nunca** logar tokens ou API keys
- Usar variáveis de ambiente para secrets
- Refresh tokens devem ser encrypted at rest
- RLS ativo em todas as tabelas
- Validar todos os inputs (Pydantic/Zod)

### Performance
- Índices em colunas de busca frequente
- Paginação em listagens
- Lazy loading de transcrições
- CDN para arquivos estáticos
- Connection pooling no banco

### Escalabilidade
- Bots são stateless (escalar horizontalmente)
- Queue permite múltiplos workers
- R2 escala automaticamente
- Considerar Kubernetes para produção

### Limites
- OpenAI Whisper: 25MB por request
- Google Calendar: 100 requests/segundo
- R2: Sem limites práticos de storage
- Supabase Free: 500MB DB, 1GB storage

## 📝 Comandos Úteis

```bash
# Desenvolvimento
docker-compose up -d              # Inicia serviços
docker-compose logs -f scheduler  # Logs do scheduler
docker exec -it meet-bot bash     # Shell no container

# Database
supabase db push                  # Aplica migrations
supabase db reset                 # Reset completo
supabase gen types typescript     # Gera types

# Testes
pytest apps/api/tests/            # Testes backend
pnpm test                         # Testes frontend

# Build
docker build -t meet-bot ./services/meet-bot
docker-compose build --no-cache
```

## 🎯 Prioridades de Desenvolvimento

### Fase 1: MVP Core
1. Setup inicial (monorepo, Docker, CI/CD)
2. Database schema + migrations
3. Supabase Auth + Google OAuth
4. Google Calendar sync básico
5. Google Meet bot funcional
6. Gravação básica (só vídeo)
7. Upload para R2
8. Dashboard mínimo (lista de reuniões)

### Fase 2: Transcrição
1. Integração OpenAI Whisper
2. Transcription worker
3. Viewer de transcrição sincronizado
4. Busca em transcrições

### Fase 3: Polish
1. UI/UX refinado
2. Notificações
3. Settings do usuário
4. Zoom bot
5. Speaker diarization

### Fase 4: Features Avançadas
1. Resumos com IA
2. Action items automáticos
3. Integrações (Slack, Notion)
4. API pública

## ❓ Perguntas Frequentes para o Desenvolvimento

**Q: Como testar o bot localmente sem reunião real?**
A: Use um servidor de teste que simula interface do Meet, ou grave reuniões de teste com conta secundária.

**Q: Como lidar com reuniões muito longas?**
A: Dividir gravação em chunks de 1 hora, processar em paralelo.

**Q: E se o bot for removido da reunião?**
A: Bot detecta evento de remoção, salva o que foi gravado, marca como parcial.

**Q: Como garantir que transcrição está sincronizada com vídeo?**
A: Whisper retorna timestamps precisos, frontend usa esses timestamps para sync.

---

*Última atualização: Janeiro 2025*
*Mantenedor: Alan (IndominusAI)*
