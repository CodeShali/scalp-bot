import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytz

from scan import TickerScanner


class TestTickerScanner(unittest.TestCase):
    """Test suite for TickerScanner."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "watchlist": {
                "symbols": ["AAPL", "MSFT", "TSLA"],
            },
            "scanning": {
                "weights": {
                    "premarket_volume": 0.3,
                    "gap_percent": 0.3,
                    "iv_rank": 0.2,
                    "option_open_interest": 0.1,
                    "atr": 0.1,
                },
                "thresholds": {
                    "min_premarket_volume": 100000,
                },
            },
        }
        self.mock_broker = Mock()
        self.mock_notifier = Mock()
        self.mock_notifier.is_configured.return_value = True
        self.scanner = TickerScanner(self.mock_broker, self.mock_notifier, self.config)

    def test_run_empty_watchlist(self):
        """Test scan with empty watchlist."""
        config = self.config.copy()
        config["watchlist"]["symbols"] = []
        scanner = TickerScanner(self.mock_broker, self.mock_notifier, config)

        result = scanner.run()
        self.assertIsNone(result)

    @patch("scan.update_state")
    @patch("scan.read_state")
    def test_run_successful_scan(self, mock_read_state, mock_update_state):
        """Test successful scan and ticker selection."""
        mock_read_state.return_value = {}

        # Mock metrics for each symbol
        self.scanner._compute_metrics = Mock(side_effect=[
            {"premarket_volume": 50, "gap_percent": 40, "iv_rank": 60, "option_open_interest": 30, "atr": 20},
            {"premarket_volume": 70, "gap_percent": 60, "iv_rank": 80, "option_open_interest": 50, "atr": 40},
            {"premarket_volume": 40, "gap_percent": 30, "iv_rank": 50, "option_open_interest": 20, "atr": 10},
        ])

        result = self.scanner.run()

        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "MSFT")  # Highest score
        self.assertIn("score", result)
        self.assertIn("metrics", result)

        # Verify state update and notification
        mock_update_state.assert_called_once()
        self.mock_notifier.alert_ticker_selection.assert_called_once()

    def test_compute_metrics_normalization(self):
        """Test metric normalization."""
        eastern = pytz.timezone("US/Eastern")
        reference_time = eastern.localize(datetime(2024, 1, 15, 8, 30))

        self.scanner._get_premarket_volume = Mock(return_value=500000)
        self.scanner._get_average_premarket_volume = Mock(return_value=250000)
        self.scanner._get_gap_percent = Mock(return_value=2.5)
        self.scanner._get_iv_rank = Mock(return_value=75.0)
        self.scanner._get_option_open_interest = Mock(return_value=50000)
        self.scanner._get_atr = Mock(return_value=3.5)

        metrics = self.scanner._compute_metrics("AAPL", reference_time, {})

        # All metrics should be normalized to 0-100
        for value in metrics.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 100.0)

    def test_compute_metrics_filter_by_volume(self):
        """Test hard filter by minimum premarket volume."""
        eastern = pytz.timezone("US/Eastern")
        reference_time = eastern.localize(datetime(2024, 1, 15, 8, 30))

        self.scanner._get_premarket_volume = Mock(return_value=50000)  # Below threshold
        self.scanner._get_average_premarket_volume = Mock(return_value=50000)
        self.scanner._get_gap_percent = Mock(return_value=2.5)
        self.scanner._get_iv_rank = Mock(return_value=75.0)
        self.scanner._get_option_open_interest = Mock(return_value=50000)
        self.scanner._get_atr = Mock(return_value=3.5)

        thresholds = {"min_premarket_volume": 100000}
        metrics = self.scanner._compute_metrics("AAPL", reference_time, thresholds)

        # All metrics should be zero when filtered
        for value in metrics.values():
            self.assertEqual(value, 0.0)

    def test_get_gap_percent(self):
        """Test gap percentage calculation."""
        bars = [
            {"o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0},
            {"o": 103.0, "h": 105.0, "l": 102.0, "c": 104.0},
        ]
        self.mock_broker.get_historical_bars = Mock(return_value=bars)

        gap_pct = self.scanner._get_gap_percent("AAPL")
        expected = (103.0 - 101.0) / 101.0 * 100
        self.assertAlmostEqual(gap_pct, expected, places=2)

    def test_get_gap_percent_insufficient_bars(self):
        """Test gap calculation with insufficient data."""
        self.mock_broker.get_historical_bars = Mock(return_value=[])

        gap_pct = self.scanner._get_gap_percent("AAPL")
        self.assertEqual(gap_pct, 0.0)

    def test_get_iv_rank(self):
        """Test IV rank calculation."""
        chain = [
            {"implied_volatility": 0.25},
            {"implied_volatility": 0.35},
            {"implied_volatility": 0.45},
            {"implied_volatility": 0.55},
        ]
        self.mock_broker.get_option_chain = Mock(return_value=chain)

        iv_rank = self.scanner._get_iv_rank("AAPL")

        # Current IV is max (0.55), so rank should be 100
        self.assertEqual(iv_rank, 100.0)

    def test_get_iv_rank_no_chain(self):
        """Test IV rank with empty chain."""
        self.mock_broker.get_option_chain = Mock(return_value=[])

        iv_rank = self.scanner._get_iv_rank("AAPL")
        self.assertEqual(iv_rank, 50.0)  # Neutral default

    def test_get_option_open_interest(self):
        """Test option open interest calculation for 0-1 DTE."""
        now = datetime.utcnow()
        chain = [
            {"expiration_date": now.isoformat(), "open_interest": 5000},
            {"expiration_date": (now.replace(day=now.day + 1)).isoformat(), "open_interest": 3000},
            {"expiration_date": (now.replace(day=now.day + 2)).isoformat(), "open_interest": 2000},  # Should skip
        ]
        self.mock_broker.get_option_chain = Mock(return_value=chain)

        oi = self.scanner._get_option_open_interest("AAPL")
        # Should sum only 0-1 DTE
        self.assertEqual(oi, 8000.0)

    def test_get_atr(self):
        """Test ATR calculation."""
        bars = []
        for i in range(20):
            bars.append({
                "h": 100.0 + i,
                "l": 98.0 + i,
                "c": 99.0 + i,
            })

        self.mock_broker.get_historical_bars = Mock(return_value=bars)

        atr = self.scanner._get_atr("AAPL", period=14)
        self.assertGreater(atr, 0.0)

    def test_get_atr_insufficient_bars(self):
        """Test ATR with insufficient data."""
        self.mock_broker.get_historical_bars = Mock(return_value=[])

        atr = self.scanner._get_atr("AAPL", period=14)
        self.assertEqual(atr, 0.0)


if __name__ == "__main__":
    unittest.main()
