# Guia de Teste do Meet Bot com Autenticação Google

Este guia descreve o passo a passo para testar o bot de gravação do Google Meet com autenticação.

---

## Pré-requisitos

### 1. Conta Google dedicada para o bot

**IMPORTANTE:** Use uma conta Google separada, não sua conta pessoal.

- Crie uma nova conta Google (ex: `meubot.meetassistant@gmail.com`)
- **Desative a verificação em duas etapas (2FA)** na conta
- Ou, se preferir manter 2FA, gere uma **Senha de App**:
  1. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
  2. Gere uma senha para "Outro (nome personalizado)"
  3. Use essa senha no lugar da senha normal

### 2. Configurar variáveis de ambiente

Crie ou edite o arquivo `.env` na pasta `infrastructure/docker/`:

```bash
cd /Users/alanfrigo/Dev/projeto-tldv/infrastructure/docker

# Criar/editar .env
nano .env
```

Adicione as credenciais:

```env
# Google Bot Authentication
GOOGLE_AUTH_LOGIN=seu-bot@gmail.com
GOOGLE_AUTH_PASSWORD=sua-senha-ou-app-password

# Outras variáveis existentes...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
# etc.
```

---

## Passo a Passo para Testar

### Passo 1: Build das imagens Docker

```bash
cd /Users/alanfrigo/Dev/projeto-tldv/infrastructure/docker

# Build do meet-bot (necessário após alterações no código)
docker-compose build meet-bot

# Build do orchestrator (se necessário)
docker-compose build bot-orchestrator
```

### Passo 2: Iniciar os serviços

```bash
# Iniciar Redis (dependência)
docker-compose up -d redis

# Aguardar Redis estar pronto
sleep 5

# Iniciar o orchestrator
docker-compose up -d bot-orchestrator
```

### Passo 3: Verificar se os serviços estão rodando

```bash
# Ver status dos containers
docker-compose ps

# Ver logs do orchestrator
docker-compose logs -f bot-orchestrator
```

### Passo 4: Criar uma reunião de teste

