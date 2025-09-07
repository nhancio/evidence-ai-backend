#!/bin/bash

echo "🧪 Testing Verdict AI Backend Deployment..."

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8080/api/health)
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "✅ Health check passed!"
    echo "Response: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed!"
    echo "Response: $HEALTH_RESPONSE"
fi

# Test root endpoint
echo "Testing root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:8080/)
if [[ $ROOT_RESPONSE == *"Verdict AI Backend"* ]]; then
    echo "✅ Root endpoint working!"
    echo "Response: $ROOT_RESPONSE"
else
    echo "❌ Root endpoint failed!"
    echo "Response: $ROOT_RESPONSE"
fi

# Test external access
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "Testing external access..."
EXTERNAL_RESPONSE=$(curl -s http://$EXTERNAL_IP:8080/api/health)
if [[ $EXTERNAL_RESPONSE == *"healthy"* ]]; then
    echo "✅ External access working!"
    echo "Your API is available at: http://$EXTERNAL_IP:8080/api/health"
else
    echo "❌ External access failed!"
    echo "Response: $EXTERNAL_RESPONSE"
fi

echo "🎉 Testing complete!"
