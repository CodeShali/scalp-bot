import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import pytz

from monitor import PositionMonitor


class TestPositionMonitor(unittest.TestCase):
    """Test suite for PositionMonitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "trading": {
                "profit_target_pct": 0.15,
                "stop_loss_pct": 0.07,
                "timeout_seconds": 300,
                "end_of_day_exit": "15:55",
            },
        }
        self.mock_broker = Mock()
        self.mock_notifier = Mock()
        self.mock_signal_detector = Mock()
        self.monitor = PositionMonitor(
            self.mock_broker,
            self.mock_notifier,
            self.mock_signal_detector,
            self.config,
        )

    @patch("monitor.read_state")
    def test_evaluate_no_position(self, mock_read_state):
        """Test evaluation with no open position."""
        mock_read_state.return_value = {}

        self.monitor.evaluate()

        # Should not attempt to close or alert
        self.mock_broker.submit_order.assert_not_called()
        self.mock_notifier.alert_exit.assert_not_called()

    @patch("monitor.append_trade_log")
    @patch("monitor.update_state")
    @patch("monitor.read_state")
    def test_evaluate_profit_target_hit(self, mock_read_state, mock_update_state, mock_log):
        """Test exit when profit target is hit."""
        eastern = pytz.timezone("US/Eastern")
        entry_time = eastern.localize(datetime(2024, 1, 15, 9, 35))

        mock_read_state.return_value = {
            "open_position": {
                "option_symbol": "AAPL_240115C00150000",
                "entry_price": 5.00,
                "direction": "call",
                "contracts": 10,
                "ticker": "AAPL",
                "entry_time": entry_time.isoformat(),
                "strike": 150.0,
                "expiration": "2024-01-15",
            }
        }

        # Current price shows 16% profit
        self.mock_broker.get_option_market_price = Mock(return_value=5.80)

        self.monitor.evaluate()

        # Should close position
        self.mock_broker.submit_order.assert_called_once()
        self.mock_notifier.alert_exit.assert_called_once()

        # Check exit reason
        call_args = self.mock_notifier.alert_exit.call_args
        self.assertEqual(call_args[1]["reason"], "profit target")

        # State should be cleared
        update_call = mock_update_state.call_args[0][0]
        self.assertIsNone(update_call["open_position"])

    @patch("monitor.append_trade_log")
    @patch("monitor.update_state")
    @patch("monitor.read_state")
    def test_evaluate_stop_loss_hit(self, mock_read_state, mock_update_state, mock_log):
        """Test exit when stop loss is hit."""
        eastern = pytz.timezone("US/Eastern")
        entry_time = eastern.localize(datetime(2024, 1, 15, 9, 35))

        mock_read_state.return_value = {
            "open_position": {
                "option_symbol": "AAPL_240115C00150000",
                "entry_price": 5.00,
                "direction": "call",
                "contracts": 10,
                "ticker": "AAPL",
                "entry_time": entry_time.isoformat(),
                "strike": 150.0,
                "expiration": "2024-01-15",
            }
        }

        # Current price shows 8% loss
        self.mock_broker.get_option_market_price = Mock(return_value=4.60)

        self.monitor.evaluate()

        # Should close position
        self.mock_broker.submit_order.assert_called_once()

        # Check exit reason
        call_args = self.mock_notifier.alert_exit.call_args
        self.assertEqual(call_args[1]["reason"], "stop loss")

    @patch("monitor.datetime")
    @patch("monitor.append_trade_log")
    @patch("monitor.update_state")
    @patch("monitor.read_state")
    def test_evaluate_timeout_exit(self, mock_read_state, mock_update_state, mock_log, mock_datetime):
        """Test exit on timeout."""
        eastern = pytz.timezone("US/Eastern")
        entry_time = eastern.localize(datetime(2024, 1, 15, 9, 35))
        current_time = eastern.localize(datetime(2024, 1, 15, 9, 45))  # 10 minutes later

        mock_datetime.now.return_value = current_time

        mock_read_state.return_value = {
            "open_position": {
                "option_symbol": "AAPL_240115C00150000",
                "entry_price": 5.00,
                "direction": "call",
                "contracts": 10,
                "ticker": "AAPL",
                "entry_time": entry_time.isoformat(),
                "strike": 150.0,
                "expiration": "2024-01-15",
            }
        }

        # Price unchanged (small profit, but not at target)
        self.mock_broker.get_option_market_price = Mock(return_value=5.20)
        self.mock_signal_detector.has_reversal = Mock(return_value=False)

        with patch("monitor.minutes_between", return_value=10.0):
            self.monitor.evaluate()

        # Should close on timeout (5 minutes = 300 seconds)
        self.mock_broker.submit_order.assert_called_once()

        call_args = self.mock_notifier.alert_exit.call_args
        self.assertEqual(call_args[1]["reason"], "timeout")

    @patch("monitor.datetime")
    @patch("monitor.append_trade_log")
    @patch("monitor.update_state")
    @patch("monitor.read_state")
    def test_evaluate_eod_exit(self, mock_read_state, mock_update_state, mock_log, mock_datetime):
        """Test end-of-day forced exit."""
        eastern = pytz.timezone("US/Eastern")
        entry_time = eastern.localize(datetime(2024, 1, 15, 15, 30))
        current_time = eastern.localize(datetime(2024, 1, 15, 15, 56))

        mock_datetime.now.return_value = current_time

        mock_read_state.return_value = {
            "open_position": {
                "option_symbol": "AAPL_240115C00150000",
                "entry_price": 5.00,
                "direction": "call",
                "contracts": 10,
                "ticker": "AAPL",
                "entry_time": entry_time.isoformat(),
                "strike": 150.0,
                "expiration": "2024-01-15",
            }
        }

        self.mock_broker.get_option_market_price = Mock(return_value=5.20)
        self.mock_signal_detector.has_reversal = Mock(return_value=False)

        with patch("monitor.minutes_between", return_value=5.0):
            self.monitor.evaluate()

        # Should close at EOD
        self.mock_broker.submit_order.assert_called_once()

        call_args = self.mock_notifier.alert_exit.call_args
        self.assertEqual(call_args[1]["reason"], "end of day")

    @patch("monitor.append_trade_log")
    @patch("monitor.update_state")
    @patch("monitor.read_state")
    def test_evaluate_ema_reversal(self, mock_read_state, mock_update_state, mock_log):
        """Test exit on EMA reversal."""
        eastern = pytz.timezone("US/Eastern")
        entry_time = eastern.localize(datetime(2024, 1, 15, 9, 35))

        mock_read_state.return_value = {
            "open_position": {
                "option_symbol": "AAPL_240115C00150000",
                "entry_price": 5.00,
                "direction": "call",
                "contracts": 10,
                "ticker": "AAPL",
                "entry_time": entry_time.isoformat(),
                "strike": 150.0,
                "expiration": "2024-01-15",
            }
        }

        self.mock_broker.get_option_market_price = Mock(return_value=5.20)
        self.mock_signal_detector.has_reversal = Mock(return_value=True)

        self.monitor.evaluate()

        # Should close on reversal
        self.mock_broker.submit_order.assert_called_once()

        call_args = self.mock_notifier.alert_exit.call_args
        self.assertEqual(call_args[1]["reason"], "ema reversal")

    @patch("monitor.read_state")
    def test_evaluate_no_price_available(self, mock_read_state):
        """Test evaluation when option price unavailable."""
        eastern = pytz.timezone("US/Eastern")
        entry_time = eastern.localize(datetime(2024, 1, 15, 9, 35))

        mock_read_state.return_value = {
            "open_position": {
                "option_symbol": "AAPL_240115C00150000",
                "entry_price": 5.00,
                "direction": "call",
                "contracts": 10,
                "ticker": "AAPL",
                "entry_time": entry_time.isoformat(),
                "strike": 150.0,
                "expiration": "2024-01-15",
            }
        }

        self.mock_broker.get_option_market_price = Mock(return_value=None)

        self.monitor.evaluate()

        # Should not close when price unavailable
        self.mock_broker.submit_order.assert_not_called()


if __name__ == "__main__":
    unittest.main()
