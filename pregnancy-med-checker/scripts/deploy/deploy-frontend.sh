#!/bin/bash

# Frontend deployment script for Vercel
# This script deploys the frontend to Vercel

set -e  # Exit on error

# Get the project root directory (parent of scripts/deploy)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

echo "🚀 Starting frontend deployment to Vercel..."

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Error: Vercel CLI is not installed"
    echo "   Install it with: npm install -g vercel"
    exit 1
fi

# Build token flag if VERCEL_TOKEN is set
TOKEN_FLAG=""
if [ -n "$VERCEL_TOKEN" ]; then
    TOKEN_FLAG="--token=$VERCEL_TOKEN"
fi

# Navigate to frontend directory
cd "$PROJECT_ROOT/frontend"

# Pull Vercel environment
echo "📥 Pulling Vercel environment..."
vercel pull --yes --environment=production $TOKEN_FLAG

# Build the project
echo "🔨 Building project..."
vercel build --prod $TOKEN_FLAG

# Deploy to production
echo "🌐 Deploying to production..."
vercel deploy --prebuilt --prod $TOKEN_FLAG

echo "✅ Frontend deployment complete!"

