import logging
import time
from datetime import datetime, time as dt_time, timedelta
from typing import Any, Dict, List, Optional

import pytz
from alpaca_trade_api import REST
from alpaca_trade_api.common import URL
from alpaca.trading.client import TradingClient


class BrokerClient:
    """Wrapper around Alpaca REST API supporting paper/live modes."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.logger = logging.getLogger(__name__)
        self.mode = config.get("mode", "paper")
        alpaca_cfg = config.get("alpaca", {})
        mode_cfg = alpaca_cfg.get(self.mode)
        if not mode_cfg:
            raise ValueError(f"Missing alpaca configuration for mode {self.mode}")

        self.api_key_id = mode_cfg.get("api_key_id")
        self.api_secret_key = mode_cfg.get("api_secret_key")
        self.base_url = URL(mode_cfg.get("endpoint"))
        self.data_feed = mode_cfg.get("data_feed", "iex")

        if not self.api_key_id or not self.api_secret_key:
            raise ValueError("Alpaca API keys must be provided in config.yaml")

        # Old SDK for market data
        self.client = REST(self.api_key_id, self.api_secret_key, self.base_url, api_version="v2")
        
        # New SDK for options data
        self.trading_client = TradingClient(
            self.api_key_id, 
            self.api_secret_key, 
            paper=(self.mode == "paper")
        )

    # -------------------- Market Data --------------------
    def get_latest_bar(self, symbol: str) -> Dict[str, Any]:
        """Get the latest price bar for a symbol."""
        try:
            bar = self.client.get_latest_bar(symbol)
            return bar._raw if hasattr(bar, '_raw') else bar.to_dict()
        except Exception as exc:
            self.logger.error("Failed to fetch latest bar for %s: %s", symbol, exc)
            raise

    def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        # Convert datetime to ISO format string for Alpaca API (without microseconds)
        if isinstance(start, datetime):
            start_str = start.replace(microsecond=0).isoformat()
        else:
            start_str = start
            
        if isinstance(end, datetime) and end:
            end_str = end.replace(microsecond=0).isoformat()
        else:
            end_str = None
        
        bars = self.client.get_bars(
            symbol,
            timeframe,
            start=start_str,
            end=end_str,
            limit=limit,
            adjustment="raw",
            feed=self.data_feed,
        )
        return [bar._raw for bar in bars]

    def get_premarket_volume(self, symbol: str, date: datetime) -> float:
        """Calculate premarket volume (before 9:30 AM ET)."""
        eastern = pytz.timezone('US/Eastern')
        if date.tzinfo is None:
            date = eastern.localize(date)
        else:
            date = date.astimezone(eastern)
        
        # Premarket typically starts at 4:00 AM ET
        start = date.replace(hour=4, minute=0, second=0, microsecond=0)
        # Market opens at 9:30 AM ET
        end = date.replace(hour=9, minute=30, second=0, microsecond=0)
        
        try:
            bars = self.get_historical_bars(symbol, "1Min", start=start, end=end)
            if not bars:
                return 0.0
            
            premarket_volume = 0.0
            market_open_time = dt_time(9, 30)
            
            for bar in bars:
                bar_time = bar.get("t")
                if isinstance(bar_time, str):
                    bar_time = datetime.fromisoformat(bar_time.replace('Z', '+00:00'))
                if bar_time.tzinfo is None:
                    bar_time = pytz.utc.localize(bar_time)
                bar_time_et = bar_time.astimezone(eastern)
                
                if bar_time_et.time() < market_open_time:
                    premarket_volume += float(bar.get("v", 0))
            
            return premarket_volume
        except Exception as exc:
            self.logger.warning("Failed to fetch premarket volume for %s: %s", symbol, exc)
            return 0.0

    def get_previous_close(self, symbol: str) -> float:
        bars = self.get_historical_bars(symbol, "1Day", start=datetime.utcnow() - timedelta(days=5), limit=2)
        if len(bars) < 2:
            raise RuntimeError("Not enough historical data to determine previous close")
        return float(bars[-2]["c"])

    def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        try:
            quote = self.client.get_latest_quote(symbol)
            # Use mid-point of bid/ask for better accuracy
            ask = float(quote.ask_price) if quote.ask_price else 0
            bid = float(quote.bid_price) if quote.bid_price else 0
            
            if ask > 0 and bid > 0:
                return (ask + bid) / 2
            elif ask > 0:
                return ask
            elif bid > 0:
                return bid
            else:
                # Fallback to last trade price
                return float(quote.price) if hasattr(quote, 'price') else 0.0
        except Exception as exc:
            self.logger.error("Failed to fetch current price for %s: %s", symbol, exc)
            raise

    def get_option_chain(self, symbol: str, expiration: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch option chain for underlying symbol."""
        try:
            from alpaca.trading.requests import GetOptionContractsRequest
            from datetime import datetime, timedelta
            
            # Get 0DTE and 1DTE options
            if expiration:
                exp_date = datetime.fromisoformat(expiration).date()
                request = GetOptionContractsRequest(
                    underlying_symbols=[symbol],
                    status='active',
                    expiration_date=exp_date,
                    limit=200
                )
            else:
                # Get nearest expirations (next 5 days to catch weekly options)
                request = GetOptionContractsRequest(
                    underlying_symbols=[symbol],
                    status='active',
                    expiration_date_gte=datetime.now().date(),
                    expiration_date_lte=(datetime.now() + timedelta(days=5)).date(),
                    limit=200
                )
            
            response = self.trading_client.get_option_contracts(request)
            contracts = response.option_contracts
            
            # Convert to dict format
            chain = []
            for contract in contracts:
                chain.append({
                    'symbol': contract.symbol,
                    'strike_price': float(contract.strike_price),
                    'option_type': contract.type,
                    'expiration_date': str(contract.expiration_date),
                    'open_interest': contract.open_interest if contract.open_interest else 0,
                    'size': contract.size,
                })
            
            return chain
        except Exception as exc:
            self.logger.warning("Failed to fetch option chain for %s: %s", symbol, exc)
            return []

    def get_option_quote(self, option_symbol: str) -> Optional[Dict[str, Any]]:
        try:
            quote = self.client.get_option_quote(option_symbol)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Failed to fetch option quote for %s: %s", option_symbol, exc)
            return None
        return quote._raw if quote else None

    def get_option_market_price(self, option_symbol: str) -> Optional[float]:
        quote = self.get_option_quote(option_symbol)
        if not quote:
            return None
        ask = quote.get("ask_price")
        bid = quote.get("bid_price")
        if ask is not None and bid is not None:
            return float((ask + bid) / 2)
        if ask is not None:
            return float(ask)
        if bid is not None:
            return float(bid)
        last_price = quote.get("last_price")
        return float(last_price) if last_price is not None else None

    # -------------------- Orders --------------------
    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        type_: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        order = self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type_,
            time_in_force=time_in_force,
            limit_price=limit_price,
        )
        self.logger.info("Submitted order %s", order.id)
        return order._raw

    def get_order(self, order_id: str) -> Dict[str, Any]:
        return self.client.get_order(order_id)._raw

    def cancel_order(self, order_id: str) -> None:
        self.client.cancel_order(order_id)

    def list_positions(self) -> List[Dict[str, Any]]:
        return [position._raw for position in self.client.list_positions()]

    def close_position(self, symbol: str) -> Dict[str, Any]:
        order = self.client.close_position(symbol)
        return order._raw

    def get_account(self) -> Dict[str, Any]:
        return self.client.get_account()._raw

    def get_cash_balance(self) -> float:
        """Get available cash balance."""
        try:
            account = self.client.get_account()
            return float(account.cash)
        except Exception as exc:
            self.logger.error("Failed to fetch cash balance: %s", exc)
            raise
    
    def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        try:
            clock = self.client.get_clock()
            return clock.is_open
        except Exception as exc:
            self.logger.error("Failed to check market status: %s", exc)
            return False
    
    def get_market_hours(self) -> Dict[str, Any]:
        """Get market hours for today."""
        try:
            clock = self.client.get_clock()
            return {
                'is_open': clock.is_open,
                'next_open': clock.next_open,
                'next_close': clock.next_close,
            }
        except Exception as exc:
            self.logger.error("Failed to fetch market hours: %s", exc)
            raise
    
    def get_news(self, symbol: str, start: Optional[datetime] = None, end: Optional[datetime] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get news articles for a symbol from Alpaca News API.
        
        Args:
            symbol: Stock symbol
            start: Start datetime for news (default: 24 hours ago)
            end: End datetime for news (default: now)
            limit: Maximum number of articles (default: 50)
            
        Returns:
            List of news articles with headline, summary, author, created_at, url, symbols, sentiment
        """
        try:
            if start is None:
                start = datetime.now(pytz.UTC) - timedelta(hours=24)
            if end is None:
                end = datetime.now(pytz.UTC)
            
            # Ensure timezone aware
            if start.tzinfo is None:
                start = pytz.UTC.localize(start)
            if end.tzinfo is None:
                end = pytz.UTC.localize(end)
            
            # Alpaca News API endpoint (remove microseconds from timestamps)
            start_str = start.replace(microsecond=0).isoformat()
            end_str = end.replace(microsecond=0).isoformat()
            news = self.client.get_news(symbol, start=start_str, end=end_str, limit=limit)
            
            articles = []
            for article in news:
                articles.append({
                    'headline': article.headline if hasattr(article, 'headline') else article.get('headline', ''),
                    'summary': article.summary if hasattr(article, 'summary') else article.get('summary', ''),
                    'author': article.author if hasattr(article, 'author') else article.get('author', ''),
                    'created_at': article.created_at if hasattr(article, 'created_at') else article.get('created_at', ''),
                    'url': article.url if hasattr(article, 'url') else article.get('url', ''),
                    'symbols': article.symbols if hasattr(article, 'symbols') else article.get('symbols', []),
                })
            
            return articles
        except Exception as exc:
            self.logger.warning("Failed to fetch news for %s: %s", symbol, exc)
            return []
