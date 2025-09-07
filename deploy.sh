#!/bin/bash

# Verdict AI Backend Deployment Script for AWS EC2
# Run this script on your EC2 instance

set -e  # Exit on any error

echo "🚀 Starting Verdict AI Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx git curl wget build-essential

# Create application directory
print_status "Setting up application directory..."
sudo mkdir -p /var/www/verdict-ai-backend
sudo chown $USER:$USER /var/www/verdict-ai-backend

# Clone or update repository
if [ -d "/var/www/verdict-ai-backend/.git" ]; then
    print_status "Updating existing repository..."
    cd /var/www/verdict-ai-backend
    git pull origin main
else
    print_status "Cloning repository..."
    git clone https://github.com/nhancio/evidence-ai-backend.git /var/www/verdict-ai-backend
    cd /var/www/verdict-ai-backend
fi

# Create virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create necessary directories
print_status "Creating necessary directories..."
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo chown -R $USER:$USER /var/log/gunicorn
sudo chown -R $USER:$USER /var/run/gunicorn

# Set up systemd service
print_status "Setting up systemd service..."
sudo cp verdict-ai-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable verdict-ai-backend

# Configure Nginx
print_status "Configuring Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/verdict-ai-backend
sudo ln -sf /etc/nginx/sites-available/verdict-ai-backend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_status "Testing Nginx configuration..."
sudo nginx -t

# Start services
print_status "Starting services..."
sudo systemctl start verdict-ai-backend
sudo systemctl restart nginx

# Enable services to start on boot
sudo systemctl enable nginx

# Check service status
print_status "Checking service status..."
sudo systemctl status verdict-ai-backend --no-pager
sudo systemctl status nginx --no-pager

# Test the application
print_status "Testing application..."
sleep 5
curl -f http://localhost/api/health || print_warning "Health check failed, but service might still be starting"

print_status "🎉 Deployment completed successfully!"
print_status "Your application should be available at: http://$(curl -s ifconfig.me)/api/health"
print_warning "Don't forget to:"
print_warning "1. Configure your domain name in nginx.conf"
print_warning "2. Set up SSL certificate with Let's Encrypt"
print_warning "3. Configure firewall rules (ufw allow 80, ufw allow 443)"
print_warning "4. Set up environment variables if needed"

echo ""
print_status "Useful commands:"
echo "  sudo systemctl status verdict-ai-backend    # Check service status"
echo "  sudo systemctl restart verdict-ai-backend   # Restart service"
echo "  sudo journalctl -u verdict-ai-backend -f    # View logs"
echo "  sudo nginx -t                               # Test nginx config"
echo "  sudo systemctl reload nginx                 # Reload nginx"
