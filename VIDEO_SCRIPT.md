# 🎬 Scalp Bot Explainer Video Script

**Duration:** 10-12 minutes  
**Target Audience:** Traders interested in automated scalping  
**Style:** Professional, educational, with screen recordings

---

## 🎥 Scene 1: Introduction (0:00 - 0:30)

### Visual:
- Animated logo/title card
- Stock charts in background
- Bot dashboard preview

### Narration:
> "Welcome! Today I'm going to show you exactly how my automated scalping bot works. This bot trades options on 10 major stocks, checking for signals every 5 seconds during market hours. By the end of this video, you'll understand every step of the process, from signal detection to trade execution to position management. Let's dive in!"

---

## 🎥 Scene 2: High-Level Overview (0:30 - 1:30)

### Visual:
- Show high-level flowchart
- Animate the main loop
- Highlight key components

### Narration:
> "Here's the big picture. The bot runs continuously from 9:30 AM to 4:00 PM Eastern time. Every 5 seconds, it checks all 10 tickers in parallel for trading signals. When it finds a valid signal, it selects the best option contract, executes the trade, and then monitors the position every 3 seconds until it hits a profit target, stop loss, or timeout. Let's break down each phase in detail."

---

## 🎥 Scene 3: Initialization Phase (1:30 - 2:30)

### Visual:
- Show config.yaml file
- Display watchlist tickers
- Show Discord startup notification
- Highlight scheduler jobs

### Narration:
> "When the bot starts at 9:30 AM, it first loads the configuration file. This includes the watchlist of 10 tickers: Apple, Microsoft, Tesla, NVIDIA, AMD, Google, Amazon, Meta, SPY, and QQQ. It authenticates with the Alpaca API for trading and market data. Then it sends a startup notification to Discord with both the ngrok URL for remote access and the local IP for WiFi access. Finally, it starts three scheduled jobs: signal detection every 5 seconds, position monitoring every 3 seconds, and news updates every hour."

---

## 🎥 Scene 4: Signal Detection - The Filters (2:30 - 4:30)

### Visual:
- Show live chart with EMA lines
- Highlight crossover moment
- Show RSI indicator
- Show volume bars
- Animate filter validation

### Narration:
> "Now let's talk about how the bot finds trading opportunities. Every 5 seconds, it checks all 10 tickers in parallel. For each ticker, it fetches the last 180 minutes of 1-minute bars from Alpaca. Then it calculates three key indicators.
>
> First, the EMA crossover. It uses a 9-period and 21-period exponential moving average. For a CALL signal, the fast EMA must cross above the slow EMA. For a PUT signal, it must cross below. This confirms trend direction.
>
> Second, RSI confirmation. For CALL signals, RSI must be at least 60, indicating bullish momentum. For PUT signals, RSI must be 40 or below, indicating bearish momentum. This filters out weak signals.
>
> Third, volume validation. Current volume must be at least 1.2 times the 20-period average. This ensures there's enough liquidity and interest in the move.
>
> Only when all three filters pass does the bot generate a signal. This triple-filter approach keeps the bot selective and reduces false signals."

---

## 🎥 Scene 5: Option Selection (4:30 - 6:00)

### Visual:
- Show option chain from Alpaca
- Highlight filtering process
- Show selected option details
- Display strike price calculation

### Narration:
> "Once a signal is validated, the bot needs to select the right option contract. Here's how it works.
>
> First, it fetches the complete option chain from Alpaca. This might include hundreds of contracts with different strikes and expirations. The bot filters for the correct type - CALL options for bullish signals, PUT options for bearish signals.
>
> Then it removes any options without valid bid-ask prices. Next comes the key part: it sorts the remaining options by two criteria. First, nearest expiration - typically 0DTE or 1DTE contracts. Second, closest to at-the-money.
>
> The bot selects the first option from this sorted list. For example, if Microsoft is trading at $427.50, it might select the $425 strike expiring today. This gives us the most liquid option with maximum theta decay for scalping.
>
> No complex calculations, no strike penalties - just the nearest ATM option on the next expiring contract. Simple and effective for scalping."

