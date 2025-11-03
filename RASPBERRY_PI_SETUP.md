# Raspberry Pi 4 Deployment Guide

Complete guide for deploying the Options Scalping Bot on Raspberry Pi 4.

## 🔧 Hardware Requirements

- **Raspberry Pi 4** (2GB RAM minimum, 4GB recommended)
- **microSD card** (16GB minimum, 32GB recommended)
- **Power supply** (official 5V/3A USB-C recommended)
- **Network connection** (Ethernet or WiFi)
- **Optional**: UPS/Battery backup for power protection

## 📦 Step 1: Prepare Raspberry Pi

### Install Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS Lite** (64-bit) to microSD
3. Enable SSH before first boot:
   - Create empty file named `ssh` in boot partition
4. Boot Pi and find IP address:
   ```bash
   # From your computer
   ping raspberrypi.local
   # Or check your router's DHCP table
   ```

### Initial SSH Connection

```bash
ssh pi@<raspberry-pi-ip>
# Default password: raspberry
```

### Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git ntp -y
```

### Configure Timezone

```bash
sudo timedatectl set-timezone America/New_York
sudo systemctl enable ntp
sudo systemctl start ntp

# Verify
timedatectl
```

## 📥 Step 2: Clone and Setup Bot

### Clone Repository

```bash
cd /home/pi
git clone <your-repo-url> scalp-bot
cd scalp-bot
```

### Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

### Configure Bot

```bash
# Copy example config
cp config.yaml.example config.yaml

# Edit with your credentials
nano config.yaml
```

Update these sections:
- Alpaca API keys (paper or live)
- Discord webhook URL
- OpenAI API key (for news sentiment)
- Watchlist symbols
- Trading parameters
- **NEW**: `max_active_tickers: 3` (monitor top 3 tickers)

### Install Dashboard Dependencies

```bash
source venv/bin/activate
pip install Flask==3.0.0
deactivate
```

## 🚀 Step 3: Install as System Services

### Install Bot Service

```bash
# Copy service file
sudo cp scalp-bot.service /etc/systemd/system/

# Edit paths if needed (default uses /home/pi/scalp-bot)
sudo nano /etc/systemd/system/scalp-bot.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable scalp-bot
sudo systemctl start scalp-bot

# Check status
sudo systemctl status scalp-bot
```

**Note:** Dashboard is now integrated into main.py - no separate service needed!

## 🌐 Step 4: Access Dashboard

### Find Your Pi's IP Address

```bash
hostname -I
# Example output: 192.168.1.100
```

### Access from Any Device

Open web browser on any device on your network:

```
http://192.168.1.100:8001
```

Replace `192.168.1.100` with your Pi's actual IP.

### Bookmark the URL

Save it on your phone/tablet for easy access!

## 📱 Step 5: Mobile Access Setup

### Option 1: Local Network Only

Simply access `http://<pi-ip>:8001` from any device on same WiFi.

### Option 2: Remote Access (Advanced)

**Using Tailscale (Recommended - Free):**

```bash
# Install Tailscale on Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Install Tailscale on your phone
# Access dashboard via Tailscale IP
```

**Using Port Forwarding (Not Recommended):**
- Forward port 8001 on your router
- ⚠️ Security risk - add authentication first!

## 🔍 Monitoring & Maintenance

### Check Bot Status

```bash
# Bot service status (includes dashboard)
sudo systemctl status scalp-bot

# View logs
sudo journalctl -u scalp-bot -f
```

### View Application Logs

```bash
# Real-time bot logs
tail -f /home/pi/scalp-bot/logs/bot.log

# Recent trades
tail -20 /home/pi/scalp-bot/data/trades.csv
```

### Restart Service

```bash
# Restart bot (includes dashboard)
sudo systemctl restart scalp-bot
```

### Stop Service

```bash
# Stop bot (includes dashboard)
sudo systemctl stop scalp-bot
```

## 🔒 Security Best Practices

### Change Default Password

```bash
passwd
# Enter new password
```

### Disable Password SSH (Use Keys)

