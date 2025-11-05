# Deploy Critical Fixes - November 4, 2025

## Issues Fixed

### ✅ 1. Timezone Issue - Scan Running at Wrong Time
**Before:** Scan ran at 8:30 AM EST (7:30 AM CST)  
**After:** Scan runs at 9:30 AM EST (8:30 AM CST) - market open

### ✅ 2. Scoring Weights Showing Zero
**Before:** All scores showed 0.0, no visibility into calculations  
**After:** Detailed logging shows each metric value and contribution

### ✅ 3. Options Data Format Errors
**Before:** Format errors when fetching options from Alpaca  
**After:** Robust date handling and error recovery

---

## Deployment Steps

### 1. Update Code on Raspberry Pi

```bash
ssh pi@<your-pi-ip>
cd /path/to/scalp-bot
git pull origin main
```

### 2. Update Your config.yaml

**IMPORTANT:** Add these new settings to your `config.yaml`:

```yaml
scanning:
  run_time: "09:30"  # Changed from 08:30 to 09:30 ET (market open)
  timezone: "US/Eastern"  # Add this line
  max_active_tickers: 3
  weights:
    premarket_volume: 0.25
    gap_percent: 0.20
    iv_rank: 0.15
    option_open_interest: 0.10
    atr: 0.10
    news_sentiment: 0.15
    news_volume: 0.05
```

**Key Changes:**
- `run_time`: Changed to `"09:30"` (market open in ET)
- `timezone`: Added `"US/Eastern"` (new field)

### 3. Enable Debug Logging (Temporary)

To see detailed scoring information, temporarily set logging to DEBUG:

```yaml
logging:
  level: DEBUG  # Change from INFO to DEBUG
  file: logs/bot.log
```

### 4. Restart the Bot

```bash
# If running as service:
sudo systemctl restart scalp-bot
sudo journalctl -u scalp-bot -f

# If running manually:
python3 main.py
```

---

## What to Look For in Logs

### Timezone Fix Verification

Look for this in logs at startup:
```
Next scan: Today at 09:30 ET
```

Or check the scheduler:
```
Pre-market scan scheduled for 09:30 ET
```

### Scoring Fix Verification

When scan runs, you should see:
```
Starting pre-market scan for symbols: ['AAPL', 'MSFT', ...]
Scoring weights: {'premarket_volume': 0.25, 'gap_percent': 0.2, ...} (sum=1.00)

AAPL - Score: 45.23 | Metrics: {'premarket_volume': 75.50, 'gap_percent': 12.30, ...}
MSFT - Score: 38.15 | Metrics: {'premarket_volume': 62.00, 'gap_percent': 8.50, ...}
```

**What to check:**
- ✅ Weights sum should be close to 1.00
- ✅ Scores should be non-zero (unless truly no activity)
- ✅ Each metric should have a value
- ✅ Score calculation shows contributions

### Options Data Fix Verification

Look for successful options fetches:
```
Fetching options for AAPL with request: ...
Found 150 option contracts for AAPL
```

**No more errors like:**
- ❌ "format error"
- ❌ "invalid date format"
- ❌ "attribute error"

---

## Testing Checklist

### Before Next Market Open (Tomorrow):

- [ ] Update config.yaml with new settings
- [ ] Set logging to DEBUG temporarily
- [ ] Restart bot
- [ ] Verify scan time shows 09:30 ET in logs
- [ ] Check bot is running: `sudo systemctl status scalp-bot`

### During Next Scan (9:30 AM EST):

- [ ] Watch logs: `sudo journalctl -u scalp-bot -f`
- [ ] Verify weights are logged with sum=1.00
- [ ] Verify each ticker shows non-zero score
- [ ] Verify metrics are populated (not all zeros)
- [ ] Verify options data fetches successfully
- [ ] Check Discord notification has proper reasoning

### After Scan:

- [ ] Review logs for any errors
- [ ] Verify top 3 tickers were selected
- [ ] Check reasoning in Discord makes sense
- [ ] Verify scores match metric values
- [ ] Set logging back to INFO if desired

---

## Troubleshooting

### If Scores Still Show Zero:

1. Check weights in config.yaml:
   ```bash
   grep -A 10 "weights:" config.yaml
   ```
   
2. Verify weights sum to ~1.0:
   ```
   0.25 + 0.20 + 0.15 + 0.10 + 0.10 + 0.15 + 0.05 = 1.00 ✅
   ```

3. Check if metrics are being calculated:
   ```bash
   grep "Metrics:" logs/bot.log
   ```

4. Look for errors in metric calculation:
   ```bash
   grep -i "error\|failed" logs/bot.log
   ```

### If Options Data Still Fails:

1. Check Alpaca API status:
   ```bash
   curl https://status.alpaca.markets/
   ```

2. Verify API keys are correct in config.yaml

3. Check logs for specific error:
   ```bash
   grep "option" logs/bot.log | grep -i error
   ```

4. Try manual test:
   ```python
   from broker import BrokerClient
   from utils import load_config
   
   config = load_config()
   broker = BrokerClient(config)
   chain = broker.get_option_chain("SPY")
   print(f"Found {len(chain)} contracts")
   ```

### If Scan Runs at Wrong Time:

1. Check system timezone:
   ```bash
   timedatectl
   ```

2. Verify config.yaml has correct run_time:
   ```bash
   grep "run_time" config.yaml
   ```

3. Check scheduler in logs:
   ```bash
   grep "CronTrigger" logs/bot.log
   ```

---

## Reverting Changes (If Needed)

If something breaks:

```bash
cd /path/to/scalp-bot
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>
sudo systemctl restart scalp-bot
```

---

## Support

If issues persist after deployment:

1. **Collect logs:**
   ```bash
   tail -100 logs/bot.log > debug.log
   sudo journalctl -u scalp-bot -n 100 >> debug.log
   ```

2. **Check config:**
   ```bash
   cat config.yaml > config_sanitized.yaml
   # Remove API keys before sharing
   ```

3. **System info:**
   ```bash
   python3 --version
   pip list | grep alpaca
   ```

---

## Expected Behavior After Fixes

### Tomorrow Morning (9:30 AM EST):

1. **9:30 AM EST** - Pre-market scan runs
2. Logs show weights and metrics for each ticker
3. Top 3 tickers selected based on scores
4. Discord notification sent with:
   - ✅ Non-zero scores
   - ✅ Proper reasoning based on metrics
   - ✅ Correct weight contributions
5. Options data fetched successfully
6. Bot starts monitoring selected tickers

### Throughout the Day:

- Bot monitors top 3 tickers
- Signals detected based on technical indicators
- Trades executed when conditions met
- All data logged properly

---

## Questions?

Check logs first:
```bash
# Live logs
sudo journalctl -u scalp-bot -f

# Recent errors
grep -i error logs/bot.log | tail -20

# Scan results
grep "Score:" logs/bot.log
```

Everything should work correctly now! 🚀
