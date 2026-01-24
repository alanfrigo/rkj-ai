# Guia de Desenvolvimento e Teste Local

Este guia descreve como configurar todo o ambiente de desenvolvimento local (Backend, Frontend e Serviços) e realizar testes ponta a ponta.

## 🏗️ Arquitetura Local

O ambiente local é composto por:

1.  **Infraestrutura (Docker)**:
    *   `ma-redis`: Fila de tarefas para o bot e transcrição.
    *   `bot-orchestrator`: Gerencia o ciclo de vida dos containers dos bots.
    *   `meet-bot`: Instâncias efêmeras que entram nas reuniões (criadas sob demanda).
    *   `ma-transcription-worker`: Processa áudio e legendas após a reunião.
    *   `supabase_db`: Banco de dados Postgres local (via Supabase CLI).

2.  **Frontend (Next.js)**:
    *   Painel de controle para iniciar gravações e visualizar resultados.
    *   Roda na porta `3000` e se comunica com o Supabase e Redis.

---

## 🚀 Pré-requisitos

1.  **Node.js 18+** e `npm`
2.  **Docker** e `docker-compose`
3.  **Supabase CLI**: Instale com `npm install -g supabase`
4.  **FFmpeg** (opcional, para testes manuais de áudio)
5.  **Conta Google de Teste**:
    *   Crie uma conta gmail dedicada (ex: `bot.teste@gmail.com`)
    *   Desative 2FA ou gere uma **App Password**

---

## 🛠️ Configuração do Ambiente

### 1. Configurar Variáveis de Ambiente

Crie o arquivo `.env` na raiz do projeto (use `.env.example` como base):

```bash
cp .env.example .env
```

**Variáveis Críticas:**

```env
# Google Auth (Para o Bot entrar no Meet)
GOOGLE_AUTH_LOGIN=seu.bot@gmail.com
GOOGLE_AUTH_PASSWORD=sua-senha-ou-app-password

# Supabase Local (Padrão do docker local)
SUPABASE_URL=http://host.docker.internal:54321
SUPABASE_SERVICE_KEY=... (pegue da saída do supabase start)

# Cloudflare R2 (Para upload de gravações)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=meeting-assistant

# OpenAI (Para transcrição)
OPENAI_API_KEY=sk-...
```

### 2. Iniciar Serviços Backend

Na raiz do projeto, use o script de desenvolvimento para subir toda a infraestrutura Docker:

```bash
./dev.sh
```

Isso irá:
1.  Subir o Supabase local.
2.  Construir as imagens do `meet-bot` e `transcription-worker`.
3.  Iniciar Redis e Orchestrator.

Verifique se tudo está rodando:

```bash
docker ps
# Deve listar: ma-redis, ma-bot-orchestrator, ma-transcription-worker, supabase_db_...
```

### 3. Iniciar Frontend

Em outro terminal:

```bash
cd apps/web
npm install
npm run dev
```

Acesse: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Teste Ponta a Ponta (End-to-End)

Agora vamos simular o fluxo real de uso.

### Passo 1: Criar uma Reunião no Google Meet

1.  Abra o [Google Meet](https://meet.google.com) no seu navegador (com sua conta **pessoal**, não a do bot).
2.  Crie uma **"Nova reunião"** > **"Iniciar uma reunião instantânea"**.
3.  Copie o link (ex: `meet.google.com/abc-defg-hij`).
4.  **Mantenha a aba aberta** e permaneça na sala.

### Passo 2: Solicitar Gravação via Dashboard

1.  No Dashboard Local (`localhost:3000`):
2.  Vá em **"Reuniões"** > Card **"Gravar Reunião Agora"**.
3.  Cole o link do Google Meet e clique em **"Gravar"**.
4.  Você será redirecionado para a página da reunião com status `Gravando...`.

### Passo 3: Aceitar o Bot

1.  Volte para a aba do Google Meet.
2.  Em instantes, o bot (`Meeting Assistant Bot`) pedirá para entrar.
3.  Clique em **"Admitir"**.
4.  **Fale algo** para testar o áudio e as legendas (ative as legendas no seu Meet para garantir que o áudio está sendo captado pelo Google).
5.  O bot deve ficar na reunião por alguns minutos.

### Passo 4: Finalizar e Verificar

1.  Encerre a chamada no Google Meet (ou remova o bot).
2.  O container do bot detectará a saída e iniciará o upload.
3.  No Dashboard, atualize a página da reunião.
4.  O status mudará para `Processando` e depois `Concluída`.
5.  **Verifique:**
    *   Vídeo disponível no player.
    *   Transcrição completa com timestamps e nomes dos falantes (ex: `[00:00:15] [Seu Nome] Olá mundo`).

---

## 🔍 Debugging e Logs

### Ver logs dos serviços

```bash
# Orchestrator (Gerencia os bots)
docker logs -f ma-bot-orchestrator

# Bot Específico (Encontre o ID com docker ps -a)
docker logs -f docker-meet-bot-...

# Worker de Transcrição
docker logs -f ma-transcription-worker
```

### Screenshots de Debug

Se o bot falhar ao entrar, ele salva screenshots em `infrastructure/recordings` (volume mapeado). Verifique as imagens para ver se houve erro de login ou bloqueio do Google.

### Acesso ao Banco de Dados

```bash
# Listar reuniões via SQL no container do Supabase
docker exec -it supabase_db_projeto-tldv psql -U postgres -c "SELECT id, status, full_text FROM transcriptions;"
```

---

## ⚠️ Problemas Comuns

1.  **Erro de Login Google**: Verifique se o IP foi bloqueado ou se o 2FA está pedindo confirmação. Tente logar manualmente no navegador da máquina para "desbloquear".
2.  **Áudio Mudo**: O bot usa um dispositivo de áudio virtual. Se estiver rodando em VPS, certifique-se que o `pulseaudio` não está bloqueando.
3.  **Docker de Rede**: Se o Frontend não conseguir falar com o Redis, verifique se estão na mesma rede ou se as portas 6379/8002 estão expostas.