```bash
# On your computer, generate key
ssh-keygen -t ed25519

# Copy to Pi
ssh-copy-id pi@<raspberry-pi-ip>

# Disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### Setup Firewall

```bash
sudo apt install ufw
sudo ufw allow ssh
sudo ufw allow 8001/tcp  # Dashboard
sudo ufw enable
```

## 📊 Dashboard Features (Updated!)

Your web dashboard now includes:

### Core Features:
- **Bot Status**: Running/stopped indicator with controls
- **Account Balance**: Cash, buying power, portfolio value
- **Performance Stats**: Win rate, average P/L, total P/L
- **Active Tickers**: Top 3 monitored tickers with ranks (🥇🥈🥉)
- **Current Position**: Live P/L for open position
- **Today's Trades**: All trades executed today

### NEW Features:
- 🌈 **Colorful Matrix Background** - Beautiful rainbow falling code
- 🎯 **Multi-Ticker Display** - See all 3 active tickers being monitored
- 💡 **Intelligent Reasoning** - Detailed explanation of why tickers were selected
- 📰 **News Sentiment** - AI-powered news analysis in metrics
- 📊 **Enhanced Logs** - Search, filter by level, pause, download
- ⚙️ **Settings Panel** - Configure bot parameters from UI
- 🤖 **TARA Branding** - New name and professional identity

**Auto-refresh**: Dashboard updates every 5 seconds automatically.

## 🛠️ Troubleshooting

### Bot Won't Start

```bash
# Check logs
sudo journalctl -u scalp-bot -n 50

# Common issues:
# - Missing config.yaml
# - Invalid API keys
# - Permission issues
```

### Dashboard Not Accessible

```bash
# Check if bot is running (includes dashboard)
sudo systemctl status scalp-bot

# Check if port is listening
sudo netstat -tuln | grep 8001

# Check firewall
sudo ufw status
```

### Can't Access from Phone

1. Ensure phone is on same WiFi network
2. Check Pi's IP hasn't changed: `hostname -I`
3. Try pinging Pi from phone's browser
4. Disable any VPN on phone

### High CPU/Memory Usage

```bash
# Check resource usage
htop

# If memory low:
# - Reduce watchlist size in config.yaml
# - Increase poll intervals
# - Consider 4GB Pi model
```

## 📈 Performance Optimization

### Reduce Logging (Save SD Card)

Edit `config.yaml`:
```yaml
logging:
  level: WARNING  # Change from INFO
```

### Log Rotation

```bash
# Install logrotate config
sudo nano /etc/logrotate.d/scalp-bot
```

Add:
```
/home/pi/scalp-bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Monitor Temperature

```bash
# Check CPU temp
vcgencmd measure_temp

# If >70°C, consider:
# - Add heatsink
# - Improve ventilation
# - Reduce watchlist size
```

## 🔄 Updates and Backups

### Update Bot Code (NEW: Automated Script!)

**Quick Update (Recommended):**
```bash
cd /home/pi/scalp-bot
./deploy.sh
```
This script automatically:
- Pulls latest code
- Updates dependencies
- Checks configuration
- Restarts service
- Verifies deployment

**Manual Update:**
```bash
cd /home/pi/scalp-bot
git pull origin main
pip3 install -r requirements.txt --upgrade
sudo systemctl restart scalp-bot
```

**Force Update (if conflicts):**
```bash
cd /home/pi/scalp-bot
git fetch origin
git reset --hard origin/main
./deploy.sh
```

### Backup Configuration

```bash
# Backup important files
cp config.yaml config.yaml.backup
cp -r data data.backup
cp -r logs logs.backup

# Or create full backup
tar -czf scalp-bot-backup-$(date +%Y%m%d).tar.gz config.yaml data/ logs/
```

### Restore from Backup

```bash
tar -xzf scalp-bot-backup-YYYYMMDD.tar.gz
sudo systemctl restart scalp-bot
```

## 📞 Support Commands

```bash
# Get Pi info
cat /proc/cpuinfo | grep "Model"
free -h
df -h

# Network info
ifconfig
ping -c 4 google.com

# Service status
systemctl status scalp-bot
```

## ✅ Quick Verification Checklist

After setup, verify:

- [ ] Bot service is running: `sudo systemctl status scalp-bot`
- [ ] Dashboard is integrated and running (check logs)
- [ ] Can access dashboard in browser: `http://<pi-ip>:8001`
- [ ] Dashboard shows "Running" status
- [ ] Account balance displays correctly
- [ ] Logs are updating
- [ ] Timezone is US/Eastern: `timedatectl`
- [ ] Bot will auto-start on reboot: `sudo systemctl is-enabled scalp-bot`
- [ ] Discord notification received

## 🎉 You're All Set!

Your bot is now running 24/7 on your Raspberry Pi!

- Monitor anytime via web dashboard
- Receive Discord alerts on your phone
- Bot auto-restarts on failure
- Runs on boot automatically

**First scan**: Monday 8:30 AM ET  
**Trading hours**: 9:30 AM - 4:00 PM ET  
**Your dashboard**: `http://<pi-ip>:8001`

Happy trading! 🚀
