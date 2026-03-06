#!/bin/bash

# Script to delete HAPI FHIR app from Fly.io
# This will permanently delete the app and all its data

set -e  # Exit on error

echo "⚠️  WARNING: This will permanently delete the HAPI FHIR app from Fly.io!"
echo "   App name: pregnancy-hapi-fhir"
echo "   This action cannot be undone!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deletion cancelled."
    exit 0
fi

echo ""
echo "🗑️  Deleting HAPI FHIR app from Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Error: flyctl is not installed"
    echo "   Install it from: https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Check if app exists
if ! flyctl apps list | grep -q "pregnancy-hapi-fhir"; then
    echo "ℹ️  App 'pregnancy-hapi-fhir' not found. It may already be deleted."
    exit 0
fi

# Delete the app (this will also delete volumes and secrets)
echo "📦 Deleting app and all associated resources..."
flyctl apps destroy pregnancy-hapi-fhir --yes

echo ""
echo "✅ HAPI FHIR app deleted successfully!"
echo ""
echo "⚠️  IMPORTANT: Update your backend configuration:"
echo "   1. Update config/fly-backend.toml:"
echo "      Change FHIR_SERVER_URL to use a different server"
echo "      (e.g., http://hapi.fhir.org/baseR4)"
echo ""
echo "   2. Or update via flyctl:"
echo "      flyctl secrets set FHIR_SERVER_URL=\"http://hapi.fhir.org/baseR4\" -a pregnancy-backend"
echo ""
echo "   3. Redeploy backend:"
echo "      make deploy-backend"

