# Pregnancy Medication Checker - Root Makefile
# Docker orchestration and project-level commands

# Docker Hub username (default: canovalentina)
DOCKER_USERNAME ?= canovalentina
IMAGE_TAG ?= latest

# Image names
HAPI_IMAGE = $(DOCKER_USERNAME)/pregnancy-hapi-fhir:$(IMAGE_TAG)
BACKEND_IMAGE = $(DOCKER_USERNAME)/pregnancy-backend:$(IMAGE_TAG)

.PHONY: help build up down restart logs clean
.PHONY: docker-login docker-build-backend docker-push-backend docker-build-hapi docker-push-hapi
.PHONY: health-check-backend health-check-frontend health-check-hapi 
.PHONY: deploy-frontend deploy-backend deploy-frontend-backend
.PHONY: fly-logs

help:
	@echo "Available commands:"
	@echo ""
	@echo "Local Development (docker-compose):"
	@echo "  make build     - Build Docker images for local dev"
	@echo "  make up        - Start all services locally"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - View logs"
	@echo "  make clean     - Clean up Docker resources"
	@echo ""
	@echo "Docker Hub Deployment:"
	@echo "  make docker-login        - Login to Docker Hub"
	@echo "  make docker-build-backend - Build Backend image for Docker Hub"
	@echo "  make docker-push-backend - Build and Push Backend image to Docker Hub"
	@echo "  make docker-build-hapi   - Build HAPI FHIR image for Docker Hub"
	@echo "  make docker-push-hapi    - Build and Push HAPI FHIR image to Docker Hub"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-frontend     - Deploy frontend to Vercel"
	@echo "  make deploy-backend      - Deploy backend to Fly.io"
	@echo "  make deploy-frontend-backend  - Deploy both frontend and backend"
	@echo ""
	@echo "Health Checks:"
	@echo "  make health-check-backend - Check Backend API health"
	@echo "  make health-check-frontend - Check Frontend health"
	@echo "  make health-check-hapi   - Check HAPI FHIR server health"
	@echo ""
	@echo "Fly.io Logs:"
	@echo "  make fly-logs           - View Fly.io backend logs"
	@echo ""
	@echo "Environment variables:"
	@echo "  DOCKER_USERNAME - Docker Hub username (default: canovalentina)"
	@echo "  IMAGE_TAG       - Image tag (default: latest)"
	@echo ""
	@echo "Examples:"
	@echo "  make docker-deploy                    # Deploy with default username"
	@echo "  make deploy-backend                   # Deploy backend only"
	@echo "  make deploy-frontend-backend          # Deploy both frontend and backend"

# Local development commands (docker-compose)
build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Build complete! Run 'make up' to start services."

up:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services started successfully!"
	@echo ""
	@echo "📍 Access your application at:"
	@echo "   Frontend:       http://localhost:5173"
	@echo "   Backend API:    http://localhost:8000"
	@echo "   API Docs:       http://localhost:8000/docs"
	@echo "   Backend Health Check:   http://localhost:8000/api/health"
	@echo "   HAPI FHIR:      http://localhost:8080"
	@echo ""
	@echo "💡 Useful commands:"
	@echo "   make logs    - View service logs"
	@echo "   make down    - Stop all services"
	@echo "   make restart - Restart all services"

down:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped."

restart: 
	@echo "🔄 Restarting all services..."
	@$(MAKE) down
	@$(MAKE) up

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f


# Docker Hub commands
docker-login:
	@echo "Logging in to Docker Hub..."
	@docker login

docker-build-hapi:
	@echo "Building HAPI FHIR image: $(HAPI_IMAGE) (platform: linux/amd64)"
	docker build --platform linux/amd64 -f config/Dockerfile.hapi -t $(HAPI_IMAGE) .

docker-build-backend:
	@echo "Building Backend image: $(BACKEND_IMAGE) (platform: linux/amd64)"
	docker build --platform linux/amd64 -f config/Dockerfile.backend -t $(BACKEND_IMAGE) .

docker-push-hapi: docker-build-hapi
	@echo "Pushing HAPI FHIR image: $(HAPI_IMAGE)"
	docker push $(HAPI_IMAGE)
	@echo "✅ HAPI FHIR image pushed successfully!"

docker-push-backend: docker-build-backend
	@echo "Pushing Backend image: $(BACKEND_IMAGE)"
	docker push $(BACKEND_IMAGE)
	@echo "✅ Backend image pushed successfully!"


# Deployment commands
deploy-frontend:
	@echo "🚀 Deploying frontend to Vercel..."
	@chmod +x scripts/deploy/deploy-frontend.sh
	@./scripts/deploy/deploy-frontend.sh
	@echo ""
	@echo "🔍 Verifying deployment..."
	@make health-check-frontend || true
	@echo ""
	@echo "📋 Frontend deployment complete!"
	@echo "   URL: https://pregnancy-med-checker.vercel.app"

deploy-backend:
	@echo "🚀 Deploying backend to Fly.io..."
	@chmod +x scripts/deploy/deploy-backend.sh
	@./scripts/deploy/deploy-backend.sh

deploy-frontend-backend: deploy-backend deploy-frontend
	@echo ""
	@echo "✅ All deployments complete!"
	@echo ""
	@echo "🔍 Running health checks..."
	@make health-check-backend || true
	@make health-check-frontend || true
	@echo ""
	@echo "📋 Deployment Summary:"
	@echo "   Frontend: https://pregnancy-med-checker.vercel.app"
	@echo "   Backend:  https://pregnancy-backend.fly.dev/api"


# Health check commands

health-check-backend:
	@echo "Checking Backend API health..."
	@curl -s -f https://pregnancy-backend.fly.dev/api/health > /dev/null && \
		echo "✅ Backend API is healthy!" || \
		(echo "❌ Backend API is not responding" && exit 1)

health-check-frontend:
	@echo "Checking Frontend health..."
	@curl -s -f https://pregnancy-med-checker.vercel.app > /dev/null && \
		echo "✅ Frontend is healthy!" || \
		(echo "❌ Frontend is not responding" && exit 1)

health-check-hapi:
	@echo "Checking HAPI FHIR server health..."
	@curl -s -f https://pregnancy-hapi-fhir.fly.dev/fhir/metadata > /dev/null && \
		echo "✅ HAPI FHIR server is healthy!" || \
		(echo "❌ HAPI FHIR server is not responding" && exit 1)

# Fly.io logs
fly-logs:
	@echo "📋 Viewing Fly.io backend logs..."
	@flyctl logs -a pregnancy-backend