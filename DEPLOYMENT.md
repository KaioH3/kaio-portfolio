# 🚀 Deployment Guide - Kaio Portfolio

Production deployment with Podman + Caddy + SSL

## 📋 Prerequisites

- VPS com Podman instalado (Hetzner CX22 ou similar)
- Domínio configurado (kaio.ia.br)
- API Keys configuradas (Groq, Voyage AI, Qdrant Cloud)

## 🔧 Quick Start

### 1. Build & Test Locally

```bash
# Build image
./scripts/build.sh

# Run locally
./scripts/run.sh

# Test
curl http://localhost:8000/api/health
```

### 2. Deploy to Production

```bash
# Deploy to VPS
./scripts/deploy.sh
```

## 📦 Container Details

### Image Info
- **Base**: python:3.11-slim
- **Size**: ~500MB (optimized)
- **Architecture**: Multi-stage build
- **User**: Non-root (appuser:1000)

### Exposed Services
- **Port 8000**: FastAPI application
- **Health Check**: `/api/health`
- **Metrics**: `/metrics` (if enabled)

### Environment Variables

```bash
# Required
GROQ_API_KEY=***
VOYAGE_API_KEY=***
QDRANT_URL=https://xxx.cloud.qdrant.io:6333
QDRANT_API_KEY=***

# Optional
PERPLEXITY_API_KEY=***
OPENAI_API_KEY=***
ENV=production
BASE_URL=https://kaio.ia.br
PROMETHEUS_ENABLED=true
RATE_LIMIT_MONTHLY=15
```

## 🔐 Production Setup (VPS)

### 1. Prepare VPS

```bash
# SSH into VPS
ssh root@kaio.ia.br

# Install Podman (if not installed)
apt update && apt install -y podman

# Create app directory
mkdir -p /opt/kaio-portfolio/data
cd /opt/kaio-portfolio

# Create .env file
nano .env
# (paste environment variables)
```

### 2. Manual Deployment

```bash
# On VPS
podman load -i kaio-portfolio.tar

podman run -d \
  --name kaio-portfolio-api \
  --publish 8000:8000 \
  --env-file /opt/kaio-portfolio/.env \
  --volume /opt/kaio-portfolio/data:/app/data:Z \
  --restart unless-stopped \
  kaio-portfolio:latest

# Check logs
podman logs -f kaio-portfolio-api

# Check health
curl http://localhost:8000/api/health
```

### 3. Setup Caddy (Reverse Proxy + SSL)

```bash
# Install Caddy
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy

# Create Caddyfile
cat > /etc/caddy/Caddyfile << 'EOF'
# Main portfolio
kaio.ia.br {
  reverse_proxy localhost:8000
  encode gzip

  # Security headers (already in app, but double layer)
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Frame-Options "DENY"
    X-Content-Type-Options "nosniff"
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

# Landing page subdomain (optional)
landing.kaio.ia.br {
  reverse_proxy localhost:8000
  encode gzip

  # Rewrite to /landing/ path
  rewrite * /landing/{uri}
}

# API subdomain (optional)
api.kaio.ia.br {
  reverse_proxy localhost:8000
  encode gzip

  # Only allow API routes
  @notapi {
    not path /api/* /docs /redoc /metrics /admin/*
  }
  respond @notapi 404
}
EOF

# Reload Caddy
systemctl reload caddy

# Check status
systemctl status caddy
```

### 4. Configure DNS (registro.br)

```
Type  | Host           | Value              | TTL
------|----------------|--------------------|-----
A     | @              | <VPS_IP>           | 3600
A     | www            | <VPS_IP>           | 3600
CNAME | landing        | kaio.ia.br         | 3600
CNAME | api            | kaio.ia.br         | 3600
```

## 🔍 Monitoring

### Check Container Status

```bash
# On VPS
podman ps
podman stats kaio-portfolio-api
podman logs -f kaio-portfolio-api
```

### Health Checks

```bash
# Local health
curl http://localhost:8000/api/health

# Public health
curl https://kaio.ia.br/api/health

# Admin dashboard
curl https://kaio.ia.br/admin/quotas | jq .
```

### View Metrics

```bash
# Prometheus metrics (if enabled)
curl https://kaio.ia.br/metrics
```

## 🔄 Updates

### Deploy New Version

```bash
# Local machine
./scripts/deploy.sh
```

### Rollback

```bash
# On VPS
podman stop kaio-portfolio-api
podman rm kaio-portfolio-api

# Load previous image
podman images | grep kaio-portfolio
podman run -d --name kaio-portfolio-api <previous-image-id>
```

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
podman logs kaio-portfolio-api

# Check environment
podman inspect kaio-portfolio-api | grep -A 20 Env

# Test manually
podman run -it --rm kaio-portfolio:latest /bin/bash
```

### High memory usage

```bash
# Check resources
podman stats

# Adjust workers in Containerfile
# CMD ["uvicorn", "app.main:app", "--workers", "2"]  # Reduce from 4 to 2
```

### SSL issues

```bash
# Check Caddy logs
journalctl -u caddy -f

# Test certificate
curl -vI https://kaio.ia.br

# Force renewal
caddy reload --force
```

## 📊 Performance

### Expected Metrics

- **RAM**: ~550MB per container
- **CPU**: <10% idle, <50% under load
- **Response Time**: <200ms (Credit Risk), ~1.5s (Doc QA)
- **Container Start**: ~5 seconds

### Optimization Tips

1. **Reduce workers**: Adjust `--workers` based on CPU cores
2. **Enable caching**: Add Redis for embeddings cache
3. **CDN**: Serve static files from CDN
4. **Database**: Move from files to PostgreSQL for scaling

## 🔐 Security Checklist

- [x] Non-root container user
- [x] HTTPS with automatic SSL (Caddy)
- [x] Security headers (CSP, HSTS, etc.)
- [x] Rate limiting (IP + API level)
- [x] Input sanitization
- [x] Health checks
- [x] Resource limits
- [x] Read-only filesystem (where possible)
- [ ] Secrets management (use Podman secrets in prod)
- [ ] Firewall rules (only 80, 443, 22)
- [ ] Fail2ban for SSH
- [ ] Regular updates

## 📚 References

- [Podman Documentation](https://docs.podman.io/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
