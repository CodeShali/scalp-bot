import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import pytz

from broker import BrokerClient
from notifications import DiscordNotifier
from utils import EASTERN_TZ, within_trading_windows, eastern_now


class SignalDetector:
    """Evaluates EMA/RSi/volume-based entry signals for a single ticker."""

    def __init__(
        self,
        broker: BrokerClient,
        notifier: DiscordNotifier,
        config: Dict[str, Any],
    ) -> None:
        self.broker = broker
        self.notifier = notifier
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.signals_cfg = config.get("signals", {})
        self.trading_cfg = config.get("trading", {})
        self.poll_interval = self.signals_cfg.get("poll_interval_seconds", 15)

    def evaluate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Evaluate the latest market data and emit a trade signal if criteria met."""
        now = eastern_now()
        trading_windows = self.signals_cfg.get("trading_windows", [])
        if trading_windows and not within_trading_windows(now, trading_windows):
            self.logger.debug("Outside trading windows for %s at %s", symbol, now)
            return None

        bars = self._get_recent_bars(symbol)
        if bars is None or len(bars) < max(self.signals_cfg.get("ema_long_period", 21) + 5, 30):
            self.logger.debug("Insufficient bar data for %s", symbol)
            return None

        df = self._prepare_dataframe(bars)
        self._compute_indicators(df)

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        direction = self._detect_crossover(previous, latest)
        if not direction:
            return None

        if not self._passes_rsi_filter(direction, latest):
            return None

        if not self._passes_volume_filter(df):
            return None

        reason = f"EMA crossover confirmed with RSI {latest['rsi']:.2f} and volume filter"

        signal = {
            "symbol": symbol,
            "direction": direction,
            "timestamp": latest.name.isoformat(),
            "price": float(latest["close"]),
            "ema_short": float(latest["ema_short"]),
            "ema_long": float(latest["ema_long"]),
            "rsi": float(latest["rsi"]),
            "volume": float(latest["volume"]),
            "reason": reason,
        }

        self.logger.info("Signal detected for %s: %s", symbol, signal)
        self.notifier.alert_signal(symbol, direction, reason)
        return signal

    def has_reversal(self, symbol: str, entry_direction: str) -> bool:
        bars = self._get_recent_bars(symbol)
        if not bars or len(bars) < 5:
            return False
        df = self._prepare_dataframe(bars)
        self._compute_indicators(df)
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        current_direction = self._detect_crossover(previous, latest)
        if not current_direction:
            # Determine if EMAs have crossed opposite to entry
            diff = latest["ema_short"] - latest["ema_long"]
            if entry_direction == "call" and diff < 0:
                return True
            if entry_direction == "put" and diff > 0:
                return True
            return False
        return current_direction != entry_direction

    # -------------------- Helpers --------------------
    def _get_recent_bars(self, symbol: str) -> Optional[list]:
        lookback_minutes = self.signals_cfg.get("lookback_minutes", 120)
        end = datetime.now(pytz.UTC)
        start = end - timedelta(minutes=lookback_minutes)
        try:
            bars = self.broker.get_historical_bars(
                symbol,
                "1Min",
                start=start,
                end=end,
                limit=lookback_minutes,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to fetch bars for %s: %s", symbol, exc)
            return None
        return bars

    def _prepare_dataframe(self, bars: list) -> pd.DataFrame:
        df = pd.DataFrame(bars)
        df["timestamp"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert(EASTERN_TZ)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        df["open"] = df["o"].astype(float)
        df["high"] = df["h"].astype(float)
        df["low"] = df["l"].astype(float)
        df["close"] = df["c"].astype(float)
        df["volume"] = df["v"].astype(float)
        return df

    def _compute_indicators(self, df: pd.DataFrame) -> None:
        short_period = self.signals_cfg.get("ema_short_period", 9)
        long_period = self.signals_cfg.get("ema_long_period", 21)
        rsi_period = self.signals_cfg.get("rsi_period", 14)

        df["ema_short"] = df["close"].ewm(span=short_period, adjust=False).mean()
        df["ema_long"] = df["close"].ewm(span=long_period, adjust=False).mean()
        df["diff"] = df["ema_short"] - df["ema_long"]

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1 / rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / rsi_period, adjust=False).mean()

        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

    def _detect_crossover(self, previous: pd.Series, latest: pd.Series) -> Optional[str]:
        prev_diff = previous["diff"]
        curr_diff = latest["diff"]
        if np.isnan(prev_diff) or np.isnan(curr_diff):
            return None
        if prev_diff <= 0 and curr_diff > 0:
            return "call"
        if prev_diff >= 0 and curr_diff < 0:
            return "put"
        return None

    def _passes_rsi_filter(self, direction: str, latest: pd.Series) -> bool:
        rsi = latest["rsi"]
        if np.isnan(rsi):
            return False
        if direction == "call":
            return rsi >= self.signals_cfg.get("rsi_call_min", 60)
        if direction == "put":
            return rsi <= self.signals_cfg.get("rsi_put_max", 40)
        return False

    def _passes_volume_filter(self, df: pd.DataFrame) -> bool:
        lookback = self.signals_cfg.get("volume_lookback", 20)
        multiplier = self.signals_cfg.get("volume_multiplier", 1.2)
        if len(df) < lookback + 1:
            return False
        recent = df.iloc[-lookback - 1 : -1]
        avg_volume = recent["volume"].mean()
        current_volume = df.iloc[-1]["volume"]
        if avg_volume == 0:
            return False
        return current_volume >= multiplier * avg_volume
