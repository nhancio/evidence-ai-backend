#!/bin/bash

# Docker Deployment Script for Verdict AI Backend
# This script deploys the application using Docker Compose

set -e  # Exit on any error

echo "🐳 Starting Docker Deployment for Verdict AI Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is installed
print_step "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Installing Docker..."
    
    # Update system
    sudo apt update
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_warning "Docker installed. Please log out and log back in, then run this script again."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

print_status "Docker and Docker Compose are ready!"

# Stop any existing containers
print_step "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Remove old images to force rebuild
print_step "Cleaning up old images..."
docker-compose down --rmi all --volumes --remove-orphans || true

# Build and start services
print_step "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_step "Waiting for services to start..."
sleep 30

# Check service status
print_step "Checking service status..."
docker-compose ps

# Test the application
print_step "Testing the application..."
sleep 10

# Test health endpoint
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    print_status "✅ Health check passed!"
    curl http://localhost/api/health
else
    print_error "❌ Health check failed!"
    print_step "Checking logs..."
    docker-compose logs --tail=50
    exit 1
fi

# Test root endpoint
if curl -f http://localhost/ > /dev/null 2>&1; then
    print_status "✅ Root endpoint working!"
else
    print_warning "⚠️ Root endpoint not responding"
fi

# Get external IP
EXTERNAL_IP=$(curl -s ifconfig.me)
print_status "🎉 Deployment completed successfully!"
print_status "Your application is available at:"
print_status "  Local: http://localhost/api/health"
print_status "  External: http://$EXTERNAL_IP/api/health"

print_step "Useful commands:"
echo "  docker-compose ps                    # Check service status"
echo "  docker-compose logs -f               # View logs"
echo "  docker-compose restart               # Restart services"
echo "  docker-compose down                  # Stop services"
echo "  docker-compose up -d                 # Start services"

print_warning "Don't forget to:"
print_warning "1. Configure your domain name in nginx-docker.conf"
print_warning "2. Set up SSL certificate with Let's Encrypt"
print_warning "3. Configure firewall rules (ufw allow 80, ufw allow 443)"
print_warning "4. Set GOOGLE_API_KEY environment variable for summarization"
