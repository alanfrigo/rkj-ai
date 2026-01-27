# 🚀 RKJ.AI Benchmark Framework

Framework profissional de testes de carga para o sistema de gravação de reuniões.

## 📋 Índice

- [Instalação](#instalação)
- [Uso Local](#uso-local)
- [Deploy na VPS com EasyPanel](#deploy-na-vps-com-easypanel)
- [Interpretando Resultados](#interpretando-resultados)
- [Sizing de VPS](#sizing-de-vps)

---

## Instalação

```bash
cd scripts/benchmark
pip install -r requirements.txt
```

## Uso Local

### Ver informações do sistema

```bash
python benchmark.py info
```

### Teste de Stress de Bots

Testa a capacidade de criar containers simultâneos:

```bash
# 10 bots por 5 minutos
python benchmark.py stress --bots 10 --duration 300

# 5 bots por 2 minutos (teste rápido)
python benchmark.py stress --bots 5 --duration 120
```

### Teste de Transcrição

Testa throughput do worker de transcrição:

```bash
# 20 arquivos de 1 minuto
python benchmark.py transcription --files 20 --duration-minutes 1
```

### Gerar Relatório HTML

```bash
python benchmark.py report results/stress_20260126_211500.json --format html
```

---

## Deploy na VPS com EasyPanel

### Passo 1: Preparar a VPS

1. **Acesse sua VPS via SSH**:
   ```bash
   ssh root@seu-servidor.com
   ```

2. **Clone o repositório** (se ainda não fez):
   ```bash
   git clone https://github.com/seu-usuario/projeto-tldv.git
   cd projeto-tldv
   ```

3. **Instale dependências do benchmark**:
   ```bash
   cd scripts/benchmark
   pip3 install -r requirements.txt
   ```

### Passo 2: Configurar Variáveis de Ambiente

Crie um arquivo `.env` no diretório benchmark:

```bash
cat > .env << 'EOF'
# Docker
DOCKER_HOST=unix:///var/run/docker.sock
BOT_IMAGE=meet-bot:latest
DOCKER_NETWORK=easypanel

# Redis (URL do container no EasyPanel)
REDIS_URL=redis://redis-rkj:6379

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-service-key

# OpenAI (para estimativa de custos)
OPENAI_PRICE_PER_MINUTE=0.006
EOF
```

### Passo 3: Ajustar Network do Docker

O EasyPanel usa uma network própria. Descubra o nome:

```bash
docker network ls | grep easypanel
```

Atualize a variável `DOCKER_NETWORK` no `.env`.

### Passo 4: Build da Imagem do Bot

Certifique-se que a imagem `meet-bot` está buildada:

```bash
cd /caminho/para/projeto-tldv
docker build -t meet-bot:latest -f services/meet-bot/Dockerfile services/meet-bot/
```

### Passo 5: Executar os Benchmarks

#### Teste de Stress (10 bots)

```bash
cd /caminho/para/projeto-tldv/scripts/benchmark

# Primeiro, verifique os recursos disponíveis
python3 benchmark.py info

# Execute o stress test
python3 benchmark.py stress --bots 10 --duration 300
```

#### Monitorar em Tempo Real

Em outro terminal, monitore o Docker:

```bash
# Uso de recursos de todos containers
docker stats

# Filtrar só os bots de benchmark
docker stats $(docker ps --format '{{.Names}}' | grep rkj-bot-benchmark)
```

#### No EasyPanel

1. Acesse o dashboard do EasyPanel
2. Vá em **Monitoring** > **Docker**
3. Observe CPU, RAM e Network em tempo real

### Passo 6: Analisar Resultados

Os resultados são salvos em `scripts/benchmark/results/`:

```bash
# Ver JSON
cat results/stress_*.json | python3 -m json.tool

# Abrir HTML (copie para sua máquina)
scp root@seu-servidor.com:/path/to/results/*.html ./
```

Ou acesse via EasyPanel:
1. Vá em **File Manager**
2. Navegue até `/path/to/projeto-tldv/scripts/benchmark/results/`
3. Baixe o arquivo HTML

---

## Interpretando Resultados

### Métricas Principais

| Métrica | O que significa | Valor ideal |
|---------|-----------------|-------------|
| **Peak CPU** | Uso máximo de CPU | < 80% |
| **Peak Memory** | RAM máxima usada | < 80% disponível |
| **Spawn Time** | Tempo para criar container | < 5s |
| **Success Rate** | Taxa de sucesso | > 95% |

### Exemplo de Resultado

```
📊 Benchmark Results
┌────────────────┬──────────────┐
│ Metric         │ Value        │
├────────────────┼──────────────┤
│ Scenario       │ bot_stress   │
│ Duration       │ 300.5s       │
│ Status         │ ✓ Success    │
│ Peak Containers│ 10           │
│ Peak CPU       │ 67.3%        │
│ Peak Memory    │ 9.2 GB       │
└────────────────┴──────────────┘

💡 Recommendations:
   → 16GB VPS recomendado

📈 Scaling Projections:
   10_bots: 10GB RAM, 4 CPUs
   20_bots: 20GB RAM, 8 CPUs
   50_bots: 50GB RAM, 20 CPUs
```

---

## Sizing de VPS

### Recomendações por Escala

| Cenário | RAM | vCPUs | Disco | Rede | Custo Estimado |
|---------|-----|-------|-------|------|----------------|
| 10 reuniões | 16 GB | 8 | 100 GB SSD | 100 Mbps | ~$50-80/mês |
| 20 reuniões | 32 GB | 16 | 200 GB SSD | 200 Mbps | ~$100-150/mês |
| 50 reuniões | 64 GB | 32 | 500 GB SSD | 500 Mbps | ~$250-400/mês |

### Provedores Recomendados

1. **Hetzner** - Melhor custo/benefício para Europa
2. **DigitalOcean** - Boa integração com EasyPanel
3. **Contabo** - Muito RAM por baixo custo
4. **OVH** - Bom para Brasil (latência)

### Configuração do EasyPanel para Alta Carga

#### 1. Aumentar limites de recursos

No EasyPanel, edite cada serviço e configure:

```yaml
# Para o bot-orchestrator
resources:
  limits:
    memory: "4Gi"
    cpu: "2"
  requests:
    memory: "1Gi"
    cpu: "0.5"
```

#### 2. Configurar múltiplas réplicas do worker

```yaml
# Para o transcription-worker
replicas: 3  # Processa 3 transcrições em paralelo
```

#### 3. Otimizar Redis

```yaml
# Aumentar memória do Redis
command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

---

## Troubleshooting

### "Bot image not found"

```bash
docker build -t meet-bot:latest -f services/meet-bot/Dockerfile services/meet-bot/
```

### "Cannot connect to Docker"

Verifique permissões:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "Out of memory"

Reduza o número de bots ou aumente a RAM da VPS:
```bash
python3 benchmark.py stress --bots 5 --duration 60
```

### Containers não aparecem no monitoramento

Verifique se o nome do container começa com `rkj-bot-`:
```bash
docker ps | grep rkj-bot
```

---

## Arquivos Importantes

```
scripts/benchmark/
├── benchmark.py          # CLI principal
├── config.py             # Configurações
├── requirements.txt      # Dependências
├── scenarios/            # Cenários de teste
│   ├── bot_stress.py     # Stress test de containers
│   └── transcription_load.py  # Load test de transcrição
├── collectors/           # Coletores de métricas
│   ├── docker_stats.py   # Métricas Docker
│   └── timing_collector.py  # Tempos
├── generators/           # Geradores de relatório
│   └── html_report.py    # Dashboard HTML
└── results/              # Resultados salvos
```

---

## Próximos Passos

1. Execute `python3 benchmark.py info` para ver recursos atuais
2. Faça um teste com 5 bots por 2 minutos
3. Analise o relatório HTML
4. Escale gradualmente: 10, 15, 20 bots
5. Defina o sizing ideal para sua VPS

---

*RKJ.AI Benchmark Framework v1.0*
