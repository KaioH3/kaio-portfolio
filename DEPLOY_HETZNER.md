# 🚀 Guia Completo de Deploy - Hetzner VPS

Deploy automatizado do Portfolio ML na Hetzner com Podman + Caddy + SSL automático.

## 📋 Pré-requisitos

### 1. VPS Hetzner

Recomendado: **CX22** (2 vCPU, 4GB RAM, 40GB SSD) - ~€5.83/mês

- ✅ CPU: 2 cores (necessário para XGBoost training)
- ✅ RAM: 4GB (mínimo 2GB)
- ✅ Storage: 40GB (datasets + models)
- ✅ OS: Ubuntu 22.04 LTS

### 2. Domínio Configurado

- Registre um domínio (ex: `kaio.ia.br` via registro.br)
- Configure DNS apontando para IP da VPS

### 3. API Keys

- **Groq API** (free tier): https://console.groq.com/
- **Voyage AI** (opcional): https://www.voyageai.com/
- **Qdrant Cloud** (opcional): https://cloud.qdrant.io/
- **Kaggle API**: https://www.kaggle.com/settings/account

---

## 🔧 Passo 1: Configurar VPS

### 1.1 Criar VPS na Hetzner

1. Acesse https://console.hetzner.cloud/
2. Crie um novo projeto
3. Crie servidor:
   - **Localização**: Nuremberg, Germany (mais próximo do Brasil)
   - **Imagem**: Ubuntu 22.04 LTS
   - **Tipo**: CX22 (ou CX21 para teste)
   - **Networking**: IPv4 + IPv6
   - **SSH Key**: Adicione sua chave pública

4. Anote o **IP público** do servidor

### 1.2 Configurar DNS

No painel do seu provedor de domínio (registro.br, Cloudflare, etc.):

```
Tipo  | Nome           | Destino          | TTL
------|----------------|------------------|-----
A     | @              | <IP_VPS>         | 3600
A     | www            | <IP_VPS>         | 3600
CNAME | api            | kaio.ia.br       | 3600
```

**Aguarde** 5-30 minutos para propagação DNS.

### 1.3 Primeiro Acesso SSH

```bash
# Substitua <IP_VPS> pelo IP real
ssh root@<IP_VPS>

# Se você configurou SSH key, não pedirá senha
# Caso contrário, use a senha enviada por email
```

### 1.4 Atualizar Sistema e Instalar Dependências

```bash
# Update packages
apt update && apt upgrade -y

# Install essentials
apt install -y \
    curl \
    wget \
    git \
    vim \
    ufw \
    fail2ban \
    htop \
    podman \
    podman-compose

# Verificar versões
podman --version    # >= 3.4
python3 --version   # 3.10+
```

---

## 🔐 Passo 2: Configurar Segurança

### 2.1 Firewall (UFW)

```bash
# Configurar firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable

# Verificar status
ufw status verbose
```

### 2.2 Fail2Ban (Proteção SSH)

```bash
# Instalar e configurar fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Verificar
fail2ban-client status sshd
```

### 2.3 Criar Usuário Não-Root (Opcional mas Recomendado)

```bash
# Criar usuário
adduser deploy
usermod -aG sudo deploy

# Adicionar SSH key
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Testar login (em outro terminal)
ssh deploy@<IP_VPS>
```

**A partir de agora, use o usuário `deploy` ao invés de `root`.**

---

## 📦 Passo 3: Deploy da Aplicação

### 3.1 Clone do Repositório

```bash
# Como usuário deploy
cd /opt
sudo mkdir kaio-portfolio
sudo chown deploy:deploy kaio-portfolio
cd kaio-portfolio

# Clone
git clone https://github.com/KaioH3/kaio-portfolio.git .
```

### 3.2 Configurar Variáveis de Ambiente

```bash
# Criar .env production
cat > .env << 'EOF'
# Application
APP_NAME="Kaio Portfolio - ML Engineer"
ENV=production
BASE_URL=https://kaio.ia.br

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security
ALLOWED_ORIGINS=https://kaio.ia.br,https://www.kaio.ia.br
RATE_LIMIT=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
PROMETHEUS_ENABLED=true

# LLM Providers
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
OPENAI_API_KEY=your_openai_key_here

# Embeddings
VOYAGE_API_KEY=your_voyage_key_here

# Vector Database
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_key_here

# RAG Config
RATE_LIMIT_MONTHLY=15
EOF

# Editar com suas keys reais
nano .env

# Proteger arquivo
chmod 600 .env
```

