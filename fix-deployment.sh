#!/bin/bash

echo "🔧 Fixing deployment - stopping existing services and restarting..."

# Stop existing services
echo "Stopping existing services..."
sudo systemctl stop nginx || true
sudo systemctl stop verdict-ai-backend || true
sudo systemctl disable nginx || true
sudo systemctl disable verdict-ai-backend || true

# Stop any existing Docker containers
echo "Stopping existing Docker containers..."
docker-compose down --remove-orphans || true

# Kill any processes using port 80
echo "Freeing up port 80..."
sudo fuser -k 80/tcp || true
sudo fuser -k 8080/tcp || true

# Wait a moment
sleep 3

# Start Docker deployment
echo "Starting Docker deployment..."
docker-compose up --build -d

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Test the application
echo "Testing application..."
curl -f http://localhost:8080/api/health && echo "✅ Health check passed!" || echo "❌ Health check failed!"

echo "🎉 Deployment fixed! Your app is available at:"
echo "  http://$(curl -s ifconfig.me):8080/api/health"
