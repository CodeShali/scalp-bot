# 📰 News Sentiment Feature Setup

## What It Does

Displays news sentiment analysis for all watchlist tickers in the dashboard:
- **Sentiment**: Bullish/Bearish/Neutral
- **Reasoning**: 1-2 sentence explanation based on recent news
- **Updates**: On bot startup + every hour

## How It Works

1. **OpenAI analyzes** market sentiment for each ticker (AAPL, MSFT, etc.)
2. **No external news API** needed - OpenAI has current market knowledge
3. **Displays in UI** - News & Sentiment panel on dashboard
4. **Auto-updates** - Runs immediately on startup, then hourly

## Setup Instructions

### 1. Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. Add to Config

Edit `~/scalp-bot/config.yaml`:

```yaml
# OpenAI API Configuration (for news analysis)
openai:
  api_key: "sk-your-actual-key-here"
```

### 3. Deploy

```bash
cd ~/scalp-bot
git pull origin main
sudo systemctl restart scalp-bot
```

### 4. Verify

```bash
# Check logs
sudo journalctl -u scalp-bot -f

# You should see:
# "📰 Running initial news sentiment analysis..."
# "✅ News sentiment updated: 10 tickers analyzed"
```

### 5. View in Dashboard

Open: http://192.168.1.14:8001

You'll see the **News & Sentiment** panel with:
- Each ticker's sentiment (color-coded)
- Reasoning for the sentiment
- Last updated timestamp

## API Endpoint

Test the API directly:

```bash
curl http://192.168.1.14:8001/api/news | python3 -m json.tool
```

Response:
```json
{
  "configured": true,
  "news": [
    {
      "symbol": "AAPL",
      "sentiment": "bullish",
      "reasoning": "Strong iPhone 15 sales and AI integration driving momentum",
      "timestamp": "2025-11-06T19:00:00Z"
    },
    {
      "symbol": "MSFT",
      "sentiment": "bullish",
      "reasoning": "Azure growth and AI Copilot adoption exceeding expectations",
      "timestamp": "2025-11-06T19:00:00Z"
    }
  ],
  "last_updated": "2025-11-06T19:00:00Z",
  "count": 10
}
```

## Cost Estimate

- **Model**: gpt-4o-mini (cheapest, fastest)
- **Usage**: 10 tickers × ~150 tokens each = ~1,500 tokens per update
- **Frequency**: Startup + hourly = ~25 updates/day
- **Daily cost**: ~$0.01 (1 cent per day)
- **Monthly cost**: ~$0.30 (30 cents per month)

Very affordable! 💰

## Troubleshooting

### "OpenAI API key not configured"

Add the key to `config.yaml` as shown above.

### "News sentiment analyzer not configured"

Make sure:
1. OpenAI key is in config.yaml
2. Bot has been restarted
3. Check logs for errors

### No data showing

```bash
# Check if it ran
sudo journalctl -u scalp-bot | grep "news sentiment"

# Force an update
curl http://192.168.1.14:8001/api/news
```

### API errors

Check your OpenAI account:
- Has credits/billing set up
- Key is valid and not expired
- Rate limits not exceeded

## Features

✅ **Automatic**: Runs on startup + hourly  
✅ **Fast**: Uses gpt-4o-mini (sub-second responses)  
✅ **Cheap**: ~$0.30/month  
✅ **Smart**: OpenAI has current market knowledge  
✅ **Visual**: Color-coded sentiment in dashboard  
✅ **Actionable**: Clear reasoning for each sentiment  

## Example Output

```
📰 AAPL - BULLISH
Strong iPhone 15 sales and AI integration driving momentum

📰 TSLA - BEARISH  
Production concerns and increased competition weighing on stock

📰 NVDA - BULLISH
AI chip demand continues to exceed supply, strong guidance
```

Enjoy your AI-powered market insights! 🚀
