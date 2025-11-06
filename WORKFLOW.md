# 🤖 Scalp Bot Complete Workflow

## 📊 What Happens During Market Hours

This document explains **exactly** what your bot does from market open to close.

---

## 🎬 High-Level Overview

```mermaid
graph TB
    Start[9:30 AM - Market Opens] --> Init[Bot Initialized]
    Init --> Loop{Every 5 Seconds}
    Loop --> Check[Check All 10 Tickers]
    Check --> Signal{Signal Found?}
    Signal -->|No| Loop
    Signal -->|Yes| Validate[Validate Signal]
    Validate --> Option[Find Option Contract]
    Option --> Execute[Execute Trade]
    Execute --> Monitor[Monitor Position]
    Monitor --> Exit{Exit Condition?}
    Exit -->|No| Monitor
    Exit -->|Yes| Close[Close Position]
    Close --> Loop
    Loop --> EOD{4:00 PM?}
    EOD -->|No| Loop
    EOD -->|Yes| End[Market Closes]
```

---

## 🔄 Detailed Workflow

### **Phase 1: Initialization (9:30 AM)**

```mermaid
sequenceDiagram
    participant Bot
    participant Alpaca
    participant Discord
    
    Bot->>Bot: Load config.yaml
    Bot->>Alpaca: Authenticate API
    Bot->>Bot: Load watchlist (10 tickers)
    Bot->>Discord: Send startup notification
    Note over Discord: Shows both ngrok & local IP
    Bot->>Bot: Start scheduler jobs
    Note over Bot: Job 1: Signal check (every 5s)
    Note over Bot: Job 2: Position monitor (every 3s)
    Note over Bot: Job 3: News update (every 1h)
```

---

### **Phase 2: Signal Detection (Every 5 Seconds)**

```mermaid
flowchart TD
    Start[Every 5 Seconds] --> Market{Market Open?}
    Market -->|No| Skip[Skip Check]
    Market -->|Yes| Paused{Bot Paused?}
    Paused -->|Yes| Skip
    Paused -->|No| Circuit{Circuit Breaker?}
    Circuit -->|Open| Skip
    Circuit -->|Closed| Position{Has Position?}
    Position -->|Yes| Skip
    Position -->|No| Parallel[Check All 10 Tickers in Parallel]
    
    Parallel --> T1[AAPL]
    Parallel --> T2[MSFT]
    Parallel --> T3[TSLA]
    Parallel --> T4[NVDA]
    Parallel --> T5[AMD]
    Parallel --> T6[GOOGL]
    Parallel --> T7[AMZN]
    Parallel --> T8[META]
    Parallel --> T9[SPY]
    Parallel --> T10[QQQ]
    
    T1 --> Check1[Fetch 180 min bars]
    T2 --> Check2[Fetch 180 min bars]
    T3 --> Check3[Fetch 180 min bars]
    T4 --> Check4[Fetch 180 min bars]
    T5 --> Check5[Fetch 180 min bars]
    T6 --> Check6[Fetch 180 min bars]
    T7 --> Check7[Fetch 180 min bars]
    T8 --> Check8[Fetch 180 min bars]
    T9 --> Check9[Fetch 180 min bars]
    T10 --> Check10[Fetch 180 min bars]
    
    Check1 --> Calc1[Calculate EMA 9/21, RSI, Volume]
    Check2 --> Calc2[Calculate EMA 9/21, RSI, Volume]
    Check3 --> Calc3[Calculate EMA 9/21, RSI, Volume]
    Check4 --> Calc4[Calculate EMA 9/21, RSI, Volume]
    Check5 --> Calc5[Calculate EMA 9/21, RSI, Volume]
    Check6 --> Calc6[Calculate EMA 9/21, RSI, Volume]
    Check7 --> Calc7[Calculate EMA 9/21, RSI, Volume]
    Check8 --> Calc8[Calculate EMA 9/21, RSI, Volume]
    Check9 --> Calc9[Calculate EMA 9/21, RSI, Volume]
    Check10 --> Calc10[Calculate EMA 9/21, RSI, Volume]
    
    Calc1 --> Filter1{Pass Filters?}
    Calc2 --> Filter2{Pass Filters?}
    Calc3 --> Filter3{Pass Filters?}
    Calc4 --> Filter4{Pass Filters?}
    Calc5 --> Filter5{Pass Filters?}
    Calc6 --> Filter6{Pass Filters?}
    Calc7 --> Filter7{Pass Filters?}
    Calc8 --> Filter8{Pass Filters?}
    Calc9 --> Filter9{Pass Filters?}
    Calc10 --> Filter10{Pass Filters?}
    
    Filter1 -->|Yes| Signal[Signal Found!]
    Filter2 -->|Yes| Signal
    Filter3 -->|Yes| Signal
    Filter4 -->|Yes| Signal
    Filter5 -->|Yes| Signal
    Filter6 -->|Yes| Signal
    Filter7 -->|Yes| Signal
    Filter8 -->|Yes| Signal
    Filter9 -->|Yes| Signal
    Filter10 -->|Yes| Signal
    
    Filter1 -->|No| Wait[Wait 5s]
    Filter2 -->|No| Wait
    Filter3 -->|No| Wait
    Filter4 -->|No| Wait
    Filter5 -->|No| Wait
    Filter6 -->|No| Wait
    Filter7 -->|No| Wait
    Filter8 -->|No| Wait
    Filter9 -->|No| Wait
    Filter10 -->|No| Wait
    
    Signal --> Trade[Execute Trade]
    Wait --> Start
    Skip --> Start
```