---

## 🎥 Scene 6: Trade Execution (6:00 - 7:00)

### Visual:
- Show quantity calculation
- Display order submission
- Show Alpaca order confirmation
- Display Discord notification

### Narration:
> "With the option selected, the bot calculates how many contracts to buy. It uses a 1% risk rule. If your account has $10,000, it risks $100 per trade. If the option costs $3.45, it buys 29 contracts.
>
> The bot submits a market order to Alpaca and waits for confirmation. If the order fills within the timeout period, great! The position is saved to the state file, and a notification is sent to Discord showing the ticker, direction, number of contracts, and fill price.
>
> If the order doesn't fill within 30 seconds, the bot cancels it and moves on. No hanging orders, no partial fills - clean execution only."

---

## 🎥 Scene 7: Position Monitoring (7:00 - 8:30)

### Visual:
- Show position monitoring loop
- Display P/L calculation
- Highlight exit conditions
- Show real-time price updates

### Narration:
> "Now the bot enters monitoring mode. Every 3 seconds, it checks the current option price and calculates profit and loss percentage. It's watching for five possible exit conditions.
>
> First, profit target. If P/L reaches 15% or higher, the bot immediately closes the position. This locks in profits quickly, which is essential for scalping.
>
> Second, stop loss. If P/L drops to negative 7% or worse, the bot cuts the loss. This protects your capital from large drawdowns.
>
> Third, timeout. If the position has been open for 5 minutes without hitting profit target or stop loss, the bot closes it. Scalping is about quick moves - if it's not working fast, get out.
>
> Fourth, end of day. At 3:55 PM, the bot force-closes any open positions. No overnight risk, no gap risk.
>
> Fifth, signal reversal. If the EMA crosses back the other way, the original signal is invalidated, so the bot exits.
>
> When any exit condition triggers, the bot submits a market sell order, records the trade to a CSV file with all details, sends a Discord notification with the results, and clears the position from state. Now it's ready for the next signal."

---

## 🎥 Scene 8: Safety Features (8:30 - 9:30)

### Visual:
- Show daily limits dashboard
- Display circuit breaker logic
- Highlight safety parameters

### Narration:
> "The bot has multiple safety features to protect your capital.
>
> Daily trade limit: Maximum 5 trades per day. This prevents overtrading and excessive commissions.
>
> Daily loss limit: If daily P/L drops to negative 3%, the bot stops trading for the day. This prevents a bad day from becoming a disaster.
>
> Circuit breaker: If the bot encounters 5 errors in the last 10 attempts, it opens the circuit breaker and pauses all trading. This requires manual reset, ensuring you review what went wrong.
>
> Position limit: Only one position at a time. No portfolio complexity, no correlation risk.
>
> Risk per trade: Fixed at 1% of capital. Even if you lose 10 trades in a row, you're only down 10%.
>
> These safety features work together to keep your account protected while the bot hunts for opportunities."

---

## 🎥 Scene 9: Real Example Walkthrough (9:30 - 11:00)

### Visual:
- Show actual log output
- Display real chart with signal
- Show order execution
- Display position monitoring
- Show exit and P/L

### Narration:
> "Let's walk through a real example from start to finish.
>
> It's 10:15:30 AM. The bot checks all 10 tickers and detects a signal on Microsoft. The price is $427.50. EMA 9 just crossed above EMA 21, confirming a bullish trend. RSI is 65.2, above our 60 threshold. Volume is 2.5 million, which is 1.8 times the average. All three filters pass!
>
> The bot fetches the option chain and gets 847 contracts. After filtering for CALL options with valid prices, 124 remain. It sorts by nearest expiration and closest to ATM. The winner: MSFT November 6th, $425 strike CALL, trading at $3.45.
>
> With $10,000 capital and 1% risk, the bot calculates 29 contracts. It submits the order to Alpaca. Within 2 seconds, the order fills at $3.45. Total cost: $100.05. Position saved, Discord notified, monitoring begins.
>
> At 10:15:33, just 3 seconds later, the option is already at $3.48. P/L: +0.87%. The bot continues monitoring.
>
> At 10:16:00, the option is at $3.62. P/L: +4.93%. Still monitoring.
>
> At 10:18:15, the option hits $3.97. P/L: +15.07%. Profit target hit! The bot immediately submits a sell order. Position closed at $3.97. Profit: $15.08 in just 2 minutes and 45 seconds.
>
> Trade recorded to CSV. Discord notification sent. State cleared. The bot is now ready for the next signal. That's how fast scalping works."

