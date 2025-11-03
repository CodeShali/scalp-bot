#!/bin/bash
# Setup script for Options Scalping Bot

set -e

echo "======================================"
echo "Options Scalping Bot - Setup"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create required directories
echo "Creating directories..."
mkdir -p data logs

# Check if config.yaml exists
if [ ! -f config.yaml ]; then
    echo "WARNING: config.yaml not found!"
    echo "Please copy config.yaml.example to config.yaml and fill in your credentials."
    exit 1
fi

# Validate config
echo "Validating configuration..."
python3 -c "
from utils import load_config
try:
    config = load_config()
    print('✓ Configuration loaded successfully')
    
    # Check for placeholder values
    alpaca = config.get('alpaca', {})
    mode = config.get('mode', 'paper')
    mode_cfg = alpaca.get(mode, {})
    
    if 'YOUR_' in mode_cfg.get('api_key_id', ''):
        print('ERROR: Please replace placeholder API keys in config.yaml')
        exit(1)
    
    discord_url = config.get('notifications', {}).get('discord_webhook_url', '')
    if 'your_webhook' in discord_url.lower():
        print('WARNING: Discord webhook not configured')
    
    print('✓ Configuration validated')
except Exception as e:
    print(f'ERROR: Configuration validation failed: {e}')
    exit(1)
"

echo ""
echo "======================================"
echo "Setup completed successfully!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review config.yaml and ensure all credentials are set"
echo "2. Run tests: pytest"
echo "3. Start the bot: python main.py"
echo ""
echo "For production deployment on Raspberry Pi:"
echo "1. Copy scalp-bot.service to /etc/systemd/system/"
echo "2. sudo systemctl daemon-reload"
echo "3. sudo systemctl enable scalp-bot"
echo "4. sudo systemctl start scalp-bot"
echo ""
