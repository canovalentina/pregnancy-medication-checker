# Fly.io Backend API Deployment Guide

## Prerequisites

1. ✅ Backend Docker image built and pushed to Docker Hub

---

## Step 1: Build and Push Backend Image

```bash
# Go to pregnancy-med-checker folder
cd pregnancy-med-checker

# Build and push backend image
make docker-push-backend
```

---

## Step 2: Create Backend App on Fly.io

```bash
# Create app (using fly-backend.toml)
flyctl apps create pregnancy-backend

# Or if the name is taken, use a different name
flyctl apps create pregnancy-backend-api
```

---

## Step 3: Deploy Backend

```bash
# Deploy using fly-backend.toml configuration
flyctl deploy --config config/fly-backend.toml

# Watch logs
flyctl logs -a pregnancy-backend
```

---

## Step 4: Verify Deployment

```bash
# Check status
flyctl status -a pregnancy-backend

# Test health endpoint
curl https://pregnancy-backend.fly.dev/api/health

# Or open in browser
flyctl open /api/health -a pregnancy-backend
```

---

## Step 5: Update Frontend Environment Variables

Update your Vercel frontend to use the new backend:

### In Vercel Dashboard:
1. Go to your project → Settings → Environment Variables
2. Update or add:
   ```
   VITE_API_BASE_URL=https://pregnancy-backend.fly.dev
   ```
3. Redeploy your frontend

### Or use Vercel CLI:
```bash
vercel env add VITE_API_BASE_URL production
# Enter: https://pregnancy-backend.fly.dev

# Redeploy
vercel --prod
```

---

## Environment Variables

The backend is configured with these environment variables (in `config/fly-backend.toml`):

- `PORT=8000`
- `APP_NAME="Pregnancy Medication Checker API"`
- `API_PREFIX="/api"`
- `FHIR_SERVER_URL="http://hapi.fhir.org/baseR4"`
- `FHIR_APP_ID="pregnancy-med-checker"`
- `FHIR_TIMEOUT="30"`
- `LOG_LEVEL="INFO"`
- `ENABLE_CORS_ORIGINS="http://localhost:5173,https://pregnancy-med-checker.vercel.app,https://www.pregsafe.org"`

### To update environment variables:

```bash
# Update FHIR server URL
flyctl secrets set FHIR_SERVER_URL="http://hapi.fhir.org/baseR4" -a pregnancy-backend

# Update CORS origins
flyctl secrets set ENABLE_CORS_ORIGINS="http://localhost:5173,https://pregnancy-med-checker.vercel.app,https://www.pregsafe.org" -a pregnancy-backend

# View all secrets
flyctl secrets list -a pregnancy-backend
```

---

## Testing End-to-End

### 1. Test Backend Health
```bash
curl https://pregnancy-backend.fly.dev/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-17T..."
}
```

### 2. Test FHIR Connection
```bash
curl -s http://hapi.fhir.org/baseR4/metadata
```

### 3. Test from Frontend
Open your Vercel frontend and verify:
- API calls work
- FHIR data loads
- No CORS errors in console

---

## Troubleshooting

### Backend won't start
```bash
# Check logs for errors
flyctl logs -a pregnancy-backend

# Common issue: Image not found
# Rebuild and push: make docker-push-backend
```

### CORS errors in frontend
```bash
# Update CORS origins to include your Vercel URL
flyctl secrets set ENABLE_CORS_ORIGINS="http://localhost:5173,https://your-vercel-app.vercel.app,https://www.pregsafe.org" -a pregnancy-backend
```

### Can't connect to HAPI FHIR
```bash
# Verify HAPI FHIR is running
curl -s http://hapi.fhir.org/baseR4/metadata

# Update backend's FHIR server URL
flyctl secrets set FHIR_SERVER_URL="https://pregnancy-hapi-fhir.fly.dev/fhir" -a pregnancy-backend
```

### Health check failing
```bash
# Check if the app is listening on port 8000
flyctl ssh console -a pregnancy-backend
# In the container:
curl localhost:8000/api/health
```

---

## Updating the Deployment

