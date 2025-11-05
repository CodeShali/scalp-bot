# Automated Options Scalping Bot

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready automated options scalping bot powered by Alpaca's API. The bot performs pre-market scanning, real-time signal detection using EMA/RSI indicators, and enforces strict risk management with profit targets, stop-losses, and time-based exits.

## ✨ Features

- **Pre-Market Scanning**: Evaluates watchlist using weighted metrics (volume, gap %, IV rank, OI, ATR)
- **Technical Analysis**: EMA crossover detection with RSI confirmation and volume filters
- **Smart Position Sizing**: Risk-based allocation (configurable % of capital per trade)
- **Exit Management**: Multiple exit triggers (profit target, stop loss, EMA reversal, timeout, EOD)
- **Discord Notifications**: Real-time alerts for all trading events
- **Web Dashboard**: Beautiful real-time web interface for monitoring from any device
- **Circuit Breaker**: Automatic pause on repeated errors for safety
- **Health Monitoring**: Built-in health checks and error tracking
- **0DTE/1DTE Focus**: Targets same-day or next-day expiration options
- **Production Ready**: Systemd service, logging, state persistence, comprehensive tests

## 📋 Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🔧 Requirements

### Software
- Python 3.9 or higher
- pip (Python package manager)
- Git

### API Access
- **Alpaca Trading Account** (paper or live)
  - Paper trading: Free with IEX data feed
  - Live trading: Requires AlgoTrader Plus subscription ($99/month) for SIP data feed
- **Discord Webhook** (optional, for notifications)

### Hardware
- Raspberry Pi 4 (2GB+ RAM) or any Linux/macOS machine
- Stable internet connection
- Recommended: UPS for power backup

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd scalp-bot
```

### 2. Run Setup

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Configure

```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys and preferences
```

### 4. Run Tests

```bash
source venv/bin/activate
pytest
```

### 5. Start Bot

```bash
python main.py
```

## ⚙️ Configuration

### API Keys

Obtain your Alpaca API keys:
1. Sign up at [alpaca.markets](https://alpaca.markets)
2. Navigate to Paper Trading or Live Trading dashboard
3. Generate API keys
4. Update `config.yaml`:

```yaml
alpaca:
  paper:
    api_key_id: "YOUR_PAPER_KEY"
    api_secret_key: "YOUR_PAPER_SECRET"
```

### Discord Notifications

1. Create a Discord server (or use existing)
2. Create a channel for bot notifications
3. Get webhook URL: Server Settings → Integrations → Webhooks → New Webhook
4. Update `config.yaml`:

```yaml
notifications:
  discord_webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK"
```

### Trading Parameters

**Risk Management:**
```yaml
trading:
  max_risk_pct: 0.01      # Risk 1% per trade
  profit_target_pct: 0.15  # 15% profit target
  stop_loss_pct: 0.07      # 7% stop loss
```

**Signal Filters:**
```yaml
signals:
  ema_short_period: 9
  ema_long_period: 21
  rsi_call_min: 60        # Bullish above 60
  rsi_put_max: 40         # Bearish below 40
  volume_multiplier: 1.2  # 20% above average
```

**Trading Windows:**
```yaml
signals:
  trading_windows:
    - "09:30-10:30"  # Market open volatility
    - "15:00-16:00"  # Market close volatility
```

## 🏗️ Architecture

### High-Level Flow

```
scalp-bot/
├── config.yaml              # Runtime configuration and API credentials
├── requirements.txt         # Python dependencies
├── main.py                  # Entry point and scheduler orchestration
├── broker.py                # Alpaca API wrapper (orders, positions, data)
├── scan.py                  # Pre-market scanning and scoring logic
├── signals.py               # Indicator calculations and signal validation
├── monitor.py               # Position monitoring and exit enforcement
├── notifications.py         # Discord webhook integration
├── utils.py                 # Shared helpers (config load, time utils, persistence)
└── data/
    └── state.json           # Persistent runtime state (e.g., ticker-of-the-day)
