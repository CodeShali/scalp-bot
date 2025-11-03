#!/bin/bash
# Raspberry Pi Setup/Update Script for TARA Scalp Bot
# Run this script whenever code changes to update everything

set -e  # Exit on error

echo "=========================================="
echo "TARA Scalp Bot - Raspberry Pi Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    print_info "Not running on Raspberry Pi, but continuing anyway..."
fi

# 1. Stop services if running
echo ""
echo "1️⃣  Stopping services..."
sudo systemctl stop scalp-bot 2>/dev/null || print_info "scalp-bot service not running"
sudo systemctl stop ngrok 2>/dev/null || print_info "ngrok service not running"
print_success "Services stopped"

# 2. Update code from git
echo ""
echo "2️⃣  Updating code from GitHub..."
git fetch origin
git reset --hard origin/main
print_success "Code updated to latest version"

# 3. Install/update Python dependencies
echo ""
echo "3️⃣  Installing Python dependencies..."
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies installed"

# 4. Check if ngrok is installed
echo ""
echo "4️⃣  Checking ngrok installation..."
if ! command -v ngrok &> /dev/null; then
    print_error "ngrok not installed!"
    echo ""
    echo "Install ngrok with:"
    echo "  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
    echo "  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "  sudo apt update && sudo apt install ngrok"
    echo ""
    echo "Then configure with your authtoken:"
    echo "  ngrok config add-authtoken YOUR_TOKEN"
    exit 1
else
    print_success "ngrok is installed"
fi

# 5. Setup ngrok service
echo ""
echo "5️⃣  Setting up ngrok service..."
sudo cp ngrok.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ngrok
print_success "ngrok service configured"

# 6. Setup bot service
echo ""
echo "6️⃣  Setting up bot service..."
sudo cp scalp-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scalp-bot
print_success "Bot service configured"

# 7. Create necessary directories
echo ""
echo "7️⃣  Creating directories..."
mkdir -p data logs
print_success "Directories created"

# 8. Check config file
echo ""
echo "8️⃣  Checking configuration..."
if [ ! -f "config.yaml" ]; then
    print_error "config.yaml not found!"
    echo ""
    echo "Copy and edit the example config:"
    echo "  cp config.yaml.example config.yaml"
    echo "  nano config.yaml"
    echo ""
    echo "Make sure to set:"
    echo "  - Alpaca API keys"
    echo "  - Discord webhook URL"
    echo "  - OpenAI API key"
    exit 1
else
    print_success "config.yaml exists"
fi

# 9. Start ngrok service
echo ""
echo "9️⃣  Starting ngrok service..."
sudo systemctl start ngrok
sleep 3

# Check if ngrok started
if sudo systemctl is-active --quiet ngrok; then
    print_success "ngrok service started"
    
    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)
    if [ ! -z "$NGROK_URL" ]; then
        print_success "ngrok tunnel: $NGROK_URL"
    fi
else
    print_error "ngrok service failed to start"
    echo "Check logs: sudo journalctl -u ngrok -n 20"
fi

# 10. Start bot service
echo ""
echo "🔟 Starting bot service..."
sudo systemctl start scalp-bot
sleep 3

# Check if bot started
if sudo systemctl is-active --quiet scalp-bot; then
    print_success "Bot service started"
else
    print_error "Bot service failed to start"
    echo "Check logs: sudo journalctl -u scalp-bot -n 20"
    exit 1
fi

# 11. Show status
echo ""
echo "=========================================="
echo "📊 Service Status"
echo "=========================================="
echo ""

echo "ngrok service:"
sudo systemctl status ngrok --no-pager -l | head -5
echo ""

echo "scalp-bot service:"
sudo systemctl status scalp-bot --no-pager -l | head -5
echo ""

# 12. Show useful commands
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo ""
echo "View bot logs:"
echo "  sudo journalctl -u scalp-bot -f"
echo ""
echo "View ngrok logs:"
echo "  sudo journalctl -u ngrok -f"
echo ""
echo "Restart bot:"
echo "  sudo systemctl restart scalp-bot"
echo ""
echo "Restart ngrok:"
echo "  sudo systemctl restart ngrok"
echo ""
echo "Stop everything:"
echo "  sudo systemctl stop scalp-bot ngrok"
echo ""
echo "Check ngrok URL:"
echo "  curl http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'"
echo ""
echo "Dashboard (local):"
echo "  http://localhost:8001"
echo ""
if [ ! -z "$NGROK_URL" ]; then
    echo "Dashboard (public):"
    echo "  $NGROK_URL"
    echo ""
fi
echo "=========================================="