When you make changes to the backend code:

```bash
# 1. Rebuild and push Docker image
cd pregnancy-med-checker
make docker-push-backend

# 2. Redeploy to Fly.io
flyctl deploy --config config/fly-backend.toml -a pregnancy-backend
```

---

## Monitoring & Management

### View logs
```bash
# View live logs
flyctl logs -a pregnancy-backend
```

### Check app status
```bash
# Get detailed app status
flyctl status -a pregnancy-backend

# List all apps
flyctl apps list

# Get app info
flyctl apps info pregnancy-backend
```

### Pause/Stop Deployment

#### Stop a running deployment script
```bash
# If deployment is running in terminal, press Ctrl+C
```

#### Pause/Stop the running app
```bash
# Scale down to 0 instances (pauses the app)
flyctl scale count 0 -a pregnancy-backend

# Stop all machines
flyctl machine stop -a pregnancy-backend

# Stop a specific machine
flyctl machine stop <machine-id> -a pregnancy-backend
```

#### Resume/Start the app
```bash
# Scale back up to 1 instance
flyctl scale count 1 -a pregnancy-backend

# Start all machines
flyctl machine start -a pregnancy-backend

# Start a specific machine
flyctl machine start <machine-id> -a pregnancy-backend
```

### Scale Management
```bash
# Scale to specific count
flyctl scale count 1 --max-per-region 1 -a pregnancy-backend

# Scale to zero (free tier - saves costs)
flyctl scale count 0 -a pregnancy-backend

# Check current scale
flyctl scale show -a pregnancy-backend

# Scale memory
flyctl scale vm memory 1024 -a pregnancy-backend

# Scale CPU
flyctl scale vm cpu 1 -a pregnancy-backend
```

### Restart
```bash
# Restart the entire app
flyctl apps restart pregnancy-backend

# Restart a specific machine
flyctl machine restart <machine-id> -a pregnancy-backend
```

### Delete App

#### Delete the entire app
```bash
# Delete app (requires confirmation)
flyctl apps destroy pregnancy-backend

# Force delete without confirmation
flyctl apps destroy pregnancy-backend --yes
```

#### Delete specific machines
```bash
# List machines
flyctl machine list -a pregnancy-backend

# Delete a specific machine
flyctl machine destroy <machine-id> -a pregnancy-backend

# Delete all machines
flyctl machine destroy-all -a pregnancy-backend
```

### Organization Management

#### List organizations
```bash
# List all organizations you belong to
flyctl orgs list

# Show current organization
flyctl orgs show
```

#### Switch organization
```bash
# Switch to a different organization
flyctl orgs switch <org-name>
```

#### Create organization
```bash
# Create a new organization
flyctl orgs create <org-name>
```

#### Invite members
```bash
# Invite a user to your organization
flyctl orgs invite <email> -a pregnancy-backend
```

### Machine Management
```bash
# List all machines
flyctl machine list -a pregnancy-backend

# Get machine details
flyctl machine status <machine-id> -a pregnancy-backend

# Clone a machine
flyctl machine clone <machine-id> -a pregnancy-backend

# Remove a machine
flyctl machine remove <machine-id> -a pregnancy-backend
```


### Secrets Management
```bash
# List all secrets
flyctl secrets list -a pregnancy-backend

# Set a secret
flyctl secrets set KEY="value" -a pregnancy-backend

# Set multiple secrets
flyctl secrets set KEY1="value1" KEY2="value2" -a pregnancy-backend

# Unset a secret
flyctl secrets unset KEY -a pregnancy-backend

# Import secrets from file
flyctl secrets import < secrets.json -a pregnancy-backend
```
---

## Additional Notes

### SSL Verification

For production, you probably want SSL verification ON (default):
```bash
# SSL verification is ON by default
# To disable it temporarily (not recommended for production):
flyctl secrets set FHIR_VERIFY_SSL=false -a pregnancy-backend
```
---

## Support

- Fly.io Docs: https://fly.io/docs
- Fly.io CLI Reference: https://fly.io/docs/flyctl/
- Backend Logs: `flyctl logs -a pregnancy-backend`