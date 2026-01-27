# Guia de Deploy em Produção (VPS Limpa)

Este guia cobre o processo de deploy da aplicação em uma VPS limpa (Ubuntu/Debian) usando **Traefik** como proxy reverso e um script de **1-Click Deploy**.

> [!NOTE]
> Recomendamos uma VPS com pelo menos **32GB RAM** e **8 vCPUs** para performance ideal, conforme configurado nos limites dos containers.

---

## 📋 Arquitetura de Produção

| Componente | Serviço | URL Pública (Exemplo) |
|------------|---------|-----------------------|
| **Proxy / SSL** | Traefik | N/A (Portas 80/443) |
| **Frontend** | Next.js | `https://rkj.seudominio.com` |
| **Backend API** | FastAPI | `https://api.seudominio.com` |
| **Database** | Supabase Cloud | `https://xxxx.supabase.co` |
| **Storage** | Cloudflare R2 | `https://pub-xxx.r2.dev` |

---

## Passo 1: Pré-requisitos

### 1.1 Domínios (DNS)

Configure os apontamentos DNS (Tipo A) no seu provedor para o IP da sua VPS:

- `rkj.seudominio.com` -> `IP_DA_VPS`
- `api.seudominio.com` -> `IP_DA_VPS`

> [!IMPORTANT]
> O DNS deve estar propagado antes de rodar o script para que o Let's Encrypt gere os certificados SSL.

### 1.2 VPS Limpa

- **OS**: Ubuntu 22.04 LTS ou 24.04 LTS recommended.
- **Acesso**: SSH root ou usuário com sudo.
- **Portas**: O script irá configurar o firewall (UFW) para abrir apenas 22 (SSH), 80 (HTTP) e 443 (HTTPS).

---

## Passo 2: Configuração de Ambiente

### 2.1 Preparar Variáveis

Crie um arquivo `.env` na raiz do projeto (ou no servidor, se estiver clonando lá) com as seguintes variáveis. Use `.env.production.example` como base.

**Variáveis Críticas para Deploy:**

```env
# Domínios
WEB_DOMAIN=rkj.seudominio.com
API_DOMAIN=api.seudominio.com
ACME_EMAIL=seu-email@dominio.com  # Para notificações do Let's Encrypt

# Supabase
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

# OpenAI & Google
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Bot Auth (Google Account para o bot entrar nas calls)
GOOGLE_AUTH_LOGIN=bot@gmail.com
GOOGLE_AUTH_PASSWORD=senha-app-password
```

---

## Passo 3: 1-Click Deploy

Use o script `deploy.sh` fornecido na raiz do projeto. Este script automatiza:
1. Instalação do Docker e Docker Compose (se necessário).
2. Configuração do Firewall (UFW).
3. Build e subida dos containers.

```bash
# Dar permissão de execução
chmod +x deploy.sh

# Executar o deploy
./deploy.sh
```

O script fará validações iniciais e pedirá confirmação antes de alterar configurações do sistema.

---

## 4. Manutenção e Troubleshooting

### Verificar Status

```bash
# Ver containers rodando
docker ps

# Ver logs do Traefik (problemas de SSL/Roteamento)
docker logs -f rkj-traefik

# Ver logs do Orchestrator
docker logs -f rkj-bot-orchestrator
```

### Atualizar Aplicação

Para atualizar a aplicação com novas mudanças do git:

```bash
# 1. Puxe as atualizações
git pull origin main

# 2. Rode o script novamente
./deploy.sh
```

### Reiniciar um Serviço Específico

```bash
docker compose -f infrastructure/docker/docker-compose.prod.yml restart web
```

### Limpeza de Disco

O sistema gera gravações e logs. Para limpar dados antigos e containers não utilizados:

```bash
docker system prune -a --volumes
```

> [!WARNING]
> Isso removerá containers parados e imagens não utilizadas. Cuidado em produção.
