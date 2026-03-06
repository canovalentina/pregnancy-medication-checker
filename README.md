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

## Demo

Below are a series of screenshots illustrating the web app's capabilities. The walkthrough is organized in two parts: **Provider workflow** (login → dashboard → client record → tools) and **Patient workflow** (dashboard and medication safety).

---

### Entry & provider home

**Homepage / login.** The app landing page with sign-in for providers and patients. Use the test accounts above to explore either portal.

![Homepage Login](Sprints/pregsafe_screenshots/01-homepage.png)

**Provider dashboard.** After logging in as a provider, you see the main dashboard with quick access to the client list, drug safety checker, and FHIR patient search.

![Provider Dashboard](Sprints/pregsafe_screenshots/02-provider-dashboard.png)

---

### Provider: example client (Sarah)

The following screens show a single client record so providers can review medications, pregnancy context, and safety information in one place.

**Client overview.** High-level summary for the example client (Sarah), including demographics and key pregnancy-related information pulled from FHIR.

![Provider Example Client Overview](Sprints/pregsafe_screenshots/03-provider-sarah-overview.png)

**Medications.** Current medication list for the client, supporting informed prescribing and interaction checks.

![Provider Example Client Medications](Sprints/pregsafe_screenshots/04-provider-sarah-medications.png)

**Medication interactions.** Pregnancy-aware drug–drug interaction results, with severity and recommendations.

![Provider Example Client Medication Interactions](Sprints/pregsafe_screenshots/05-provider-sarah-med-interaction.png)

**Pregnancy observations.** FHIR-based pregnancy observations (e.g., trimester, due date) used to tailor safety advice.

![Provider Example Client Pregnancy Observations](Sprints/pregsafe_screenshots/06-provider-sarah-pregnancy-observations.png)

**Diet–food interactions.** Warnings about food or dietary interactions with the client’s medications.

![Provider Example Client Diet-Food Interactions](Sprints/pregsafe_screenshots/07-provider-sarah-diet-food-interactions.png)

**Notes.** Clinical notes for the client, for documentation and handoff.

![Provider Example Client Notes](Sprints/pregsafe_screenshots/08-provider-sarah-notes.png)

**Messages.** In-app messaging between provider and client for follow-up and questions.

![Provider Example Client Messages](Sprints/pregsafe_screenshots/09-provider-sarah-messages.png)

---

### Provider: drug safety & FHIR search

**Drug safety checker.** Standalone tool for providers to look up a medication and see pregnancy/lactation safety and warnings without opening a specific client.

![Provider Drug Safety Checker](Sprints/pregsafe_screenshots/10-provider-drug-safety-checker.png)

**Drug safety checker with evidence.** Same tool with linked PubMed citations, giving providers quick access to evidence behind the safety information.

![Provider Drug Safety Checker with PubMed Evidence](Sprints/pregsafe_screenshots/11-provider-drug-safety-checker-evidence.png)

**FHIR patient search.** Search for patients in the connected FHIR server (e.g., by name or ID) to open their record in the app.

![Provider FHIR Patient Search](Sprints/pregsafe_screenshots/12-provider-patient-search.png)

**FHIR patient search results.** Search results listing matching patients; selecting one loads their data into the provider workflow.

![Provider FHIR Patient Search Results](Sprints/pregsafe_screenshots/13-provider-patient-search-2.png)

---

### Patient experience

**Patient dashboard.** After logging in as a patient, the dashboard shows their medications, pregnancy-related info, and clear safety summaries.

![Patient Dashboard](Sprints/pregsafe_screenshots/15-client-dashboard.png)

**Patient dashboard (continued).** Additional sections of the patient view, such as alerts, reminders, or other personalized content.

![Patient Dashboard (Continued)](Sprints/pregsafe_screenshots/16-client-dashboard-2.png)

**Patient medication interactions.** The patient-facing view of medication interactions, with plain-language explanations so they can understand risks and discuss with their provider.

![Patient Medication Interactions](Sprints/pregsafe_screenshots/17-patient-med-interactions.png)