```

### Module Overview

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `main.py` | Orchestrator | Scheduler, job coordination, circuit breaker, health checks |
| `broker.py` | Alpaca API | Market data, orders, positions, account info |
| `scan.py` | Pre-market analysis | Metric calculation, scoring, ticker selection |
| `signals.py` | Technical analysis | EMA/RSI indicators, signal detection, filters |
| `monitor.py` | Exit management | Position tracking, exit rule enforcement |
| `notifications.py` | Alerts | Discord webhook integration |
| `utils.py` | Utilities | Config, logging, state persistence, helpers |

### Execution Flow

```
08:30 ET → Pre-Market Scan
   ↓
   Evaluate watchlist metrics
   ↓
   Select Ticker of the Day
   ↓
   Persist to state.json
   ↓
   Alert via Discord

During Trading Windows (09:30-10:30, 15:00-16:00)
   ↓
   Poll for price data (every 15s)
   ↓
   Calculate EMA/RSI indicators
   ↓
   Check for crossover signal
   ↓
   Validate RSI + volume filters
   ↓
   [Signal Detected]
   ↓
   Select ATM/OTM option contract
   ↓
   Calculate position size (1% risk)
   ↓
   Submit buy order
   ↓
   Wait for fill
   ↓
   Persist position state
   ↓
   Alert via Discord

Position Monitoring (every 5s)
   ↓
   Check profit target (15%)
   Check stop loss (7%)
   Check EMA reversal
   Check timeout (5 min)
   Check EOD (15:55)
   ↓
   [Exit Trigger]
   ↓
   Close position
   ↓
   Log trade to CSV
   ↓
   Alert via Discord
```

### Safety Features

- **Circuit Breaker**: Automatically pauses trading after 5 errors in 5 minutes
- **Health Checks**: Validates broker connectivity and state file access
- **Error Tracking**: Maintains error window for pattern detection
- **Timeout Protection**: Exits stale positions after 5 minutes
- **EOD Exit**: Force-closes positions 5 minutes before market close
- **State Persistence**: Survives restarts without losing position data
- **Comprehensive Logging**: All actions logged with timestamps

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html for coverage report
```

### Run Specific Test Modules

```bash
pytest tests/test_utils.py -v
pytest tests/test_broker.py -v
pytest tests/test_signals.py -v
```

### Test Categories

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test module interactions (mark with `@pytest.mark.integration`)
- **Mocked Tests**: All external API calls are mocked for reliability

## 🚀 Deployment

### Raspberry Pi Setup

#### 1. Prepare System

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv git -y

# Configure NTP for accurate time
sudo timedatectl set-timezone America/New_York
sudo apt install ntp -y
sudo systemctl enable ntp
```

#### 2. Clone and Setup

```bash
cd /home/pi
git clone <your-repo-url> scalp-bot
cd scalp-bot
./setup.sh
```

#### 3. Install as Service

```bash
# Copy service file
sudo cp scalp-bot.service /etc/systemd/system/

# Edit service file if needed (adjust paths/user)
sudo nano /etc/systemd/system/scalp-bot.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable scalp-bot
sudo systemctl start scalp-bot
```

#### 4. Verify Status

```bash
# Check service status
sudo systemctl status scalp-bot

# View logs
sudo journalctl -u scalp-bot -f

