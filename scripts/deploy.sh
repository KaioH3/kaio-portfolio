#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Deploy to Production VPS (Hetzner)
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Configuration
VPS_HOST="kaio.ia.br"  # Update with your VPS IP or domain
VPS_USER="root"        # Update if different
IMAGE_NAME="kaio-portfolio:latest"
CONTAINER_NAME="kaio-portfolio-api"

echo "🚀 Deploying to Production: $VPS_HOST"
echo ""

# Step 1: Build image
echo "1️⃣  Building image..."
./scripts/build.sh

# Step 2: Save image to tar
echo ""
echo "2️⃣  Saving image to tar..."
podman save -o kaio-portfolio.tar $IMAGE_NAME
echo "✅ Image saved to kaio-portfolio.tar"

# Step 3: Transfer to VPS
echo ""
echo "3️⃣  Transferring to VPS..."
scp kaio-portfolio.tar $VPS_USER@$VPS_HOST:/tmp/
echo "✅ Image transferred"

# Step 4: Deploy on VPS
echo ""
echo "4️⃣  Deploying on VPS..."
ssh $VPS_USER@$VPS_HOST << 'ENDSSH'
  set -e

  # Load image
  echo "Loading image..."
  podman load -i /tmp/kaio-portfolio.tar
  rm /tmp/kaio-portfolio.tar

  # Stop existing container
  echo "Stopping existing container..."
  podman stop kaio-portfolio-api 2>/dev/null || true
  podman rm kaio-portfolio-api 2>/dev/null || true

  # Run new container
  echo "Starting new container..."
  podman run -d \
    --name kaio-portfolio-api \
    --publish 8000:8000 \
    --env-file /opt/kaio-portfolio/.env \
    --volume /opt/kaio-portfolio/data:/app/data:Z \
    --restart unless-stopped \
    --health-cmd "curl -f http://localhost:8000/api/health || exit 1" \
    --health-interval 30s \
    kaio-portfolio:latest

  echo "✅ Container started!"

  # Wait for health check
  echo "Waiting for health check..."
  sleep 5
  podman healthcheck run kaio-portfolio-api || echo "⚠️  Health check pending..."

  # Show status
  echo ""
  echo "Container status:"
  podman ps | grep kaio-portfolio
ENDSSH

# Step 5: Cleanup local tar
rm kaio-portfolio.tar

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Verify deployment:"
echo "  curl https://kaio.ia.br/api/health"
echo ""
echo "View logs:"
echo "  ssh $VPS_USER@$VPS_HOST 'podman logs -f kaio-portfolio-api'"
echo ""
echo "Check status:"
echo "  ssh $VPS_USER@$VPS_HOST 'podman ps'"
echo ""
