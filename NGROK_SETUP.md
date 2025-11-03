# ngrok Service Setup Guide

This guide shows how to run ngrok as a systemd service that starts on boot.

## Benefits

- ✅ ngrok starts automatically on boot
- ✅ ngrok runs independently of bot
- ✅ No ERR_NGROK_108 errors
- ✅ Bot just detects and uses existing tunnel
- ✅ Easier to manage and troubleshoot

## Setup Instructions

### 1. Copy ngrok service file

```bash
sudo cp ngrok.service /etc/systemd/system/
```

### 2. Reload systemd

```bash
sudo systemctl daemon-reload
```

### 3. Enable ngrok service (start on boot)

```bash
sudo systemctl enable ngrok
```

### 4. Start ngrok service now

```bash
sudo systemctl start ngrok
```

### 5. Check ngrok status

```bash
sudo systemctl status ngrok
```

You should see:
```
● ngrok.service - ngrok tunnel service
   Loaded: loaded (/etc/systemd/system/ngrok.service; enabled)
   Active: active (running)
```

### 6. Get ngrok URL

```bash
curl http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

Or visit: http://localhost:4040/status

## Managing ngrok Service

### Start
```bash
sudo systemctl start ngrok
```

### Stop
```bash
sudo systemctl stop ngrok
```

### Restart
```bash
sudo systemctl restart ngrok
```

### View logs
```bash
sudo journalctl -u ngrok -f
```

### Disable auto-start
```bash
sudo systemctl disable ngrok
```

## Bot Integration

The bot will automatically:
1. Check if ngrok is running (localhost:4040)
2. Get the public URL from ngrok API
3. Use it in Discord notifications
4. Fall back to localhost if ngrok not running

## Troubleshooting

### ERR_NGROK_108 (Session limit exceeded)

If you see this error:
```bash
# Stop ngrok service
sudo systemctl stop ngrok

# Wait a few seconds
sleep 5

# Start again
sudo systemctl start ngrok
```

### ngrok not starting

Check logs:
```bash
sudo journalctl -u ngrok -n 50
```

Common issues:
- ngrok not installed: `sudo apt install ngrok` or download from https://ngrok.com/download
- Wrong path in service file: Update `ExecStart` path
- Port 8001 already in use: Change port in ngrok.service

### Check if ngrok is accessible

```bash
curl http://localhost:4040/api/tunnels
```

Should return JSON with tunnel info.

## Complete Setup (Fresh Install)

```bash
# 1. Install ngrok (if not installed)
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok

# 2. Configure ngrok with your authtoken
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE

# 3. Setup ngrok service
cd scalp-bot
sudo cp ngrok.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ngrok
sudo systemctl start ngrok

# 4. Setup bot service
sudo cp scalp-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scalp-bot
sudo systemctl start scalp-bot

# 5. Check both services
sudo systemctl status ngrok
sudo systemctl status scalp-bot
```

## Service Start Order

1. **Boot** → Network ready
2. **ngrok service** starts → Creates tunnel
3. **scalp-bot service** starts → Detects ngrok URL
4. **Discord notification** sent with public URL

Both services run independently and restart automatically if they crash.
