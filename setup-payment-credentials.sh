#!/bin/bash

# Setup Payment Service Credentials
# This script helps you configure WayForPay credentials

set -e

echo "🔧 Payment Service Credentials Setup"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to read input with default value
read_with_default() {
    local prompt="$1"
    local default="$2"
    local value
    
    read -p "$prompt [$default]: " value
    echo "${value:-$default}"
}

echo "📋 Step 1: WayForPay Credentials"
echo "--------------------------------"
echo "Get these from https://wayforpay.com/uk/cabinet/settings/api"
echo ""

MERCHANT_ACCOUNT=$(read_with_default "Merchant Account" "test_merch_n1")
SECRET_KEY=$(read_with_default "Secret Key" "your_secret_key_here")
MERCHANT_DOMAIN=$(read_with_default "Merchant Domain" "example.com")

echo ""
echo "🌐 Step 2: URLs Configuration"
echo "-----------------------------"
echo ""

# Check if ngrok is installed
if command -v ngrok &> /dev/null; then
    echo -e "${GREEN}✓ ngrok is installed${NC}"
    echo ""
    echo "Do you want to use ngrok for local testing? (recommended)"
    read -p "Use ngrok? (y/n): " use_ngrok
    
    if [[ "$use_ngrok" == "y" || "$use_ngrok" == "Y" ]]; then
        echo ""
        echo -e "${YELLOW}Please start ngrok in another terminal:${NC}"
        echo "  ngrok http 8013"
        echo ""
        read -p "Enter your ngrok HTTPS URL (e.g., https://abc123.ngrok.io): " NGROK_URL
        
        if [[ -z "$NGROK_URL" ]]; then
            CALLBACK_URL="http://payment_service:8000/v1/webhooks/wayforpay"
            echo -e "${YELLOW}⚠ No ngrok URL provided. Using default (webhooks won't work)${NC}"
        else
            CALLBACK_URL="${NGROK_URL}/v1/webhooks/wayforpay"
            echo -e "${GREEN}✓ Callback URL: $CALLBACK_URL${NC}"
        fi
    else
        CALLBACK_URL=$(read_with_default "Callback URL" "http://payment_service:8000/v1/webhooks/wayforpay")
    fi
else
    echo -e "${YELLOW}⚠ ngrok is not installed${NC}"
    echo "For local testing with webhooks, install ngrok:"
    echo "  macOS: brew install ngrok"
    echo "  Linux: https://ngrok.com/download"
    echo ""
    CALLBACK_URL=$(read_with_default "Callback URL" "http://payment_service:8000/v1/webhooks/wayforpay")
fi

RETURN_URL=$(read_with_default "Return URL (frontend)" "http://localhost:5173/payment/return")

echo ""
echo "📝 Step 3: Summary"
echo "-----------------"
echo "Merchant Account: $MERCHANT_ACCOUNT"
echo "Secret Key: ${SECRET_KEY:0:10}..."
echo "Merchant Domain: $MERCHANT_DOMAIN"
echo "Callback URL: $CALLBACK_URL"
echo "Return URL: $RETURN_URL"
echo ""

read -p "Is this correct? (y/n): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo "🔧 Updating docker-compose.yml..."

# Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Update docker-compose.yml using sed
sed -i.tmp "s|WAYFORPAY_MERCHANT_ACCOUNT:.*|WAYFORPAY_MERCHANT_ACCOUNT: \"$MERCHANT_ACCOUNT\"|" docker-compose.yml
sed -i.tmp "s|WAYFORPAY_MERCHANT_SECRET_KEY:.*|WAYFORPAY_MERCHANT_SECRET_KEY: \"$SECRET_KEY\"|" docker-compose.yml
sed -i.tmp "s|WAYFORPAY_MERCHANT_DOMAIN:.*|WAYFORPAY_MERCHANT_DOMAIN: \"$MERCHANT_DOMAIN\"|" docker-compose.yml
sed -i.tmp "s|WAYFORPAY_CALLBACK_URL:.*|WAYFORPAY_CALLBACK_URL: \"$CALLBACK_URL\"|" docker-compose.yml
sed -i.tmp "s|WAYFORPAY_RETURN_URL:.*|WAYFORPAY_RETURN_URL: \"$RETURN_URL\"|" docker-compose.yml

# Remove backup file
rm docker-compose.yml.tmp 2>/dev/null || true

echo -e "${GREEN}✓ docker-compose.yml updated${NC}"
echo "  (backup saved as docker-compose.yml.backup)"
echo ""

echo "🚀 Step 4: Restart Services"
echo "--------------------------"
read -p "Restart payment_service now? (y/n): " restart

if [[ "$restart" == "y" || "$restart" == "Y" ]]; then
    echo "Restarting payment_service..."
    docker-compose restart payment_service
    
    echo ""
    echo "Waiting for service to start..."
    sleep 5
    
    echo "Checking health..."
    if curl -sf http://localhost:8013/health/ready > /dev/null; then
        echo -e "${GREEN}✓ Payment service is healthy!${NC}"
    else
        echo -e "${YELLOW}⚠ Payment service health check failed${NC}"
        echo "Check logs: docker-compose logs payment_service"
    fi
fi

echo ""
echo "✅ Setup Complete!"
echo "================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Configure Callback URL in WayForPay Dashboard:"
echo "   → Go to https://wayforpay.com/uk/cabinet/settings/api"
echo "   → Set Service URL to: $CALLBACK_URL"
echo ""
echo "2. Test the payment flow:"
echo "   → Start frontend: cd frontend && npm run dev"
echo "   → Open http://localhost:5173/pricing"
echo "   → Click 'Choose Plan' on any paid plan"
echo ""
echo "3. Check logs if needed:"
echo "   → docker-compose logs -f payment_service"
echo ""
echo "4. Test card for WayForPay:"
echo "   → Card: 4111111111111111"
echo "   → CVV: 111"
echo "   → Expiry: 11/26"
echo ""
echo "📚 Documentation:"
echo "   → See WAYFORPAY_SETUP.md for detailed guide"
echo "   → See payment_service/README.md for API docs"
echo ""
echo "Happy testing! 🎉"