### 3.3 Configurar Kaggle (Para Credit Risk)

```bash
# Criar diretório Kaggle
mkdir -p ~/.kaggle

# Copiar kaggle.json (baixe de https://www.kaggle.com/settings/account)
# Opção 1: Copiar via SCP (do seu PC)
# scp ~/Downloads/kaggle.json deploy@<IP_VPS>:~/.kaggle/

# Opção 2: Criar manualmente
nano ~/.kaggle/kaggle.json
# Cole o conteúdo:
# {"username":"seu_usuario","key":"sua_chave"}

# Proteger
chmod 600 ~/.kaggle/kaggle.json
```

### 3.4 Build e Run Container

```bash
# Build container
podman build -t kaio-portfolio:latest -f Containerfile .

# Criar diretório para dados persistentes
mkdir -p data/models
mkdir -p data/quotas
mkdir -p data/qdrant

# Run container
podman run -d \
  --name kaio-portfolio-api \
  --publish 8000:8000 \
  --env-file .env \
  --volume ./data:/app/data:Z \
  --restart unless-stopped \
  --health-cmd "curl -f http://localhost:8000/api/health || exit 1" \
  --health-interval 30s \
  --health-timeout 10s \
  --health-retries 3 \
  kaio-portfolio:latest

# Verificar logs
podman logs -f kaio-portfolio-api

# Testar health
curl http://localhost:8000/api/health
```

**Saída esperada**:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0"
}
```

---

## 🌐 Passo 4: Configurar Caddy (Reverse Proxy + SSL)

### 4.1 Instalar Caddy

```bash
# Adicionar repositório Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list

# Instalar
sudo apt update
sudo apt install -y caddy
```

### 4.2 Configurar Caddyfile

```bash
# Criar Caddyfile
sudo nano /etc/caddy/Caddyfile
```

**Cole este conteúdo** (substitua `kaio.ia.br` pelo seu domínio):

```caddyfile
# Main portfolio domain
kaio.ia.br, www.kaio.ia.br {
    # Reverse proxy para FastAPI
    reverse_proxy localhost:8000

    # Compression
    encode gzip

    # Security headers
    header {
        # HSTS
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

        # XSS Protection
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"

        # Referrer Policy
        Referrer-Policy "strict-origin-when-cross-origin"

        # Permissions Policy
        Permissions-Policy "geolocation=(), microphone=(), camera=()"
    }

    # Logging
    log {
        output file /var/log/caddy/kaio-portfolio.log {
            roll_size 10MB
            roll_keep 5
        }
        format json
    }

    # Rate limiting (Caddy level)
    rate_limit {
        zone portfolio {
            key {remote_host}
            events 100
            window 1m
        }
    }
}