# Check bot logs
tail -f logs/bot.log
```

### Production Checklist

- [ ] API keys configured and tested
- [ ] Discord webhook receiving notifications
- [ ] Watchlist contains liquid, high-volume symbols
- [ ] Risk parameters appropriate for account size
- [ ] Time zone configured correctly (US/Eastern)
- [ ] NTP service running for accurate time
- [ ] Systemd service enabled for auto-restart
- [ ] Log rotation configured
- [ ] Backup power (UPS) connected
- [ ] Monitoring/alerting configured

## 📊 Monitoring

### Log Files

- **Application logs**: `logs/bot.log`
- **Trade records**: `data/trades.csv`
- **Runtime state**: `data/state.json`
- **System logs**: `journalctl -u scalp-bot`

### Key Metrics to Monitor

1. **Daily P/L**: Track in `data/trades.csv`
2. **Win Rate**: Number of profitable trades / total trades
3. **Average Return**: Mean P/L percentage
4. **Max Drawdown**: Largest peak-to-trough decline
5. **Error Rate**: Check logs for exceptions
6. **Circuit Breaker**: Monitor for activation events

### Discord Alerts

The bot sends notifications for:
- ✅ Startup confirmation
- 🎯 Ticker of the Day selection
- 📈 Trade signals (call/put)
- 💰 Order fills
- 🚪 Position exits (with P/L and reason)
- ⚠️ Errors and warnings
- 🛑 Circuit breaker activation

### Health Checks

Manual health check:
```python
from main import ScalpingBot
bot = ScalpingBot()
status = bot.health_check()
print(status)
```

## 🔧 Troubleshooting

### Bot Won't Start

**Check logs:**
```bash
sudo journalctl -u scalp-bot -n 50
```

**Common issues:**
- Missing API keys in config.yaml
- Invalid config.yaml syntax
- Permission issues on data/ or logs/ directories
- Python version < 3.9

### No Trades Executing

**Verify:**
1. Market is open: `broker.is_market_open()`
2. Ticker selected: Check `data/state.json`
3. Current time in trading window
4. Sufficient account balance
5. Signal criteria met (check logs for "Signal detected")

### Circuit Breaker Activated

**Steps:**
1. Review logs for root cause: `tail -100 logs/bot.log`
2. Fix underlying issue (API keys, network, etc.)
3. Restart service: `sudo systemctl restart scalp-bot`
4. Monitor for recurrence

### Orders Not Filling

**Check:**
- Option liquidity (low volume options may not fill)
- Bid-ask spread too wide
- Market conditions (halt, circuit breaker)
- Account buying power

### High CPU/Memory Usage

**Optimize:**
- Reduce polling frequency in config
- Decrease watchlist size
- Check for memory leaks in logs
- Monitor with `top` or `htop`

## 📝 File Structure

```
scalp-bot/
├── main.py                 # Bot orchestrator and entry point
├── broker.py               # Alpaca API wrapper
├── scan.py                 # Pre-market scanning logic
├── signals.py              # Technical indicators and signal detection
├── monitor.py              # Position monitoring and exits
├── notifications.py        # Discord integration
├── utils.py                # Shared utilities
├── config.yaml             # Configuration (not in git)
├── config.yaml.example     # Configuration template
├── requirements.txt        # Python dependencies
├── setup.sh                # Setup automation script
├── scalp-bot.service       # Systemd service definition
├── pytest.ini              # Test configuration
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── data/                   # Runtime data (gitignored)
│   ├── state.json          # Persistent bot state
│   └── trades.csv          # Trade history log
├── logs/                   # Application logs (gitignored)
│   └── bot.log            # Rotating log file
└── tests/                  # Unit tests
    ├── test_broker.py
    ├── test_scan.py
    ├── test_signals.py
    ├── test_monitor.py
    ├── test_notifications.py
    └── test_utils.py
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## ⚖️ License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

**This bot is for educational purposes only. Trading options involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk. The authors assume no liability for trading losses.**

## 📚 Resources

- [Alpaca API Documentation](https://alpaca.markets/docs/)
- [Options Trading Basics](https://www.investopedia.com/options-basics-tutorial-4583012)
- [Technical Analysis](https://www.investopedia.com/terms/t/technicalanalysis.asp)
- [Risk Management](https://www.investopedia.com/articles/forex/06/fxrisk.asp)
# Test auto-deploy
# Test 2
# Test 3
