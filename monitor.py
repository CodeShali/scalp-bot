import logging
from datetime import datetime
from typing import Any, Dict, Optional

from broker import BrokerClient
from notifications import DiscordNotifier
from signals import SignalDetector
from utils import EASTERN_TZ, ensure_timezone, minutes_between, read_state, update_state, append_trade_log


class PositionMonitor:
    """Monitors open option positions and enforces exit rules."""

    def __init__(
        self,
        broker: BrokerClient,
        notifier: DiscordNotifier,
        signal_detector: SignalDetector,
        config: Dict[str, Any],
    ) -> None:
        self.broker = broker
        self.notifier = notifier
        self.signal_detector = signal_detector
        self.config = config
        self.trading_cfg = config.get("trading", {})
        self.logger = logging.getLogger(__name__)

    def evaluate(self) -> None:
        self.logger.info("👀 Checking for open positions...")
        state = read_state()
        position_state = state.get("open_position")
        if not position_state:
            self.logger.info("✅ No open positions to monitor")
            return

        option_symbol = position_state.get("option_symbol")
        entry_price = position_state.get("entry_price")
        direction = position_state.get("direction")
        contracts = position_state.get("contracts", 0)
        ticker = position_state.get("ticker")
        entry_time = ensure_timezone(datetime.fromisoformat(position_state["entry_time"]))

        self.logger.info(f"📊 Monitoring {ticker} {option_symbol}: {contracts} contracts @ ${entry_price:.2f}")
        
        current_price = self.broker.get_option_market_price(option_symbol)
        if current_price is None:
            self.logger.warning(f"⚠️ No option price available for {option_symbol}")
            return

        pnl_pct = (current_price - entry_price) / entry_price * 100.0
        pnl_dollar = (current_price - entry_price) * contracts * 100
        
        self.logger.info(f"💰 Current P/L: {pnl_pct:+.2f}% (${pnl_dollar:+.2f}) | Price: ${current_price:.2f}")

        reason = self._exit_reason(
            ticker=ticker,
            direction=direction,
            entry_time=entry_time,
            pnl_pct=pnl_pct,
        )
        if not reason:
            return

        self.logger.info(
            "Exit triggered for %s (reason=%s, pnl=%.2f%%)", option_symbol, reason, pnl_pct
        )
        self._close_position(option_symbol, contracts)

        trade_record = {
            "timestamp": datetime.now(EASTERN_TZ).isoformat(),
            "ticker": ticker,
            "direction": direction,
            "strike": position_state.get("strike"),
            "expiration": position_state.get("expiration"),
            "entry_price": entry_price,
            "exit_price": current_price,
            "contracts": contracts,
            "pnl_pct": pnl_pct,
            "exit_reason": reason,
        }
        append_trade_log(trade_record)

        self.notifier.alert_exit(
            ticker=ticker,
            option_symbol=option_symbol,
            contracts=contracts,
            exit_price=current_price,
            pnl_pct=pnl_pct,
            reason=reason,
        )

        state["open_position"] = None
        update_state(state)

    # -------------------- Helpers --------------------
    def _exit_reason(
        self,
        ticker: str,
        direction: str,
        entry_time: datetime,
        pnl_pct: float,
    ) -> Optional[str]:
        profit_target_pct = self.trading_cfg.get("profit_target_pct", 0.15) * 100
        stop_loss_pct = self.trading_cfg.get("stop_loss_pct", 0.07) * 100
        timeout_seconds = self.trading_cfg.get("timeout_seconds", 300)
        end_of_day_exit = self.trading_cfg.get("end_of_day_exit", "15:55")

        now = datetime.now(EASTERN_TZ)
        elapsed_minutes = minutes_between(entry_time, now)

        if pnl_pct >= profit_target_pct:
            return "profit target"
        if pnl_pct <= -stop_loss_pct:
            return "stop loss"
        if self.signal_detector.has_reversal(ticker, direction):
            return "ema reversal"
        if elapsed_minutes * 60 >= timeout_seconds:
            return "timeout"

        eod_hour, eod_minute = map(int, end_of_day_exit.split(":"))
        if now.hour > eod_hour or (now.hour == eod_hour and now.minute >= eod_minute):
            return "end of day"
        return None

    def _close_position(self, option_symbol: str, contracts: int) -> None:
        try:
            self.broker.submit_order(
                symbol=option_symbol,
                qty=contracts,
                side="sell",
                type_="market",
                time_in_force="day",
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Failed to close position %s: %s", option_symbol, exc)
            self.notifier.alert_error("close_position", exc)
    
    def _force_close(self, reason: str = "manual_close") -> None:
        """Force close the current position immediately."""
        state = read_state()
        position_state = state.get("open_position")
        if not position_state:
            return
        
        option_symbol = position_state.get("option_symbol")
        contracts = position_state.get("contracts", 0)
        ticker = position_state.get("ticker")
        entry_price = position_state.get("entry_price")
        direction = position_state.get("direction")
        
        # Get current price
        current_price = self.broker.get_option_market_price(option_symbol)
        if current_price is None:
            current_price = entry_price  # Fallback to entry price
        
        pnl_pct = (current_price - entry_price) / entry_price * 100.0
        
        self.logger.warning("Force closing position: %s (reason: %s)", option_symbol, reason)
        self._close_position(option_symbol, contracts)
        
        # Log the trade
        trade_record = {
            "timestamp": datetime.now(EASTERN_TZ).isoformat(),
            "ticker": ticker,
            "direction": direction,
            "strike": position_state.get("strike"),
            "expiration": position_state.get("expiration"),
            "entry_price": entry_price,
            "exit_price": current_price,
            "contracts": contracts,
            "pnl_pct": pnl_pct,
            "exit_reason": reason,
        }
        append_trade_log(trade_record)
        
        # Send notification
        self.notifier.alert_exit(
            ticker=ticker,
            option_symbol=option_symbol,
            contracts=contracts,
            exit_price=current_price,
            pnl_pct=pnl_pct,
            reason=reason,
        )
        
        # Clear position from state
        state["open_position"] = None
        update_state(state)
