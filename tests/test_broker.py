import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytz

from broker import BrokerClient


class TestBrokerClient(unittest.TestCase):
    """Test suite for BrokerClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "mode": "paper",
            "alpaca": {
                "paper": {
                    "api_key_id": "test_paper_key",
                    "api_secret_key": "test_paper_secret",
                    "endpoint": "https://paper-api.alpaca.markets",
                    "data_feed": "iex",
                },
                "live": {
                    "api_key_id": "test_live_key",
                    "api_secret_key": "test_live_secret",
                    "endpoint": "https://api.alpaca.markets",
                    "data_feed": "sip",
                },
            },
        }

    @patch("broker.REST")
    def test_init_paper_mode(self, mock_rest):
        """Test initialization in paper mode."""
        broker = BrokerClient(self.config)
        self.assertEqual(broker.mode, "paper")
        self.assertEqual(broker.api_key_id, "test_paper_key")
        self.assertEqual(broker.data_feed, "iex")

    @patch("broker.REST")
    def test_init_live_mode(self, mock_rest):
        """Test initialization in live mode."""
        config = self.config.copy()
        config["mode"] = "live"
        broker = BrokerClient(config)
        self.assertEqual(broker.mode, "live")
        self.assertEqual(broker.api_key_id, "test_live_key")
        self.assertEqual(broker.data_feed, "sip")

    @patch("broker.REST")
    def test_init_missing_keys(self, mock_rest):
        """Test initialization with missing API keys."""
        config = {"mode": "paper", "alpaca": {"paper": {}}}
        with self.assertRaises(ValueError):
            BrokerClient(config)

    @patch("broker.REST")
    def test_get_current_price_bid_ask(self, mock_rest):
        """Test current price calculation with bid/ask."""
        mock_client = MagicMock()
        mock_quote = Mock()
        mock_quote.ask_price = 150.50
        mock_quote.bid_price = 150.00
        mock_client.get_latest_quote.return_value = mock_quote

        broker = BrokerClient(self.config)
        broker.client = mock_client

        price = broker.get_current_price("AAPL")
        expected = (150.50 + 150.00) / 2
        self.assertEqual(price, expected)

    @patch("broker.REST")
    def test_get_current_price_ask_only(self, mock_rest):
        """Test current price with only ask available."""
        mock_client = MagicMock()
        mock_quote = Mock()
        mock_quote.ask_price = 150.50
        mock_quote.bid_price = None
        mock_client.get_latest_quote.return_value = mock_quote

        broker = BrokerClient(self.config)
        broker.client = mock_client

        price = broker.get_current_price("AAPL")
        self.assertEqual(price, 150.50)

    @patch("broker.REST")
    def test_get_premarket_volume(self, mock_rest):
        """Test premarket volume calculation."""
        mock_client = MagicMock()
        eastern = pytz.timezone("US/Eastern")

        # Mock bars from 4:00 AM to 10:00 AM
        mock_bars = [
            {"t": eastern.localize(datetime(2024, 1, 15, 8, 0)), "v": 1000},
            {"t": eastern.localize(datetime(2024, 1, 15, 9, 0)), "v": 2000},
            {"t": eastern.localize(datetime(2024, 1, 15, 9, 30)), "v": 3000},  # After open
            {"t": eastern.localize(datetime(2024, 1, 15, 10, 0)), "v": 4000},  # After open
        ]

        broker = BrokerClient(self.config)
        broker.client = mock_client
        broker.get_historical_bars = Mock(return_value=mock_bars)

        date = eastern.localize(datetime(2024, 1, 15, 8, 30))
        volume = broker.get_premarket_volume("AAPL", date)

        # Should sum only bars before 9:30 AM
        expected = 1000 + 2000
        self.assertEqual(volume, expected)

    @patch("broker.REST")
    def test_get_cash_balance(self, mock_rest):
        """Test cash balance retrieval."""
        mock_client = MagicMock()
        mock_account = Mock()
        mock_account.cash = "50000.00"
        mock_client.get_account.return_value = mock_account

        broker = BrokerClient(self.config)
        broker.client = mock_client

        balance = broker.get_cash_balance()
        self.assertEqual(balance, 50000.00)

    @patch("broker.REST")
    def test_is_market_open_true(self, mock_rest):
        """Test market status check when open."""
        mock_client = MagicMock()
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_client.get_clock.return_value = mock_clock

        broker = BrokerClient(self.config)
        broker.client = mock_client

        self.assertTrue(broker.is_market_open())

    @patch("broker.REST")
    def test_is_market_open_false(self, mock_rest):
        """Test market status check when closed."""
        mock_client = MagicMock()
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_client.get_clock.return_value = mock_clock

        broker = BrokerClient(self.config)
        broker.client = mock_client

        self.assertFalse(broker.is_market_open())

    @patch("broker.REST")
    def test_submit_order(self, mock_rest):
        """Test order submission."""
        mock_client = MagicMock()
        mock_order = Mock()
        mock_order.id = "order_123"
        mock_order._raw = {"id": "order_123", "symbol": "AAPL"}
        mock_client.submit_order.return_value = mock_order

        broker = BrokerClient(self.config)
        broker.client = mock_client

        result = broker.submit_order(symbol="AAPL", qty=10, side="buy")
        self.assertEqual(result["id"], "order_123")
        mock_client.submit_order.assert_called_once()

    @patch("broker.REST")
    def test_get_option_market_price(self, mock_rest):
        """Test option market price calculation."""
        mock_client = MagicMock()

        broker = BrokerClient(self.config)
        broker.client = mock_client
        broker.get_option_quote = Mock(return_value={
            "ask_price": 5.50,
            "bid_price": 5.30,
        })

        price = broker.get_option_market_price("AAPL_240115C00150000")
        expected = (5.50 + 5.30) / 2
        self.assertEqual(price, expected)

    @patch("broker.REST")
    def test_get_option_market_price_no_quote(self, mock_rest):
        """Test option market price when quote unavailable."""
        broker = BrokerClient(self.config)
        broker.get_option_quote = Mock(return_value=None)

        price = broker.get_option_market_price("AAPL_240115C00150000")
        self.assertIsNone(price)


if __name__ == "__main__":
    unittest.main()
