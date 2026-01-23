# 🚀 Getting Started - Meeting Assistant

Este guia detalha os primeiros passos para configurar e iniciar o desenvolvimento do Meeting Assistant.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Docker** e **Docker Compose** (v2.0+)
- **Python** 3.11+
- **Node.js** 20+ e **pnpm**
- **Git**

### Contas necessárias

1. **Supabase** - [supabase.com](https://supabase.com) (gratuito)
2. **Cloudflare** - [cloudflare.com](https://cloudflare.com) (R2 tem tier gratuito)
3. **OpenAI** - [platform.openai.com](https://platform.openai.com) (pago por uso)
4. **Google Cloud** - [console.cloud.google.com](https://console.cloud.google.com) (gratuito para OAuth)

---

## 🔧 Passo 1: Configuração Inicial

### 1.1 Clone o repositório

```bash
git clone https://github.com/seu-usuario/meeting-assistant.git
cd meeting-assistant
```

### 1.2 Copie o arquivo de ambiente

```bash
cp .env.example .env
```

---

## 🗄️ Passo 2: Configurar Supabase

### 2.1 Criar projeto

1. Acesse [app.supabase.com](https://app.supabase.com)
2. Clique em **"New Project"**
3. Escolha um nome (ex: `meeting-assistant`)
4. Defina uma senha forte para o banco
5. Selecione a região mais próxima (ex: `South America (São Paulo)`)

### 2.2 Obter credenciais

Após criar o projeto, vá em **Settings > API** e copie:

```env
# Adicione ao seu .env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...
```

### 2.3 Executar migrations

```bash
# Instale o CLI do Supabase se necessário
npm install -g supabase

# Faça login
supabase login

# Link ao projeto
supabase link --project-ref xxxxx

# Execute as migrations
supabase db push
```

Ou execute manualmente no SQL Editor do Supabase copiando o conteúdo de:
`infrastructure/supabase/migrations/00001_initial_schema.sql`

---

## 📦 Passo 3: Configurar Cloudflare R2

### 3.1 Criar bucket

1. Acesse [dash.cloudflare.com](https://dash.cloudflare.com)
2. No menu lateral, clique em **R2**
3. Clique em **"Create bucket"**
4. Nome: `meeting-assistant`
5. Região: **Automatic** (mais próximo dos usuários)

### 3.2 Criar API Token

1. Vá em **R2 > Manage R2 API Tokens**
2. Clique em **"Create API token"**
3. Permissões: **Admin Read & Write**
4. Escopo: **Apply to specific bucket only** > `meeting-assistant`
5. Copie as credenciais geradas

```env
# Adicione ao seu .env
R2_ACCOUNT_ID=xxxxx  # Visível na sidebar do dashboard
R2_ACCESS_KEY_ID=xxxxx
R2_SECRET_ACCESS_KEY=xxxxx
R2_BUCKET_NAME=meeting-assistant
```

### 3.3 (Opcional) Configurar domínio público

Para URLs públicas de recordings:

1. Em R2 > seu bucket > **Settings**
2. Ative **"Public access"**
3. Copie a URL pública para `R2_PUBLIC_URL`

---

## 🤖 Passo 4: Configurar OpenAI

### 4.1 Criar API Key

1. Acesse [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Clique em **"Create new secret key"**
3. Copie a chave (ela só aparece uma vez!)

```env
# Adicione ao seu .env
OPENAI_API_KEY=sk-xxxxx
```

### 4.2 Verificar créditos

Para usar o Whisper API, você precisa ter créditos na conta. O custo é aproximadamente **$0.006 por minuto** de áudio.

---

## 🔐 Passo 5: Configurar Google OAuth

### 5.1 Criar projeto no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione um existente

### 5.2 Ativar APIs

1. Vá em **APIs & Services > Library**
2. Busque e ative:
   - **Google Calendar API**
   - **Google People API**

### 5.3 Configurar OAuth Consent Screen

1. Vá em **APIs & Services > OAuth consent screen**
2. Selecione **External**
3. Preencha as informações básicas:
   - App name: `Meeting Assistant`
   - User support email: seu email
   - Developer contact: seu email
4. Em **Scopes**, adicione:
   - `userinfo.email`
   - `userinfo.profile`
   - `calendar.readonly`
   - `calendar.events.readonly`

### 5.4 Criar credenciais OAuth

1. Vá em **APIs & Services > Credentials**
2. Clique em **"Create Credentials" > "OAuth client ID"**
3. Tipo: **Web application**
4. Nome: `Meeting Assistant Web`
5. **Authorized redirect URIs**:
   - `http://localhost:3000/api/auth/callback/google`
   - (produção) `https://seudominio.com/api/auth/callback/google`
6. Copie as credenciais

```env
# Adicione ao seu .env
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx
```

---

## 🐳 Passo 6: Iniciar os Serviços

### 6.1 Dar permissão ao script

```bash
chmod +x scripts/dev.sh
```

### 6.2 Iniciar serviços Docker

```bash
./scripts/dev.sh up
```

Isso irá iniciar:
- Redis (porta 6379)
- API Backend (porta 8000)
- Scheduler
- Transcription Worker
- Media Processor

### 6.3 Verificar se está funcionando

```bash
# Ver logs
./scripts/dev.sh logs

# Testar API
curl http://localhost:8000/health
```

---

## 🌐 Passo 7: Iniciar o Frontend (Opcional)

O frontend NextJS ainda precisa ser criado. Para iniciar:

```bash
cd apps/web

# Criar projeto NextJS (primeira vez)
pnpm create next-app . --typescript --tailwind --app --src-dir

# Instalar dependências adicionais
pnpm add @supabase/supabase-js @supabase/ssr

# Iniciar dev server
pnpm dev
```

---

## ✅ Checklist de Configuração

- [ ] `.env` criado com todas as variáveis
- [ ] Supabase: projeto criado e migrations executadas
- [ ] Cloudflare R2: bucket criado e credenciais configuradas
- [ ] OpenAI: API key criada e com créditos
- [ ] Google Cloud: OAuth configurado com redirect URIs
- [ ] Docker: serviços rodando (`./scripts/dev.sh up`)
- [ ] API: respondendo em `http://localhost:8000/health`

---

## 🐛 Troubleshooting

### Redis não conecta

```bash
# Verificar se Redis está rodando
docker ps | grep redis

# Reiniciar Redis
./scripts/dev.sh down && ./scripts/dev.sh up
```

### Erro de autenticação Supabase

- Verifique se `SUPABASE_URL` não tem barra no final
- Confirme que está usando a chave correta (anon para frontend, service para backend)

### Erro no upload R2

- Verifique se o Account ID está correto (não é o bucket ID)
- Confirme as permissões do API token

### Erro no Google OAuth

- Verifique se as redirect URIs estão exatamente iguais
- Confirme que as APIs estão ativadas no projeto correto

---

## 📚 Próximos Passos

Após a configuração inicial, você pode:

1. **Desenvolver o Frontend**: Criar as páginas do dashboard
2. **Testar Calendar Sync**: Conectar sua conta Google e ver eventos
3. **Criar o Meet Bot**: Implementar o bot que entra nas reuniões
4. **Testar Transcrição**: Fazer upload manual de áudio para testar

Consulte o `CLAUDE.md` para contexto detalhado da arquitetura e decisões técnicas.

---

*Em caso de dúvidas, abra uma issue no repositório!*
