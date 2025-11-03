#!/bin/bash
#
# Deployment script for Raspberry Pi
# Usage: ./deploy_to_pi.sh pi@192.168.1.100
#

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 pi@<raspberry-pi-ip>"
    echo "Example: $0 pi@192.168.1.100"
    exit 1
fi

PI_HOST="$1"
REMOTE_DIR="~/scalp-bot"

echo "========================================"
echo "Deploying Scalp Bot to Raspberry Pi"
echo "========================================"
echo "Target: $PI_HOST"
echo "Remote Directory: $REMOTE_DIR"
echo ""

# Check if we can connect
echo "Testing connection..."
ssh "$PI_HOST" "echo 'Connection successful'" || {
    echo "ERROR: Cannot connect to $PI_HOST"
    echo "Make sure SSH is enabled on your Pi and you can connect without password (use ssh-copy-id)"
    exit 1
}

# Create remote directory
echo "Creating remote directory..."
ssh "$PI_HOST" "mkdir -p $REMOTE_DIR"

# Sync files (excluding venv, logs, data, cache)
echo "Syncing files..."
rsync -av --delete \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude 'logs/' \
    --exclude 'data/state.json' \
    --exclude 'data/trades.csv' \
    --exclude 'config.yaml' \
    --exclude '.pytest_cache/' \
    --exclude 'tests/' \
    ./ "$PI_HOST:$REMOTE_DIR/"

echo ""
echo "Files synced successfully!"
echo ""
echo "Next steps on your Raspberry Pi:"
echo "1. SSH into Pi: ssh $PI_HOST"
echo "2. Navigate to directory: cd $REMOTE_DIR"
echo "3. Run setup script: bash pi_setup.sh"
echo ""
echo "The setup script will:"
echo "  - Install Python dependencies"
echo "  - Set up ngrok authentication"
echo "  - Configure config.yaml with your API keys"
echo "  - Set up systemd service for auto-start"
echo ""
