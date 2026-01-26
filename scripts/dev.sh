#!/bin/bash
# ===========================================
# Meeting Assistant - Development Script
# ===========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if Supabase CLI is installed
check_supabase_cli() {
    if ! command -v supabase >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Supabase CLI not found. Installing via Homebrew...${NC}"
        if command -v brew >/dev/null 2>&1; then
            brew install supabase/tap/supabase
        else
            echo -e "${RED}❌ Homebrew not found. Please install Supabase CLI manually:${NC}"
            echo "  https://supabase.com/docs/guides/cli/getting-started"
            exit 1
        fi
    fi
}

# Function to start Supabase
start_supabase() {
    echo -e "${BLUE}📦 Starting Supabase local instance...${NC}"
    cd "$PROJECT_ROOT/supabase"
    
    # Check if Supabase is already running
    if supabase status >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Supabase is already running${NC}"
    else
        supabase start
        echo -e "${GREEN}✓ Supabase started${NC}"
    fi
    
    cd "$PROJECT_ROOT"
}

# Function to stop Supabase
stop_supabase() {
    echo -e "${YELLOW}📦 Stopping Supabase local instance...${NC}"
    cd "$PROJECT_ROOT/supabase"
    supabase stop 2>/dev/null || true
    echo -e "${GREEN}✓ Supabase stopped${NC}"
    cd "$PROJECT_ROOT"
}

# Function to build meet-bot image
build_meet_bot() {
    echo -e "${BLUE}🤖 Building meet-bot Docker image...${NC}"
    docker_compose -f infrastructure/docker/docker-compose.yml build meet-bot
    echo -e "${GREEN}✓ meet-bot image built (docker-meet-bot:latest)${NC}"
}

# Function to check if meet-bot image exists
check_meet_bot_image() {
    if ! docker images | grep -q "docker-meet-bot"; then
        echo -e "${YELLOW}⚠️  meet-bot image not found. Building...${NC}"
        build_meet_bot
    else
        echo -e "${GREEN}✓ meet-bot image exists${NC}"
    fi
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo ""
    
    # Docker containers
    echo -e "${BLUE}Docker Containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "^NAMES|^rkj-" || echo "  No containers running"
    echo ""
    
    # Meet-bot image
    echo -e "${BLUE}Meet-bot Image:${NC}"
    docker images | grep -E "REPOSITORY|docker-meet-bot" || echo "  Image not found"
    echo ""
    
    # Supabase
    echo -e "${BLUE}Supabase Status:${NC}"
    cd "$PROJECT_ROOT/supabase"
    supabase status 2>/dev/null || echo "  Supabase not running"
    cd "$PROJECT_ROOT"
}

case "${1:-help}" in
    up)
        echo -e "${GREEN}🐳 Starting all services...${NC}"
        echo ""
        
        # 1. Check and start Supabase
        check_supabase_cli
        start_supabase
        echo ""
        
        # 2. Build meet-bot image (required for orchestrator to spawn bots)
        check_meet_bot_image
        echo ""
        
        # 3. Start Docker services
        echo -e "${BLUE}🐳 Starting Docker services...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml up -d
        echo ""
        
        echo -e "${GREEN}✅ All services started!${NC}"
        echo ""
        echo -e "${BLUE}Service URLs:${NC}"
        echo "  🌐 Frontend:        http://localhost:3000"
        echo "  🔌 API:             http://localhost:8000"
        echo "  📖 API Docs:        http://localhost:8000/docs"
        echo "  📊 Redis:           localhost:6379"
        echo "  🤖 Bot Orchestrator: http://localhost:8002"
        echo ""
        echo -e "${BLUE}Supabase URLs:${NC}"
        echo "  📦 Studio:          http://localhost:54323"
        echo "  🔗 API:             http://localhost:54321"
        echo "  📧 Inbucket:        http://localhost:54324"
        echo ""
        echo -e "${YELLOW}💡 Tip: Use './scripts/dev.sh logs' to follow service logs${NC}"
        echo -e "${YELLOW}💡 Tip: Use './scripts/dev.sh status' to check service status${NC}"
        ;;
    
    down)
        echo -e "${YELLOW}🛑 Stopping all services...${NC}"
        echo ""
        
        # Stop Docker services first
        echo -e "${YELLOW}Stopping Docker services...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml down
        echo ""
        
        # Stop Supabase
        stop_supabase
        echo ""
        
        echo -e "${GREEN}✅ All services stopped.${NC}"
        ;;
    
    status)
        show_status
        ;;
    
    build-bot)
        echo -e "${GREEN}🤖 Building meet-bot image...${NC}"
        build_meet_bot
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
        echo -e "${GREEN}🏗️  Building all Docker images...${NC}"
        docker_compose -f infrastructure/docker/docker-compose.yml build
        echo -e "${GREEN}✅ Build complete!${NC}"
        ;;
    
    clean)
        echo -e "${YELLOW}🧹 Cleaning up everything...${NC}"
        
        # Stop and remove Docker services
        docker_compose -f infrastructure/docker/docker-compose.yml down -v
        
        # Stop Supabase
        stop_supabase
        
        # Prune Docker
        docker system prune -f
        
        echo -e "${GREEN}✅ Cleanup complete!${NC}"
        ;;
    
    db:migrate)
        echo -e "${GREEN}📊 Running database migrations...${NC}"
        cd supabase
        supabase db push
        echo -e "${GREEN}✅ Migrations applied!${NC}"
        ;;
    
    db:reset)
        echo -e "${YELLOW}⚠️  Resetting database...${NC}"
        cd supabase
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
        echo -e "${BLUE}Main Commands:${NC}"
        echo "  up          Start all services (Supabase + Docker)"
        echo "  down        Stop all services (Docker + Supabase)"
        echo "  status      Show status of all services"
        echo "  logs [svc]  Follow logs (optionally for specific service)"
        echo ""
        echo -e "${BLUE}Development:${NC}"
        echo "  api         Run API in development mode (with hot reload)"
        echo "  web         Run frontend in development mode"
        echo ""
        echo -e "${BLUE}Build \u0026 Maintenance:${NC}"
        echo "  build       Build all Docker images"
        echo "  build-bot   Build meet-bot image only"
        echo "  clean       Stop services and clean up volumes"
        echo ""
        echo -e "${BLUE}Database:${NC}"
        echo "  db:migrate  Run database migrations"
        echo "  db:reset    Reset database (WARNING: destroys data)"
        echo ""
        echo -e "${BLUE}Testing:${NC}"
        echo "  test        Run tests"
        echo "  help        Show this help message"
        echo ""
        ;;
esac
