#!/usr/bin/env python3
"""
AI-powered news analyzer for watchlist tickers.
Fetches latest news and provides sentiment + trade likelihood analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Analyzes news for watchlist tickers using AI."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_api_key = config.get('openai', {}).get('api_key')
        self.alpaca_api_key = config.get('alpaca', {}).get(config.get('mode', 'paper'), {}).get('api_key_id')
        self.alpaca_secret = config.get('alpaca', {}).get(config.get('mode', 'paper'), {}).get('api_secret_key')
        
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured - news analysis disabled")
    
    def is_configured(self) -> bool:
        """Check if news analyzer is properly configured."""
        return self.client is not None and self.alpaca_api_key is not None
    
    def get_news_for_ticker(self, symbol: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Fetch recent news for a ticker from Alpaca."""
        if not self.alpaca_api_key:
            return []
        
        try:
            # Calculate time range
            end = datetime.utcnow()
            start = end - timedelta(hours=hours)
            
            # Alpaca News API
            url = "https://data.alpaca.markets/v1beta1/news"
            headers = {
                "APCA-API-KEY-ID": self.alpaca_api_key,
                "APCA-API-SECRET-KEY": self.alpaca_secret
            }
            params = {
                "symbols": symbol,
                "start": start.isoformat() + "Z",
                "end": end.isoformat() + "Z",
                "limit": 5,
                "sort": "desc"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            news_data = response.json()
            articles = news_data.get('news', [])
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch news for {symbol}: {e}")
            return []
    
    def analyze_ticker_news(self, symbol: str, hours: int = 1) -> Optional[Dict[str, Any]]:
        """Analyze news for a single ticker using AI."""
        if not self.is_configured():
            return None
        
        # Get news articles
        articles = self.get_news_for_ticker(symbol, hours)
        
        if not articles:
            return {
                "symbol": symbol,
                "summary": "No recent news",
                "sentiment": "neutral",
                "entry_likelihood": "low",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Prepare news text for AI
        news_text = ""
        for i, article in enumerate(articles[:5], 1):
            headline = article.get('headline', '')
            summary = article.get('summary', '')
            news_text += f"{i}. {headline}\n{summary}\n\n"
        
        # AI prompt
        prompt = f"""Analyze the following news for {symbol} and provide:
1. A 1-2 sentence summary of the key developments
2. Overall sentiment (bullish/bearish/neutral)
3. Likelihood of a good scalping entry in next few hours (high/medium/low)

News articles:
{news_text}

Respond in this exact JSON format:
{{
    "summary": "1-2 sentence summary here",
    "sentiment": "bullish/bearish/neutral",
    "entry_likelihood": "high/medium/low",
    "reasoning": "Brief reason for the likelihood"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial news analyst specializing in short-term trading opportunities. Be concise and actionable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "symbol": symbol,
                "summary": result.get("summary", "No summary available"),
                "sentiment": result.get("sentiment", "neutral"),
                "entry_likelihood": result.get("entry_likelihood", "low"),
                "reasoning": result.get("reasoning", ""),
                "news_count": len(articles),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed for {symbol}: {e}")
            return {
                "symbol": symbol,
                "summary": f"Analysis error: {str(e)[:50]}",
                "sentiment": "neutral",
                "entry_likelihood": "low",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def analyze_watchlist(self, symbols: List[str], hours: int = 1) -> List[Dict[str, Any]]:
        """Analyze news for all watchlist tickers."""
        if not self.is_configured():
            logger.warning("News analyzer not configured")
            return []
        
        logger.info(f"Analyzing news for {len(symbols)} tickers...")
        
        results = []
        for symbol in symbols:
            try:
                analysis = self.analyze_ticker_news(symbol, hours)
                if analysis:
                    results.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
        
        logger.info(f"Completed news analysis for {len(results)}/{len(symbols)} tickers")
        return results
