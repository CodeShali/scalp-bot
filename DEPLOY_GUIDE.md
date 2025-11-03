# 🚀 TARA Deployment Guide for Raspberry Pi

## Quick Deploy (One Command)

```bash
cd ~/scalp-bot && ./deploy.sh
```

This script will:
1. ✅ Pull latest changes from GitHub
2. ✅ Update Python dependencies
3. ✅ Check configuration
4. ✅ Restart TARA service
5. ✅ Verify deployment

---

## Manual Deployment Steps

If you prefer to do it manually:

### 1. Pull Latest Changes
```bash
cd ~/scalp-bot
git pull origin main
```

### 2. Update Dependencies
```bash
pip3 install -r requirements.txt --upgrade
```

### 3. Update Configuration

Make sure your `config.yaml` has these new settings:

```yaml
# Add to scanning section
scanning:
  max_active_tickers: 3  # Monitor top 3 tickers

# Add OpenAI section (if not present)
openai:
  api_key: "YOUR_OPENAI_API_KEY"
  model: "gpt-4o-mini"
  max_articles_per_ticker: 10
```

### 4. Restart TARA

**If running as systemd service:**
```bash
sudo systemctl restart scalp-bot
sudo systemctl status scalp-bot
```

**If running manually:**
```bash
pkill -f "python3 main.py"
nohup python3 main.py > logs/tara.log 2>&1 &
```

---

## Verification

### Check if TARA is running:
```bash
ps aux | grep main.py
```

### Check dashboard:
```bash
curl http://localhost:8001
```
Or open in browser: http://YOUR_PI_IP:8001

### View logs:
```bash
tail -f logs/bot.log
```

### Check service status:
```bash
sudo systemctl status scalp-bot
```

---

## Recent Updates

### ✨ New Features:
- 🎯 **Multi-Ticker Monitoring** - Now monitors top 3 tickers simultaneously
- 🌈 **Colorful Matrix Background** - Beautiful rainbow falling characters
- 📊 **Enhanced Logs** - Search, filter, pause, download
- ⚙️ **Settings Panel** - Configure bot from dashboard
- 🤖 **TARA Branding** - New name and identity
- 📰 **News Sentiment** - AI-powered news analysis with OpenAI
- 💡 **Intelligent Reasoning** - See why tickers were selected

### 🔧 Configuration Changes:
- Added `max_active_tickers: 3` to scanning
- Added `openai` section for news sentiment
- Updated weights to include news_sentiment and news_volume

---

## Troubleshooting

### Dashboard not accessible:
```bash
# Check if port 8001 is in use
sudo lsof -i :8001

# Kill and restart
sudo systemctl restart scalp-bot
```

### Service won't start:
```bash
# Check logs
sudo journalctl -u scalp-bot -n 50

# Check for errors
tail -n 50 logs/bot.log
```

### Dependencies issues:
```bash
# Reinstall all dependencies
pip3 install -r requirements.txt --upgrade --force-reinstall
```

### Config issues:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

---

## Useful Commands

```bash
# Start TARA
sudo systemctl start scalp-bot

# Stop TARA
sudo systemctl stop scalp-bot

# Restart TARA
sudo systemctl restart scalp-bot

# View status
sudo systemctl status scalp-bot

# View logs (live)
tail -f logs/bot.log

# View logs (last 100 lines)
tail -n 100 logs/bot.log

# View system logs
sudo journalctl -u scalp-bot -f

# Check Python version
python3 --version

# Check installed packages
pip3 list | grep -E "alpaca|openai|flask"
```

---

## Quick Health Check

Run this to verify everything is working:

```bash
cd ~/scalp-bot
echo "🔍 Checking TARA health..."
echo ""
echo "📦 Git status:"
git status
echo ""
echo "🐍 Python packages:"
pip3 list | grep -E "alpaca|openai|flask|pandas"
echo ""
echo "🤖 TARA process:"
ps aux | grep main.py | grep -v grep
echo ""
echo "🌐 Dashboard:"
curl -s http://localhost:8001 > /dev/null && echo "✅ Dashboard is UP" || echo "❌ Dashboard is DOWN"
echo ""
echo "📝 Recent logs:"
tail -n 5 logs/bot.log
```

---

## Support

- 📖 **Full Setup Guide**: See `RASPBERRY_PI_SETUP.md`
- 🔧 **Quick Reference**: See `QUICK_REFERENCE.md`
- 📊 **Dashboard**: http://localhost:8001
- 💬 **Discord**: Check notifications channel

---

**Happy Trading with TARA! 🤖📈✨**
