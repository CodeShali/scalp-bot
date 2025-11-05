#!/usr/bin/env python3
"""Quick test to verify Alpaca API connectivity and data access."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from broker import BrokerClient
from utils import load_config

def quick_test():
    """Quick test of Alpaca API."""
    print("Loading config...")
    config = load_config()
    
    print(f"Mode: {config.get('mode')}")
    print("\nInitializing broker...")
    broker = BrokerClient(config)
    
    print("\nTesting SPY data fetch...")
    
    # Test 1: Current price
    try:
        price = broker.get_current_price('SPY')
        print(f"✅ Current SPY price: ${price:.2f}")
    except Exception as e:
        print(f"❌ Failed to get price: {e}")
        return
    
    # Test 2: Historical bars
    try:
        from datetime import datetime, timedelta
        end = datetime.now().date()
        start = end - timedelta(days=5)
        
        bars = broker.client.get_bars(
            'SPY',
            timeframe='1Day',
            start=start.isoformat(),
            end=end.isoformat(),
            limit=10,
            feed=broker.data_feed
        )
        
        if bars:
            print(f"✅ Got {len(bars)} historical bars")
            last_bar = bars[-1]
            print(f"   Last close: ${last_bar.c:.2f}")
        else:
            print("❌ No historical bars returned")
    except Exception as e:
        print(f"❌ Failed to get bars: {e}")
        return
    
    # Test 3: Options
    try:
        chain = broker.get_option_chain('SPY')
        if chain:
            print(f"✅ Got {len(chain)} option contracts")
            if len(chain) > 0:
                print(f"   Sample: {chain[0].get('symbol', 'N/A')}")
        else:
            print("⚠️  No options returned (may be normal if market closed)")
    except Exception as e:
        print(f"❌ Failed to get options: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ All basic tests passed!")
    print("Alpaca API is working correctly.")

if __name__ == "__main__":
    quick_test()