1. Acesse [meet.google.com](https://meet.google.com) com sua conta pessoal
2. Clique em **"Nova reunião"** > **"Iniciar uma reunião instantânea"**
3. Copie o link da reunião (ex: `https://meet.google.com/abc-defg-hij`)

### Passo 5: Disparar o bot manualmente

Você pode testar o bot de duas formas:

#### Opção A: Via Redis (simula o fluxo real)

```bash
# Conectar ao Redis
docker exec -it ma-redis redis-cli

# Publicar job na fila
LPUSH queue:join_meeting '{"meeting_id":"test-123","meeting_url":"https://meet.google.com/SEU-CODIGO-AQUI","user_id":"test-user"}'

# Sair do redis-cli
exit
```

#### Opção B: Executar o bot diretamente (para debug)

```bash
# Rodar container do bot manualmente
docker run --rm -it \
  --name ma-meet-bot-test \
  --network meeting-assistant-network \
  --shm-size=2g \
  -e MEETING_ID="test-123" \
  -e MEETING_URL="https://meet.google.com/SEU-CODIGO-AQUI" \
  -e USER_ID="test-user" \
  -e BOT_DISPLAY_NAME="Meeting Assistant Bot" \
  -e GOOGLE_AUTH_LOGIN="seu-bot@gmail.com" \
  -e GOOGLE_AUTH_PASSWORD="sua-senha" \
  -e SUPABASE_URL="${SUPABASE_URL}" \
  -e SUPABASE_SERVICE_KEY="${SUPABASE_SERVICE_KEY}" \
  -e REDIS_URL="redis://redis:6379" \
  -v docker_recordings:/recordings \
  docker-meet-bot:latest
```

### Passo 6: Monitorar o bot

```bash
# Ver logs em tempo real
docker logs -f ma-meet-bot-test

# Ou se foi criado pelo orchestrator
docker logs -f ma-meet-bot-test-123
```

### Passo 7: Admitir o bot na reunião

1. Na sua reunião do Google Meet, você verá uma notificação:
   > "Meeting Assistant Bot quer participar"
2. Clique em **"Admitir"** para permitir a entrada

### Passo 8: Verificar screenshots de debug

Os screenshots são salvos no volume `recordings`. Para acessá-los:

```bash
# Listar arquivos no volume
docker run --rm -v docker_recordings:/recordings alpine ls -la /recordings/

# Copiar screenshots para sua máquina
docker run --rm -v docker_recordings:/recordings -v $(pwd):/output alpine cp -r /recordings/*.png /output/

# Ou acessar diretamente (se souber o path do volume)
# No macOS com Docker Desktop, volumes ficam em uma VM
```

**Screenshots esperados:**

| Arquivo | Descrição |
|---------|-----------|
| `01_page_loaded.png` | Página inicial do Meet |
| `02_signin_required.png` | Se login foi necessário |
| `auth_01_signin_page.png` | Página de login Google |
| `auth_02_after_email.png` | Após inserir email |
| `auth_03_after_password.png` | Após inserir senha |
| `02b_after_auth.png` | Voltando para o Meet após auth |
| `03_name_entered.png` | Nome do bot preenchido |
| `04_before_join_click.png` | Antes de clicar em entrar |
| `05_after_join_click.png` | Após clicar em entrar |
| `06_in_meeting.png` | Bot dentro da reunião |

---

## Troubleshooting

### Erro: "Google authentication failed"

**Possíveis causas:**
1. Credenciais incorretas no `.env`
2. 2FA está ativado na conta
3. Google bloqueou por "atividade suspeita"

**Soluções:**
- Verifique as credenciais
- Desative 2FA ou use App Password
- Faça login manual na conta pelo navegador para "desbloquear"
- Verifique o screenshot `auth_error.png` ou `auth_challenge.png`

### Erro: "ACCESS DENIED: Bot was blocked"

**Possíveis causas:**
1. Reunião requer conta da organização
2. Configurações de segurança da reunião

**Soluções:**
- Use uma reunião pública (não corporativa)
- Verifique as configurações da reunião no Google Meet

### Bot não aparece para ser admitido

**Possíveis causas:**
1. Bot travou antes de entrar
2. URL da reunião incorreta

**Soluções:**
- Verifique os logs do container
- Verifique os screenshots de debug
- Confirme que a URL está correta

### Container morre imediatamente

```bash
# Ver logs do container que morreu
docker logs ma-meet-bot-test-123

# Verificar exit code
docker inspect ma-meet-bot-test-123 --format='{{.State.ExitCode}}'
```

**Exit codes:**
- `0`: Sucesso
- `1`: Erro genérico
- `2`: Falha ao entrar na reunião
- `3`: Timeout
- `4`: Erro de gravação
- `5`: Erro de upload

---

## Limpeza após testes

```bash
# Parar todos os containers
docker-compose down

# Remover containers de teste
docker rm -f $(docker ps -aq --filter "name=ma-meet-bot")

# Limpar volume de recordings (cuidado!)
docker volume rm docker_recordings
```

---

## Teste Completo (Checklist)

- [ ] `.env` configurado com credenciais
- [ ] Imagem `meet-bot` buildada
- [ ] Redis rodando
- [ ] Orchestrator rodando
- [ ] Reunião de teste criada
- [ ] Bot disparado (via Redis ou direto)
- [ ] Bot admitido na reunião
- [ ] Screenshots verificados
- [ ] Gravação salva (se aplicável)

---

## Comandos Úteis

```bash
# Ver todos os containers (incluindo parados)
docker ps -a

# Ver logs do orchestrator
docker-compose logs -f bot-orchestrator

# Entrar no container do bot (se ainda estiver rodando)
docker exec -it ma-meet-bot-test-123 bash

# Ver uso de recursos
docker stats

# Rebuild forçado (sem cache)
docker-compose build --no-cache meet-bot
```

---

*Última atualização: Janeiro 2025*
