#!/bin/bash

# ==============================================================================
# 🚀 1-Click Deploy Script for Meeting Assistant (VPS Backend)
# ==============================================================================
# This script deploys the BACKEND services to a VPS.
# The FRONTEND (Next.js) is deployed separately to Vercel.
#
# Architecture:
#   - Frontend: Vercel (https://rkj.ai)
#   - Backend:  This VPS (https://api.rkj.ai)
# ==============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       🚀 Meeting Assistant - Backend Deployment           ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Check Root Privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (sudo ./deploy.sh)${NC}"
  exit 1
fi

# 2. Check for .env file
if [ ! -f .env ]; then
  echo -e "${RED}Error: .env file not found!${NC}"
  echo -e "Please create a .env file from .env.production.example before deploying."
  exit 1
fi

# 3. Check critical env vars
source .env
if [ -z "$API_DOMAIN" ]; then
  echo -e "${RED}Error: API_DOMAIN not set in .env${NC}"
  exit 1
fi

echo -e "${GREEN}✓ API Domain: ${API_DOMAIN}${NC}"

# 4. Install/Update Docker
echo -e "\n${YELLOW}[1/4] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}Docker installed successfully.${NC}"
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# 5. Configure Firewall (UFW)
echo -e "\n${YELLOW}[2/4] Configuring Firewall (UFW)...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp comment 'SSH'
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    # Block direct access to internal ports
    ufw deny 3000/tcp 2>/dev/null || true
    ufw deny 6379/tcp 2>/dev/null || true
    ufw deny 8000/tcp 2>/dev/null || true
    ufw deny 8002/tcp 2>/dev/null || true
    
    echo "y" | ufw enable 2>/dev/null || true
    echo -e "${GREEN}Firewall configured: SSH(22), HTTP(80), HTTPS(443) allowed.${NC}"
else
    echo -e "${YELLOW}UFW not found. Skipping firewall configuration.${NC}"
fi

# 6. Deploy with Docker Compose
echo -e "\n${YELLOW}[3/4] Building and Starting Backend Containers...${NC}"
docker compose -f infrastructure/docker/docker-compose.prod.yml pull 2>/dev/null || true
docker compose -f infrastructure/docker/docker-compose.prod.yml build
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d --remove-orphans

# 7. Verification
echo -e "\n${YELLOW}[4/4] Verifying Deployment...${NC}"
sleep 5

if docker ps | grep -q "rkj-traefik"; then
    echo -e "\n${GREEN}══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Backend Deployment SUCCESS!${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "   ${CYAN}API URL:${NC}  https://${API_DOMAIN}"
    echo ""
    echo -e "   ${YELLOW}Frontend:${NC} Deploy to Vercel separately."
    echo -e "            Set NEXT_PUBLIC_API_URL=https://${API_DOMAIN}"
    echo ""
    echo -e "   ${CYAN}Logs:${NC}     docker logs -f rkj-api"
    echo ""
else
    echo -e "${RED}❌ Deployment FAILED! Check docker logs.${NC}"
    exit 1
fi
