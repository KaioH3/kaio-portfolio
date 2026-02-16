#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# 🚀 Deploy Script - Kaio Portfolio
# Automatiza deploy via SSH para Hetzner VPS
# ══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error
set -u  # Exit on undefined variable

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

REMOTE_HOST="${DEPLOY_HOST:-}"
REMOTE_USER="${DEPLOY_USER:-deploy}"
REMOTE_DIR="/opt/kaio-portfolio"
IMAGE_NAME="kaio-portfolio:latest"
IMAGE_TAR="kaio-portfolio-$(date +%Y%m%d-%H%M%S).tar"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────

log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# ──────────────────────────────────────────────────────────────────────────────
# Validations
# ──────────────────────────────────────────────────────────────────────────────

if [ -z "$REMOTE_HOST" ]; then
    log_error "DEPLOY_HOST não configurado!"
    echo ""
    echo "Configure com:"
    echo "  export DEPLOY_HOST=seu-ip-ou-dominio.com"
    echo "  export DEPLOY_USER=deploy  # (opcional, padrão: deploy)"
    echo ""
    echo "Exemplo:"
    echo "  export DEPLOY_HOST=123.45.67.89"
    echo "  ./scripts/deploy.sh"
    exit 1
fi

log_info "Configuração:"
echo "  Host: ${REMOTE_HOST}"
echo "  User: ${REMOTE_USER}"
echo "  Dir:  ${REMOTE_DIR}"
echo ""

# ──────────────────────────────────────────────────────────────────────────────
# Pre-deploy checks
# ──────────────────────────────────────────────────────────────────────────────

log_info "Verificando pré-requisitos..."

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    log_error "Podman não instalado! Instale com: sudo apt install podman"
    exit 1
fi

# Check if SSH key is configured
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} true 2>/dev/null; then
    log_warning "SSH sem chave configurada. Você precisará digitar a senha várias vezes."
    read -p "Continuar? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log_success "Pré-requisitos OK"

# ──────────────────────────────────────────────────────────────────────────────
# Build container image
# ──────────────────────────────────────────────────────────────────────────────

log_info "Construindo imagem Docker..."
podman build -t ${IMAGE_NAME} -f Containerfile .
log_success "Imagem construída"

# ──────────────────────────────────────────────────────────────────────────────
# Save and transfer image
# ──────────────────────────────────────────────────────────────────────────────

log_info "Salvando imagem para arquivo..."
podman save -o ${IMAGE_TAR} ${IMAGE_NAME}
IMAGE_SIZE=$(du -h ${IMAGE_TAR} | cut -f1)
log_success "Imagem salva (${IMAGE_SIZE})"

log_info "Transferindo para ${REMOTE_HOST}..."
scp ${IMAGE_TAR} ${REMOTE_USER}@${REMOTE_HOST}:/tmp/
log_success "Transferência completa"

# Cleanup local tar
rm ${IMAGE_TAR}

# ──────────────────────────────────────────────────────────────────────────────
# Deploy on remote server
# ──────────────────────────────────────────────────────────────────────────────

log_info "Executando deploy no servidor..."

ssh ${REMOTE_USER}@${REMOTE_HOST} << ENDSSH
set -e

# Colors in SSH session
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\${BLUE}[REMOTE]\${NC} Carregando imagem..."
podman load -i /tmp/${IMAGE_TAR}

echo -e "\${BLUE}[REMOTE]\${NC} Removendo imagem temporária..."
rm /tmp/${IMAGE_TAR}

echo -e "\${BLUE}[REMOTE]\${NC} Parando container antigo..."
podman stop kaio-portfolio-api 2>/dev/null || true
podman rm kaio-portfolio-api 2>/dev/null || true

echo -e "\${BLUE}[REMOTE]\${NC} Iniciando novo container..."
podman run -d \\
  --name kaio-portfolio-api \\
  --publish 8000:8000 \\
  --env-file ${REMOTE_DIR}/.env \\
  --volume ${REMOTE_DIR}/data:/app/data:Z \\
  --restart unless-stopped \\
  --health-cmd "curl -f http://localhost:8000/api/health || exit 1" \\
  --health-interval 30s \\
  --health-timeout 10s \\
  --health-retries 3 \\
  ${IMAGE_NAME}

echo -e "\${BLUE}[REMOTE]\${NC} Aguardando inicialização..."
sleep 8

echo -e "\${BLUE}[REMOTE]\${NC} Verificando saúde da aplicação..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
  echo -e "\${GREEN}✓\${NC} Aplicação saudável!"
else
  echo -e "\${RED}✗\${NC} Health check falhou! Logs:"
  podman logs --tail 50 kaio-portfolio-api
  exit 1
fi

echo -e "\${BLUE}[REMOTE]\${NC} Limpando imagens antigas..."
podman image prune -f

echo -e "\${GREEN}✓\${NC} Deploy concluído com sucesso!"
ENDSSH

# ──────────────────────────────────────────────────────────────────────────────
# Final checks
# ──────────────────────────────────────────────────────────────────────────────

log_info "Verificando endpoint público..."

sleep 3

if curl -f https://${REMOTE_HOST}/api/health > /dev/null 2>&1; then
    log_success "Endpoint público respondendo!"
else
    log_warning "Endpoint público ainda não disponível (pode levar alguns segundos para SSL)"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Success message
# ──────────────────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 Portfolio:   https://${REMOTE_HOST}"
echo "  📊 Health:      https://${REMOTE_HOST}/api/health"
echo "  📈 Metrics:     https://${REMOTE_HOST}/metrics"
echo "  🔧 Admin:       https://${REMOTE_HOST}/admin/quotas"
echo ""
echo "Comandos úteis:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'podman logs -f kaio-portfolio-api'"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'podman stats kaio-portfolio-api'"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