---

## 🎥 Scene 10: Dashboard & Monitoring (11:00 - 11:45)

### Visual:
- Show live dashboard
- Highlight key metrics
- Display trade history
- Show news panel

### Narration:
> "You can monitor everything in real-time through the web dashboard. It shows your account balance, current position if any, today's trades, profit and loss, and daily limits. The dashboard updates every 3 seconds when accessed via local IP, or every 30 seconds via ngrok.
>
> The news panel shows AI-powered sentiment analysis for all watchlist tickers, updated hourly. This gives you context on what's moving the market.
>
> All trades are logged to a CSV file with timestamp, ticker, direction, entry price, exit price, P/L, and duration. Perfect for backtesting and strategy refinement."

---

## 🎥 Scene 11: Conclusion & Call to Action (11:45 - 12:00)

### Visual:
- Show GitHub repository
- Display setup documentation
- Show Discord community link

### Narration:
> "And that's the complete workflow! The bot checks 10 tickers every 5 seconds, validates signals with three filters, selects the best option contract, executes with 1% risk, monitors every 3 seconds, and exits on profit target, stop loss, or timeout. All with built-in safety features to protect your capital.
>
> The code is open source on GitHub. Check the description for links to the repository, setup guide, and Discord community. If you found this helpful, give it a star on GitHub and subscribe for more trading automation content. Thanks for watching!"

---

## 🎬 Production Notes

### Screen Recordings Needed:
1. ✅ Config file walkthrough
2. ✅ Bot startup sequence
3. ✅ Live signal detection (logs)
4. ✅ Option chain selection
5. ✅ Order execution on Alpaca
6. ✅ Position monitoring (real-time)
7. ✅ Trade exit and P/L
8. ✅ Dashboard overview
9. ✅ Discord notifications
10. ✅ Trade history CSV

### Charts/Diagrams to Create:
1. ✅ High-level flowchart
2. ✅ Signal detection workflow
3. ✅ Filter validation diagram
4. ✅ Option selection process
5. ✅ Position monitoring loop
6. ✅ Exit conditions decision tree

### B-Roll Footage:
- Stock charts with indicators
- Order book depth
- Real-time price action
- Dashboard metrics updating
- Discord notifications appearing

### Music:
- Upbeat, professional background music
- Lower volume during narration
- Slightly more energetic during example walkthrough

### Text Overlays:
- Key statistics (5s checks, 3s monitoring, etc.)
- Filter criteria (EMA, RSI, Volume)
- Exit conditions (15% profit, 7% loss, 5min timeout)
- Safety limits (5 trades/day, 3% daily loss, 1% risk)

### Transitions:
- Smooth fades between sections
- Quick cuts during example walkthrough
- Zoom effects on important UI elements

---

## 📝 Transcript for Captions

[Full transcript is the narration text above, formatted for closed captions with proper timing]

---

## 🎯 Key Takeaways to Emphasize

1. **Speed**: Checks every 5 seconds, monitors every 3 seconds
2. **Selectivity**: Three filters must pass (EMA, RSI, Volume)
3. **Simplicity**: Nearest ATM on next expiring contract
4. **Safety**: Multiple layers of protection
5. **Transparency**: All trades logged, real-time monitoring
6. **Automation**: Runs 6.5 hours/day without intervention

---

## 📊 Video Metrics to Track

- Watch time
- Retention rate (especially at filter explanation)
- Click-through to GitHub
- Comments asking for clarification
- Likes/dislikes ratio

---

This script is ready for production! 🎬