---

### **Phase 3: Signal Validation (When Signal Found)**

```mermaid
flowchart TD
    Signal[Signal Detected] --> EMA{EMA Crossover?}
    
    EMA -->|CALL| EMA_Call[EMA 9 > EMA 21<br/>AND Previous: EMA 9 <= EMA 21]
    EMA -->|PUT| EMA_Put[EMA 9 < EMA 21<br/>AND Previous: EMA 9 >= EMA 21]
    
    EMA_Call --> RSI_Call{RSI Check}
    EMA_Put --> RSI_Put{RSI Check}
    
    RSI_Call -->|RSI >= 60| Vol_Call[Volume Check]
    RSI_Put -->|RSI <= 40| Vol_Put[Volume Check]
    
    RSI_Call -->|RSI < 60| Reject1[❌ Reject: RSI too low]
    RSI_Put -->|RSI > 40| Reject2[❌ Reject: RSI too high]
    
    Vol_Call --> VolCheck_Call{Volume > 1.2x Avg?}
    Vol_Put --> VolCheck_Put{Volume > 1.2x Avg?}
    
    VolCheck_Call -->|Yes| Valid_Call[✅ Valid CALL Signal]
    VolCheck_Put -->|Yes| Valid_Put[✅ Valid PUT Signal]
    
    VolCheck_Call -->|No| Reject3[❌ Reject: Low volume]
    VolCheck_Put -->|No| Reject4[❌ Reject: Low volume]
    
    Valid_Call --> Execute[Execute Trade]
    Valid_Put --> Execute
    
    Reject1 --> Wait[Wait for next check]
    Reject2 --> Wait
    Reject3 --> Wait
    Reject4 --> Wait
```

---

### **Phase 4: Option Selection & Trade Execution**

```mermaid
flowchart TD
    Signal[Valid Signal] --> Fetch[Fetch Option Chain from Alpaca]
    Fetch --> Filter[Filter Options]
    
    Filter --> Type{Match Type}
    Type -->|CALL Signal| GetCalls[Get all CALL options]
    Type -->|PUT Signal| GetPuts[Get all PUT options]
    
    GetCalls --> Price1[Filter: Has valid bid/ask price]
    GetPuts --> Price2[Filter: Has valid bid/ask price]
    
    Price1 --> Sort1[Sort by:<br/>1. Nearest expiration<br/>2. Closest to ATM]
    Price2 --> Sort2[Sort by:<br/>1. Nearest expiration<br/>2. Closest to ATM]
    
    Sort1 --> Select1[Select #1 option]
    Sort2 --> Select2[Select #1 option]
    
    Select1 --> Example1[Example: MSFT at $427.50<br/>Selected: MSFT251106C00425000<br/>Strike: $425, Exp: Today, Price: $3.45]
    Select2 --> Example2[Example: TSLA at $250.00<br/>Selected: TSLA251106P00250000<br/>Strike: $250, Exp: Today, Price: $2.80]
    
    Example1 --> CalcQty[Calculate Quantity]
    Example2 --> CalcQty
    
    CalcQty --> Risk[Risk = 1% of capital<br/>Qty = Risk / Option Price]
    Risk --> QtyExample[Example:<br/>Capital: $10,000<br/>Risk: $100<br/>Option: $3.45<br/>Qty: 100/3.45 = 29 contracts]
    
    QtyExample --> Order[Submit Market Order to Alpaca]
    Order --> Wait{Wait for Fill}
    Wait -->|Filled| Success[✅ Order Filled]
    Wait -->|Timeout| Cancel[❌ Cancel Order]
    
    Success --> Notify[Discord Notification:<br/>✅ Order filled: MSFT CALL<br/>29 contracts @ $3.45]
    Success --> SaveState[Save position to state.json]
    Success --> StartMonitor[Start Position Monitoring]
```

