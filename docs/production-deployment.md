# Guia de Deploy em Produção

Este guia cobre o processo de deploy da aplicação completa em um ambiente de produção (VPS Linux).

## 📋 Arquitetura de Produção

*   **Banco de Dados**: Supabase Cloud (gerenciado).
*   **Armazenamento**: Cloudflare R2.
*   **Serviços (Backend)**: Docker Swarm ou Docker Compose em VPS (Hetzner/AWS/DigitalOcean).
    *   Bot Orchestrator
    *   Transcription Worker
    *   Redis
*   **Frontend**: Vercel (recomendado) ou Docker na mesma VPS.

---

## Passo 1: Infraestrutura (Supabase & Cloudflare)

### 1. Supabase (Banco de Dados)
1.  Crie um projeto em [supabase.com](https://supabase.com).
2.  Vá em **Project Settings > Database** e copie a Connection String (`postgresql://...`).
3.  Vá em **Project Settings > API** e copie `Project URL` e `service_role key`.
4.  Rode as migrations do projeto local para produção:
    ```bash
    # Login na CLI
    supabase login
    
    # Linkar projeto local com remoto
    supabase link --project-ref seu-project-id
    
    # Enviar esquema do banco
    supabase db push
    ```

### 2. Cloudflare R2 (Storage)
1.  Crie um Bucket chamado `meeting-assistant`.
2.  Em **R2 > Manage R2 API Tokens**, crie um token com permissão **Admin Read & Write**.
3.  Anote: `Account ID`, `Access Key ID`, `Secret Access Key`.

---

## Passo 2: Preparar a VPS (Ubuntu)

Recomendado: Máquina com **4GB+ RAM** (Bots consomem memória do Chrome).

1.  Acesse servidor via SSH.
2.  Instale Docker e Docker Compose:
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    ```

3.  Clone o repositório:
    ```bash
    git clone https://github.com/seu-usuario/projeto-tldv.git
    cd projeto-tldv
    ```

---

## Passo 3: Configuração dos Serviços

1.  Crie o arquivo `.env.production` na pasta `infrastructure/docker` com as credenciais reais:

```bash
cd infrastructure/docker
cp .env.example .env.production
nano .env.production
```

**Ajustes Importantes no .env.production**:
*   `SUPABASE_URL`: URL do seu projeto Supabase Cloud.
*   `SUPABASE_SERVICE_KEY`: Chave `service_role` (NÃO use a anon key).
*   `REDIS_URL`: `redis://ma-redis:6379` (nome do serviço no docker network).
*   `ORCHESTRATOR_URL`: A URL pública ou interna onde o orchestrator ouvirá.

2.  Ajuste o `docker-compose.prod.yml` (opcional):
    *   Garanta que policies de restart estejam como `always`.
    *   Configure logs rotation para não encher o disco.

---

## Passo 4: Build e Deploy dos Serviços

Na VPS, construa e suba os containers:

```bash
# Build das imagens (pode demorar na primeira vez)
docker compose -f docker-compose.yml --env-file .env.production build

# Subir em background
docker compose -f docker-compose.yml --env-file .env.production up -d
```

Verifique:
```bash
docker compose logs -f
```

---

## Passo 5: Deploy do Frontend (Vercel)

1.  Instale Vercel CLI ou conecte seu GitHub na Vercel.
2.  Importe o projeto `apps/web`.
3.  Configure as Variáveis de Ambiente na Vercel:
    *   `NEXT_PUBLIC_SUPABASE_URL`: URL do projeto Supabase.
    *   `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Chave anônima (segura para frontend).
    *   `SUPABASE_SERVICE_KEY`: Chave service_role (para API routes).
    *   `REDIS_URL`: **Atenção**: O Frontend na Vercel não consegue acessar o Redis na sua VPS diretamente.
        *   **Solução A (Recomendada)**: Use [Upstash Redis](https://upstash.com/) (Serverless Redis) tanto para a Vercel quanto para a VPS.
        *   **Solução B**: Exponha o Redis da VPS (com senha forte e TLS) ou use uma VPN (Tailscale).

---

## Checklist de Produção

- [ ] **Segurança**: Redis protegido por senha (se exposto).
- [ ] **Google Auth**: Conta do bot não deve ter 2FA (use app password).
- [ ] **Timezone**: Configure a VPS para UTC ou o fuso desejado.
- [ ] **Limpeza**: Configure um cronjob para limpar containers `meet-bot` antigos (`docker system prune`).
