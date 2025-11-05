import logging
import os
import signal
import sys
import threading
import time
import hmac
import hashlib
import subprocess
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, render_template, jsonify, request
import pandas as pd

from broker import BrokerClient
from monitor import PositionMonitor
from notifications import DiscordNotifier
from scan import TickerScanner
from signals import SignalDetector
from utils import (
    EASTERN_TZ,
    ensure_directories,
    load_config,
    read_state,
    setup_logging,
    update_state,
)

logger = logging.getLogger(__name__)

# Flask app for web dashboard
app = Flask(__name__)
app.config['SECRET_KEY'] = 'scalp-bot-dashboard-secret'
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reload
app.jinja_env.auto_reload = True

# Suppress Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class ScalpingBot:
    """Top-level orchestrator for the options scalping workflow."""

    _instance = None  # Singleton for dashboard access

    def __init__(self) -> None:
        ensure_directories()
        self.config = load_config()
        setup_logging(self.config)
        
        ScalpingBot._instance = self  # Store for dashboard access
        
        # Initialize ngrok management
        self.ngrok_process = None
        self.ngrok_url = None
        self._ensure_ngrok_running()
        
        self.notifier = DiscordNotifier(self.config)

        self.broker = BrokerClient(self.config)
        self.scanner = TickerScanner(self.broker, self.notifier, self.config)
        self.signal_detector = SignalDetector(self.broker, self.notifier, self.config)
        self.monitor = PositionMonitor(self.broker, self.notifier, self.signal_detector, self.config)

        self.scheduler = BackgroundScheduler(timezone=EASTERN_TZ)
        
        # Circuit breaker for error tracking
        self.error_window = deque(maxlen=10)  # Track last 10 errors
        self.circuit_breaker_threshold = 5  # Trip after 5 errors in window
        self.circuit_open = False
        
        # Manual controls
        self.paused = False
        
        # Daily tracking for safety limits
        self.daily_reset_date = None
        self.daily_trades_count = 0
        self.daily_pnl_pct = 0.0
        self.daily_loss_limit_hit = False
        
        self._register_jobs()
        self._log_startup_info()
    
    def _ensure_ngrok_running(self) -> None:
        """Start ngrok and get its URL."""
        import subprocess
        import requests
        import time
        
        try:
            # Check if ngrok already running
            try:
                response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
                if response.status_code == 200:
                    tunnels = response.json().get("tunnels", [])
                    https_tunnels = [t for t in tunnels if t.get("proto") == "https"]
                    if https_tunnels:
                        self.ngrok_url = https_tunnels[0].get("public_url")
                        logger.info("✅ ngrok already running: %s", self.ngrok_url)
                        return
            except:
                pass
            
            # Kill any old ngrok processes
            logger.info("Starting ngrok tunnel...")
            try:
                subprocess.run(["pkill", "-9", "ngrok"], stderr=subprocess.DEVNULL)
                time.sleep(2)
            except:
                pass
            
            # Start ngrok with browser warning skip
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "http", "8001", "--host-header", "rewrite"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # Wait for tunnel to establish
            for attempt in range(10):
                try:
                    response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
                    if response.status_code == 200:
                        tunnels = response.json().get("tunnels", [])
                        https_tunnels = [t for t in tunnels if t.get("proto") == "https"]
                        if https_tunnels:
                            self.ngrok_url = https_tunnels[0].get("public_url")
                            logger.info("✅ ngrok tunnel started: %s", self.ngrok_url)
                            return
                except:
                    pass
                time.sleep(2)
            
            # Failed to start
            logger.warning("ngrok failed to start, using localhost")
            self.ngrok_url = "http://localhost:8001"
            
        except FileNotFoundError:
            logger.warning("ngrok not installed, using localhost")
            self.ngrok_url = "http://localhost:8001"
        except Exception as e:
            logger.error("Error starting ngrok: %s", e)
            self.ngrok_url = "http://localhost:8001"
    
    def _stop_ngrok(self) -> None:
        """Stop ngrok process."""
        if self.ngrok_process:
            try:
                logger.info("Stopping ngrok...")
                os.killpg(os.getpgid(self.ngrok_process.pid), signal.SIGTERM)
                self.ngrok_process.wait(timeout=5)
                logger.info("ngrok stopped")
            except Exception as e:
                logger.warning("Error stopping ngrok: %s", e)
                try:
                    self.ngrok_process.kill()
                except:
                    pass
    
    def _get_dashboard_url(self) -> str:
        """Return the dashboard URL (managed by ngrok service)."""
        return self.ngrok_url or "http://localhost:8001"
    
    def _log_startup_info(self) -> None:
        """Log bot configuration and status at startup."""
        logger.info("========================================")
        logger.info("Options Scalping Bot Starting")
        logger.info("========================================")
        logger.info("Mode: %s", self.config.get("mode"))
        logger.info("Watchlist: %s", self.config.get("watchlist", {}).get("symbols", []))
        logger.info("Trading windows: %s", self.config.get("signals", {}).get("trading_windows", []))
        logger.info("Risk per trade: %.1f%%", self.config.get("trading", {}).get("max_risk_pct", 0.01) * 100)
        logger.info("Profit target: %.1f%%", self.config.get("trading", {}).get("profit_target_pct", 0.15) * 100)
        logger.info("Stop loss: %.1f%%", self.config.get("trading", {}).get("stop_loss_pct", 0.07) * 100)
        logger.info("Market hours: Mon-Fri 9:30 AM - 4:00 PM ET (monitoring only)")
        logger.info("========================================")
        
        # Auto-detect and set dashboard URL
        dashboard_url = self._get_dashboard_url()
        if 'dashboard' not in self.config:
            self.config['dashboard'] = {}
        self.config['dashboard']['public_url'] = dashboard_url
        
        # Reinitialize notifier with updated config (including dashboard URL)
        self.notifier = DiscordNotifier(self.config)
        
        # Update notifier references in all components
        self.scanner.notifier = self.notifier
        self.signal_detector.notifier = self.notifier
        self.monitor.notifier = self.notifier
        
        # Send startup notification with dashboard link
        if self.notifier.is_configured():
            # Get next scan time
            scanning_cfg = self.config.get("scanning", {})
            run_time = scanning_cfg.get("run_time", "08:30")
            next_scan = f"Tomorrow at {run_time} ET" if datetime.now(EASTERN_TZ).hour > 8 else f"Today at {run_time} ET"
            
            self.notifier.alert_startup(
                mode=self.config.get("mode", "paper"),
                next_scan_time=next_scan
            )

    def _register_jobs(self) -> None:
        scanning_cfg = self.config.get("scanning", {})
        run_time = scanning_cfg.get("run_time", "08:30")
        hour, minute = map(int, run_time.split(":"))

        self.scheduler.add_job(
            self._run_premarket_scan,
            CronTrigger(hour=hour, minute=minute, timezone=EASTERN_TZ),
            name="pre-market-scan",
            max_instances=1,
        )

        signal_interval = self.config.get("signals", {}).get("poll_interval_seconds", 15)
        self.scheduler.add_job(
            self._poll_for_signals,
            "interval",
            seconds=signal_interval,
            next_run_time=datetime.now(EASTERN_TZ),
            name="signal-evaluator",
            max_instances=1,
        )

        monitor_interval = self.config.get("trading", {}).get("monitor_interval_seconds", 5)
        self.scheduler.add_job(
            self._monitor_position,
            "interval",
            seconds=monitor_interval,
            next_run_time=datetime.now(EASTERN_TZ),
            name="position-monitor",
            max_instances=1,
        )

    def start(self) -> None:
        logger.info("Starting scalping bot scheduler")
        self.scheduler.start()
        self._install_signal_handlers()
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutdown requested; stopping scheduler")
            self.scheduler.shutdown(wait=False)

    def _install_signal_handlers(self) -> None:
        def _handle_signal(signum: int, frame: Optional[Any]) -> None:  # noqa: ANN401
            logger.info("Received signal %s; shutting down", signum)
            self.scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

    # -------------------- Scheduled Tasks --------------------
    def _run_premarket_scan(self) -> None:
        """Run the pre-market scan with error tracking."""
        if self.circuit_open:
            logger.warning("Circuit breaker open; skipping pre-market scan")
            return
        
        try:
            logger.info("Starting pre-market scan")
            result = self.scanner.run()
            if result:
                logger.info("Scan completed: selected %s with score %.2f", 
                           result['symbol'], result['score'])
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pre-market scan failed: %s", exc)
            self.notifier.alert_error("pre-market scan", exc)
            self._record_error("scan")

    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (Mon-Fri 9:30 AM - 4:00 PM ET)."""
        now = datetime.now(EASTERN_TZ)
        
        # Check if weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check if within trading hours (9:30 AM - 4:00 PM)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def _calculate_daily_stats(self) -> tuple[int, float]:
        """Calculate today's trade count and P/L from trades.csv.
        
        Returns:
            (trade_count, total_pnl_pct)
        """
        from pathlib import Path
        try:
            csv_path = Path('data/trades.csv')
            if not csv_path.exists():
                return 0, 0.0
            
            df = pd.read_csv(csv_path)
            if len(df) == 0:
                return 0, 0.0
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            today = datetime.now(EASTERN_TZ).date()
            today_trades = df[df['timestamp'].dt.date == today]
            
            trade_count = len(today_trades)
            # Sum P/L as decimals (e.g., 0.05 for 5%)
            total_pnl_pct = today_trades['pnl_pct'].sum() / 100.0 if trade_count > 0 else 0.0
            
            return trade_count, total_pnl_pct
        except Exception as exc:
            logger.error("Error calculating daily stats: %s", exc)
            return 0, 0.0
    
    def _reset_daily_limits_if_needed(self) -> None:
        """Reset daily counters if it's a new trading day."""
        today = datetime.now(EASTERN_TZ).date()
        if self.daily_reset_date != today:
            self.daily_reset_date = today
            # Recalculate from trades.csv
            self.daily_trades_count, self.daily_pnl_pct = self._calculate_daily_stats()
            self.daily_loss_limit_hit = False
            logger.info("Daily limits reset for %s - %d trades, %.2f%% P/L from history", 
                       today, self.daily_trades_count, self.daily_pnl_pct * 100)
    
    def _check_daily_limits(self) -> tuple[bool, Optional[str]]:
        """Check if daily trading limits allow a new trade.
        
        Returns:
            (allowed, reason) - True if allowed, False with reason if not
        """
        self._reset_daily_limits_if_needed()
        
        # Recalculate from CSV to get latest data
        self.daily_trades_count, self.daily_pnl_pct = self._calculate_daily_stats()
        
        # Check max trades per day
        max_trades = self.config.get("trading", {}).get("max_trades_per_day", 999)
        if self.daily_trades_count >= max_trades:
            return False, f"Daily trade limit reached ({max_trades} trades)"
        
        # Check daily loss limit
        max_loss_pct = self.config.get("trading", {}).get("max_daily_loss_pct", 0.10)
        if self.daily_pnl_pct <= -max_loss_pct:
            if not self.daily_loss_limit_hit:
                self.daily_loss_limit_hit = True
                logger.error("Daily loss limit hit: %.2f%% (limit: %.2f%%)", 
                           self.daily_pnl_pct * 100, max_loss_pct * 100)
                self.notifier.send(
                    f"🛑 **DAILY LOSS LIMIT HIT**\n"
                    f"Loss: {self.daily_pnl_pct * 100:.2f}%\n"
                    f"Limit: {max_loss_pct * 100:.2f}%\n"
                    f"Trading suspended for today"
                )
            return False, f"Daily loss limit hit ({self.daily_pnl_pct*100:.2f}%)"
        
        return True, None
    
    def pause_trading(self) -> None:
        """Pause automated trading."""
        self.paused = True
        logger.warning("Trading PAUSED by user")
        self.notifier.send("⏸️ **Trading PAUSED**")
    
    def resume_trading(self) -> None:
        """Resume automated trading."""
        self.paused = False
        logger.info("Trading RESUMED by user")
        self.notifier.send("▶️ **Trading RESUMED**")
    
    def force_close_position(self) -> bool:
        """Force close current position immediately.
        
        Returns:
            True if position was closed, False if no position or error
        """
        try:
            state = read_state()
            position = state.get("open_position")
            if not position:
                logger.warning("No position to force close")
                return False
            
            logger.warning("Force closing position: %s", position['ticker'])
            self.notifier.send(f"🚨 **FORCE CLOSING** {position['ticker']}")
            
            # Use monitor to close position
            self.monitor._force_close(reason="manual_force_close")
            return True
        except Exception as exc:
            logger.exception("Error force closing position: %s", exc)
            return False
    
    def _poll_for_signals(self) -> None:
        """Poll for trading signals with circuit breaker."""
        # Skip if market is closed
        if not self._is_market_hours():
            logger.debug("Market closed - skipping signal evaluation")
            return
        
        # Skip if paused
        if self.paused:
            logger.debug("Bot is paused - skipping signal evaluation")
            return
        
        # Skip if circuit breaker open
        if self.circuit_open:
            logger.debug("Circuit breaker open; skipping signal poll")
            return
        
        # Check daily limits
        allowed, reason = self._check_daily_limits()
        if not allowed:
            logger.debug("Daily limit check failed: %s", reason)
            return
        
        try:
            state = read_state()
            
            # Get all active tickers (fallback to single ticker for backward compatibility)
            active_tickers = state.get("active_tickers", [])
            if not active_tickers:
                # Fallback to old single ticker approach
                ticker = state.get("ticker_of_the_day")
                if ticker:
                    active_tickers = [{"symbol": ticker, "rank": 1}]
            
            if not active_tickers:
                return

            open_position = state.get("open_position")
            if open_position:
                return

            # Check each active ticker for signals (in rank order)
            for ticker_info in active_tickers:
                ticker = ticker_info["symbol"]
                rank = ticker_info.get("rank", 1)
                
                signal_payload = self.signal_detector.evaluate(ticker)
                if signal_payload:
                    logger.info("Signal detected on #%d ticker %s: %s at %.2f", 
                               rank, ticker, signal_payload['direction'].upper(), signal_payload['price'])
                    self._execute_trade(signal_payload)
                    break  # Only take first signal
                    
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error while evaluating signals: %s", exc)
            self.notifier.alert_error("signal evaluation", exc)
            self._record_error("signal")
    
    def _monitor_position(self) -> None:
        """Monitor open positions (only during market hours)."""
        # Skip if market is closed
        if not self._is_market_hours():
            logger.debug("Market closed - skipping position monitoring")
            return
        
        try:
            self.monitor.evaluate()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error during position monitoring: %s", exc)
            self.notifier.alert_error("position monitoring", exc)

    # -------------------- Trade Execution --------------------
    def _execute_trade(self, signal_payload: Dict[str, Any]) -> None:
        """Execute a trade with comprehensive error handling."""
        try:
            logger.info("Executing trade for signal: %s", signal_payload)
            
            option_contract = self._select_option_contract(signal_payload)
            if not option_contract:
                logger.warning("No suitable option contract found for %s", signal_payload['symbol'])
                return

            option_price = option_contract["price"]
            contracts = self._calculate_contract_quantity(option_price)
            if contracts <= 0:
                logger.warning("Insufficient funds for trade (price: %.2f)", option_price)
                return

            logger.info("Placing order: %s %dx at $%.2f", 
                       option_contract["symbol"], contracts, option_price)
            
            option_symbol = option_contract["symbol"]
            order = self.broker.submit_order(
                symbol=option_symbol,
                qty=contracts,
                side="buy",
                type_="market",
                time_in_force="day",
            )
            
            filled_order = self._wait_for_fill(order.get("id"))
            if not filled_order or float(filled_order.get("filled_qty", 0)) <= 0:
                logger.warning("Order not filled within timeout, canceling")
                try:
                    self.broker.cancel_order(order.get("id"))
                except Exception as cancel_exc:
                    logger.error("Failed to cancel order: %s", cancel_exc)
                return

            fill_price = float(filled_order.get("filled_avg_price") or option_price)
            logger.info("Order filled: %dx %s at $%.2f", contracts, option_symbol, fill_price)
            
            self.notifier.alert_order_filled(
                ticker=signal_payload["symbol"],
                option_symbol=option_symbol,
                direction=signal_payload["direction"],
                contracts=contracts,
                fill_price=fill_price,
            )

            state_update = {
                "open_position": {
                    "ticker": signal_payload["symbol"],
                    "direction": signal_payload["direction"],
                    "option_symbol": option_symbol,
                    "strike": option_contract["strike"],
                    "expiration": option_contract["expiration"],
                    "contracts": contracts,
                    "entry_price": fill_price,
                    "entry_time": datetime.now(EASTERN_TZ).isoformat(),
                    "order_id": order.get("id"),
                }
            }
            update_state(state_update)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Trade execution failed: %s", exc)
            self.notifier.alert_error("trade execution", exc)
            self._record_error("trade")

    def _select_option_contract(self, signal_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        symbol = signal_payload["symbol"]
        direction = signal_payload["direction"]
        underlying_price = self.broker.get_current_price(symbol)
        chain = self.broker.get_option_chain(symbol)
        if not chain:
            return None

        trading_cfg = self.config.get("trading", {})
        max_dte_days = trading_cfg.get("max_option_dte_days", 1)
        now = datetime.utcnow()
        candidates = []
        for option in chain:
            option_type = str(option.get("type") or option.get("option_type") or option.get("option_type"))
            if not option_type:
                continue
            option_type = option_type.lower()
            if direction == "call" and option_type not in {"call", "c"}:
                continue
            if direction == "put" and option_type not in {"put", "p"}:
                continue

            strike_raw = option.get("strike") or option.get("strike_price")
            if strike_raw is None:
                continue
            strike = float(strike_raw)

            expiration_raw = option.get("expiration") or option.get("expiration_date")
            if not expiration_raw:
                continue
            try:
                expiration = datetime.fromisoformat(expiration_raw)
            except ValueError:
                continue
            dte = max((expiration - now).total_seconds() / 86400.0, 0)
            if dte > max_dte_days + 0.1:
                continue

            penalty = self._strike_penalty(direction, strike, underlying_price)
            if penalty is None:
                continue

            price = self._infer_option_price(option)
            if price is None or price <= 0:
                continue

            candidates.append(
                {
                    "symbol": option.get("symbol"),
                    "strike": strike,
                    "expiration": expiration_raw,
                    "price": price,
                    "dte": dte,
                    "penalty": penalty,
                }
            )

        if not candidates:
            return None

        candidates.sort(key=lambda opt: (abs(opt["dte"]), opt["penalty"]))
        return candidates[0]

    def _strike_penalty(self, direction: str, strike: float, underlying_price: float) -> Optional[float]:
        trading_cfg = self.config.get("trading", {})
        max_otm_pct = trading_cfg.get("max_otm_pct", 0.02)
        atm_tolerance_pct = trading_cfg.get("atm_tolerance_pct", 0.005)
        if underlying_price <= 0:
            return None

        diff = strike - underlying_price
        tolerance = underlying_price * atm_tolerance_pct
        otm_limit = underlying_price * max_otm_pct

        if direction == "call":
            if diff < -tolerance:
                return None  # materially ITM
            if diff > otm_limit:
                return None
            return abs(diff)

        if direction == "put":
            diff = underlying_price - strike
            if diff < -tolerance:
                return None
            if diff > otm_limit:
                return None
            return abs(diff)

        return None

    def _infer_option_price(self, option: Dict[str, Any]) -> Optional[float]:
        ask = option.get("ask_price")
        bid = option.get("bid_price")
        last = option.get("last_price") or option.get("last_trade_price")
        if ask is not None and bid is not None and ask > 0 and bid > 0:
            return float((ask + bid) / 2)
        if ask is not None and ask > 0:
            return float(ask)
        if bid is not None and bid > 0:
            return float(bid)
        if last is not None and last > 0:
            return float(last)
        return None

    def _calculate_contract_quantity(self, option_price: float) -> int:
        cash_available = self.broker.get_cash_balance()
        max_risk_pct = self.config.get("trading", {}).get("max_risk_pct", 0.01)
        risk_capital = cash_available * max_risk_pct
        contract_cost = option_price * 100
        if contract_cost <= 0:
            return 0
        return int(risk_capital // contract_cost)

    def _wait_for_fill(self, order_id: Optional[str], timeout_seconds: int = 60) -> Optional[Dict[str, Any]]:
        if not order_id:
            return None
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            order = self.broker.get_order(order_id)
            if order.get("status") == "filled":
                return order
            time.sleep(2)
        return self.broker.get_order(order_id)


    def _record_error(self, context: str) -> None:
        """Record an error and check circuit breaker."""
        self.error_window.append(time.time())
        
        # Check if we should trip the circuit breaker
        if len(self.error_window) >= self.circuit_breaker_threshold:
            # Check if all errors occurred within last 5 minutes
            time_span = self.error_window[-1] - self.error_window[0]
            if time_span < 300:  # 5 minutes
                self.circuit_open = True
                logger.error("Circuit breaker tripped! Too many errors in %s context", context)
                self.notifier.send(
                    "⚠️ **CIRCUIT BREAKER ACTIVATED** ⚠️\n"
                    f"Context: {context}\n"
                    "Bot operations paused for safety. Manual intervention required."
                )
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        status = {
            "healthy": True,
            "circuit_open": self.circuit_open,
            "errors_in_window": len(self.error_window),
            "mode": self.config.get("mode"),
        }
        
        try:
            # Check broker connectivity
            self.broker.is_market_open()
            status["broker_connected"] = True
        except Exception as exc:
            logger.error("Health check failed: broker connectivity: %s", exc)
            status["broker_connected"] = False
            status["healthy"] = False
        
        try:
            # Check state file
            read_state()
            status["state_accessible"] = True
        except Exception as exc:
            logger.error("Health check failed: state file: %s", exc)
            status["state_accessible"] = False
            status["healthy"] = False
        
        return status
    
    def start_dashboard(self) -> None:
        """Start web dashboard in background thread."""
        def run_dashboard():
            logger.info("Starting web dashboard on port 8001")
            app.run(host='0.0.0.0', port=8001, debug=False, use_reloader=False)
        
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Give Flask a moment to start
        time.sleep(2)
        logger.info("Dashboard started on http://localhost:8001")
        logger.info("Public URL: %s", self.ngrok_url)


# ==================== Dashboard Routes ====================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """Get current bot status and overview."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    try:
        # Account info
        account = bot.broker.get_account()
        account_info = {
            'cash': float(account.get('cash', 0)),
            'buying_power': float(account.get('buying_power', 0)),
            'portfolio_value': float(account.get('portfolio_value', 0)),
            'equity': float(account.get('equity', 0)),
        }
    except Exception:
        account_info = {}
    
    # Current position
    state = read_state()
    position = state.get('open_position')
    
    if position:
        try:
            current_price = bot.broker.get_option_market_price(position['option_symbol'])
            if current_price:
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price * 100
                position['current_price'] = current_price
                position['pnl_pct'] = pnl_pct
        except Exception:
            pass
    
    # Ticker of day and active tickers
    ticker = state.get('ticker_of_the_day')
    ticker_info = None
    if ticker:
        ticker_info = {
            'symbol': ticker,
            'selection_time': state.get('ticker_selection_time'),
            'score': state.get('ticker_score', 0),
            'metrics': state.get('ticker_metrics', {})
        }
    
    # Get all active tickers
    active_tickers = state.get('active_tickers', [])
    
    # Today's trades
    from pathlib import Path
    from datetime import datetime
    today_trades = []
    try:
        csv_path = Path('data/trades.csv')
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            today = datetime.now(EASTERN_TZ).date()
            today_df = df[df['timestamp'].dt.date == today]
            today_trades = today_df.to_dict('records')
    except Exception:
        pass
    
    return jsonify({
        'bot': {
            'running': True,
            'status': 'Paused' if bot.paused else 'Running',
            'circuit_open': bot.circuit_open,
            'paused': bot.paused
        },
        'account': account_info,
        'position': position,
        'ticker_of_day': ticker_info,
        'active_tickers': active_tickers,
        'today_trades': today_trades,
        'config': {
            'watchlist': bot.config.get('watchlist', {}),
            'trading': bot.config.get('trading', {}),
            'signals': bot.config.get('signals', {}),
            'scanning': bot.config.get('scanning', {})
        },
        'timestamp': datetime.now(EASTERN_TZ).isoformat()
    })


@app.route('/api/performance')
def api_performance():
    """Get performance statistics."""
    from pathlib import Path
    try:
        csv_path = Path('data/trades.csv')
        if not csv_path.exists():
            return jsonify({'total_trades': 0})
        
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            return jsonify({'total_trades': 0})
        
        total_trades = len(df)
        wins = len(df[df['pnl_pct'] > 0])
        losses = len(df[df['pnl_pct'] < 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = df[df['pnl_pct'] > 0]['pnl_pct'].mean() if wins > 0 else 0
        avg_loss = df[df['pnl_pct'] < 0]['pnl_pct'].mean() if losses > 0 else 0
        avg_pnl = df['pnl_pct'].mean()
        total_pnl = df['pnl_pct'].sum()
        best_trade = df['pnl_pct'].max()
        worst_trade = df['pnl_pct'].min()
        
        return jsonify({
            'total_trades': int(total_trades),
            'wins': int(wins),
            'losses': int(losses),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'avg_pnl': float(avg_pnl),
            'total_pnl': float(total_pnl),
            'best_trade': float(best_trade),
            'worst_trade': float(worst_trade),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs')
def api_logs():
    """Get recent log lines."""
    from pathlib import Path
    lines = int(request.args.get('lines', 30))
    try:
        log_path = Path('logs/bot.log')
        if not log_path.exists():
            return jsonify([])
        
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            return jsonify(all_lines[-lines:])
    except Exception:
        return jsonify([])


@app.route('/api/controls/pause', methods=['POST'])
def api_pause():
    """Pause automated trading."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    bot.pause_trading()
    return jsonify({'status': 'paused', 'message': 'Trading paused successfully'})


@app.route('/api/controls/resume', methods=['POST'])
def api_resume():
    """Resume automated trading."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    bot.resume_trading()
    return jsonify({'status': 'resumed', 'message': 'Trading resumed successfully'})


@app.route('/api/controls/force_close', methods=['POST'])
def api_force_close():
    """Force close current position."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    success = bot.force_close_position()
    if success:
        return jsonify({'status': 'closed', 'message': 'Position closed successfully'})
    else:
        return jsonify({'status': 'failed', 'message': 'No position to close or error occurred'}), 400


@app.route('/api/market_status')
def api_market_status():
    """Get market status and timing information."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    now = datetime.now(EASTERN_TZ)
    is_open = bot._is_market_hours()
    
    # Calculate next market open
    next_open = None
    if not is_open:
        next_day = now
        while True:
            # Move to next day if after market close or weekend
            if next_day.weekday() >= 5 or next_day.hour >= 16:
                next_day = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
                next_day += timedelta(days=1)
            else:
                next_day = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
            
            # Skip weekends
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            
            break
        
        next_open = next_day.isoformat()
    
    # Next scan time (8:30 AM ET tomorrow if it's a weekday)
    next_scan = now.replace(hour=8, minute=30, second=0, microsecond=0)
    if now.hour >= 8 and now.minute >= 30:
        next_scan += timedelta(days=1)
    while next_scan.weekday() >= 5:
        next_scan += timedelta(days=1)
    
    return jsonify({
        'market_open': is_open,
        'current_time': now.isoformat(),
        'next_market_open': next_open,
        'next_scan': next_scan.isoformat(),
        'timezone': 'America/New_York'
    })


@app.route('/api/chart_data')
def api_chart_data():
    """Get performance chart data."""
    from pathlib import Path
    try:
        csv_path = Path('data/trades.csv')
        if not csv_path.exists():
            return jsonify({'trades': [], 'equity_curve': []})
        
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            return jsonify({'trades': [], 'equity_curve': []})
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate cumulative P/L for equity curve
        df['cumulative_pnl'] = df['pnl_pct'].cumsum()
        
        # Last 30 days of data
        cutoff = datetime.now(EASTERN_TZ) - timedelta(days=30)
        recent_df = df[df['timestamp'] > cutoff]
        
        equity_curve = recent_df[['timestamp', 'cumulative_pnl']].to_dict('records')
        
        # Group by day for daily P/L
        recent_df['date'] = recent_df['timestamp'].dt.date.astype(str)
        daily_pnl = recent_df.groupby('date')['pnl_pct'].sum().reset_index()
        daily_pnl.columns = ['date', 'pnl']
        
        return jsonify({
            'equity_curve': equity_curve,
            'daily_pnl': daily_pnl.to_dict('records')
        })
    except Exception as e:
        logger.error("Error generating chart data: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily_limits')
def api_daily_limits():
    """Get current daily limits status."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    # Get fresh stats
    trade_count, pnl_pct = bot._calculate_daily_stats()
    
    max_trades = bot.config.get("trading", {}).get("max_trades_per_day", 999)
    max_loss_pct = bot.config.get("trading", {}).get("max_daily_loss_pct", 0.10)
    
    return jsonify({
        'trades_today': trade_count,
        'max_trades': max_trades,
        'daily_pnl_pct': pnl_pct * 100,
        'max_loss_pct': max_loss_pct * 100,
        'loss_limit_hit': bot.daily_loss_limit_hit,
        'paused': bot.paused,
        'circuit_open': bot.circuit_open
    })


@app.route('/api/dashboard_url')
def api_dashboard_url():
    """Get dashboard URLs."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    return jsonify({
        'local': 'http://localhost:8001',
        'public': getattr(bot, 'dashboard_url', 'http://localhost:8001')
    })


@app.route('/api/portfolio/history')
def api_portfolio_history():
    """Get portfolio value history from Alpaca."""
    bot = ScalpingBot._instance
    if not bot or not bot.broker:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Get portfolio history from Alpaca
        # Alpaca provides portfolio history via portfolio_history endpoint
        timeframe = request.args.get('timeframe', '1D')
        
        # Map timeframe to Alpaca parameters
        timeframe_map = {
            '1D': {'period': '1D', 'timeframe': '5Min'},
            '1W': {'period': '1W', 'timeframe': '1H'},
            '1M': {'period': '1M', 'timeframe': '1D'},
            '3M': {'period': '3M', 'timeframe': '1D'},
            'ALL': {'period': '1A', 'timeframe': '1D'}
        }
        
        params = timeframe_map.get(timeframe, timeframe_map['1D'])
        
        # Get account info for current value
        account = bot.broker.trading_client.get_account()
        current_equity = float(account.equity)
        
        # Try to get portfolio history from Alpaca
        data = []
        try:
            history = bot.broker.trading_client.get_portfolio_history(
                period=params['period'],
                timeframe=params['timeframe']
            )
            
            # Format data for chart
            if history.timestamp and history.equity and len(history.timestamp) > 1:
                for i, timestamp in enumerate(history.timestamp):
                    dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                    equity = history.equity[i]
                    
                    # Format time based on timeframe
                    if timeframe == '1D':
                        time_str = dt.strftime('%H:%M')
                    elif timeframe in ['1W', '1M']:
                        time_str = dt.strftime('%b %d')
                    else:
                        time_str = dt.strftime('%b %y')
                    
                    data.append({
                        'time': time_str,
                        'value': float(equity) if equity else current_equity
                    })
        except Exception as e:
            logger.warning(f"Could not fetch portfolio history: {e}")
        
        # If insufficient data, create simple 2-point chart showing current value
        if len(data) < 2:
            logger.info(f"Portfolio history unavailable, showing current value only")
            # Show current value as flat line (start of period to now)
            now = datetime.now(pytz.timezone('US/Eastern'))
            
            if timeframe == '1D':
                start_time = now.replace(hour=9, minute=30, second=0)
                data = [
                    {'time': start_time.strftime('%H:%M'), 'value': current_equity},
                    {'time': now.strftime('%H:%M'), 'value': current_equity}
                ]
            elif timeframe == '1W':
                start_time = now - timedelta(days=7)
                data = [
                    {'time': start_time.strftime('%b %d'), 'value': current_equity},
                    {'time': now.strftime('%b %d'), 'value': current_equity}
                ]
            elif timeframe == '1M':
                start_time = now - timedelta(days=30)
                data = [
                    {'time': start_time.strftime('%b %d'), 'value': current_equity},
                    {'time': now.strftime('%b %d'), 'value': current_equity}
                ]
            elif timeframe == '3M':
                start_time = now - timedelta(days=90)
                data = [
                    {'time': start_time.strftime('%b %d'), 'value': current_equity},
                    {'time': now.strftime('%b %d'), 'value': current_equity}
                ]
            else:  # ALL
                start_time = now - timedelta(days=365)
                data = [
                    {'time': start_time.strftime('%b %y'), 'value': current_equity},
                    {'time': now.strftime('%b %y'), 'value': current_equity}
                ]
        
        return jsonify({
            'data': data,
            'current_value': current_equity,
            'timeframe': timeframe
        })
        
    except Exception as e:
        logger.error(f"Error fetching portfolio history: {e}")
        # Return current account value as fallback
        try:
            account = bot.broker.trading_client.get_account()
            current_equity = float(account.equity)
            return jsonify({
                'data': [{
                    'time': datetime.now().strftime('%H:%M'),
                    'value': current_equity
                }],
                'current_value': current_equity,
                'timeframe': timeframe
            })
        except:
            return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist')
def api_get_watchlist():
    """Get current watchlist."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    watchlist = bot.config.get('watchlist', {}).get('symbols', [])
    return jsonify({'watchlist': watchlist})


@app.route('/api/watchlist/add', methods=['POST'])
def api_add_to_watchlist():
    """Add ticker to watchlist."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    data = request.get_json()
    ticker = data.get('ticker', '').upper().strip()
    
    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400
    
    # Validate ticker format (basic check)
    if not ticker.isalpha() or len(ticker) > 5:
        return jsonify({'error': 'Invalid ticker format'}), 400
    
    # Get current watchlist
    if 'watchlist' not in bot.config:
        bot.config['watchlist'] = {}
    if 'symbols' not in bot.config['watchlist']:
        bot.config['watchlist']['symbols'] = []
    
    watchlist = bot.config['watchlist']['symbols']
    
    if ticker in watchlist:
        return jsonify({'error': f'{ticker} already in watchlist'}), 400
    
    # Add ticker
    watchlist.append(ticker)
    
    # Save to config file
    try:
        import yaml
        with open('config.yaml', 'w') as f:
            yaml.dump(bot.config, f, default_flow_style=False)
        
        logger.info("Added %s to watchlist", ticker)
        from datetime import datetime
        embed = {
            "title": "✅ Watchlist Updated",
            "description": f"Added **{ticker}** to watchlist",
            "color": 3066993,
            "fields": [
                {"name": "Ticker", "value": f"`{ticker}`", "inline": True},
                {"name": "Total Tickers", "value": f"`{len(watchlist)}`", "inline": True},
            ],
            "footer": {"text": "Scalp Bot | Watchlist Manager"},
            "timestamp": datetime.utcnow().isoformat()
        }
        bot.notifier.send("", embeds=[embed])
        
        return jsonify({
            'success': True,
            'message': f'{ticker} added to watchlist',
            'watchlist': watchlist
        })
    except Exception as exc:
        logger.error("Failed to update config: %s", exc)
        return jsonify({'error': 'Failed to save configuration'}), 500


@app.route('/api/watchlist/remove', methods=['POST'])
def api_remove_from_watchlist():
    """Remove ticker from watchlist."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    data = request.get_json()
    ticker = data.get('ticker', '').upper().strip()
    
    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400
    
    watchlist = bot.config.get('watchlist', {}).get('symbols', [])
    
    if ticker not in watchlist:
        return jsonify({'error': f'{ticker} not in watchlist'}), 400
    
    # Remove ticker
    watchlist.remove(ticker)
    
    # Save to config file
    try:
        import yaml
        with open('config.yaml', 'w') as f:
            yaml.dump(bot.config, f, default_flow_style=False)
        
        logger.info("Removed %s from watchlist", ticker)
        from datetime import datetime
        embed = {
            "title": "🗑️ Watchlist Updated",
            "description": f"Removed **{ticker}** from watchlist",
            "color": 15105570,
            "fields": [
                {"name": "Ticker", "value": f"`{ticker}`", "inline": True},
                {"name": "Total Tickers", "value": f"`{len(watchlist)}`", "inline": True},
            ],
            "footer": {"text": "Scalp Bot | Watchlist Manager"},
            "timestamp": datetime.utcnow().isoformat()
        }
        bot.notifier.send("", embeds=[embed])
        
        return jsonify({
            'success': True,
            'message': f'{ticker} removed from watchlist',
            'watchlist': watchlist
        })
    except Exception as exc:
        logger.error("Failed to update config: %s", exc)
        return jsonify({'error': 'Failed to save configuration'}), 500


@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Update bot configuration settings."""
    bot = ScalpingBot._instance
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    data = request.get_json()
    
    try:
        import yaml
        
        # Update trading settings
        if 'trading' in data:
            if 'trading' not in bot.config:
                bot.config['trading'] = {}
            bot.config['trading'].update(data['trading'])
        
        # Update signal settings
        if 'signals' in data:
            if 'signals' not in bot.config:
                bot.config['signals'] = {}
            bot.config['signals'].update(data['signals'])
        
        # Save to config file
        with open('config.yaml', 'w') as f:
            yaml.dump(bot.config, f, default_flow_style=False)
        
        logger.info("Settings updated successfully")
        bot.notifier.send("⚙️ **Settings Updated**\nConfiguration changes saved and applied.")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except Exception as exc:
        logger.error("Failed to update settings: %s", exc)
        return jsonify({'error': 'Failed to save settings'}), 500


@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook for auto-deploy."""
    try:
        bot = ScalpingBot._instance
        if not bot:
            return jsonify({'error': 'Bot not initialized'}), 503
        
        # Get secret from config
        secret = bot.config.get('webhook_secret', '')
        
        if not secret:
            logger.warning("Webhook secret not configured in config.yaml")
            return jsonify({'error': 'Webhook not configured'}), 500
        
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256')
        if signature:
            hash_object = hmac.new(
                secret.encode('utf-8'),
                msg=request.data,
                digestmod=hashlib.sha256
            )
            expected_signature = "sha256=" + hash_object.hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                logger.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 403
        
        # Get event type
        event = request.headers.get('X-GitHub-Event', 'ping')
        
        if event == 'ping':
            logger.info("✅ Received ping from GitHub webhook")
            return jsonify({'message': 'Pong!'}), 200
        
        if event == 'push':
            payload = request.json
            ref = payload.get('ref', '')
            commits = payload.get('commits', [])
            pusher = payload.get('pusher', {}).get('name', 'unknown')
            
            logger.info(f"📦 Push event received from {pusher}")
            logger.info(f"   Ref: {ref}")
            logger.info(f"   Commits: {len(commits)}")
            
            # Only deploy on push to main
            if ref == 'refs/heads/main':
                logger.info("🚀 Push to main detected - starting auto-deploy")
                
                # Send Discord notification
                bot.notifier.send(f"🔄 **Auto-Deploy Started**\nPushed by: {pusher}\nCommits: {len(commits)}")
                
                # Run git pull and restart in background
                def deploy():
                    try:
                        # Git pull
                        result = subprocess.run(
                            ['git', 'pull', 'origin', 'main'],
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            logger.info(f"✅ Git pull successful: {result.stdout}")
                            bot.notifier.send(f"✅ **Code Updated**\n```\n{result.stdout}\n```")
                            
                            # Restart service
                            logger.info("🔄 Restarting service...")
                            subprocess.run(
                                ['sudo', 'systemctl', 'restart', 'scalp-bot'],
                                timeout=30
                            )
                            logger.info("✅ Service restart initiated")
                            bot.notifier.send("🎉 **Auto-Deploy Complete**\nBot is restarting with new code!")
                        else:
                            logger.error(f"❌ Git pull failed: {result.stderr}")
                            bot.notifier.send(f"❌ **Deploy Failed**\n```\n{result.stderr}\n```")
                    except Exception as e:
                        logger.error(f"❌ Deploy error: {e}")
                        bot.notifier.send(f"❌ **Deploy Error**\n```\n{str(e)}\n```")
                
                # Run in background thread
                threading.Thread(target=deploy, daemon=True).start()
                
                return jsonify({
                    'message': 'Deploy started',
                    'commits': len(commits),
                    'pusher': pusher
                }), 200
            else:
                logger.info(f"⏭️  Ignoring push to {ref} (not main branch)")
                return jsonify({'message': 'Ignored - not main branch'}), 200
        
        return jsonify({'message': 'Event received'}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/health', methods=['GET'])
def webhook_health():
    """Health check for webhook."""
    bot = ScalpingBot._instance
    return jsonify({
        'status': 'healthy',
        'service': 'scalp-bot',
        'webhook': 'enabled',
        'ngrok_url': bot.ngrok_url if bot else None
    }), 200


def main() -> None:
    """Main entry point for the bot."""
    import atexit
    
    try:
        bot = ScalpingBot()
        
        # Register cleanup function
        def cleanup():
            logger.info("Performing cleanup...")
            bot._stop_ngrok()
            logger.info("Cleanup complete")
        
        atexit.register(cleanup)
        
        # Start dashboard first
        bot.start_dashboard()
        
        # Then start bot
        bot.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        sys.exit(0)
    except Exception as exc:
        logger.exception("Fatal error during bot startup: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
