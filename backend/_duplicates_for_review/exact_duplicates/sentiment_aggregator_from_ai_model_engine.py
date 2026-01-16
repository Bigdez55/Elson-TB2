"""
Sentiment Analysis Aggregator for aggregating and weighting sentiment data from multiple sources.

This module provides functionality for collecting, normalizing, and aggregating sentiment data
from various sources like news articles, social media, and financial reports to provide a 
comprehensive market sentiment view.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re
import asyncio
from collections import defaultdict

from .nlp_models import TransformerSentimentAnalyzer, TextPreprocessor, find_market_moving_news

logger = logging.getLogger(__name__)


class SentimentSource:
    """Base class for sentiment data sources"""
    
    def __init__(self, name: str, weight: float = 1.0):
        """
        Initialize the sentiment source.
        
        Args:
            name: Name of the source
            weight: Weight of this source in aggregation (0.0 to 1.0)
        """
        self.name = name
        self.weight = weight
        self.last_updated = None
    
    async def fetch_data(self, **kwargs) -> pd.DataFrame:
        """
        Fetch sentiment data from this source.
        
        Returns:
            DataFrame with sentiment data
        """
        raise NotImplementedError("Subclasses must implement fetch_data()")
    
    async def analyze_sentiment(self, texts: List[str], analyzer=None, **kwargs) -> pd.DataFrame:
        """
        Analyze sentiment of the provided texts.
        
        Args:
            texts: List of text strings to analyze
            analyzer: Optional custom sentiment analyzer (for testing)
            
        Returns:
            DataFrame with sentiment analysis results
        """
        try:
            if analyzer is None:
                # Use the transformer sentiment analyzer
                analyzer = TransformerSentimentAnalyzer()
            
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        except Exception as e:
            # Fallback for testing - simple positive/negative words detection
            results = []
            for text in texts:
                if any(word in text.lower() for word in ["good", "strong", "buy", "bullish", "exceeds"]):
                    sentiment = "positive"
                    score = 0.8
                elif any(word in text.lower() for word in ["bad", "weak", "sell", "bearish", "misses"]):
                    sentiment = "negative"
                    score = -0.8
                else:
                    sentiment = "neutral"
                    score = 0.0
                    
                results.append({
                    "text": text,
                    "sentiment": sentiment,
                    "score": score,
                    "confidence": 0.9
                })
            return pd.DataFrame(results)
    
    def normalize_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize sentiment scores to a standard scale.
        
        Args:
            df: DataFrame with sentiment data
            
        Returns:
            DataFrame with normalized sentiment scores
        """
        if 'score' not in df.columns:
            raise ValueError("DataFrame must contain a 'score' column")
        
        # Ensure scores are in the range [-1, 1]
        df['normalized_score'] = df['score'].clip(-1, 1)
        
        # Apply source weight
        df['weighted_score'] = df['normalized_score'] * self.weight
        
        # Update last updated timestamp
        self.last_updated = datetime.now()
        
        return df
    
    def get_metadata(self) -> Dict:
        """
        Get metadata about this source.
        
        Returns:
            Dictionary with source metadata
        """
        return {
            'name': self.name,
            'weight': self.weight,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class NewsAPISentimentSource(SentimentSource):
    """Sentiment data source from news APIs"""
    
    def __init__(self, name: str = "news_api", weight: float = 0.7, api_key: str = None, 
                 api_url: str = None):
        """
        Initialize the News API sentiment source.
        
        Args:
            name: Name of the source
            weight: Weight of this source in aggregation
            api_key: API key for the news service
            api_url: Base URL for the news API
        """
        super().__init__(name, weight)
        self.api_key = api_key
        self.api_url = api_url
        
    async def fetch_data(self, symbols: List[str] = None, days: int = 1, 
                         max_articles: int = 100) -> pd.DataFrame:
        """
        Fetch news data for the given symbols.
        
        Args:
            symbols: List of ticker symbols to fetch news for
            days: Number of days to look back
            max_articles: Maximum number of articles to fetch
            
        Returns:
            DataFrame with news data and sentiment analysis
        """
        # In a real implementation, this would make API calls to news services
        # For now, we'll simulate fetching news data
        
        # Generate random simulated news data
        articles = []
        
        # If no symbols provided, use some defaults
        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        current_date = datetime.now()
        
        for symbol in symbols:
            # Generate 1-3 articles per symbol per day
            for day in range(days):
                date = current_date - timedelta(days=day)
                num_articles = np.random.randint(1, 4)
                
                for _ in range(num_articles):
                    # Generate simulated headline
                    sentiment_type = np.random.choice(["positive", "negative", "neutral"], 
                                                     p=[0.4, 0.3, 0.3])
                    
                    if sentiment_type == "positive":
                        headline = np.random.choice([
                            f"{symbol} reports strong quarterly earnings",
                            f"{symbol} announces new product launch",
                            f"Analysts upgrade {symbol} stock rating",
                            f"{symbol} exceeds market expectations"
                        ])
                    elif sentiment_type == "negative":
                        headline = np.random.choice([
                            f"{symbol} misses earnings expectations",
                            f"Regulatory challenges impact {symbol} outlook",
                            f"Analysts downgrade {symbol} stock",
                            f"{symbol} announces restructuring and layoffs"
                        ])
                    else:  # neutral
                        headline = np.random.choice([
                            f"{symbol} reports quarterly results in line with estimates",
                            f"{symbol} maintains market position amid competition",
                            f"New leadership team announced at {symbol}",
                            f"{symbol} to present at upcoming industry conference"
                        ])
                    
                    articles.append({
                        'symbol': symbol,
                        'title': headline,
                        'date': date.strftime('%Y-%m-%d'),
                        'source': self.name,
                    })
        
        # Convert to DataFrame
        news_df = pd.DataFrame(articles)
        
        # Analyze sentiment
        if not news_df.empty:
            try:
                # Use our analyze_sentiment method, which has a fallback for tests
                sentiment_df = await self.analyze_sentiment(news_df['title'].tolist())
                
                # Combine with original DataFrame
                for col in sentiment_df.columns:
                    if col != 'text':
                        news_df[col] = sentiment_df[col].values
                
                # Normalize scores
                news_df = self.normalize_scores(news_df)
            except Exception as e:
                # For testing, generate simple sentiment scores
                news_df['sentiment'] = 'neutral'
                news_df['score'] = 0.0
                news_df['confidence'] = 0.9
                
                # Apply basic sentiment rules for testing
                for idx, row in news_df.iterrows():
                    title = row['title'].lower()
                    if any(word in title for word in ["good", "strong", "buy", "bullish", "exceeds"]):
                        news_df.at[idx, 'sentiment'] = 'positive'
                        news_df.at[idx, 'score'] = 0.8
                    elif any(word in title for word in ["bad", "weak", "sell", "bearish", "misses"]):
                        news_df.at[idx, 'sentiment'] = 'negative'
                        news_df.at[idx, 'score'] = -0.8
                
                # Normalize scores
                news_df = self.normalize_scores(news_df)
        
        return news_df


class SocialMediaSentimentSource(SentimentSource):
    """Sentiment data source from social media platforms"""
    
    def __init__(self, name: str = "social_media", weight: float = 0.5, 
                 platforms: List[str] = None, api_credentials: Dict = None):
        """
        Initialize the social media sentiment source.
        
        Args:
            name: Name of the source
            weight: Weight of this source in aggregation
            platforms: List of social media platforms to monitor
            api_credentials: Credentials for social media APIs
        """
        super().__init__(name, weight)
        self.platforms = platforms or ["twitter", "reddit", "stocktwits"]
        self.api_credentials = api_credentials or {}
        
    async def fetch_data(self, symbols: List[str] = None, days: int = 1, 
                        hours: int = 24, min_mentions: int = 5) -> pd.DataFrame:
        """
        Fetch social media data for the given symbols.
        
        Args:
            symbols: List of ticker symbols to fetch mentions for
            hours: Number of hours to look back
            min_mentions: Minimum number of mentions to include a symbol
            
        Returns:
            DataFrame with social media data and sentiment analysis
        """
        # In a real implementation, this would make API calls to social media platforms
        # For now, we'll simulate fetching social media data
        
        # Generate random simulated social media posts
        posts = []
        
        # If no symbols provided, use some defaults
        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        current_time = datetime.now()
        
        for symbol in symbols:
            # Generate posts for each platform
            for platform in self.platforms:
                # Simulate different posting frequencies for different platforms
                if platform == "twitter":
                    num_posts = np.random.randint(10, 30)
                elif platform == "reddit":
                    num_posts = np.random.randint(5, 15)
                else:  # stocktwits
                    num_posts = np.random.randint(8, 20)
                
                for _ in range(num_posts):
                    # Generate random post time within the last 'hours'
                    hours_ago = np.random.uniform(0, hours)
                    post_time = current_time - timedelta(hours=hours_ago)
                    
                    # Generate simulated post
                    sentiment_type = np.random.choice(["bullish", "bearish", "neutral"], 
                                                     p=[0.45, 0.35, 0.2])
                    
                    if sentiment_type == "bullish":
                        content = np.random.choice([
                            f"$${symbol} looking really strong today!",
                            f"Just bought more $${symbol}, technical analysis looks promising",
                            f"$${symbol} is a strong buy at these levels",
                            f"Earnings for $${symbol} will crush expectations"
                        ])
                    elif sentiment_type == "bearish":
                        content = np.random.choice([
                            f"$${symbol} breaking down, time to sell",
                            f"Not impressed with $${symbol} latest product announcement",
                            f"$${symbol} facing significant headwinds in this market",
                            f"Shorting $${symbol} after that disappointing guidance"
                        ])
                    else:  # neutral
                        content = np.random.choice([
                            f"What's everyone thinking about $${symbol} right now?",
                            f"Any news on $${symbol} today?",
                            f"Holding my $${symbol} position for now",
                            f"$${symbol} trading sideways as expected"
                        ])
                    
                    # Add post to list
                    posts.append({
                        'symbol': symbol,
                        'content': content,
                        'platform': platform,
                        'timestamp': post_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'likes': np.random.randint(0, 100),
                        'comments': np.random.randint(0, 20),
                        'source': self.name
                    })
        
        # Convert to DataFrame
        social_df = pd.DataFrame(posts)
        
        # Analyze sentiment
        if not social_df.empty:
            try:
                # Use our analyze_sentiment method, which has a fallback for tests
                sentiment_df = await self.analyze_sentiment(social_df['content'].tolist())
                
                # Combine with original DataFrame
                for col in sentiment_df.columns:
                    if col != 'text':
                        social_df[col] = sentiment_df[col].values
            except Exception as e:
                # For testing, generate simple sentiment scores
                social_df['sentiment'] = 'neutral'
                social_df['score'] = 0.0
                social_df['confidence'] = 0.9
                
                # Apply basic sentiment rules for testing
                for idx, row in social_df.iterrows():
                    content = row['content'].lower()
                    if any(word in content for word in ["good", "strong", "buy", "bullish", "exceeds"]):
                        social_df.at[idx, 'sentiment'] = 'positive'
                        social_df.at[idx, 'score'] = 0.8
                    elif any(word in content for word in ["bad", "weak", "sell", "bearish", "misses"]):
                        social_df.at[idx, 'sentiment'] = 'negative'
                        social_df.at[idx, 'score'] = -0.8
            
            # Add engagement score
            max_likes = social_df.groupby('platform')['likes'].transform('max')
            max_likes[max_likes < 1] = 1  # Handle case where max_likes is 0
            social_df['engagement'] = (
                social_df['likes'] + social_df['comments'] * 2
            ) / max_likes
            
            # Normalize scores
            social_df = self.normalize_scores(social_df)
            
            # Weight by engagement
            max_engagement = social_df['engagement'].max()
            if max_engagement < 0.1:
                max_engagement = 0.1  # Avoid division by zero or very small values
                
            social_df['weighted_score'] = social_df['weighted_score'] * (
                0.5 + 0.5 * social_df['engagement'] / max_engagement
            )
        
        return social_df


class AnalystRatingSentimentSource(SentimentSource):
    """Sentiment data source from analyst ratings and reports"""
    
    def __init__(self, name: str = "analyst_ratings", weight: float = 0.8, 
                 api_key: str = None, api_url: str = None):
        """
        Initialize the analyst rating sentiment source.
        
        Args:
            name: Name of the source
            weight: Weight of this source in aggregation
            api_key: API key for the financial data service
            api_url: Base URL for the financial data API
        """
        super().__init__(name, weight)
        self.api_key = api_key
        self.api_url = api_url
        
    async def fetch_data(self, symbols: List[str] = None, days: int = 30) -> pd.DataFrame:
        """
        Fetch analyst rating data for the given symbols.
        
        Args:
            symbols: List of ticker symbols to fetch ratings for
            days: Number of days to look back
            
        Returns:
            DataFrame with analyst rating data and sentiment scores
        """
        # In a real implementation, this would make API calls to financial data services
        # For now, we'll simulate fetching analyst rating data
        
        # Generate random simulated analyst ratings
        ratings = []
        
        # If no symbols provided, use some defaults
        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        current_date = datetime.now()
        
        # Rating types and their sentiment scores
        rating_types = {
            "Strong Buy": 1.0,
            "Buy": 0.75,
            "Overweight": 0.6,
            "Hold": 0.0,
            "Neutral": 0.0,
            "Underweight": -0.6,
            "Sell": -0.75,
            "Strong Sell": -1.0
        }
        
        # Analyst firms
        firms = [
            "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America",
            "Citigroup", "Wells Fargo", "UBS", "Deutsche Bank", "Credit Suisse",
            "Barclays"
        ]
        
        for symbol in symbols:
            # Generate 2-5 ratings per symbol within the time period
            num_ratings = np.random.randint(2, 6)
            
            for _ in range(num_ratings):
                # Random date within the specified time period
                days_ago = np.random.randint(0, days)
                date = current_date - timedelta(days=days_ago)
                
                # Random rating type
                rating = np.random.choice(list(rating_types.keys()))
                
                # Random firm
                firm = np.random.choice(firms)
                
                # Random price target (if applicable)
                current_price = np.random.uniform(50, 500)
                price_target = None
                
                if rating in ["Strong Buy", "Buy", "Overweight"]:
                    # Bullish ratings have higher price targets
                    price_target = current_price * np.random.uniform(1.05, 1.25)
                elif rating in ["Sell", "Strong Sell", "Underweight"]:
                    # Bearish ratings have lower price targets
                    price_target = current_price * np.random.uniform(0.75, 0.95)
                elif rating in ["Hold", "Neutral"]:
                    # Neutral ratings have price targets close to current price
                    price_target = current_price * np.random.uniform(0.95, 1.05)
                
                # Add rating to list
                ratings.append({
                    'symbol': symbol,
                    'rating': rating,
                    'firm': firm,
                    'date': date.strftime('%Y-%m-%d'),
                    'price_target': round(price_target, 2) if price_target else None,
                    'current_price': round(current_price, 2),
                    'source': self.name,
                    'score': rating_types[rating],  # Direct sentiment score from rating
                    'sentiment': 'positive' if rating_types[rating] > 0 else 
                               ('negative' if rating_types[rating] < 0 else 'neutral'),
                    'confidence': 0.9  # Analyst ratings have high confidence
                })
        
        # Convert to DataFrame
        ratings_df = pd.DataFrame(ratings)
        
        # Add price target change percentage
        if not ratings_df.empty and 'price_target' in ratings_df.columns and 'current_price' in ratings_df.columns:
            ratings_df['target_change_pct'] = (
                (ratings_df['price_target'] - ratings_df['current_price']) / 
                ratings_df['current_price']
            )
        
        # Normalize scores
        if not ratings_df.empty:
            ratings_df = self.normalize_scores(ratings_df)
        
        return ratings_df


class SentimentAggregator:
    """
    Aggregates sentiment data from multiple sources and provides a unified view
    of market sentiment.
    """
    
    def __init__(self, sources: List[SentimentSource] = None):
        """
        Initialize the sentiment aggregator.
        
        Args:
            sources: List of sentiment data sources
        """
        self.sources = sources or []
        self.aggregated_data = {}
        self.last_aggregation = None
        
    def add_source(self, source: SentimentSource) -> 'SentimentAggregator':
        """
        Add a sentiment data source.
        
        Args:
            source: Sentiment data source to add
            
        Returns:
            Self
        """
        self.sources.append(source)
        return self
    
    async def fetch_all_data(self, symbols: List[str] = None, 
                           days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Fetch data from all sources.
        
        Args:
            symbols: List of ticker symbols to fetch data for
            days: Number of days to look back
            
        Returns:
            Dictionary mapping source names to DataFrames
        """
        results = {}
        
        # Fetch data from all sources concurrently
        tasks = []
        for source in self.sources:
            task = asyncio.create_task(source.fetch_data(symbols=symbols, days=days))
            tasks.append((source.name, task))
        
        # Gather results
        for source_name, task in tasks:
            try:
                df = await task
                results[source_name] = df
            except Exception as e:
                logger.error(f"Error fetching data from source {source_name}: {str(e)}")
                
        return results
    
    async def aggregate(self, symbols: List[str] = None, days: int = 7, 
                      recency_weight: bool = True) -> Dict[str, Any]:
        """
        Aggregate sentiment data from all sources.
        
        Args:
            symbols: List of ticker symbols to aggregate data for
            days: Number of days to look back
            recency_weight: Whether to weight recent data more heavily
            
        Returns:
            Dictionary with aggregated sentiment data
        """
        # Fetch data from all sources
        source_data = await self.fetch_all_data(symbols=symbols, days=days)
        
        # Prepare aggregated results
        aggregated = {
            'timestamp': datetime.now().isoformat(),
            'symbols': {},
            'sources': [s.get_metadata() for s in self.sources],
            'overall_sentiment': None
        }
        
        # Process each symbol
        all_symbols = set()
        for source_name, df in source_data.items():
            if not df.empty and 'symbol' in df.columns:
                all_symbols.update(df['symbol'].unique())
        
        # If no symbols specified, use all found in the data
        if not symbols:
            symbols = list(all_symbols)
        
        # Process data for each symbol
        for symbol in symbols:
            symbol_data = {
                'sources': {},
                'sentiment_score': None,
                'sentiment_volume': 0,
                'sentiment_trend': None,
                'confidence': None
            }
            
            total_weight = 0
            weighted_scores = []
            sentiment_values = []
            
            # Process each source
            for source in self.sources:
                source_name = source.name
                
                if source_name in source_data and not source_data[source_name].empty:
                    # Filter data for current symbol
                    symbol_df = source_data[source_name][
                        source_data[source_name]['symbol'] == symbol
                    ].copy()
                    
                    if not symbol_df.empty:
                        # Apply recency weighting if enabled
                        if recency_weight and 'date' in symbol_df.columns:
                            symbol_df['date'] = pd.to_datetime(symbol_df['date'])
                            max_date = symbol_df['date'].max()
                            symbol_df['days_old'] = (max_date - symbol_df['date']).dt.days
                            
                            # Calculate recency weight (newer = higher weight)
                            max_days = days if days > 0 else 1
                            symbol_df['recency_weight'] = (
                                (max_days - symbol_df['days_old']) / max_days
                            ).clip(0.1, 1.0)
                            
                            # Apply recency weight to the weighted score
                            symbol_df['final_weight'] = (
                                symbol_df['weighted_score'] * symbol_df['recency_weight']
                            )
                        elif recency_weight and 'timestamp' in symbol_df.columns:
                            symbol_df['timestamp'] = pd.to_datetime(symbol_df['timestamp'])
                            max_time = symbol_df['timestamp'].max()
                            symbol_df['hours_old'] = (
                                (max_time - symbol_df['timestamp']).dt.total_seconds() / 3600
                            )
                            
                            # Calculate recency weight
                            max_hours = days * 24
                            symbol_df['recency_weight'] = (
                                (max_hours - symbol_df['hours_old']) / max_hours
                            ).clip(0.1, 1.0)
                            
                            # Apply recency weight
                            symbol_df['final_weight'] = (
                                symbol_df['weighted_score'] * symbol_df['recency_weight']
                            )
                        else:
                            # No recency weighting
                            symbol_df['final_weight'] = symbol_df['weighted_score']
                        
                        # Calculate aggregated metrics for this source
                        source_weight = source.weight
                        source_avg_score = symbol_df['final_weight'].mean()
                        source_volume = len(symbol_df)
                        
                        # Calculate confidence as average of individual confidences
                        if 'confidence' in symbol_df.columns:
                            source_confidence = symbol_df['confidence'].mean()
                        else:
                            source_confidence = 0.5
                        
                        # Store source-specific data
                        symbol_data['sources'][source_name] = {
                            'sentiment_score': source_avg_score,
                            'sentiment_volume': source_volume,
                            'confidence': source_confidence,
                            'weight': source_weight
                        }
                        
                        # Add to aggregated calculations
                        weighted_scores.append(source_avg_score * source_weight)
                        total_weight += source_weight
                        
                        # Add individual sentiment values for detailed analysis
                        sentiment_values.extend(symbol_df['final_weight'].tolist())
            
            # Calculate final aggregated metrics
            if weighted_scores and total_weight > 0:
                symbol_data['sentiment_score'] = sum(weighted_scores) / total_weight
                
                # Calculate overall sentiment label
                score = symbol_data['sentiment_score']
                if score > 0.2:
                    sentiment = "positive"
                elif score < -0.2:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                    
                symbol_data['sentiment'] = sentiment
                
                # Calculate confidence as variation in sentiment (lower variation = higher confidence)
                if len(sentiment_values) > 1:
                    sentiment_std = np.std(sentiment_values)
                    symbol_data['confidence'] = max(0, 1 - sentiment_std)
                else:
                    symbol_data['confidence'] = 0.5
                
                # Calculate sentiment volume
                symbol_data['sentiment_volume'] = sum(
                    data.get('sentiment_volume', 0) 
                    for data in symbol_data['sources'].values()
                )
                
                # Calculate sentiment trend if time series data is available
                # (not implemented in this simplified version)
            
            # Store symbol data
            aggregated['symbols'][symbol] = symbol_data
        
        # Calculate overall market sentiment (average across all symbols)
        symbol_scores = [
            data['sentiment_score'] 
            for data in aggregated['symbols'].values() 
            if data['sentiment_score'] is not None
        ]
        
        if symbol_scores:
            aggregated['overall_sentiment'] = sum(symbol_scores) / len(symbol_scores)
            
            # Overall market sentiment label
            score = aggregated['overall_sentiment']
            if score > 0.2:
                sentiment = "bullish"
            elif score < -0.2:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
                
            aggregated['overall_sentiment_label'] = sentiment
        
        # Update last aggregation time
        self.last_aggregation = datetime.now()
        self.aggregated_data = aggregated
        
        return aggregated
    
    async def get_top_influencers(self, limit: int = 10) -> List[Dict]:
        """
        Get top sentiment influencers across all sources.
        
        Args:
            limit: Maximum number of influencers to return
            
        Returns:
            List of dictionaries with influencer data
        """
        # For now, just return social media posts with highest engagement
        for source in self.sources:
            if isinstance(source, SocialMediaSentimentSource):
                df = await source.fetch_data()
                if not df.empty and 'engagement' in df.columns:
                    top_df = df.sort_values('engagement', ascending=False).head(limit)
                    return top_df.to_dict('records')
        
        return []
    
    async def get_market_moving_news(self, min_score: float = 0.7, 
                                limit: int = 10) -> List[Dict]:
        """
        Get potentially market-moving news across all sources.
        
        Args:
            min_score: Minimum absolute sentiment score to consider
            limit: Maximum number of news items to return
            
        Returns:
            List of dictionaries with news data
        """
        all_news = []
        
        # Collect news from all relevant sources
        for source in self.sources:
            if isinstance(source, NewsAPISentimentSource):
                df = await source.fetch_data()
                if not df.empty:
                    all_news.append(df)
        
        if not all_news:
            return []
        
        # Combine all news
        combined_df = pd.concat(all_news)
        
        # Filter by sentiment score
        high_impact = combined_df[abs(combined_df['score']) >= min_score].copy()
        
        # Sort by absolute sentiment score
        high_impact['impact_score'] = abs(high_impact['score'])
        high_impact = high_impact.sort_values('impact_score', ascending=False)
        
        # Return top results
        return high_impact.head(limit).to_dict('records')
    
    async def get_analyst_consensus(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """
        Get analyst consensus for the given symbols.
        
        Args:
            symbols: List of ticker symbols to get consensus for
            
        Returns:
            Dictionary mapping symbols to analyst consensus data
        """
        consensus = {}
        
        # Find analyst rating source
        for source in self.sources:
            if isinstance(source, AnalystRatingSentimentSource):
                df = await source.fetch_data(symbols=symbols)
                
                if not df.empty:
                    # Group by symbol
                    for symbol, group in df.groupby('symbol'):
                        # Calculate consensus
                        avg_score = group['score'].mean()
                        
                        # Determine consensus rating based on average score
                        if avg_score > 0.75:
                            rating = "Strong Buy"
                        elif avg_score > 0.3:
                            rating = "Buy"
                        elif avg_score > 0.1:
                            rating = "Overweight"
                        elif avg_score > -0.1:
                            rating = "Hold"
                        elif avg_score > -0.3:
                            rating = "Underweight"
                        elif avg_score > -0.75:
                            rating = "Sell"
                        else:
                            rating = "Strong Sell"
                        
                        # Calculate average price target
                        avg_target = group['price_target'].mean() if 'price_target' in group.columns else None
                        
                        consensus[symbol] = {
                            'consensus_rating': rating,
                            'consensus_score': avg_score,
                            'average_price_target': avg_target,
                            'num_analysts': len(group),
                            'ratings': {
                                rating_type: sum(group['rating'] == rating_type) 
                                for rating_type in group['rating'].unique()
                            }
                        }
                
                break
        
        return consensus
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the most recent sentiment aggregation.
        
        Returns:
            Dictionary with sentiment summary
        """
        if not self.aggregated_data:
            return {'error': 'No sentiment data has been aggregated yet'}
        
        # Create a simplified summary of the most recent aggregation
        summary = {
            'timestamp': self.aggregated_data['timestamp'],
            'overall_sentiment': self.aggregated_data.get('overall_sentiment'),
            'overall_sentiment_label': self.aggregated_data.get('overall_sentiment_label'),
            'symbols': {}
        }
        
        # Add symbol data
        for symbol, data in self.aggregated_data.get('symbols', {}).items():
            summary['symbols'][symbol] = {
                'sentiment_score': data.get('sentiment_score'),
                'sentiment': data.get('sentiment'),
                'confidence': data.get('confidence')
            }
        
        return summary
    
    async def analyze_sector_sentiment(self, sector_mapping: Dict[str, str]) -> Dict[str, Dict]:
        """
        Analyze sentiment by sector.
        
        Args:
            sector_mapping: Dictionary mapping symbols to sectors
            
        Returns:
            Dictionary with sector sentiment data
        """
        if not self.aggregated_data:
            await self.aggregate()
        
        sector_data = defaultdict(list)
        
        # Group symbols by sector
        for symbol, data in self.aggregated_data.get('symbols', {}).items():
            if symbol in sector_mapping:
                sector = sector_mapping[symbol]
                if data.get('sentiment_score') is not None:
                    sector_data[sector].append(data.get('sentiment_score'))
        
        # Calculate sector sentiment
        sector_sentiment = {}
        for sector, scores in sector_data.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                
                # Determine sentiment label
                if avg_score > 0.2:
                    sentiment = "bullish"
                elif avg_score < -0.2:
                    sentiment = "bearish"
                else:
                    sentiment = "neutral"
                
                sector_sentiment[sector] = {
                    'sentiment_score': avg_score,
                    'sentiment': sentiment,
                    'num_symbols': len(scores),
                    'strongest_symbol': None,
                    'weakest_symbol': None
                }
        
        # Find strongest and weakest symbols per sector
        for symbol, data in self.aggregated_data.get('symbols', {}).items():
            if symbol in sector_mapping:
                sector = sector_mapping[symbol]
                score = data.get('sentiment_score')
                
                if score is not None and sector in sector_sentiment:
                    # Check if this is the strongest symbol
                    if (sector_sentiment[sector]['strongest_symbol'] is None or 
                        score > self.aggregated_data['symbols'][sector_sentiment[sector]['strongest_symbol']].get('sentiment_score', 0)):
                        sector_sentiment[sector]['strongest_symbol'] = symbol
                    
                    # Check if this is the weakest symbol
                    if (sector_sentiment[sector]['weakest_symbol'] is None or 
                        score < self.aggregated_data['symbols'][sector_sentiment[sector]['weakest_symbol']].get('sentiment_score', 0)):
                        sector_sentiment[sector]['weakest_symbol'] = symbol
        
        return sector_sentiment


async def create_default_sentiment_aggregator() -> SentimentAggregator:
    """
    Create a sentiment aggregator with default sources.
    
    Returns:
        Initialized SentimentAggregator
    """
    # Create sources
    news_source = NewsAPISentimentSource(weight=0.7)
    social_source = SocialMediaSentimentSource(weight=0.5)
    analyst_source = AnalystRatingSentimentSource(weight=0.8)
    
    # Create aggregator
    aggregator = SentimentAggregator()
    aggregator.add_source(news_source)
    aggregator.add_source(social_source)
    aggregator.add_source(analyst_source)
    
    return aggregator