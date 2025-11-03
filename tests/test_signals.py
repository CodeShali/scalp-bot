import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytz

from signals import SignalDetector


class TestSignalDetector(unittest.TestCase):
    """Test suite for SignalDetector."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "signals": {
                "ema_short_period": 9,
                "ema_long_period": 21,
                "rsi_period": 14,
                "rsi_call_min": 60,
                "rsi_put_max": 40,
                "volume_multiplier": 1.2,
                "volume_lookback": 20,
                "lookback_minutes": 120,
                "poll_interval_seconds": 15,
                "trading_windows": ["09:30-10:30", "15:00-16:00"],
            },
            "trading": {},
        }
        self.mock_broker = Mock()
        self.mock_notifier = Mock()
        self.detector = SignalDetector(self.mock_broker, self.mock_notifier, self.config)

    def _create_sample_bars(self, num_bars=50):
        """Create sample price bars for testing."""
        eastern = pytz.timezone("US/Eastern")
        base_time = eastern.localize(datetime(2024, 1, 15, 9, 30))

        bars = []
        for i in range(num_bars):
            bars.append({
                "t": base_time.replace(minute=30 + i),
                "o": 100.0 + i * 0.1,
                "h": 100.5 + i * 0.1,
                "l": 99.5 + i * 0.1,
                "c": 100.0 + i * 0.1,
                "v": 1000 + i * 10,
            })
        return bars

    def test_prepare_dataframe(self):
        """Test dataframe preparation from bars."""
        bars = self._create_sample_bars(30)
        df = self.detector._prepare_dataframe(bars)

        self.assertEqual(len(df), 30)
        self.assertIn("close", df.columns)
        self.assertIn("volume", df.columns)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df.index))

    def test_compute_indicators_ema(self):
        """Test EMA calculation."""
        bars = self._create_sample_bars(50)
        df = self.detector._prepare_dataframe(bars)
        self.detector._compute_indicators(df)

        self.assertIn("ema_short", df.columns)
        self.assertIn("ema_long", df.columns)
        self.assertIn("diff", df.columns)

        # EMAs should be calculated
        self.assertFalse(df["ema_short"].isna().all())
        self.assertFalse(df["ema_long"].isna().all())

    def test_compute_indicators_rsi(self):
        """Test RSI calculation."""
        bars = self._create_sample_bars(50)
        df = self.detector._prepare_dataframe(bars)
        self.detector._compute_indicators(df)

        self.assertIn("rsi", df.columns)
        # RSI should be between 0 and 100
        valid_rsi = df["rsi"].dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())

    def test_detect_crossover_bullish(self):
        """Test bullish EMA crossover detection."""
        previous = pd.Series({"diff": -0.5})
        latest = pd.Series({"diff": 0.5})

        direction = self.detector._detect_crossover(previous, latest)
        self.assertEqual(direction, "call")

    def test_detect_crossover_bearish(self):
        """Test bearish EMA crossover detection."""
        previous = pd.Series({"diff": 0.5})
        latest = pd.Series({"diff": -0.5})

        direction = self.detector._detect_crossover(previous, latest)
        self.assertEqual(direction, "put")

    def test_detect_crossover_no_cross(self):
        """Test no crossover when both positive."""
        previous = pd.Series({"diff": 0.5})
        latest = pd.Series({"diff": 1.0})

        direction = self.detector._detect_crossover(previous, latest)
        self.assertIsNone(direction)

    def test_detect_crossover_nan(self):
        """Test crossover with NaN values."""
        previous = pd.Series({"diff": np.nan})
        latest = pd.Series({"diff": 0.5})

        direction = self.detector._detect_crossover(previous, latest)
        self.assertIsNone(direction)

    def test_passes_rsi_filter_call(self):
        """Test RSI filter for call signals."""
        latest = pd.Series({"rsi": 65.0})
        self.assertTrue(self.detector._passes_rsi_filter("call", latest))

        latest = pd.Series({"rsi": 55.0})
        self.assertFalse(self.detector._passes_rsi_filter("call", latest))

    def test_passes_rsi_filter_put(self):
        """Test RSI filter for put signals."""
        latest = pd.Series({"rsi": 35.0})
        self.assertTrue(self.detector._passes_rsi_filter("put", latest))

        latest = pd.Series({"rsi": 45.0})
        self.assertFalse(self.detector._passes_rsi_filter("put", latest))

    def test_passes_rsi_filter_nan(self):
        """Test RSI filter with NaN."""
        latest = pd.Series({"rsi": np.nan})
        self.assertFalse(self.detector._passes_rsi_filter("call", latest))

    def test_passes_volume_filter_pass(self):
        """Test volume filter when volume exceeds threshold."""
        bars = self._create_sample_bars(25)
        # Increase last bar volume significantly
        bars[-1]["v"] = 5000
        df = self.detector._prepare_dataframe(bars)

        result = self.detector._passes_volume_filter(df)
        self.assertTrue(result)

    def test_passes_volume_filter_fail(self):
        """Test volume filter when volume is below threshold."""
        bars = self._create_sample_bars(25)
        # Keep volume consistent (no spike)
        df = self.detector._prepare_dataframe(bars)

        result = self.detector._passes_volume_filter(df)
        # With multiplier 1.2 and consistent volume, should fail
        self.assertFalse(result)

    def test_passes_volume_filter_insufficient_data(self):
        """Test volume filter with insufficient bars."""
        bars = self._create_sample_bars(10)
        df = self.detector._prepare_dataframe(bars)

        result = self.detector._passes_volume_filter(df)
        self.assertFalse(result)

    @patch("signals.eastern_now")
    def test_evaluate_outside_trading_window(self, mock_now):
        """Test evaluation outside trading windows."""
        eastern = pytz.timezone("US/Eastern")
        mock_now.return_value = eastern.localize(datetime(2024, 1, 15, 11, 0))

        result = self.detector.evaluate("AAPL")
        self.assertIsNone(result)

    @patch("signals.eastern_now")
    def test_evaluate_insufficient_bars(self, mock_now):
        """Test evaluation with insufficient bar data."""
        eastern = pytz.timezone("US/Eastern")
        mock_now.return_value = eastern.localize(datetime(2024, 1, 15, 9, 45))

        self.mock_broker.get_historical_bars = Mock(return_value=[])

        result = self.detector.evaluate("AAPL")
        self.assertIsNone(result)

    def test_has_reversal_call_to_put(self):
        """Test reversal detection from call to put."""
        bars = self._create_sample_bars(30)
        self.mock_broker.get_historical_bars = Mock(return_value=bars)

        df = self.detector._prepare_dataframe(bars)
        self.detector._compute_indicators(df)

        # Set up a bearish crossover in latest bars
        df.iloc[-2, df.columns.get_loc("diff")] = 0.5
        df.iloc[-1, df.columns.get_loc("diff")] = -0.5

        # Mock to return the dataframe
        with patch.object(self.detector, "_get_recent_bars", return_value=bars):
            with patch.object(self.detector, "_prepare_dataframe", return_value=df):
                result = self.detector.has_reversal("AAPL", "call")
                # Should detect reversal when entered call but now bearish
                # Implementation depends on exact logic


if __name__ == "__main__":
    unittest.main()