---

### **Phase 5: Position Monitoring (Every 3 Seconds)**

```mermaid
flowchart TD
    Start[Every 3 Seconds] --> HasPos{Has Position?}
    HasPos -->|No| Skip[Skip]
    HasPos -->|Yes| GetPrice[Get Current Option Price]
    
    GetPrice --> CalcPnL[Calculate P/L %<br/>PnL = (Current - Entry) / Entry × 100]
    
    CalcPnL --> Example[Example:<br/>Entry: $3.45<br/>Current: $3.97<br/>PnL: +15.07%]
    
    Example --> Check1{Profit Target?}
    Check1 -->|PnL >= 15%| Exit1[✅ EXIT: Profit Target Hit!]
    Check1 -->|No| Check2{Stop Loss?}
    
    Check2 -->|PnL <= -7%| Exit2[🛑 EXIT: Stop Loss Hit!]
    Check2 -->|No| Check3{Timeout?}
    
    Check3 -->|> 5 minutes| Exit3[⏰ EXIT: Timeout!]
    Check3 -->|No| Check4{EOD?}
    
    Check4 -->|Time >= 3:55 PM| Exit4[🌅 EXIT: End of Day!]
    Check4 -->|No| Check5{Reversal?}
    
    Check5 -->|EMA Reversed| Exit5[🔄 EXIT: Signal Reversed!]
    Check5 -->|No| Continue[Continue Monitoring]
    
    Exit1 --> Close[Close Position]
    Exit2 --> Close
    Exit3 --> Close
    Exit4 --> Close
    Exit5 --> Close
    
    Close --> SubmitOrder[Submit Market Sell Order]
    SubmitOrder --> WaitFill{Wait for Fill}
    WaitFill -->|Filled| Record[Record Trade in CSV]
    WaitFill -->|Timeout| ForceClose[Force Close]
    
    Record --> NotifyExit[Discord Notification:<br/>💰 Position closed: MSFT CALL<br/>Entry: $3.45, Exit: $3.97<br/>P/L: +15.07% (+$15.08)]
    
    NotifyExit --> ClearState[Clear position from state.json]
    ClearState --> Ready[Ready for next signal]
    
    Continue --> Start
    Skip --> Start
```

---

### **Phase 6: Daily Limits & Circuit Breaker**

```mermaid
flowchart TD
    Trade[Before Each Trade] --> CheckLimits{Check Daily Limits}
    
    CheckLimits --> Trades{Trades Today?}
    Trades -->|>= 5| Block1[❌ BLOCK: Max 5 trades/day reached]
    Trades -->|< 5| Loss{Daily Loss?}
    
    Loss -->|<= -3%| Block2[❌ BLOCK: Max 3% daily loss reached]
    Loss -->|> -3%| Circuit{Circuit Breaker?}
    
    Circuit -->|5 errors in 10 attempts| Block3[🚨 BLOCK: Circuit breaker open]
    Circuit -->|< 5 errors| Allow[✅ ALLOW: Trade can proceed]
    
    Block1 --> Wait[Wait until tomorrow]
    Block2 --> Wait
    Block3 --> Manual[Requires manual reset]
    
    Allow --> Execute[Execute Trade]
```

---

## 📋 Complete Daily Timeline Example

### **9:30 AM - Market Opens**
```
✅ Bot initialized
✅ Loaded 10 tickers: AAPL, MSFT, TSLA, NVDA, AMD, GOOGL, AMZN, META, SPY, QQQ
✅ Discord notification sent
✅ Started signal detection (every 5s)
✅ Started position monitoring (every 3s)
✅ Started news updates (every 1h)
```

### **9:30:05 AM - First Signal Check**
```
🔍 Checking AAPL... No signal
🔍 Checking MSFT... No signal
🔍 Checking TSLA... No signal
🔍 Checking NVDA... No signal
🔍 Checking AMD... No signal
🔍 Checking GOOGL... No signal
🔍 Checking AMZN... No signal
🔍 Checking META... No signal
🔍 Checking SPY... No signal
🔍 Checking QQQ... No signal
⏳ Wait 5 seconds...
```

