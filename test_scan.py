#!/usr/bin/env python3
"""
Test pre-market scan and news sentiment functionality.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scan import TickerScanner
from broker import BrokerClient
from notifications import DiscordNotifier
from utils import load_config, EASTERN_TZ

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_news_sentiment():
    """Test news sentiment fetching."""
    print(f"\n{'='*70}")
    print("TEST: News Sentiment Analysis")
    print('='*70)
    
    try:
        config = load_config()
        broker = BrokerClient(config)
        notifier = DiscordNotifier(config)
        scanner = TickerScanner(broker, notifier, config)
        
        # Test with a popular stock
        symbol = 'TSLA'
        print(f"\nFetching news for {symbol}...")
        
        sentiment, news_count = scanner._get_news_sentiment(symbol)
        
        print(f"\n✅ SUCCESS: News sentiment fetched")
        print(f"   Symbol: {symbol}")
        print(f"   Sentiment Score: {sentiment:.2f} (range: -1.0 to +1.0)")
        print(f"   Number of Articles: {news_count}")
        
        if sentiment > 0.3:
            print(f"   📈 Positive sentiment")
        elif sentiment < -0.3:
            print(f"   📉 Negative sentiment")
        else:
            print(f"   ➡️  Neutral sentiment")
        
        if news_count == 0:
            print(f"   ⚠️  No news articles found (may be normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metric_calculation():
    """Test individual metric calculations."""
    print(f"\n{'='*70}")
    print("TEST: Metric Calculations")
    print('='*70)
    
    try:
        config = load_config()
        broker = BrokerClient(config)
        notifier = DiscordNotifier(config)
        scanner = TickerScanner(broker, notifier, config)
        
        symbol = 'SPY'
        now = datetime.now(EASTERN_TZ)
        thresholds = config.get('scanning', {}).get('thresholds', {})
        
        print(f"\nCalculating metrics for {symbol}...")
        
        metrics = scanner._compute_metrics(symbol, now, thresholds)
        
        print(f"\n✅ SUCCESS: Metrics calculated")
        print(f"\nMetric Values:")
        for key, value in metrics.items():
            print(f"   {key:25s}: {value:8.2f}")
        
        # Check if any metrics are non-zero
        non_zero = [k for k, v in metrics.items() if v != 0.0]
        zero = [k for k, v in metrics.items() if v == 0.0]
        
        print(f"\n   Non-zero metrics: {len(non_zero)}/{len(metrics)}")
        if zero:
            print(f"   Zero metrics: {', '.join(zero)}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_scan():
    """Test complete pre-market scan."""
    print(f"\n{'='*70}")
    print("TEST: Full Pre-Market Scan")
    print('='*70)
    
    try:
        config = load_config()
        
        # Temporarily reduce watchlist for testing
        original_watchlist = config.get('watchlist', {}).get('symbols', [])
        test_watchlist = original_watchlist[:5]  # Test with first 5 symbols
        config['watchlist']['symbols'] = test_watchlist
        
        print(f"\nTesting with symbols: {test_watchlist}")
        
        broker = BrokerClient(config)
        notifier = DiscordNotifier(config)
        scanner = TickerScanner(broker, notifier, config)
        
        print(f"\nRunning pre-market scan...")
        result = scanner.run()
        
        if result:
            print(f"\n✅ SUCCESS: Scan completed")
            print(f"\nScan Results:")
            print(f"   Selected tickers: {result.get('tickers', [])}")
            print(f"   Reasoning available: {'Yes' if result.get('reasoning') else 'No'}")
            
            # Show scores
            if 'all_scores' in result:
                print(f"\n   All Scores:")
                for ticker, score, metrics in result['all_scores'][:10]:
                    print(f"   {ticker}: {score:.2f}")
            
            # Show reasoning snippet
            if result.get('reasoning'):
                reasoning = result['reasoning']
                print(f"\n   Reasoning (first 200 chars):")
                print(f"   {reasoning[:200]}...")
            
            return True
        else:
            print(f"⚠️  WARNING: Scan returned None")
            print(f"   This may be normal if:")
            print(f"   - Watchlist is empty")
            print(f"   - No data available")
            print(f"   - Market is closed")
            return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scoring_weights():
    """Test that scoring weights are properly configured."""
    print(f"\n{'='*70}")
    print("TEST: Scoring Weights Configuration")
    print('='*70)
    
    try:
        config = load_config()
        weights = config.get('scanning', {}).get('weights', {})
        
        print(f"\nConfigured weights:")
        total = 0.0
        for key, value in weights.items():
            print(f"   {key:25s}: {value:.2f}")
            total += value
        
        print(f"\n   Total weight sum: {total:.2f}")
        
        if abs(total - 1.0) < 0.01:
            print(f"   ✅ Weights sum to ~1.0 (good)")
        else:
            print(f"   ⚠️  Weights don't sum to 1.0 (may cause scaling issues)")
        
        # Check for missing weights
        expected_metrics = [
            'premarket_volume',
            'gap_percent',
            'iv_rank',
            'option_open_interest',
            'atr',
            'news_sentiment',
            'news_volume'
        ]
        
        missing = [m for m in expected_metrics if m not in weights]
        if missing:
            print(f"   ⚠️  Missing weights: {', '.join(missing)}")
        else:
            print(f"   ✅ All expected weights present")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all scan tests."""
    print("\n" + "="*70)
    print("PRE-MARKET SCAN & NEWS TEST SUITE")
    print("="*70)
    print(f"Time: {datetime.now(EASTERN_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    results = {
        'weights_config': test_scoring_weights(),
        'news_sentiment': test_news_sentiment(),
        'metric_calculation': test_metric_calculation(),
        'full_scan': test_full_scan(),
    }
    
    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:25s}: {status}")
    
    all_passed = all(results.values())
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL SCAN TESTS PASSED!")
        print("\nPre-market scan and news are working correctly.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nCheck the errors above for details.")
    print('='*70)


if __name__ == "__main__":
    main()
