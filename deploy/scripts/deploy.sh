#!/bin/bash
#============================================================================
# Deploy script para VPS Hetzner
#============================================================================

set -e

echo "Deploying Kaio Portfolio to Production..."

# Build image
echo "Building container image..."
cd ..
podman build -t kaio-portfolio-api:latest -f containerfiles/Containerfile.api .

# Stop existing containers
echo "Stopping existing containers..."
podman-compose -f deploy/podman-compose.yml down || true

# Start new containers
echo "Starting new containers..."
podman-compose -f deploy/podman-compose.yml up -d

# Show status
echo ""
echo "Deployment complete!"
echo ""
echo "Container status:"
podman ps

echo ""
echo "Health check:"
sleep 5
curl -s http://localhost:8000/api/health | jq

echo ""
echo "🎉 Application available at http://localhost:8000"
