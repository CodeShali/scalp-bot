#!/bin/bash
#
# Raspberry Pi Setup Script for Scalp Bot
# Run this script on your Raspberry Pi after deploying the code
#

set -e

BOT_DIR="$HOME/scalp-bot"
SERVICE_FILE="scalp-bot.service"

echo "========================================"
echo "Scalp Bot - Raspberry Pi Setup"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found. Please run this script from the scalp-bot directory."
    exit 1
fi

# Update system
echo "Step 1: Updating system packages..."
sudo apt-get update

# Install Python3 and pip if not present
echo "Step 2: Installing Python3 and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
echo "Step 3: Creating Python virtual environment..."
python3 -m venv venv

# Activate venv and install requirements
echo "Step 4: Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Step 5: Creating required directories..."
mkdir -p data logs

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "Step 6: Setting up configuration..."
    if [ -f "config.yaml.example" ]; then
        cp config.yaml.example config.yaml
        echo "Created config.yaml from example template"
        echo ""
        echo "⚠️  IMPORTANT: You need to edit config.yaml with your API keys!"
        echo "   Run: nano config.yaml"
        echo "   Update:"
        echo "   - alpaca_api_key"
        echo "   - alpaca_secret_key"
        echo "   - discord_webhook_url (optional)"
        echo ""
    else
        echo "ERROR: config.yaml.example not found"
        exit 1
    fi
else
    echo "Step 6: config.yaml already exists, skipping..."
fi

# Setup ngrok
echo ""
read -p "Do you have an ngrok auth token? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your ngrok auth token: " NGROK_TOKEN
    python3 -c "from pyngrok import ngrok; ngrok.set_auth_token('$NGROK_TOKEN')"
    echo "✓ Ngrok authentication configured"
else
    echo "⚠️  Skipping ngrok setup. Dashboard will only be accessible locally."
    echo "   To enable public access later, get a token from: https://dashboard.ngrok.com"
    echo "   Then run: python3 -c \"from pyngrok import ngrok; ngrok.set_auth_token('YOUR_TOKEN')\""
fi

# Setup systemd service
echo ""
echo "Step 7: Setting up systemd service for auto-start..."

# Update service file with correct paths
CURRENT_USER=$(whoami)
WORKING_DIR=$(pwd)
sudo sed -i "s|User=pi|User=$CURRENT_USER|g" scalp-bot.service
sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$WORKING_DIR|g" scalp-bot.service
sudo sed -i "s|ExecStart=.*|ExecStart=$WORKING_DIR/venv/bin/python3 $WORKING_DIR/main.py|g" scalp-bot.service

# Copy service file
sudo cp scalp-bot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "Configuration file: $WORKING_DIR/config.yaml"
echo ""
echo "Available Commands:"
echo "  Start bot:        sudo systemctl start scalp-bot"
echo "  Stop bot:         sudo systemctl stop scalp-bot"
echo "  Restart bot:      sudo systemctl restart scalp-bot"
echo "  View logs:        sudo journalctl -u scalp-bot -f"
echo "  Enable auto-start: sudo systemctl enable scalp-bot"
echo ""
echo "Before starting the bot:"
echo "  1. Edit config.yaml with your API keys: nano config.yaml"
echo "  2. Test the bot manually first: venv/bin/python3 main.py"
echo "  3. Then enable systemd service: sudo systemctl enable scalp-bot"
echo "  4. Start the service: sudo systemctl start scalp-bot"
echo ""
echo "Dashboard will be available at:"
echo "  Local: http://$(hostname -I | awk '{print $1}'):8001"
echo "  Public: (check Discord or logs for ngrok URL)"
echo ""
