# Pregnancy Medication Checker

A full-stack application for checking medication interactions during pregnancy using FHIR (Fast Healthcare Interoperability Resources) standards.

## 🏗️ Project Structure

```
pregnancy-med-checker/
├── .env                  # Environment configuration (create from .env.example)
├── docker-compose.yml    # Docker orchestration
├── Makefile             # Docker commands
├── backend/             # FastAPI backend service
│   ├── Makefile         # Backend development commands
│   ├── pyproject.toml   # Python dependencies
│   └── README.md        # Backend documentation
└── frontend/            # React/Vite frontend
    ├── package.json     # Node dependencies
    └── README.md        # Frontend documentation
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (usually pre-installed on macOS)

### Getting Started

1. **Clone and navigate to the project:**

   ```bash
   cd pregnancy-med-checker
   ```

2. **Create environment file:**

   ```bash
   cp .env.example .env
   ```

3. **Start all services:**

   ```bash
   make build  # Build Docker images
   make up     # Start services
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📋 Available Commands (Root Level)

Run these from the `pregnancy-med-checker/` directory:

### Docker Management

```bash
make build     # Build Docker images for all services
make up        # Start all services in detached mode
make down      # Stop all services
make restart   # Restart all services
make logs      # View logs from all services
make clean     # Stop services and clean up volumes
```

### Manual Docker Commands

```bash
# Build and start everything
docker-compose up --build

# Start specific service
docker-compose up backend

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down
```

## 🔧 Configuration

**Important:** This project uses a **single `.env` file** at the root level for all configuration.

Create it from the example:

```bash
cp .env.example .env
```

The `.env` file contains all configuration for both frontend and backend services:

- **Ports**: `BACKEND_PORT`, `FRONTEND_PORT`
- **FHIR Server**: `FHIR_SERVER_URL`, `FHIR_APP_ID`
- **Logging**: `LOG_LEVEL`, `LOG_FORMAT`
- **CORS**: `ENABLE_CORS_ORIGINS`

Both local development (using Makefiles) and Docker use this single `.env` file.

## 🛠️ Development

### Backend Development (Local)

For local backend development without Docker:

```bash
cd backend
make setup    # Setup Python environment
make dev      # Run development server
make test     # Run tests
```

See `backend/README.md` for detailed backend documentation.

### Frontend Development (Local)

For local frontend development without Docker:

```bash
cd frontend
npm install
npm run dev   # Run development server
```

See `frontend/README.md` for detailed frontend documentation.

## 📦 Services

### Backend (FastAPI)

- **Framework**: FastAPI
- **Language**: Python 3.12
- **Port**: 8000 (configurable via `.env`)
- **Features**: FHIR integration, medication checking API

### Frontend (React + Vite)

- **Framework**: React 19
- **Language**: TypeScript
- **Port**: 5173 (configurable via `.env`)
- **Features**: Modern UI for medication checking

## 🔍 API Documentation

When the backend is running, access interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Backend Tests

```bash
cd backend
make test  # Run all backend tests
```

### Full Stack Testing

```bash
# Start services
make up

# Test API endpoints
curl http://localhost:8000/api/health
```

## 🐛 Troubleshooting

### Port Already in Use

Edit `.env` file and change ports:

```bash
BACKEND_PORT=8001
FRONTEND_PORT=3000
```

### Services Won't Start

1. Check if ports are available
2. Verify `.env` file exists
3. Check Docker logs: `make logs`

### Environment Variables Not Working

1. Ensure `.env` file exists in root directory
2. Restart services: `make restart`
3. Check variable names match `.env.example`

## 📝 Environment Variables

All environment variables are documented in `.env.example`. Key variables:

| Variable          | Description              | Default                     |
| ----------------- | ------------------------ | --------------------------- |
| `BACKEND_PORT`    | Backend API port         | 8000                        |
| `FRONTEND_PORT`   | Frontend dev server port | 5173                        |
| `FHIR_SERVER_URL` | FHIR server endpoint     | http://hapi.fhir.org/baseR4 |
| `LOG_LEVEL`       | Logging level            | INFO                        |

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `cd backend && make test`
4. Submit a pull request

## 📄 License

[Add your license information here]

## 👥 Authors

- Valentina Cano Arcay (varcay3@gatech.edu)
- Lana P Kareem (lkareem6@gatech.edu)
- Faezeh Goli (faezeh@gatech.edu)

## 🔗 Links

- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [FHIR Documentation](https://www.hl7.org/fhir/)