### **10:15:30 AM - Signal Detected!**
```
🚨 SIGNAL DETECTED: MSFT CALL
📊 Price: $427.50
📈 EMA 9: 426.80 > EMA 21: 425.50 (Crossover confirmed!)
📊 RSI: 65.2 (> 60 ✅)
📊 Volume: 2.5M (1.8x average ✅)
✅ All filters passed!

🔍 Selecting option contract...
📋 Got 847 options in chain
✅ Filtered to 124 valid CALL options
🎯 Selected: MSFT251106C00425000
   Strike: $425.00 ($2.50 from ATM)
   Expiration: 2025-11-06 (0.3 DTE)
   Price: $3.45

💰 Calculating quantity...
   Capital: $10,000
   Risk: 1% = $100
   Option price: $3.45
   Quantity: 29 contracts

📤 Submitting order to Alpaca...
⏳ Waiting for fill...
✅ Order filled: 29 contracts @ $3.45
💵 Total cost: $100.05

📱 Discord notification sent
💾 Position saved to state.json
👁️ Started monitoring position
```

### **10:15:33 AM - Position Monitoring Starts**
```
📊 Monitoring MSFT CALL position...
   Entry: $3.45
   Current: $3.48
   P/L: +0.87% (+$0.87)
⏳ Continue monitoring...
```

### **10:16:00 AM - Still Monitoring**
```
📊 Monitoring MSFT CALL position...
   Entry: $3.45
   Current: $3.62
   P/L: +4.93% (+$4.93)
⏳ Continue monitoring...
```

### **10:18:15 AM - Profit Target Hit!**
```
📊 Monitoring MSFT CALL position...
   Entry: $3.45
   Current: $3.97
   P/L: +15.07% (+$15.08)
✅ PROFIT TARGET HIT! (>= 15%)

🔄 Closing position...
📤 Submitting sell order...
✅ Position closed @ $3.97
💰 Profit: +$15.08 (+15.07%)

📊 Trade recorded to CSV:
   Ticker: MSFT
   Direction: CALL
   Entry: $3.45
   Exit: $3.97
   Contracts: 29
   P/L: +$15.08
   Duration: 2m 45s

📱 Discord notification sent
💾 State cleared
✅ Ready for next signal
```

### **10:18:20 AM - Back to Signal Detection**
```
🔍 Checking all tickers again...
⏳ No signals found
⏳ Wait 5 seconds...
```

### **11:30:00 AM - News Update**
```
📰 Updating news for 10 tickers...
🤖 Calling OpenAI for analysis...
✅ News updated:
   AAPL: Bullish, High entry likelihood
   MSFT: Bullish, Medium entry likelihood
   TSLA: Bearish, Low entry likelihood
   ...
💾 Cached for dashboard display
```

### **3:55:00 PM - End of Day Check**
```
⏰ 3:55 PM - End of day approaching
📊 Checking for open positions...
✅ No open positions
📊 Daily summary:
   Trades: 3
   Wins: 2
   Losses: 1
   P/L: +$28.50 (+0.29%)
```

### **4:00:00 PM - Market Closes**
```
🌅 Market closed
⏸️ Signal detection paused
⏸️ Position monitoring paused
📊 Bot remains running (ready for tomorrow)
```

---

## 🎯 Key Points

### **What Bot Does:**
1. ✅ Checks 10 tickers every 5 seconds
2. ✅ Validates signals with 3 filters (EMA, RSI, Volume)
3. ✅ Selects nearest ATM option on next expiring contract
4. ✅ Executes trade with 1% risk
5. ✅ Monitors position every 3 seconds
6. ✅ Exits on profit target (15%), stop loss (7%), timeout (5min), or EOD
7. ✅ Records all trades to CSV
8. ✅ Sends Discord notifications
9. ✅ Updates news hourly

### **What Bot Doesn't Do:**
- ❌ Trade outside market hours (9:30 AM - 4:00 PM)
- ❌ Trade when paused or circuit breaker open
- ❌ Trade if already has a position
- ❌ Trade if daily limits reached (5 trades or 3% loss)
- ❌ Hold positions overnight (force exit at 3:55 PM)

### **Safety Features:**
- 🛡️ Max 1% risk per trade
- 🛡️ Max 5 trades per day
- 🛡️ Max 3% daily loss
- 🛡️ Circuit breaker (5 errors = pause)
- 🛡️ Force exit before market close
- 🛡️ Stop loss at 7%
- 🛡️ Timeout after 5 minutes

---

## 📊 Statistics

**Per Day:**
- Signal checks: ~4,680 (6.5 hours × 12 checks/min)
- Position checks: ~7,800 (when in position, every 3s)
- API calls to Alpaca: ~5,000-10,000
- Trades: 0-5 (limited by daily max)
- News updates: 6-7 (hourly during market hours)

**Per Trade:**
- Average duration: 2-5 minutes
- Success rate: Depends on market conditions
- Risk per trade: 1% of capital
- Potential profit: 15% (target)
- Potential loss: 7% (stop loss)

---

This is your bot's complete workflow! 🚀
