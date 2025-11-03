import unittest
from unittest.mock import Mock, patch

from notifications import DiscordNotifier


class TestDiscordNotifier(unittest.TestCase):
    """Test suite for DiscordNotifier."""

    def setUp(self):
        """Set up test fixtures."""
        self.webhook_url = "https://discord.com/api/webhooks/123/abc"
        self.notifier = DiscordNotifier(self.webhook_url)

    def test_is_configured_true(self):
        """Test configured check with valid webhook."""
        self.assertTrue(self.notifier.is_configured())

    def test_is_configured_false(self):
        """Test configured check without webhook."""
        notifier = DiscordNotifier(None)
        self.assertFalse(notifier.is_configured())

    @patch("notifications.requests.post")
    def test_send_success(self, mock_post):
        """Test successful message send."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.notifier.send("Test message")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], self.webhook_url)
        self.assertEqual(call_args[1]["json"]["content"], "Test message")

    @patch("notifications.requests.post")
    def test_send_with_embeds(self, mock_post):
        """Test sending with Discord embeds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        embeds = [{"title": "Test", "description": "Embed content"}]
        self.notifier.send("Test message", embeds=embeds)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["content"], "Test message")
        self.assertEqual(payload["embeds"], embeds)

    @patch("notifications.requests.post")
    def test_send_error_handling(self, mock_post):
        """Test error handling on failed send."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Should not raise exception
        self.notifier.send("Test message")

    @patch("notifications.requests.post")
    def test_send_not_configured(self, mock_post):
        """Test send when not configured."""
        notifier = DiscordNotifier(None)
        notifier.send("Test message")

        # Should not call post
        mock_post.assert_not_called()

    @patch("notifications.requests.post")
    def test_alert_ticker_selection(self, mock_post):
        """Test ticker selection alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        metrics = {
            "premarket_volume": 75.0,
            "gap_percent": 50.0,
            "iv_rank": 80.0,
        }

        self.notifier.alert_ticker_selection("AAPL", 85.5, metrics)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        content = call_args[1]["json"]["content"]

        self.assertIn("AAPL", content)
        self.assertIn("85.5", content)
        self.assertIn("premarket_volume", content)

    @patch("notifications.requests.post")
    def test_alert_signal(self, mock_post):
        """Test signal alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.notifier.alert_signal("AAPL", "call", "EMA crossover with RSI confirmation")

        call_args = mock_post.call_args
        content = call_args[1]["json"]["content"]

        self.assertIn("AAPL", content)
        self.assertIn("CALL", content)
        self.assertIn("EMA crossover", content)

    @patch("notifications.requests.post")
    def test_alert_order_filled(self, mock_post):
        """Test order filled alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.notifier.alert_order_filled(
            ticker="AAPL",
            option_symbol="AAPL_240115C00150000",
            direction="call",
            contracts=10,
            fill_price=5.25,
        )

        call_args = mock_post.call_args
        content = call_args[1]["json"]["content"]

        self.assertIn("AAPL", content)
        self.assertIn("CALL", content)
        self.assertIn("10", content)
        self.assertIn("5.25", content)

    @patch("notifications.requests.post")
    def test_alert_exit(self, mock_post):
        """Test exit alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.notifier.alert_exit(
            ticker="AAPL",
            option_symbol="AAPL_240115C00150000",
            contracts=10,
            exit_price=6.00,
            pnl_pct=14.3,
            reason="profit target",
        )

        call_args = mock_post.call_args
        content = call_args[1]["json"]["content"]

        self.assertIn("AAPL", content)
        self.assertIn("6.00", content)
        self.assertIn("14.3", content)
        self.assertIn("profit target", content)

    @patch("notifications.requests.post")
    def test_alert_error(self, mock_post):
        """Test error alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        test_error = ValueError("Test error message")
        self.notifier.alert_error("trade execution", test_error)

        call_args = mock_post.call_args
        content = call_args[1]["json"]["content"]

        self.assertIn("trade execution", content)
        self.assertIn("Test error message", content)


if __name__ == "__main__":
    unittest.main()
