#!/usr/bin/env python3
"""
Test Alpaca API data fetching to diagnose scoring issues.

This script tests all the data sources used in the scoring algorithm:
1. Current price
2. Previous day's close
3. Pre-market bars
4. Option chain
5. Historical bars for ATR

Run this to verify Alpaca API is working correctly.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from broker import BrokerClient
from utils import load_config, EASTERN_TZ

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_current_price(broker: BrokerClient, symbol: str):
    """Test fetching current price."""
    print(f"\n{'='*70}")
    print(f"TEST 1: Current Price for {symbol}")
    print('='*70)
    
    try:
        price = broker.get_current_price(symbol)
        print(f"✅ SUCCESS: Current price = ${price:.2f}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_previous_close(broker: BrokerClient, symbol: str):
    """Test fetching previous day's close."""
    print(f"\n{'='*70}")
    print(f"TEST 2: Previous Close for {symbol}")
    print('='*70)
    
    try:
        # Get yesterday's date
        today = datetime.now(EASTERN_TZ).date()
        yesterday = today - timedelta(days=1)
        
        # Skip weekends
        while yesterday.weekday() >= 5:
            yesterday -= timedelta(days=1)
        
        print(f"Fetching data for: {yesterday}")
        
        bars = broker.client.get_bars(
            symbol,
            timeframe='1Day',
            start=yesterday.isoformat(),
            end=today.isoformat(),
            limit=5,
            feed=broker.data_feed
        )
        
        if bars and len(bars) > 0:
            last_bar = bars[-1]
            close_price = float(last_bar.c)
            print(f"✅ SUCCESS: Previous close = ${close_price:.2f}")
            print(f"   Date: {last_bar.t}")
            print(f"   OHLC: O=${last_bar.o:.2f} H=${last_bar.h:.2f} L=${last_bar.l:.2f} C=${last_bar.c:.2f}")
            print(f"   Volume: {last_bar.v:,}")
            return True
        else:
            print(f"❌ FAILED: No bars returned")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_premarket_volume(broker: BrokerClient, symbol: str):
    """Test fetching pre-market bars."""
    print(f"\n{'='*70}")
    print(f"TEST 3: Pre-Market Volume for {symbol}")
    print('='*70)
    
    try:
        now = datetime.now(EASTERN_TZ)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        premarket_start = now.replace(hour=4, minute=0, second=0, microsecond=0)
        
        print(f"Fetching pre-market bars from {premarket_start.strftime('%H:%M')} to {market_open.strftime('%H:%M')}")
        
        bars = broker.client.get_bars(
            symbol,
            timeframe='1Min',
            start=premarket_start.isoformat(),
            end=market_open.isoformat(),
            limit=1000,
            feed=broker.data_feed
        )
        
        if bars:
            total_volume = sum(int(bar.v) for bar in bars)
            num_bars = len(bars)
            print(f"✅ SUCCESS: Pre-market data fetched")
            print(f"   Number of bars: {num_bars}")
            print(f"   Total volume: {total_volume:,}")
            print(f"   Average volume per minute: {total_volume/num_bars:,.0f}")
            
            if num_bars > 0:
                first_bar = bars[0]
                last_bar = bars[-1]
                print(f"   First bar: {first_bar.t} - Vol: {first_bar.v:,}")
                print(f"   Last bar: {last_bar.t} - Vol: {last_bar.v:,}")
            
            return True
        else:
            print(f"⚠️  WARNING: No pre-market bars (market may not be open yet)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_historical_bars_for_atr(broker: BrokerClient, symbol: str):
    """Test fetching historical bars for ATR calculation."""
    print(f"\n{'='*70}")
    print(f"TEST 4: Historical Bars for ATR ({symbol})")
    print('='*70)
    
    try:
        end_date = datetime.now(EASTERN_TZ).date()
        start_date = end_date - timedelta(days=30)
        
        print(f"Fetching daily bars from {start_date} to {end_date}")
        
        bars = broker.client.get_bars(
            symbol,
            timeframe='1Day',
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            limit=30,
            feed=broker.data_feed
        )
        
        if bars and len(bars) > 0:
            num_bars = len(bars)
            print(f"✅ SUCCESS: Historical data fetched")
            print(f"   Number of bars: {num_bars}")
            
            # Show sample data
            recent_bars = list(bars)[-5:]
            print(f"\n   Last 5 days:")
            for bar in recent_bars:
                tr = max(
                    float(bar.h) - float(bar.l),
                    abs(float(bar.h) - float(bar.c)),
                    abs(float(bar.l) - float(bar.c))
                )
                print(f"   {bar.t.date()}: H=${bar.h:.2f} L=${bar.l:.2f} C=${bar.c:.2f} TR=${tr:.2f}")
            
            return True
        else:
            print(f"❌ FAILED: No historical bars returned")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_option_chain(broker: BrokerClient, symbol: str):
    """Test fetching option chain."""
    print(f"\n{'='*70}")
    print(f"TEST 5: Option Chain for {symbol}")
    print('='*70)
    
    try:
        print(f"Fetching option contracts...")
        
        chain = broker.get_option_chain(symbol)
        
        if chain:
            print(f"✅ SUCCESS: Option chain fetched")
            print(f"   Total contracts: {len(chain)}")
            
            # Group by expiration
            expirations = {}
            for contract in chain:
                exp = contract.get('expiration_date', 'unknown')
                if exp not in expirations:
                    expirations[exp] = []
                expirations[exp].append(contract)
            
            print(f"   Expirations: {len(expirations)}")
            
            # Show sample contracts
            print(f"\n   Sample contracts:")
            for i, contract in enumerate(chain[:5]):
                print(f"   {i+1}. {contract.get('symbol', 'N/A')}")
                print(f"      Strike: ${contract.get('strike_price', 0):.2f}")
                print(f"      Type: {contract.get('option_type', 'N/A')}")
                print(f"      Expiration: {contract.get('expiration_date', 'N/A')}")
                print(f"      Open Interest: {contract.get('open_interest', 0):,}")
            
            # Calculate total open interest
            total_oi = sum(c.get('open_interest', 0) for c in chain)
            print(f"\n   Total Open Interest: {total_oi:,}")
            
            return True
        else:
            print(f"⚠️  WARNING: No option contracts returned")
            print(f"   This could be normal if:")
            print(f"   - Market is closed")
            print(f"   - No options available for this symbol")
            print(f"   - Symbol doesn't support options")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gap_calculation(broker: BrokerClient, symbol: str):
    """Test gap calculation (today's open vs yesterday's close)."""
    print(f"\n{'='*70}")
    print(f"TEST 6: Gap Calculation for {symbol}")
    print('='*70)
    
    try:
        today = datetime.now(EASTERN_TZ).date()
        yesterday = today - timedelta(days=1)
        
        # Skip weekends
        while yesterday.weekday() >= 5:
            yesterday -= timedelta(days=1)
        
        print(f"Fetching data for gap calculation...")
        
        # Get yesterday's close
        bars_yesterday = broker.client.get_bars(
            symbol,
            timeframe='1Day',
            start=yesterday.isoformat(),
            end=today.isoformat(),
            limit=5,
            feed=broker.data_feed
        )
        
        if not bars_yesterday or len(bars_yesterday) == 0:
            print(f"❌ FAILED: No data for yesterday")
            return False
        
        prev_close = float(bars_yesterday[-1].c)
        print(f"   Yesterday's close: ${prev_close:.2f}")
        
        # Get today's open
        current_price = broker.get_current_price(symbol)
        print(f"   Current price: ${current_price:.2f}")
        
        # Calculate gap
        gap_pct = ((current_price - prev_close) / prev_close) * 100
        
        print(f"\n✅ SUCCESS: Gap calculated")
        print(f"   Gap: {gap_pct:+.2f}%")
        
        if abs(gap_pct) > 1.0:
            print(f"   ⚡ Significant gap detected!")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("ALPACA API DATA FETCHING TEST")
    print("="*70)
    
    # Load config
    try:
        config = load_config()
        print(f"\n✅ Config loaded successfully")
        print(f"   Mode: {config.get('mode', 'unknown')}")
    except Exception as e:
        print(f"\n❌ Failed to load config: {e}")
        return
    
    # Initialize broker
    try:
        broker = BrokerClient(config)
        print(f"✅ Broker client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize broker: {e}")
        return
    
    # Test symbols
    test_symbols = ['SPY', 'AAPL', 'TSLA']
    
    print(f"\nTesting with symbols: {test_symbols}")
    print(f"Time: {datetime.now(EASTERN_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Run tests for each symbol
    results = {}
    
    for symbol in test_symbols:
        print(f"\n\n{'#'*70}")
        print(f"# TESTING SYMBOL: {symbol}")
        print(f"{'#'*70}")
        
        symbol_results = {
            'current_price': test_current_price(broker, symbol),
            'previous_close': test_previous_close(broker, symbol),
            'premarket_volume': test_premarket_volume(broker, symbol),
            'historical_bars': test_historical_bars_for_atr(broker, symbol),
            'option_chain': test_option_chain(broker, symbol),
            'gap_calculation': test_gap_calculation(broker, symbol),
        }
        
        results[symbol] = symbol_results
    
    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    
    for symbol, tests in results.items():
        print(f"\n{symbol}:")
        for test_name, passed in tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name:20s}: {status}")
    
    # Overall result
    all_passed = all(all(tests.values()) for tests in results.values())
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nAlpaca API is working correctly.")
        print("If scores are still zero, the issue is in the scoring logic, not data fetching.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nAlpaca API has issues. This could explain zero scores.")
        print("Check:")
        print("  1. API keys are correct in config.yaml")
        print("  2. Account has data permissions")
        print("  3. Market is open (for some tests)")
        print("  4. Network connectivity")
    print('='*70)


if __name__ == "__main__":
    main()