# API subdomain (opcional)
api.kaio.ia.br {
    reverse_proxy localhost:8000
    encode gzip

    # Apenas permitir rotas de API
    @notapi {
        not path /api/* /docs /redoc /metrics /admin/*
    }
    respond @notapi "Not found" 404
}
```

### 4.3 Iniciar Caddy

```bash
# Testar configuração
sudo caddy validate --config /etc/caddy/Caddyfile

# Recarregar Caddy
sudo systemctl reload caddy

# Verificar status
sudo systemctl status caddy

# Ver logs em tempo real
sudo journalctl -u caddy -f
```

### 4.4 Verificar SSL

Aguarde 1-2 minutos para Caddy obter certificado Let's Encrypt automaticamente.

```bash
# Testar HTTPS
curl -I https://kaio.ia.br

# Deve retornar HTTP/2 200
```

Acesse no navegador: **https://kaio.ia.br** 🎉

---

## 🔍 Passo 5: Monitoring e Manutenção

### 5.1 Verificar Status dos Serviços

```bash
# Status do container
podman ps
podman stats kaio-portfolio-api

# Logs da aplicação
podman logs -f kaio-portfolio-api

# Status do Caddy
sudo systemctl status caddy

# Ver logs do Caddy
sudo tail -f /var/log/caddy/kaio-portfolio.log
```

### 5.2 Endpoints de Health Check

```bash
# Application health
curl https://kaio.ia.br/api/health

# Readiness probe
curl https://kaio.ia.br/api/ready

# Prometheus metrics (se habilitado)
curl https://kaio.ia.br/metrics

# Admin quotas
curl https://kaio.ia.br/admin/quotas
```

### 5.3 Systemd Service (Para Auto-Start)

Criar service para auto-start do container:

```bash
# Criar service file
sudo nano /etc/systemd/system/kaio-portfolio.service
```

**Cole**:

```ini
[Unit]
Description=Kaio Portfolio ML API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/kaio-portfolio
ExecStart=/usr/bin/podman start -a kaio-portfolio-api
ExecStop=/usr/bin/podman stop -t 10 kaio-portfolio-api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Ativar**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kaio-portfolio
sudo systemctl start kaio-portfolio
sudo systemctl status kaio-portfolio
```

---

## 🔄 Atualizações e Deploy

### Método 1: Script Automatizado

No seu **PC local**:

```bash
# Editar scripts/deploy.sh com IP e usuário da VPS
nano scripts/deploy.sh

# Deploy
./scripts/deploy.sh
```

### Método 2: Manual

Na **VPS**:

```bash
# 1. Pull latest code
cd /opt/kaio-portfolio
git pull origin main

# 2. Rebuild container
podman build -t kaio-portfolio:latest -f Containerfile .

# 3. Stop e remove container antigo
podman stop kaio-portfolio-api
podman rm kaio-portfolio-api

# 4. Run novo container
podman run -d \
  --name kaio-portfolio-api \
  --publish 8000:8000 \
  --env-file .env \
  --volume ./data:/app/data:Z \
  --restart unless-stopped \
  kaio-portfolio:latest

# 5. Verificar
podman logs -f kaio-portfolio-api
curl http://localhost:8000/api/health
```

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
podman logs kaio-portfolio-api

# Inspecionar container
podman inspect kaio-portfolio-api

# Testar manualmente
podman run -it --rm --env-file .env kaio-portfolio:latest /bin/bash
# Dentro do container:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### SSL não funciona

```bash
# Ver logs do Caddy
sudo journalctl -u caddy -f

# Testar configuração
sudo caddy validate --config /etc/caddy/Caddyfile

# Verificar DNS
dig kaio.ia.br +short  # Deve retornar IP da VPS

# Forçar renovação de certificado
sudo systemctl restart caddy
```

### Alta utilização de recursos

```bash
# Ver uso de recursos
podman stats kaio-portfolio-api
htop

# Reduzir workers (editar Containerfile)
# CMD ["uvicorn", "app.main:app", "--workers", "2"]  # De 4 para 2

# Rebuild e redeploy
```

### Erro de permissão nos volumes

```bash
# Corrigir permissões
sudo chown -R 1000:1000 /opt/kaio-portfolio/data

# Ajustar SELinux labels (se aplicável)
sudo chcon -Rt svirt_sandbox_file_t /opt/kaio-portfolio/data
```

---

## 📊 Backup e Restore

### Backup

```bash
# Backup dos dados
cd /opt/kaio-portfolio
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Mover para local seguro
scp backup-*.tar.gz seu-pc:~/backups/
```

### Restore

```bash
# Restore dados
cd /opt/kaio-portfolio
tar -xzf backup-YYYYMMDD.tar.gz

# Restart container
podman restart kaio-portfolio-api
```

---

## 📈 Próximos Passos

- [ ] Configurar Prometheus + Grafana para dashboards
- [ ] Setup de backups automáticos (cron + rclone para S3)
- [ ] Configurar alertas (PagerDuty, Slack)
- [ ] Implementar CI/CD com GitHub Actions
- [ ] Setup de staging environment
- [ ] Configurar CDN (Cloudflare) para static assets

---

## 💬 Suporte

Se encontrar problemas:

1. Verifique os logs: `podman logs kaio-portfolio-api`
2. Teste health endpoint: `curl http://localhost:8000/api/health`
3. Abra issue no GitHub: https://github.com/KaioH3/kaio-portfolio/issues

---

**🎉 Parabéns! Seu portfolio ML está em produção!**

Acesse: **https://kaio.ia.br**
