# Pregnancy Medication Checker

A full-stack web application for checking medication interactions during pregnancy and lactation periods. The system integrates with FHIR (Fast Healthcare Interoperability Resources) standards to provide personalized medication safety assessments for both patients and healthcare providers.

## Overview

The Pregnancy Medication Checker addresses a critical gap in healthcare: most drug interaction checkers are built for general use and do not account for reproductive health factors like pregnancy and lactation. This application provides:

- **Medication Interaction Checking**: Real-time drug interaction analysis with pregnancy-specific warnings
- **FHIR Integration**: Access to patient data including medications, conditions, and pregnancy observations
- **Provider & Patient Portals**: Separate interfaces for healthcare providers and patients
- **Research Integration**: PubMed article search for evidence-based medication safety information
- **FDA Safety Data**: Integration with OpenFDA for drug labeling and adverse event data

## Tech Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI (Python 3.12)
- **FHIR Server**: HAPI FHIR
- **APIs**: RxNorm, OpenFDA, PubMed
- **Containerization**: Docker & Docker Compose
- **Deployment**: Vercel, fly.io

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, for convenience commands)

### Test Accounts

- **Provider**: 
  - Username: `provider`
  - Password: `provider123`
  
- **Patient**: 
  - Username: `patient`
  - Password: `patient123`

### Running Locally with Docker

0. **Clone repository:**
   ```bash
   git clone https://github.gatech.edu/lkareem6/CS6440-Final-Project.git
   ```

1. **Navigate to the project directory:**
   ```bash
   cd pregnancy-med-checker
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env  # Create .env file from example (if .env.example exists)
   ```
   Note: The project uses a single `.env` file at the root for all services.

3. **Build and start all services:**
   ```bash
   make build  # Build Docker images
   make up     # Start all services
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Backend API Health Check: http://localhost:8000/api/health
   - HAPI FHIR Server (if deployed): http://localhost:8080

5. **Stop services:**
   ```bash
   make down # Stop services
   ```

## Project Structure

```
pregnancy-med-checker/
├── backend/          # FastAPI backend service
├── frontend/         # React frontend application
├── docker-compose.yml # Docker orchestration
├── Makefile          # Convenience commands
└── README.md        
```

## Production Deployment

The application is deployed to production:

- **Frontend**: https://pregnancy-med-checker.vercel.app (Vercel)
- **Backend API**: https://pregnancy-backend.fly.dev/api (Fly.io)

### Deployment Commands

From the `pregnancy-med-checker/` directory:

```bash
make deploy-frontend          # Deploy frontend to Vercel
make deploy-backend           # Deploy backend to Fly.io
make deploy-frontend-backend  # Deploy both frontend and backend
```

**Note:** The deployment currently uses a team member's Docker Hub username by default. To use your own Docker Hub account:

1. Login to Docker Hub: `docker login`
2. Set your username when deploying: `DOCKER_USERNAME=yourusername make deploy-backend`
3. Or update the `DOCKER_USERNAME` variable in the Makefile
4. Update the Docker image in `pregnancy-med-checker/config/fly-backend.toml` (`image = "yourusername/pregnancy-backend:latest"`)
5. Redeploy backend

For more detailed backend deployment instructions, see:
- [Backend Deployment Guide](pregnancy-med-checker/docs/fly_backend_deployment.md)

## Team

- **Valentina Cano Arcay** (varcay3@gatech.edu)
- **Lana P Kareem** (lkareem6@gatech.edu)
- **Faezeh Goli** (faezeh@gatech.edu)
