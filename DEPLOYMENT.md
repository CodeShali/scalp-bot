# Raspberry Pi Deployment Guide

Complete guide for deploying the Scalp Bot to your Raspberry Pi 4.

## 🚀 Quick Deployment (3 Steps)

### Step 1: Deploy from Your Computer

```bash
# Make sure you're in the scalp-bot directory
cd /path/to/scalp-bot

# Deploy to your Pi (replace with your Pi's IP)
./deploy_to_pi.sh pi@192.168.1.100
```

### Step 2: Setup on Raspberry Pi

```bash
# SSH into your Pi
ssh pi@192.168.1.100

# Navigate to the bot directory
cd ~/scalp-bot

# Run the setup script
bash pi_setup.sh
```

### Step 3: Configure and Start

```bash
# Edit configuration with your API keys
nano config.yaml

# Test the bot manually first
venv/bin/python3 main.py

# If it works, enable auto-start
sudo systemctl enable scalp-bot
sudo systemctl start scalp-bot

# Check status
sudo systemctl status scalp-bot
```

## 📋 Prerequisites

### On Your Computer
- Git repository cloned
- SSH access to Raspberry Pi
- rsync installed (usually pre-installed on Mac/Linux)

### On Raspberry Pi
- Raspberry Pi 4 (2GB+ RAM recommended)
- Raspbian/Raspberry Pi OS installed
- Internet connection
- SSH enabled

## 🔑 Configuration

Edit `config.yaml` on your Pi with:

```yaml
# Trading Configuration
mode: "paper"  # or "live" when ready

# Alpaca API Credentials
alpaca:
  api_key: "YOUR_ALPACA_API_KEY"
  secret_key: "YOUR_ALPACA_SECRET_KEY"
  base_url: "https://paper-api.alpaca.markets"  # paper trading

# Discord Notifications (optional)
notifications:
  discord_webhook_url: "YOUR_DISCORD_WEBHOOK_URL"
```

## 🌐 Ngrok Setup (Public Dashboard Access)

1. Sign up at https://dashboard.ngrok.com/signup (free)
2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Run on Pi:
   ```bash
   python3 -c "from pyngrok import ngrok; ngrok.set_auth_token('YOUR_TOKEN')"
   ```

## 🎛️ Systemd Service Commands

```bash
# Start the bot
sudo systemctl start scalp-bot

# Stop the bot
sudo systemctl stop scalp-bot

# Restart the bot
sudo systemctl restart scalp-bot

# Enable auto-start on boot
sudo systemctl enable scalp-bot

# Disable auto-start
sudo systemctl disable scalp-bot

# Check status
sudo systemctl status scalp-bot

# View live logs
sudo journalctl -u scalp-bot -f

# View recent logs
sudo journalctl -u scalp-bot -n 100
```

## 🔍 Troubleshooting

### Bot won't start
```bash
# Check logs for errors
sudo journalctl -u scalp-bot -n 50

# Test manually
cd ~/scalp-bot
source venv/bin/activate
python3 main.py
```

### Dashboard not accessible
```bash
# Check if bot is running
sudo systemctl status scalp-bot

# Check logs for dashboard URL
sudo journalctl -u scalp-bot | grep "Dashboard"

# Check local access
curl http://localhost:8001
```

### API Connection Issues
```bash
# Verify config.yaml has correct keys
cat config.yaml

# Test internet connection
ping api.alpaca.markets
```

## 📊 Accessing the Dashboard

### Local Network
- From any device on same network
- URL: `http://<pi-ip-address>:8001`
- Example: `http://192.168.1.100:8001`

### From Anywhere (with Ngrok)
- Public URL sent to Discord on startup
- Check logs: `sudo journalctl -u scalp-bot | grep "Public URL"`
- URL format: `https://xxxx-xx-xx.ngrok-free.app`

## 🔄 Updating the Bot

```bash
# On your computer
cd /path/to/scalp-bot
git pull  # if using git
./deploy_to_pi.sh pi@192.168.1.100

# On Raspberry Pi
cd ~/scalp-bot
sudo systemctl restart scalp-bot
```

## 📁 Directory Structure on Pi

```
~/scalp-bot/
├── main.py              # Main bot script
├── config.yaml          # Your configuration
├── requirements.txt     # Python dependencies
├── venv/               # Virtual environment
├── data/               # Trade data and state
├── logs/               # Log files
├── templates/          # Dashboard HTML
└── static/             # Dashboard CSS/JS
```

## 💾 Resource Usage

Typical usage on Raspberry Pi 4:
- **CPU:** 5-15% (peaks during market hours)
- **RAM:** 150-250 MB
- **Disk:** ~100 MB (plus logs/data)
- **Network:** Minimal (API calls only)

## 🛡️ Security Notes

1. **Keep config.yaml secure** - Contains API keys
2. **Use strong Pi password** - Change default if using 'pi' user
3. **Firewall** - Consider restricting port 8001 to local network
4. **Ngrok URLs** - Don't share publicly, they give dashboard access
5. **Monitor logs** - Check regularly for suspicious activity

## 📞 Support

If you encounter issues:
1. Check logs: `sudo journalctl -u scalp-bot -f`
2. Test manually: `venv/bin/python3 main.py`
3. Verify config: `cat config.yaml`
4. Check Discord for notifications
