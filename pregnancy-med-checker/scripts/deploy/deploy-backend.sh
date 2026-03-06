#!/bin/bash

# Backend deployment script for Fly.io
# This script builds, pushes, and deploys the backend to Fly.io

set -e  # Exit on error

# Get the project root directory (parent of scripts/deploy)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

echo "🚀 Starting backend deployment to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Error: flyctl is not installed"
    echo "   Install it from: https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if logged in to Docker Hub (if needed)
if [ -z "$DOCKER_USERNAME" ]; then
    DOCKER_USERNAME="canovalentina"
fi

# Navigate to project root
cd "$PROJECT_ROOT"

echo "📦 Step 1: Building and pushing backend image to Docker Hub..."
echo "   Image: ${DOCKER_USERNAME}/pregnancy-backend:latest"

# Build and push the image
docker build --platform linux/amd64 -f config/Dockerfile.backend -t ${DOCKER_USERNAME}/pregnancy-backend:latest .
docker push ${DOCKER_USERNAME}/pregnancy-backend:latest

echo "✅ Backend image pushed successfully!"

echo ""
echo "🌐 Step 2: Deploying to Fly.io..."

# Ensure app exists; create only if it doesn't (name may already exist in another org)
if ! flyctl apps list 2>/dev/null | grep -q "pregnancy-backend"; then
    echo "📝 Creating Fly.io app: pregnancy-backend"
    if ! flyctl apps create pregnancy-backend 2>/dev/null; then
        echo "   (App name may already exist; proceeding to deploy...)"
    fi
fi

# Deploy using fly-backend.toml
flyctl deploy --config config/fly-backend.toml -a pregnancy-backend

echo ""
echo "✅ Backend deployment complete!"
echo ""
echo "🔍 Verifying deployment..."

# Wait a bit for the app to start
sleep 5

# Check health
if curl -s -f https://pregnancy-backend.fly.dev/api/health > /dev/null; then
    echo "✅ Backend is healthy and responding!"
    echo "   URL: https://pregnancy-backend.fly.dev/api"
else
    echo "⚠️  Backend deployed but health check failed"
    echo "   Check logs: flyctl logs -a pregnancy-backend"
fi

echo ""
echo "📋 Useful commands:"
echo "   View logs:    flyctl logs -a pregnancy-backend"
echo "   Check status: flyctl status -a pregnancy-backend"
echo "   Open app:     flyctl open -a pregnancy-backend"
echo "   Delete app:   fly apps destroy pregnancy-backend --yes"
