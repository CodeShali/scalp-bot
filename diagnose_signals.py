#!/usr/bin/env python3
"""
Diagnose why signals did or did not trigger today for all watchlist tickers.
Prints step-by-step status per symbol: data, crossover, RSI, volume.

Run:
  python3 diagnose_signals.py
"""
import json
import logging
from typing import Dict, Any

from utils import load_config, setup_logging, eastern_now
from broker import BrokerClient
from notifications import DiscordNotifier
from signals import SignalDetector


def diagnose_symbol(detector: SignalDetector, symbol: str) -> Dict[str, Any]:
    cfg = detector.signals_cfg

    # 1) Fetch bars
    bars = detector._get_recent_bars(symbol)
    if not bars or len(bars) < max(cfg.get("ema_long_period", 21) + 5, 30):
        return {
            "symbol": symbol,
            "status": "insufficient_data",
            "bars": 0 if not bars else len(bars),
        }

    # 2) Indicators
    df = detector._prepare_dataframe(bars)
    detector._compute_indicators(df)
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # 3) EMA crossover
    direction = detector._detect_crossover(previous, latest)
    if not direction:
        return {
            "symbol": symbol,
            "status": "no_crossover",
            "ema_short": float(latest["ema_short"]),
            "ema_long": float(latest["ema_long"]),
            "rsi": float(latest["rsi"]),
            "price": float(latest["close"]),
        }

    # 4) RSI filter
    rsi_ok = detector._passes_rsi_filter(direction, latest)
    if not rsi_ok:
        return {
            "symbol": symbol,
            "status": "rsi_block",
            "direction": direction,
            "rsi": float(latest["rsi"]),
            "rsi_call_min": cfg.get("rsi_call_min", 60),
            "rsi_put_max": cfg.get("rsi_put_max", 40),
        }

    # 5) Volume filter
    vol_ok = detector._passes_volume_filter(df)
    if not vol_ok:
        lookback = cfg.get("volume_lookback", 20)
        multiplier = cfg.get("volume_multiplier", 1.2)
        recent = df.iloc[-lookback - 1 : -1] if len(df) >= lookback + 1 else df.iloc[:-1]
        avg_volume = float(recent["volume"].mean()) if len(recent) else 0.0
        curr_volume = float(df.iloc[-1]["volume"])
        return {
            "symbol": symbol,
            "status": "volume_block",
            "current_volume": curr_volume,
            "avg_volume": avg_volume,
            "required_min": round(multiplier * avg_volume, 2),
            "lookback": lookback,
            "multiplier": multiplier,
        }

    # 6) Signal ready
    return {
        "symbol": symbol,
        "status": "signal",
        "direction": direction,
        "price": float(latest["close"]),
        "rsi": float(latest["rsi"]),
    }


def main() -> None:
    config = load_config()
    setup_logging(config)
    logging.getLogger().setLevel(logging.INFO)

    broker = BrokerClient(config)
    notifier = DiscordNotifier(config)
    detector = SignalDetector(broker, notifier, config)

    symbols = config.get("watchlist", {}).get("symbols", [])
    if not symbols:
        print("No watchlist symbols configured.")
        return

    print(f"\n🔍 Diagnosing signals @ {eastern_now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    results = []
    for sym in symbols:
        try:
            res = diagnose_symbol(detector, sym)
        except Exception as e:
            res = {"symbol": sym, "status": "error", "error": str(e)}
        results.append(res)

    # Pretty print a compact summary line per symbol
    for res in results:
        sym = res["symbol"]
        st = res["status"]
        if st == "signal":
            print(f"✅ {sym}: SIGNAL - {res['direction'].upper()} price={res['price']:.2f} rsi={res['rsi']:.1f}")
        elif st == "no_crossover":
            print(f"—  {sym}: no EMA crossover (ema_s={res['ema_short']:.2f}, ema_l={res['ema_long']:.2f}, rsi={res['rsi']:.1f})")
        elif st == "rsi_block":
            print(f"—  {sym}: RSI block rsi={res['rsi']:.1f} dir={res['direction']} (call_min={res['rsi_call_min']}, put_max={res['rsi_put_max']})")
        elif st == "volume_block":
            print(
                f"—  {sym}: volume block curr={int(res['current_volume'])} avg={int(res['avg_volume'])} req>={int(res['required_min'])}"
            )
        elif st == "insufficient_data":
            print(f"—  {sym}: insufficient intraday bars (got {res['bars']})")
        elif st == "error":
            print(f"❌ {sym}: error {res['error']}")
        else:
            print(f"—  {sym}: {st}")

    # Also dump JSON for deeper inspection if needed
    print("\nJSON:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
