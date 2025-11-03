import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pytz

from utils import (
    chunk_list,
    eastern_now,
    ensure_timezone,
    load_config,
    minutes_between,
    parse_time_range,
    rolling_iv_rank,
    weighted_score,
    within_trading_windows,
)


class TestUtils(unittest.TestCase):
    """Test suite for utility functions."""

    def test_parse_time_range(self):
        """Test time range parsing."""
        start, end = parse_time_range("09:30-10:30")
        self.assertEqual(start, 9 * 60 + 30)
        self.assertEqual(end, 10 * 60 + 30)

    def test_parse_time_range_evening(self):
        """Test time range parsing for evening hours."""
        start, end = parse_time_range("15:00-16:00")
        self.assertEqual(start, 15 * 60)
        self.assertEqual(end, 16 * 60)

    def test_within_trading_windows_inside(self):
        """Test detection when inside trading window."""
        eastern = pytz.timezone("US/Eastern")
        dt = eastern.localize(datetime(2024, 1, 15, 9, 45))  # 9:45 AM ET
        windows = ["09:30-10:30", "15:00-16:00"]
        self.assertTrue(within_trading_windows(dt, windows))

    def test_within_trading_windows_outside(self):
        """Test detection when outside trading window."""
        eastern = pytz.timezone("US/Eastern")
        dt = eastern.localize(datetime(2024, 1, 15, 11, 0))  # 11:00 AM ET
        windows = ["09:30-10:30", "15:00-16:00"]
        self.assertFalse(within_trading_windows(dt, windows))

    def test_within_trading_windows_second_window(self):
        """Test detection in second trading window."""
        eastern = pytz.timezone("US/Eastern")
        dt = eastern.localize(datetime(2024, 1, 15, 15, 30))  # 3:30 PM ET
        windows = ["09:30-10:30", "15:00-16:00"]
        self.assertTrue(within_trading_windows(dt, windows))

    def test_ensure_timezone_naive(self):
        """Test timezone enforcement on naive datetime."""
        naive_dt = datetime(2024, 1, 15, 10, 0)
        result = ensure_timezone(naive_dt)
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.tzinfo, pytz.timezone("US/Eastern"))

    def test_ensure_timezone_aware(self):
        """Test timezone enforcement on aware datetime."""
        utc = pytz.utc
        aware_dt = utc.localize(datetime(2024, 1, 15, 15, 0))
        result = ensure_timezone(aware_dt)
        self.assertEqual(result.tzinfo, pytz.timezone("US/Eastern"))

    def test_minutes_between(self):
        """Test minutes calculation between two datetimes."""
        eastern = pytz.timezone("US/Eastern")
        dt1 = eastern.localize(datetime(2024, 1, 15, 9, 30))
        dt2 = eastern.localize(datetime(2024, 1, 15, 10, 0))
        minutes = minutes_between(dt1, dt2)
        self.assertEqual(minutes, 30.0)

    def test_eastern_now_has_timezone(self):
        """Test eastern_now returns timezone-aware datetime."""
        now = eastern_now()
        self.assertIsNotNone(now.tzinfo)
        self.assertEqual(now.tzinfo, pytz.timezone("US/Eastern"))

    def test_weighted_score(self):
        """Test weighted scoring calculation."""
        metrics = {"volume": 50.0, "gap": 75.0, "iv": 60.0}
        weights = {"volume": 0.5, "gap": 0.3, "iv": 0.2}
        score = weighted_score(metrics, weights)
        expected = 50.0 * 0.5 + 75.0 * 0.3 + 60.0 * 0.2
        self.assertAlmostEqual(score, expected, places=2)

    def test_weighted_score_missing_keys(self):
        """Test weighted scoring with missing metric keys."""
        metrics = {"volume": 50.0}
        weights = {"volume": 0.5, "gap": 0.3, "iv": 0.2}
        score = weighted_score(metrics, weights)
        expected = 50.0 * 0.5  # Only volume contributes
        self.assertAlmostEqual(score, expected, places=2)

    def test_rolling_iv_rank(self):
        """Test IV rank calculation."""
        iv_values = [20.0, 30.0, 40.0, 50.0, 60.0]
        current_iv = 45.0
        rank = rolling_iv_rank(iv_values, current_iv)
        expected = (45.0 - 20.0) / (60.0 - 20.0) * 100
        self.assertAlmostEqual(rank, expected, places=2)

    def test_rolling_iv_rank_at_min(self):
        """Test IV rank at minimum value."""
        iv_values = [20.0, 30.0, 40.0]
        current_iv = 20.0
        rank = rolling_iv_rank(iv_values, current_iv)
        self.assertEqual(rank, 0.0)

    def test_rolling_iv_rank_at_max(self):
        """Test IV rank at maximum value."""
        iv_values = [20.0, 30.0, 40.0]
        current_iv = 40.0
        rank = rolling_iv_rank(iv_values, current_iv)
        self.assertEqual(rank, 100.0)

    def test_rolling_iv_rank_empty(self):
        """Test IV rank with empty list."""
        rank = rolling_iv_rank([], 30.0)
        self.assertIsNone(rank)

    def test_chunk_list(self):
        """Test list chunking."""
        items = list(range(10))
        chunks = list(chunk_list(items, 3))
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0], [0, 1, 2])
        self.assertEqual(chunks[1], [3, 4, 5])
        self.assertEqual(chunks[2], [6, 7, 8])
        self.assertEqual(chunks[3], [9])

    def test_load_config(self):
        """Test config loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("mode: paper\n")
            f.write("alpaca:\n")
            f.write("  paper:\n")
            f.write("    api_key_id: test_key\n")
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertEqual(config["mode"], "paper")
            self.assertEqual(config["alpaca"]["paper"]["api_key_id"], "test_key")
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    unittest.main()
