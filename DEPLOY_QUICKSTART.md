# 🚀 Quick Deploy to Raspberry Pi

Ultra-fast deployment guide. Get your bot running on Pi in under 5 minutes!

## ⚡ Super Quick Start

```bash
# 1. Deploy from your computer
./deploy_to_pi.sh pi@192.168.1.100

# 2. SSH to Pi and setup
ssh pi@192.168.1.100
cd ~/scalp-bot
bash pi_setup.sh

# 3. Configure and start
nano config.yaml  # Add your API keys
sudo systemctl enable scalp-bot
sudo systemctl start scalp-bot
```

That's it! Bot is running! 🎉

## 📝 One-Time Setup Checklist

Before first deployment:

- [ ] Raspberry Pi 4 with Raspbian installed
- [ ] SSH enabled on Pi (`sudo raspi-config` → Interface Options → SSH)
- [ ] SSH key copied to Pi: `ssh-copy-id pi@192.168.1.100`
- [ ] Alpaca API keys ready (from alpaca.markets)
- [ ] Ngrok account created (optional, for remote dashboard)
- [ ] Discord webhook URL (optional, for notifications)

## 🔧 Deployment Script Details

### `deploy_to_pi.sh`
**What it does:**
- Syncs all code to your Pi (excludes venv, logs, secrets)
- Uses rsync for efficient updates
- Only transfers changed files

**Usage:**
```bash
./deploy_to_pi.sh pi@<IP_ADDRESS>
./deploy_to_pi.sh pi@raspberrypi.local  # if using hostname
```

### `pi_setup.sh`
**What it does:**
- Installs Python 3 and dependencies
- Creates virtual environment
- Installs all required packages
- Sets up ngrok (if you provide token)
- Configures systemd service
- Creates data/logs directories

**Runs on Pi:**
```bash
bash pi_setup.sh
```

## 📊 Accessing Dashboard

After starting the bot, get URLs from:

```bash
# Check Discord - URL sent automatically
# OR check logs
sudo journalctl -u scalp-bot | grep "Public URL"

# Local access
http://<pi-ip>:8001
```

## 🔄 Quick Update Workflow

When you make code changes:

```bash
# 1. Commit changes (optional)
git add .
git commit -m "Updated feature X"

# 2. Deploy to Pi
./deploy_to_pi.sh pi@192.168.1.100

# 3. Restart on Pi
ssh pi@192.168.1.100 "sudo systemctl restart scalp-bot"
```

## 💡 Pro Tips

1. **Use hostname instead of IP:**
   ```bash
   ./deploy_to_pi.sh pi@raspberrypi.local
   ```

2. **Check bot status quickly:**
   ```bash
   ssh pi@192.168.1.100 "sudo systemctl status scalp-bot"
   ```

3. **Watch logs in real-time:**
   ```bash
   ssh pi@192.168.1.100 "sudo journalctl -u scalp-bot -f"
   ```

4. **Test before deploying:**
   ```bash
   python3 main.py  # Test locally first
   ```

## 🚨 Troubleshooting

**Can't connect to Pi:**
```bash
# Test connection
ping 192.168.1.100
ssh pi@192.168.1.100

# Setup SSH key if needed
ssh-copy-id pi@192.168.1.100
```

**Bot won't start:**
```bash
# SSH to Pi and check logs
ssh pi@192.168.1.100
sudo journalctl -u scalp-bot -n 50
```

**Dashboard not working:**
```bash
# Check if bot is running
sudo systemctl status scalp-bot

# Test locally
curl http://localhost:8001
```

## 📞 Need More Details?

See **DEPLOYMENT.md** for comprehensive guide including:
- Detailed configuration options
- Security best practices
- Performance tuning
- Advanced troubleshooting
