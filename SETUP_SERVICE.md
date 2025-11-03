# Setup Bot as Service (Run on Boot)

## Quick Setup

```bash
# 1. Copy service file
sudo cp scalp-bot.service /etc/systemd/system/

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Enable service (start on boot)
sudo systemctl enable scalp-bot

# 4. Start service now
sudo systemctl start scalp-bot

# 5. Check status
sudo systemctl status scalp-bot
```

## Service Commands

```bash
# Start
sudo systemctl start scalp-bot

# Stop
sudo systemctl stop scalp-bot

# Restart
sudo systemctl restart scalp-bot

# Status
sudo systemctl status scalp-bot

# View logs (live)
sudo journalctl -u scalp-bot -f

# View last 50 lines
sudo journalctl -u scalp-bot -n 50

# Disable auto-start on boot
sudo systemctl disable scalp-bot
```

## What Happens on Boot

1. Raspberry Pi boots up
2. Network comes online
3. `scalp-bot` service starts automatically
4. Bot starts ngrok tunnel
5. Bot detects ngrok URL
6. Bot sends Discord notification with dashboard link
7. Bot starts trading operations

## Verify Service is Enabled

```bash
sudo systemctl is-enabled scalp-bot
# Should output: enabled
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u scalp-bot -n 50

# Common issues:
# - Missing config.yaml
# - Wrong paths in service file
# - Virtual environment not activated
```

### Service starts but bot crashes
```bash
# Check bot logs
tail -f /home/pi/scalp-bot/logs/bot.log

# Check if all packages installed
source /home/pi/scalp-bot/venv/bin/activate
pip list
```

### ngrok not starting
```bash
# Make sure ngrok is installed
which ngrok

# Make sure authtoken is configured
ngrok config check
```

## Update After Code Changes

```bash
cd /home/pi/scalp-bot
git pull origin main
sudo systemctl restart scalp-bot
```

That's it! Your bot will now run automatically on every boot! 🚀
