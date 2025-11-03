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

    def alert_ticker_selection(self, ticker: str, score: float, metrics: Dict[str, float]) -> None:
        message = f"**Ticker of the Day:** {ticker}\nScore: {score:.3f}\n" + "\n".join(
            f"{key}: {value:.3f}" for key, value in metrics.items()
        )
        self.send(message)

    def alert_signal(self, ticker: str, direction: str, reason: str) -> None:
        self.send(f"Signal detected for {ticker}: **{direction.upper()}** ({reason})")

    def alert_order_filled(
        self,
        ticker: str,
        option_symbol: str,
        direction: str,
        contracts: int,
        fill_price: float,
    ) -> None:
        message = (
            f"Order filled: {direction.upper()} {contracts}x {option_symbol} ({ticker})\n"
            f"Fill price: ${fill_price:.2f}"
        )
        self.send(message)

    def alert_exit(
        self,
        ticker: str,
        option_symbol: str,
        contracts: int,
        exit_price: float,
        pnl_pct: float,
        reason: str,
    ) -> None:
        message = (
            f"Exit triggered for {option_symbol} ({ticker})\n"
            f"Contracts: {contracts}\n"
            f"Exit price: ${exit_price:.2f}\n"
            f"P/L: {pnl_pct:.2f}%\n"
            f"Reason: {reason}"
        )
        self.send(message)

    def alert_error(self, context: str, error: Exception) -> None:
        self.send(f"Error in {context}: {error}")
