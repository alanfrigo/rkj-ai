#!/bin/bash
# ===========================================
# Meeting Assistant - Development Script
# ===========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}🚀 Meeting Assistant - Development Setup${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env with your credentials before continuing.${NC}"
    exit 1
fi

# Load environment variables from .env
set -a  # automatically export all variables
source .env
set +a

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker is required but not installed.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v "docker compose" >/dev/null 2>&1 || { echo -e "${RED}❌ Docker Compose is required but not installed.${NC}" >&2; exit 1; }

# Function to run docker compose (handles both old and new versions)
docker_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

case "${1:-help}" in
    up)
        echo -e "${GREEN}🐳 Starting Docker services...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml up -d
        echo ""
        echo -e "${GREEN}✅ Services started!${NC}"
        echo ""
        echo "  📊 Redis:     localhost:6379"
        echo "  🔌 API:       http://localhost:8000"
        echo "  📖 API Docs:  http://localhost:8000/docs"
        echo ""
        ;;
    
    down)
        echo -e "${YELLOW}🛑 Stopping Docker services...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml down
        echo -e "${GREEN}✅ Services stopped.${NC}"
        ;;
    
    logs)
        service="${2:-}"
        if [ -n "$service" ]; then
            docker_compose -f infrastructure/docker/docker-compose.yml logs -f "$service"
        else
            docker_compose -f infrastructure/docker/docker-compose.yml logs -f
        fi
        ;;
    
    api)
        echo -e "${GREEN}🔧 Starting API in development mode...${NC}"
        cd apps/api
        if [ ! -d "venv" ]; then
            echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install -r requirements.txt
        uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    
    web)
        echo -e "${GREEN}🌐 Starting frontend in development mode...${NC}"
        cd apps/web
        if [ ! -d "node_modules" ]; then
            echo -e "${YELLOW}📦 Installing dependencies...${NC}"
            pnpm install
        fi
        pnpm dev
        ;;
    
    build)
        echo -e "${GREEN}🏗️  Building Docker images...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml build
        echo -e "${GREEN}✅ Build complete!${NC}"
        ;;
    
    clean)
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml down -v
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup complete!${NC}"
        ;;
    
    db:migrate)
        echo -e "${GREEN}📊 Running database migrations...${NC}"
        cd infrastructure/supabase
        supabase db push
        echo -e "${GREEN}✅ Migrations applied!${NC}"
        ;;
    
    db:reset)
        echo -e "${YELLOW}⚠️  Resetting database...${NC}"
        cd infrastructure/supabase
        supabase db reset
        echo -e "${GREEN}✅ Database reset!${NC}"
        ;;
    
    test)
        echo -e "${GREEN}🧪 Running tests...${NC}"
        cd apps/api
        source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
        pip install -r requirements.txt -q
        pytest
        ;;
    
    help|*)
        echo "Usage: ./scripts/dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  up          Start all Docker services"
        echo "  down        Stop all Docker services"
        echo "  logs [svc]  Follow logs (optionally for specific service)"
        echo "  api         Run API in development mode (with hot reload)"
        echo "  web         Run frontend in development mode"
        echo "  build       Build all Docker images"
        echo "  clean       Stop services and clean up volumes"
        echo "  db:migrate  Run database migrations"
        echo "  db:reset    Reset database (WARNING: destroys data)"
        echo "  test        Run tests"
        echo "  help        Show this help message"
        echo ""
        ;;
esac
