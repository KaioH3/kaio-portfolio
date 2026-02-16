#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Run Container Locally (Development Test)
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🚀 Starting Kaio Portfolio container..."
echo ""

# Load .env file
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
  echo "✅ Loaded .env file"
else
  echo "⚠️  Warning: .env file not found"
fi

# Stop existing container if running
podman stop kaio-portfolio-api 2>/dev/null || true
podman rm kaio-portfolio-api 2>/dev/null || true

# Run container
podman run -d \
  --name kaio-portfolio-api \
  --publish 8000:8000 \
  --env ENV=development \
  --env GROQ_API_KEY="${GROQ_API_KEY}" \
  --env PERPLEXITY_API_KEY="${PERPLEXITY_API_KEY}" \
  --env OPENAI_API_KEY="${OPENAI_API_KEY}" \
  --env VOYAGE_API_KEY="${VOYAGE_API_KEY}" \
  --env QDRANT_URL="${QDRANT_URL}" \
  --env QDRANT_API_KEY="${QDRANT_API_KEY}" \
  --volume ./data:/app/data:Z \
  --health-cmd "curl -f http://localhost:8000/api/health || exit 1" \
  --health-interval 30s \
  kaio-portfolio:latest

echo ""
echo "✅ Container started!"
echo ""
echo "Access:"
echo "  • Homepage: http://localhost:8000"
echo "  • Docs: http://localhost:8000/docs"
echo "  • Health: http://localhost:8000/api/health"
echo "  • Admin: http://localhost:8000/admin/quotas"
echo ""
echo "Logs:"
echo "  podman logs -f kaio-portfolio-api"
echo ""
echo "Stop:"
echo "  podman stop kaio-portfolio-api"
