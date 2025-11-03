#!/bin/bash
# Quick script to update the service on Raspberry Pi

echo "Updating scalp-bot service..."

# Stop service
echo "Stopping service..."
sudo systemctl stop scalp-bot

# Copy new service file
echo "Copying new service file..."
sudo cp scalp-bot.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Start service
echo "Starting service..."
sudo systemctl start scalp-bot

# Show status
echo ""
echo "Service status:"
sudo systemctl status scalp-bot --no-pager -l

echo ""
echo "✅ Service updated!"
echo ""
echo "View logs with: sudo journalctl -u scalp-bot -f"
