#!/usr/bin/env python3
"""
News sentiment analyzer using OpenAI.
Fetches and analyzes news for watchlist tickers.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class NewsSentimentAnalyzer:
    """Analyzes news sentiment for tickers using OpenAI."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.openai_api_key = config.get('openai', {}).get('api_key')
        
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI client initialized for news analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
                self.client = None
        else:
            self.client = None
            logger.info("OpenAI API key not configured - news analysis disabled")
    
    def is_configured(self) -> bool:
        """Check if analyzer is ready to use."""
        return self.client is not None
    
    def analyze_ticker(self, symbol: str) -> Optional[Dict]:
        """Analyze news sentiment for a single ticker using OpenAI.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Dict with sentiment and reasoning, or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            # Prompt OpenAI to analyze recent news
            prompt = f"""Analyze the latest news and market sentiment for {symbol} stock.

Provide:
1. Overall sentiment: bullish, bearish, or neutral
2. Brief reasoning (1-2 sentences) based on recent news/events

Respond in this exact JSON format:
{{
    "sentiment": "bullish/bearish/neutral",
    "reasoning": "Brief explanation here"
}}

Be concise and focus on actionable insights for day trading."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst providing concise market sentiment analysis for day traders. You have access to current market news and data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'symbol': symbol,
                'sentiment': result.get('sentiment', 'neutral').lower(),
                'reasoning': result.get('reasoning', 'No analysis available'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return {
                'symbol': symbol,
                'sentiment': 'neutral',
                'reasoning': 'Analysis unavailable',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def analyze_watchlist(self, symbols: List[str]) -> List[Dict]:
        """Analyze news sentiment for all watchlist tickers.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            List of analysis results
        """
        if not self.is_configured():
            logger.warning("News analyzer not configured")
            return []
        
        logger.info(f"📰 Analyzing news sentiment for {len(symbols)} tickers...")
        
        results = []
        for symbol in symbols:
            try:
                analysis = self.analyze_ticker(symbol)
                if analysis:
                    results.append(analysis)
                    logger.info(f"  ✅ {symbol}: {analysis['sentiment']} - {analysis['reasoning'][:50]}...")
            except Exception as e:
                logger.error(f"  ❌ {symbol}: {e}")
        
        logger.info(f"✅ Completed analysis for {len(results)}/{len(symbols)} tickers")
        return results
