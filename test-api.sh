#!/bin/bash

echo "🧪 Testing Verdict AI Backend API Endpoints..."

BASE_URL="http://localhost:8080"

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/api/health")
echo "Response: $HEALTH_RESPONSE"
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
ROOT_RESPONSE=$(curl -s "$BASE_URL/")
echo "Response: $ROOT_RESPONSE"
echo ""

# Test SMS analysis endpoint
echo "3. Testing SMS analysis endpoint..."
SMS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/analyze_sms" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am so happy and excited about this project!"}')
echo "Response: $SMS_RESPONSE"
echo ""

# Test external access
echo "4. Testing external access..."
EXTERNAL_IP=$(curl -s ifconfig.me)
EXTERNAL_RESPONSE=$(curl -s "http://$EXTERNAL_IP:8080/api/health")
echo "External IP: $EXTERNAL_IP"
echo "External Response: $EXTERNAL_RESPONSE"
echo ""

echo "🎉 API testing complete!"
echo "If external access fails, check your AWS security group settings."
