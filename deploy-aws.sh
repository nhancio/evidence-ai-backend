#!/bin/bash

# EvidenceAI Backend Deployment Script for AWS EC2
# Run this script on your EC2 instance after uploading the code

echo "🚀 Starting EvidenceAI Backend Deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install python3-pip python3-venv nginx git build-essential python3-dev -y

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔑 Creating .env file..."
    cat > .env << EOF
HF_TOKEN=your_huggingface_token_here
PORT=8080
FLASK_ENV=production
EOF
    echo "⚠️  Please edit .env and add your Hugging Face token!"
fi

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/evidenceai.service > /dev/null << EOF
[Unit]
Description=EvidenceAI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8080 --timeout 120 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/evidenceai > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/evidenceai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx
sudo nginx -t

# Start services
echo "🔥 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable evidenceai
sudo systemctl start evidenceai
sudo systemctl restart nginx

# Check status
echo "✅ Checking service status..."
sudo systemctl status evidenceai --no-pager

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env and add your Hugging Face token:"
echo "   nano .env"
echo ""
echo "2. Restart the service:"
echo "   sudo systemctl restart evidenceai"
echo ""
echo "3. Test the API:"
echo "   curl http://localhost/api/health"
echo ""
echo "4. Check logs if needed:"
echo "   sudo journalctl -u evidenceai -f"

