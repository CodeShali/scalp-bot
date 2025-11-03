import logging
from typing import Any, Dict, Optional

import requests


class DiscordNotifier:
    """Simple Discord webhook integration for bot alerts."""

    def __init__(self, webhook_url: Optional[str]) -> None:
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send(self, message: str, embeds: Optional[list] = None) -> None:
        if not self.is_configured():
            self.logger.debug("Discord webhook not configured; skipping message: %s", message)
            return

        payload: Dict[str, Any] = {"content": message}
        if embeds:
            payload["embeds"] = embeds

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            if response.status_code >= 400:
                self.logger.error(
                    "Failed to post Discord message (%s): %s", response.status_code, response.text
                )
        except requests.RequestException as exc:
            self.logger.exception("Error sending Discord notification: %s", exc)

    def alert_ticker_selection(self, ticker: str, score: float, metrics: Dict[str, float], active_tickers: list = None) -> None:
        # Build description with all active tickers
        if active_tickers and len(active_tickers) > 1:
            description = f"**Top {len(active_tickers)} tickers** selected for monitoring:\n\n"
            for t in active_tickers:
                emoji = "🥇" if t['rank'] == 1 else "🥈" if t['rank'] == 2 else "🥉"
                description += f"{emoji} **#{t['rank']}: {t['symbol']}** (Score: {t['score']:.3f})\n"
        else:
            description = f"**{ticker}** has been selected for today's trading"
        
        embed = {
            "title": "🎯 Active Tickers Selected" if active_tickers and len(active_tickers) > 1 else "🎯 Ticker of the Day Selected",
            "description": description,
            "color": 3447003,  # Blue
            "fields": [
                {"name": "📊 Primary Score", "value": f"`{score:.3f}`", "inline": True},
                {"name": "📈 Monitoring", "value": f"`{len(active_tickers) if active_tickers else 1} ticker(s)`", "inline": True},
            ],
            "footer": {"text": "TARA | Pre-Market Scan"},
            "timestamp": self._get_timestamp()
        }
        self.send("", embeds=[embed])

    def alert_signal(self, ticker: str, direction: str, reason: str) -> None:
        color = 5763719 if direction.lower() == 'call' else 15548997  # Green for calls, red for puts
        emoji = "📈" if direction.lower() == 'call' else "📉"
        embed = {
            "title": f"{emoji} Trading Signal Detected",
            "description": f"**{ticker}** - {direction.upper()}",
            "color": color,
            "fields": [
                {"name": "Direction", "value": f"`{direction.upper()}`", "inline": True},
                {"name": "Reason", "value": reason, "inline": False},
            ],
            "footer": {"text": "Scalp Bot | Signal Generator"},
            "timestamp": self._get_timestamp()
        }
        self.send("", embeds=[embed])

    def alert_order_filled(
        self,
        ticker: str,
        option_symbol: str,
        direction: str,
        contracts: int,
        fill_price: float,
    ) -> None:
        embed = {
            "title": "✅ Order Filled",
            "description": f"Successfully entered position in **{ticker}**",
            "color": 3066993,  # Green
            "fields": [
                {"name": "📋 Contract", "value": f"`{option_symbol}`", "inline": False},
                {"name": "📊 Direction", "value": f"`{direction.upper()}`", "inline": True},
                {"name": "🔢 Quantity", "value": f"`{contracts}x`", "inline": True},
                {"name": "💰 Fill Price", "value": f"`${fill_price:.2f}`", "inline": True},
                {"name": "💵 Total Cost", "value": f"`${fill_price * contracts * 100:.2f}`", "inline": True},
            ],
            "footer": {"text": "Scalp Bot | Order Execution"},
            "timestamp": self._get_timestamp()
        }
        self.send("", embeds=[embed])

    def alert_exit(
        self,
        ticker: str,
        option_symbol: str,
        contracts: int,
        exit_price: float,
        pnl_pct: float,
        reason: str,
    ) -> None:
        color = 3066993 if pnl_pct >= 0 else 15158332  # Green for profit, red for loss
        emoji = "🎉" if pnl_pct >= 0 else "⚠️"
        status = "PROFIT" if pnl_pct >= 0 else "LOSS"
        
        embed = {
            "title": f"{emoji} Position Closed - {status}",
            "description": f"Exited position in **{ticker}**",
            "color": color,
            "fields": [
                {"name": "📋 Contract", "value": f"`{option_symbol}`", "inline": False},
                {"name": "🔢 Quantity", "value": f"`{contracts}x`", "inline": True},
                {"name": "💰 Exit Price", "value": f"`${exit_price:.2f}`", "inline": True},
                {"name": "📊 P/L", "value": f"`{pnl_pct:+.2f}%`", "inline": True},
                {"name": "📝 Exit Reason", "value": reason, "inline": False},
            ],
            "footer": {"text": "Scalp Bot | Position Management"},
            "timestamp": self._get_timestamp()
        }
        self.send("", embeds=[embed])

    def alert_error(self, context: str, error: Exception) -> None:
        embed = {
            "title": "🚨 Error Alert",
            "description": f"An error occurred in **{context}**",
            "color": 15158332,  # Red
            "fields": [
                {"name": "Error Type", "value": f"`{type(error).__name__}`", "inline": True},
                {"name": "Error Message", "value": f"```{str(error)[:1000]}```", "inline": False},
            ],
            "footer": {"text": "Scalp Bot | Error Handler"},
            "timestamp": self._get_timestamp()
        }
        self.send("", embeds=[embed])
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format for Discord embeds."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
