#!/bin/bash

# ==============================================================================
# 🚀 1-Click Deploy Script for Meeting Assistant (Production)
# ==============================================================================
# This script prepares the server, configures firewall, keeps Docker updated,
# and deploys the application stack using Traefik and Docker Compose.
# ==============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Deployment Process...${NC}"

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

# 3. Install/Update Docker
echo -e "${YELLOW}Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}Docker installed successfully.${NC}"
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# 4. Configure Firewall (UFW)
echo -e "${YELLOW}Configuring Firewall (UFW)...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp comment 'SSH'
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    # Deny typical exposed ports just in case Docker exposes them unexpectedly (though Traefik handles this)
    ufw deny 3000/tcp
    ufw deny 8000/tcp
    ufw deny 8002/tcp
    
    echo "y" | ufw enable
    echo -e "${GREEN}Firewall configured: SSH (22), HTTP (80), HTTPS (443) allowed.${NC}"
else
    echo -e "${YELLOW}UFW not found. Skipping firewall configuration.${NC}"
fi

# 5. Deploy with Docker Compose
echo -e "${YELLOW}Building and Starting Containers...${NC}"
docker compose -f infrastructure/docker/docker-compose.prod.yml pull
docker compose -f infrastructure/docker/docker-compose.prod.yml build
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d --remove-orphans

# 6. Verification
echo -e "${YELLOW}Verifying Deployment...${NC}"
sleep 5

if docker ps | grep -q "rkj-traefik"; then
    echo -e "${GREEN}✅ deployment SUCCESS!${NC}"
    echo -e "Traefik and services are running."
    echo -e "Check logs with: docker logs -f rkj-traefik"
else
    echo -e "${RED}❌ deployment FAILED! Traefik container is not running.${NC}"
    exit 1
fi
