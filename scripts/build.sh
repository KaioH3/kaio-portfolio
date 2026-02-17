#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Build Podman Image
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "Building Kaio Portfolio Container..."
echo ""

# Build image with Podman
podman build \
  --tag kaio-portfolio:latest \
  --tag kaio-portfolio:$(date +%Y%m%d) \
  --file Containerfile \
  --format docker \
  .

echo ""
echo "Build complete!"
echo ""
echo "Image tags:"
podman images | grep kaio-portfolio | head -5

echo ""
echo "Next steps:"
echo "  1. Test locally: ./scripts/run.sh"
echo "  2. Deploy to VPS: ./scripts/deploy.sh"
