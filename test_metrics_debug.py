#!/usr/bin/env python3
"""
Debug script to see actual raw metric values.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytz

sys.path.insert(0, str(Path(__file__).parent))

from scan import TickerScanner
from broker import BrokerClient
from notifications import DiscordNotifier
from utils import load_config, EASTERN_TZ

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_individual_metrics():
    """Test each metric calculation individually to see raw values."""
    print("\n" + "="*70)
    print("INDIVIDUAL METRIC DEBUG TEST")
    print("="*70)
    
    config = load_config()
    broker = BrokerClient(config)
    notifier = DiscordNotifier(config)
    scanner = TickerScanner(broker, notifier, config)
    
    symbol = 'SPY'
    now = datetime.now(EASTERN_TZ)
    
    print(f"\nTesting {symbol} at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("="*70)
    
    # 1. Premarket Volume
    print("\n1. PREMARKET VOLUME:")
    try:
        pm_vol = scanner._get_premarket_volume(symbol, now)
        avg_pm_vol = scanner._get_average_premarket_volume(symbol, now, days=5)
        ratio = pm_vol / avg_pm_vol if avg_pm_vol > 0 else 1.0
        print(f"   Today's premarket: {pm_vol:,.0f}")
        print(f"   5-day average: {avg_pm_vol:,.0f}")
        print(f"   Ratio: {ratio:.2f}")
        print(f"   Normalized (ratio * 50): {min(100.0, max(0.0, ratio * 50)):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Gap Percent
    print("\n2. GAP PERCENT:")
    try:
        gap = scanner._get_gap_percent(symbol)
        print(f"   Gap: {gap:.2f}%")
        print(f"   Normalized (abs(gap) * 10): {min(100.0, max(0.0, abs(gap) * 10)):.2f}")
        
        # Show the bars used
        bars = broker.get_historical_bars(
            symbol,
            "1Day",
            start=datetime.now(pytz.UTC) - timedelta(days=10),
            limit=5,
        )
        if bars and len(bars) >= 2:
            print(f"   Last 2 bars:")
            for i, bar in enumerate(bars[-2:]):
                print(f"     Bar {i}: O=${bar.get('o'):.2f} H=${bar.get('h'):.2f} L=${bar.get('l'):.2f} C=${bar.get('c'):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. IV Rank
    print("\n3. IV RANK:")
    try:
        iv_rank = scanner._get_iv_rank(symbol)
        print(f"   IV Rank: {iv_rank:.2f}")
        print(f"   Normalized: {min(100.0, max(0.0, iv_rank)):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Option Open Interest
    print("\n4. OPTION OPEN INTEREST:")
    try:
        oi = scanner._get_option_open_interest(symbol)
        print(f"   Total OI: {oi:,.0f}")
        print(f"   Normalized (oi / 1000): {min(100.0, max(0.0, oi / 1000)):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. ATR
    print("\n5. ATR (Average True Range):")
    try:
        atr = scanner._get_atr(symbol, period=14)
        print(f"   ATR: ${atr:.2f}")
        print(f"   Normalized (atr * 10): {min(100.0, max(0.0, atr * 10)):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 6. News Sentiment
    print("\n6. NEWS SENTIMENT:")
    try:
        sentiment, news_count = scanner._get_news_sentiment(symbol)
        print(f"   Sentiment: {sentiment:.2f} (range: -1.0 to +1.0)")
        print(f"   News count: {news_count}")
        print(f"   Normalized sentiment ((sentiment + 1) * 50): {min(100.0, max(0.0, (sentiment + 1) * 50)):.2f}")
        print(f"   Normalized news (count * 5): {min(100.0, max(0.0, news_count * 5)):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 7. Full metrics calculation
    print("\n7. FULL METRICS CALCULATION:")
    try:
        thresholds = config.get('scanning', {}).get('thresholds', {})
        metrics = scanner._compute_metrics(symbol, now, thresholds)
        print(f"   Final normalized metrics:")
        for key, value in metrics.items():
            print(f"     {key:25s}: {value:8.2f}")
        
        # Calculate score
        weights = config.get('scanning', {}).get('weights', {})
        score = sum(metrics.get(k, 0) * w for k, w in weights.items())
        print(f"\n   FINAL SCORE: {score:.2f}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_individual_metrics()
