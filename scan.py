import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from broker import BrokerClient
from notifications import DiscordNotifier
from utils import EASTERN_TZ, read_state, update_state, weighted_score


class TickerScanner:
    """Performs the pre-market ticker scan and selects a ticker of the day."""

    def __init__(
        self,
        broker: BrokerClient,
        notifier: DiscordNotifier,
        config: Dict[str, Any],
    ) -> None:
        self.broker = broker
        self.notifier = notifier
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run(self) -> Optional[Dict[str, Any]]:
        watchlist = self.config.get("watchlist", {}).get("symbols", [])
        if not watchlist:
            self.logger.warning("Watchlist is empty; skipping pre-market scan")
            return None

        scanning_cfg = self.config.get("scanning", {})
        weights = scanning_cfg.get("weights", {})
        thresholds = scanning_cfg.get("thresholds", {})

        self.logger.info("Starting pre-market scan for symbols: %s", watchlist)

        scored_tickers: List[Tuple[str, float, Dict[str, float]]] = []
        now_eastern = datetime.now(EASTERN_TZ)

        for symbol in watchlist:
            try:
                metrics = self._compute_metrics(symbol, now_eastern, thresholds)
                score = weighted_score(metrics, weights)
                scored_tickers.append((symbol, score, metrics))
                self.logger.debug("%s metrics=%s score=%.4f", symbol, metrics, score)
            except Exception as exc:  # noqa: BLE001
                self.logger.exception("Failed to evaluate metrics for %s: %s", symbol, exc)

        if not scored_tickers:
            self.logger.error("No tickers produced metrics; scan aborted")
            return None

        scored_tickers.sort(key=lambda item: item[1], reverse=True)
        winner_symbol, winner_score, winner_metrics = scored_tickers[0]

        self.logger.info("Ticker of the Day selected: %s (score %.4f)", winner_symbol, winner_score)

        state = read_state()
        state.update(
            {
                "ticker_of_the_day": winner_symbol,
                "ticker_selection_time": now_eastern.isoformat(),
                "ticker_metrics": winner_metrics,
                "ticker_score": winner_score,
            }
        )
        update_state(state)

        if self.notifier.is_configured():
            self.notifier.alert_ticker_selection(winner_symbol, winner_score, winner_metrics)

        return {
            "symbol": winner_symbol,
            "score": winner_score,
            "metrics": winner_metrics,
        }

    # -------------------- Metric Calculations --------------------
    def _compute_metrics(
        self,
        symbol: str,
        reference_time: datetime,
        thresholds: Dict[str, Any],
    ) -> Dict[str, float]:
        """Compute all scoring metrics for a symbol."""
        today = reference_time.astimezone(EASTERN_TZ)
        
        # Fetch raw metrics with fallbacks
        premarket_volume = self._get_premarket_volume(symbol, today)
        avg_premarket_volume = self._get_average_premarket_volume(symbol, today, days=5)
        volume_ratio = (
            (premarket_volume / avg_premarket_volume)
            if avg_premarket_volume > 0
            else 1.0  # Neutral ratio if no historical data
        )

        gap_percent = self._get_gap_percent(symbol)
        iv_rank = self._get_iv_rank(symbol)
        option_open_interest = self._get_option_open_interest(symbol)
        atr = self._get_atr(symbol, period=14)
        
        # Get news sentiment
        news_sentiment, news_volume = self._get_news_sentiment(symbol)

        # Normalize metrics to 0-100 scale for weighted scoring
        metrics = {
            "premarket_volume": min(100.0, max(0.0, volume_ratio * 50)),  # Normalize ratio
            "gap_percent": min(100.0, max(0.0, abs(gap_percent) * 10)),  # Scale gap
            "iv_rank": min(100.0, max(0.0, iv_rank)),
            "option_open_interest": min(100.0, max(0.0, option_open_interest / 1000)),  # Scale OI
            "atr": min(100.0, max(0.0, atr * 10)),  # Scale ATR
            "news_sentiment": min(100.0, max(0.0, (news_sentiment + 1) * 50)),  # Convert -1 to +1 range to 0-100
            "news_volume": min(100.0, max(0.0, news_volume * 5)),  # Scale news count
        }

        # Apply hard filters
        min_volume = thresholds.get("min_premarket_volume")
        if min_volume and premarket_volume < min_volume:
            self.logger.debug("%s filtered out by min premarket volume %s", symbol, min_volume)
            # Zero out score for filtered tickers
            return {key: 0.0 for key in metrics}

        return metrics

    def _get_premarket_volume(self, symbol: str, as_of: datetime) -> float:
        return self.broker.get_premarket_volume(symbol, as_of)

    def _get_average_premarket_volume(self, symbol: str, as_of: datetime, days: int = 5) -> float:
        total = 0.0
        count = 0
        for offset in range(1, days + 1):
            day = as_of - timedelta(days=offset)
            try:
                vol = self.broker.get_premarket_volume(symbol, day)
            except Exception as exc:  # noqa: BLE001
                self.logger.debug("Failed to fetch premarket volume for %s on %s: %s", symbol, day.date(), exc)
                continue
            if vol > 0:
                total += vol
                count += 1
        return total / count if count else 0.0

    def _get_gap_percent(self, symbol: str) -> float:
        """Calculate gap % from previous close to today's open."""
        try:
            bars = self.broker.get_historical_bars(
                symbol,
                "1Day",
                start=datetime.utcnow() - timedelta(days=10),
                limit=5,
            )
            if len(bars) < 2:
                return 0.0
            today_bar = bars[-1]
            prev_bar = bars[-2]
            prev_close = float(prev_bar.get("c", 0))
            today_open = float(today_bar.get("o", 0))
            if prev_close == 0:
                return 0.0
            return (today_open - prev_close) / prev_close * 100.0
        except Exception as exc:
            self.logger.warning("Failed to calculate gap for %s: %s", symbol, exc)
            return 0.0

    def _get_iv_rank(self, symbol: str) -> float:
        """Calculate IV rank (0-100) for the symbol."""
        try:
            chain = self.broker.get_option_chain(symbol)
            if not chain:
                return 50.0  # Neutral if no data
            
            iv_values = []
            for opt in chain:
                iv = opt.get("implied_volatility") or opt.get("iv")
                if iv is not None and float(iv) > 0:
                    iv_values.append(float(iv))
            
            if not iv_values:
                return 50.0
            
            current_iv = float(max(iv_values))
            iv_min = min(iv_values)
            iv_max = max(iv_values)
            
            if iv_max == iv_min:
                return 50.0
            
            return (current_iv - iv_min) / (iv_max - iv_min) * 100.0
        except Exception as exc:
            self.logger.warning("Failed to calculate IV rank for %s: %s", symbol, exc)
            return 50.0

    def _get_option_open_interest(self, symbol: str) -> float:
        chain = self.broker.get_option_chain(symbol)
        total_interest = 0.0
        now = datetime.utcnow()
        for option in chain:
            expiration = option.get("expiration_date")
            if not expiration:
                continue
            try:
                expiration_dt = datetime.fromisoformat(expiration)
            except ValueError:
                continue
            days_to_exp = (expiration_dt - now).days
            if days_to_exp not in {0, 1}:
                continue
            oi = option.get("open_interest")
            if oi is not None:
                total_interest += float(oi)
        return total_interest

    def _get_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range for volatility measure."""
        try:
            bars = self.broker.get_historical_bars(
                symbol,
                "1Day",
                start=datetime.utcnow() - timedelta(days=period * 3),
            )
            if len(bars) < period:
                return 0.0

            df = pd.DataFrame(bars)
            df["high"] = df["h"].astype(float)
            df["low"] = df["l"].astype(float)
            df["close"] = df["c"].astype(float)
            df["prev_close"] = df["close"].shift(1)

            tr_components = pd.DataFrame(
                {
                    "hl": df["high"] - df["low"],
                    "hc": (df["high"] - df["prev_close"]).abs(),
                    "lc": (df["low"] - df["prev_close"]).abs(),
                }
            )
            df["tr"] = tr_components.max(axis=1)

            atr = df["tr"].rolling(window=period).mean().iloc[-1]
            return float(atr) if pd.notna(atr) else 0.0
        except Exception as exc:
            self.logger.warning("Failed to calculate ATR for %s: %s", symbol, exc)
            return 0.0
    
    def _get_news_sentiment(self, symbol: str) -> tuple[float, int]:
        """Calculate news sentiment and volume for a symbol.
        
        Returns:
            (sentiment_score, news_count)
            sentiment_score: -1.0 (very negative) to +1.0 (very positive)
            news_count: number of articles in last 24 hours
        """
        try:
            # Get news from last 24 hours
            articles = self.broker.get_news(symbol, limit=50)
            
            if not articles:
                return 0.0, 0  # Neutral sentiment, no news
            
            # Simple sentiment analysis based on keywords
            positive_keywords = ['beat', 'surge', 'gain', 'up', 'high', 'profit', 'growth', 'strong', 
                               'upgrade', 'buy', 'bullish', 'positive', 'record', 'success', 'win']
            negative_keywords = ['miss', 'drop', 'fall', 'down', 'low', 'loss', 'decline', 'weak',
                               'downgrade', 'sell', 'bearish', 'negative', 'concern', 'fail', 'lawsuit']
            
            sentiment_scores = []
            for article in articles:
                headline = (article.get('headline', '') + ' ' + article.get('summary', '')).lower()
                
                positive_count = sum(1 for word in positive_keywords if word in headline)
                negative_count = sum(1 for word in negative_keywords if word in headline)
                
                # Calculate article sentiment (-1 to +1)
                if positive_count + negative_count > 0:
                    article_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                else:
                    article_sentiment = 0.0
                
                sentiment_scores.append(article_sentiment)
            
            # Average sentiment across all articles
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            news_count = len(articles)
            
            self.logger.debug("%s news: %d articles, sentiment: %.2f", symbol, news_count, avg_sentiment)
            
            return avg_sentiment, news_count
            
        except Exception as exc:
            self.logger.warning("Failed to calculate news sentiment for %s: %s", symbol, exc)
            return 0.0, 0
