# Quick Reference Guide

## Daily Operations

### Start Bot
```bash
python main.py
# Or with systemd:
sudo systemctl start scalp-bot
```

### Check Status
```bash
sudo systemctl status scalp-bot
tail -f logs/bot.log
```

### Stop Bot
```bash
# Graceful shutdown
sudo systemctl stop scalp-bot
# Or Ctrl+C if running manually
```

### View Today's Trades
```bash
tail -20 data/trades.csv
```

## Common Commands

### Check Account Balance
```python
from broker import BrokerClient
from utils import load_config

config = load_config()
broker = BrokerClient(config)
balance = broker.get_cash_balance()
print(f"Cash: ${balance:.2f}")
```

### Check Open Positions
```python
from utils import read_state

state = read_state()
position = state.get('open_position')
if position:
    print(f"Open: {position['option_symbol']}")
    print(f"Entry: ${position['entry_price']}")
else:
    print("No open positions")
```

### Force Exit Position
```python
from broker import BrokerClient
from utils import load_config, read_state

config = load_config()
broker = BrokerClient(config)
state = read_state()

position = state.get('open_position')
if position:
    broker.close_position(position['option_symbol'])
    print("Position closed")
```

### Check Market Status
```python
from broker import BrokerClient
from utils import load_config

config = load_config()
broker = BrokerClient(config)
is_open = broker.is_market_open()
print(f"Market open: {is_open}")
```

## Configuration Quick Edits

### Change Risk Per Trade
```bash
# Edit config.yaml
trading:
  max_risk_pct: 0.02  # Change to 2%
```

### Modify Trading Windows
```bash
signals:
  trading_windows:
    - "09:30-10:00"  # First 30 min only
    - "15:30-16:00"  # Last 30 min only
```

### Adjust Profit Target / Stop Loss
```bash
trading:
  profit_target_pct: 0.20  # 20% target
  stop_loss_pct: 0.10      # 10% stop
```

## Log Analysis

### Show Last 50 Lines
```bash
tail -50 logs/bot.log
```

### Search for Errors
```bash
grep "ERROR" logs/bot.log
grep "exception" logs/bot.log -i
```

### Show Signal Detections
```bash
grep "Signal detected" logs/bot.log
```

### Show Trade Fills
```bash
grep "Order filled" logs/bot.log
```

### Calculate Win Rate
```python
import pandas as pd

df = pd.read_csv('data/trades.csv')
wins = len(df[df['pnl_pct'] > 0])
total = len(df)
win_rate = wins / total * 100 if total > 0 else 0
print(f"Win rate: {win_rate:.1f}% ({wins}/{total})")
```

### Calculate Average P/L
```python
import pandas as pd

df = pd.read_csv('data/trades.csv')
avg_pnl = df['pnl_pct'].mean()
print(f"Average P/L: {avg_pnl:.2f}%")
```

## Troubleshooting Quick Fixes

### Reset State File
```bash
rm data/state.json
# Bot will create fresh state on next run
```

### Clear Old Logs
```bash
rm logs/bot.log.*
# Keep only current log
```

### Restart After Config Change
```bash
sudo systemctl restart scalp-bot
# Or Ctrl+C and restart if running manually
```

### Check for API Key Issues
```bash
python -c "
from broker import BrokerClient
from utils import load_config
try:
    config = load_config()
    broker = BrokerClient(config)
    broker.get_account()
    print('✓ API keys valid')
except Exception as e:
    print(f'✗ API error: {e}')
"
```

### Test Discord Webhook
```bash
python -c "
from notifications import DiscordNotifier
from utils import load_config

config = load_config()
webhook_url = config.get('notifications', {}).get('discord_webhook_url')
notifier = DiscordNotifier(webhook_url)
notifier.send('Test message from bot')
print('Message sent')
"
```

## Performance Monitoring

### Today's P/L
```bash
python -c "
import pandas as pd
from datetime import datetime

df = pd.read_csv('data/trades.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
today = datetime.now().date()
today_trades = df[df['timestamp'].dt.date == today]

if len(today_trades) > 0:
    total_pnl = today_trades['pnl_pct'].sum()
    print(f'Today: {total_pnl:.2f}% ({len(today_trades)} trades)')
else:
    print('No trades today')
"
```

### Weekly Summary
```bash
python -c "
import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv('data/trades.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
week_ago = datetime.now() - timedelta(days=7)
week_trades = df[df['timestamp'] > week_ago]

if len(week_trades) > 0:
    total = week_trades['pnl_pct'].sum()
    wins = len(week_trades[week_trades['pnl_pct'] > 0])
    rate = wins / len(week_trades) * 100
    print(f'Week: {total:.2f}% ({wins}/{len(week_trades)} wins, {rate:.1f}% rate)')
else:
    print('No trades this week')
"
```

## Emergency Procedures

### Immediate Shutdown
```bash
sudo systemctl stop scalp-bot
# Verify stopped
sudo systemctl status scalp-bot
```

### Close All Positions Manually
```bash
python -c "
from broker import BrokerClient
from utils import load_config

config = load_config()
broker = BrokerClient(config)
positions = broker.list_positions()

for pos in positions:
    symbol = pos['symbol']
    broker.close_position(symbol)
    print(f'Closed {symbol}')
"
```

### Disable Auto-Restart
```bash
sudo systemctl disable scalp-bot
```

### Enable Auto-Restart
```bash
sudo systemctl enable scalp-bot
```

## Systemd Service Commands

```bash
# View service status
sudo systemctl status scalp-bot

# Start service
sudo systemctl start scalp-bot

# Stop service
sudo systemctl stop scalp-bot

# Restart service
sudo systemctl restart scalp-bot

# Enable auto-start on boot
sudo systemctl enable scalp-bot

# Disable auto-start
sudo systemctl disable scalp-bot

# View service logs
sudo journalctl -u scalp-bot -f

# View last 100 lines
sudo journalctl -u scalp-bot -n 100

# View logs since today
sudo journalctl -u scalp-bot --since today
```

## Testing Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_broker.py

# Run with coverage
pytest --cov=.

# Run only fast tests (skip slow/integration)
pytest -m "not slow"
```
