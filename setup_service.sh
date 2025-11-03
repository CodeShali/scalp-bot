#!/bin/bash
# Setup systemd service for scalp-bot
# This script automatically detects the correct path

set -e

echo "=========================================="
echo "Setting up scalp-bot systemd service"
echo "=========================================="
echo ""

# Get the current directory (where the bot is)
BOT_DIR=$(pwd)
echo "Bot directory: $BOT_DIR"

# Get current user
CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"

# Create temporary service file with correct paths
echo ""
echo "Creating service file with correct paths..."
cat > /tmp/scalp-bot.service << EOF
[Unit]
Description=TARA Options Scalping Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$BOT_DIR

# Environment
Environment="PATH=$BOT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HOME=$HOME"

# Run main.py
ExecStart=$BOT_DIR/venv/bin/python3 $BOT_DIR/main.py

# Restart on failure
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=scalp-bot

# Resource limits
LimitNOFILE=65536
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
EOF

# Show the service file
echo ""
echo "Service file contents:"
echo "----------------------------------------"
cat /tmp/scalp-bot.service
echo "----------------------------------------"
echo ""

# Ask for confirmation
read -p "Does this look correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Stop existing service if running
echo ""
echo "Stopping existing service (if running)..."
sudo systemctl stop scalp-bot 2>/dev/null || true

# Copy service file
echo "Installing service file..."
sudo cp /tmp/scalp-bot.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service (start on boot)..."
sudo systemctl enable scalp-bot

# Start service
echo "Starting service..."
sudo systemctl start scalp-bot

# Wait a moment
sleep 2

# Show status
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
sudo systemctl status scalp-bot --no-pager -l || true

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  sudo systemctl status scalp-bot    # Check status"
echo "  sudo systemctl restart scalp-bot   # Restart"
echo "  sudo systemctl stop scalp-bot      # Stop"
echo "  sudo journalctl -u scalp-bot -f    # View logs"
echo ""
