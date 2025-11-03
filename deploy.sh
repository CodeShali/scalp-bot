#!/bin/bash

# TARA Deployment Script for Raspberry Pi
# This script pulls latest changes and updates the bot

echo "🤖 TARA Deployment Script"
echo "=========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run this script from the scalp-bot directory.${NC}"
    exit 1
fi

echo -e "${YELLOW}📥 Step 1: Pulling latest changes from GitHub...${NC}"
git pull origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git pull failed. Please resolve conflicts manually.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Code updated successfully${NC}"
echo ""

echo -e "${YELLOW}📦 Step 2: Installing/updating Python dependencies...${NC}"
pip3 install -r requirements.txt --upgrade
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Dependency installation failed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dependencies updated${NC}"
echo ""

echo -e "${YELLOW}🔧 Step 3: Checking configuration...${NC}"
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}❌ config.yaml not found!${NC}"
    echo "Please create config.yaml from config.yaml.example"
    exit 1
fi

# Check for required config settings
if ! grep -q "max_active_tickers" config.yaml; then
    echo -e "${YELLOW}⚠️  Warning: max_active_tickers not found in config.yaml${NC}"
    echo "Add this to your scanning section:"
    echo "  max_active_tickers: 3"
fi

if ! grep -q "api_key.*sk-proj" config.yaml; then
    echo -e "${YELLOW}⚠️  Warning: OpenAI API key might not be configured${NC}"
fi

echo -e "${GREEN}✅ Configuration checked${NC}"
echo ""

echo -e "${YELLOW}🔄 Step 4: Restarting TARA service...${NC}"

# Check if running as systemd service
if systemctl is-active --quiet scalp-bot; then
    echo "Restarting systemd service..."
    sudo systemctl restart scalp-bot
    sleep 2
    if systemctl is-active --quiet scalp-bot; then
        echo -e "${GREEN}✅ Service restarted successfully${NC}"
    else
        echo -e "${RED}❌ Service failed to start. Check logs with: sudo journalctl -u scalp-bot -n 50${NC}"
        exit 1
    fi
else
    # Not running as service, kill and restart manually
    echo "Stopping any running instances..."
    pkill -f "python3 main.py" || true
    sleep 2
    
    echo "Starting TARA in background..."
    nohup python3 main.py > logs/tara.log 2>&1 &
    sleep 3
    
    if pgrep -f "python3 main.py" > /dev/null; then
        echo -e "${GREEN}✅ TARA started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start TARA. Check logs/tara.log${NC}"
        exit 1
    fi
fi
echo ""

echo -e "${YELLOW}📊 Step 5: Verifying deployment...${NC}"
sleep 2

# Check if dashboard is accessible
if curl -s http://localhost:8001 > /dev/null; then
    echo -e "${GREEN}✅ Dashboard is accessible at http://localhost:8001${NC}"
else
    echo -e "${RED}❌ Dashboard is not responding${NC}"
fi

# Show recent logs
echo ""
echo -e "${YELLOW}📝 Recent logs:${NC}"
if [ -f "logs/bot.log" ]; then
    tail -n 10 logs/bot.log
else
    echo "No log file found"
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "📍 Dashboard: http://localhost:8001"
echo "📝 Logs: tail -f logs/bot.log"
echo "🔄 Restart: sudo systemctl restart scalp-bot"
echo "📊 Status: sudo systemctl status scalp-bot"
echo ""
