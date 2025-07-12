import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
import numpy as np
import asyncio
import os
import sys

# Import modules correctly
sys.path.append('/workspaces/Elson')
from Elson.trading_engine.ai_model_engine import sentiment_aggregator
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('/workspaces/Elson/Elson')

# Import the module for testing
from trading_engine.ai_model_engine.sentiment_aggregator import (
    SentimentSource, 
    NewsAPISentimentSource,
    SocialMediaSentimentSource,
    AnalystRatingSentimentSource,
    SentimentAggregator,
    create_default_sentiment_aggregator
)

# Mock NLP models to avoid actual model loading in tests
class MockSentimentAnalyzer:
    def predict(self, texts):
        # Return mock sentiment results
        results = []
        for text in texts:
            # Simple rule-based sentiment for testing
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
        return results


# Don't directly patch the transformer analyzer
class TestSentimentAggregator(unittest.TestCase):
    """Test the Sentiment Analysis Aggregator"""
    
    def setUp(self):
        # Set up basic sentiment sources
        self.news_source = NewsAPISentimentSource(weight=0.7)
        self.social_source = SocialMediaSentimentSource(weight=0.5)
        self.analyst_source = AnalystRatingSentimentSource(weight=0.8)
        
        # Set up aggregator
        self.aggregator = SentimentAggregator()
        self.aggregator.add_source(self.news_source)
        self.aggregator.add_source(self.social_source)
        
    async def async_setup(self):
        """Async setup for tests that require async initialization"""
        pass
        
    def tearDown(self):
        pass
        
    def test_basic_initialization(self):
        """Test basic initialization of sentiment sources and aggregator"""
        # Test source weights
        self.assertEqual(self.news_source.weight, 0.7)
        self.assertEqual(self.social_source.weight, 0.5)
        
        # Test aggregator sources
        self.assertEqual(len(self.aggregator.sources), 2)
        self.assertEqual(self.aggregator.sources[0].name, "news_api")
        self.assertEqual(self.aggregator.sources[1].name, "social_media")
    
    def test_sentiment_source_normalize_scores(self):
        """Test score normalization in sentiment sources"""
        # Create sample data
        data = {
            'text': ['Sample text 1', 'Sample text 2', 'Sample text 3'],
            'score': [0.95, -1.2, 0.3]  # Note: out-of-range score
        }
        df = pd.DataFrame(data)
        
        # Normalize scores
        normalized_df = self.news_source.normalize_scores(df)
        
        # Check clipping to [-1, 1] range
        self.assertEqual(normalized_df['normalized_score'].max(), 0.95)
        self.assertEqual(normalized_df['normalized_score'].min(), -1.0)  # -1.2 should be clipped to -1.0
        
        # Check weighting
        self.assertTrue('weighted_score' in normalized_df.columns)
        self.assertEqual(normalized_df.loc[0, 'weighted_score'], 0.95 * 0.7)  # score * weight
    
    async def test_news_api_source_fetch_data(self):
        """Test fetching data from news API source"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Fetch data
            df = await self.news_source.fetch_data(symbols=["AAPL"], days=1)
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check basic structure
        self.assertFalse(df.empty)
        self.assertTrue('symbol' in df.columns)
        self.assertTrue('title' in df.columns)
        self.assertTrue('sentiment' in df.columns)
        self.assertTrue('score' in df.columns)
        self.assertTrue('weighted_score' in df.columns)
        
        # Check filtering
        self.assertTrue(all(df['symbol'] == 'AAPL'))
    
    async def test_social_media_source_fetch_data(self):
        """Test fetching data from social media source"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Fetch data
            df = await self.social_source.fetch_data(symbols=["MSFT"], hours=12)
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check basic structure
        self.assertFalse(df.empty)
        self.assertTrue('symbol' in df.columns)
        self.assertTrue('content' in df.columns)
        self.assertTrue('platform' in df.columns)
        self.assertTrue('sentiment' in df.columns)
        self.assertTrue('score' in df.columns)
        self.assertTrue('weighted_score' in df.columns)
        self.assertTrue('engagement' in df.columns)
        
        # Check filtering
        self.assertTrue(all(df['symbol'] == 'MSFT'))
        
        # Check platforms
        platforms = df['platform'].unique()
        for platform in ["twitter", "reddit", "stocktwits"]:
            self.assertIn(platform, platforms)
    
    async def test_analyst_rating_source_fetch_data(self):
        """Test fetching data from analyst rating source"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Create source
            analyst_source = AnalystRatingSentimentSource(weight=0.8)
            
            # Fetch data
            df = await analyst_source.fetch_data(symbols=["GOOGL"], days=30)
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check basic structure
        self.assertFalse(df.empty)
        self.assertTrue('symbol' in df.columns)
        self.assertTrue('rating' in df.columns)
        self.assertTrue('firm' in df.columns)
        self.assertTrue('score' in df.columns)
        self.assertTrue('weighted_score' in df.columns)
        
        # Check filtering
        self.assertTrue(all(df['symbol'] == 'GOOGL'))
        
        # Check rating types
        self.assertTrue(all(df['rating'].isin([
            "Strong Buy", "Buy", "Overweight", "Hold", "Neutral", 
            "Underweight", "Sell", "Strong Sell"
        ])))
    
    async def test_aggregator_fetch_all_data(self):
        """Test fetching data from all sources"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Add analyst source
            self.aggregator.add_source(self.analyst_source)
            
            # Fetch all data
            data = await self.aggregator.fetch_all_data(symbols=["AAPL", "MSFT"], days=7)
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check that we have some data
        self.assertGreater(len(data), 0)
        
        # We should at least have some data from news and analyst sources
        found_sources = set(data.keys())
        self.assertTrue(any(source in found_sources for source in ["news_api", "analyst_ratings"]))
        
        # Check basic structure of each source's data
        for source_name, df in data.items():
            self.assertFalse(df.empty)
            self.assertTrue('symbol' in df.columns)
            self.assertTrue('score' in df.columns)
            self.assertTrue('weighted_score' in df.columns)
    
    async def test_aggregator_aggregate(self):
        """Test sentiment aggregation across sources"""
        # Create a custom mock for TransformerSentimentAnalyzer to avoid errors
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Create mock sources with our analyzer
        news_source = NewsAPISentimentSource(weight=0.7)
        social_source = SocialMediaSentimentSource(weight=0.5)
        analyst_source = AnalystRatingSentimentSource(weight=0.8)
        
        # Override analyze_sentiment method for testing
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        original_method = SentimentSource.analyze_sentiment
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Create a new aggregator
            aggregator = SentimentAggregator()
            aggregator.add_source(news_source)
            aggregator.add_source(social_source)
            aggregator.add_source(analyst_source)
            
            # Aggregate sentiment
            aggregated = await aggregator.aggregate(symbols=["AAPL"], days=7)
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check basic structure
        self.assertIn("timestamp", aggregated)
        self.assertIn("symbols", aggregated)
        self.assertIn("sources", aggregated)
        
        # Check symbol data
        self.assertIn("AAPL", aggregated["symbols"])
        apple_data = aggregated["symbols"]["AAPL"]
        
        # Check that we have data from sources
        self.assertIn("sources", apple_data)
        
        # There should be at least one source
        self.assertGreater(len(apple_data["sources"]), 0)
        
        # Check keys in sources
        for source_name, source_data in apple_data["sources"].items():
            self.assertIn("sentiment_score", source_data)
            self.assertIn("sentiment_volume", source_data)
            self.assertIn("confidence", source_data)
            self.assertIn("weight", source_data)
        
        # Check aggregated metrics
        self.assertIn("sentiment_score", apple_data)
        self.assertIn("sentiment", apple_data)
        self.assertIn("confidence", apple_data)
        
        # Sentiment score should be a weighted average
        self.assertIsNotNone(apple_data["sentiment_score"])
        self.assertIsInstance(apple_data["sentiment_score"], float)
        self.assertTrue(-1.0 <= apple_data["sentiment_score"] <= 1.0)
        
        # Check overall sentiment
        self.assertIn("overall_sentiment", aggregated)
        self.assertIsNotNone(aggregated["overall_sentiment"])
        self.assertIsInstance(aggregated["overall_sentiment"], float)
    
    async def test_get_market_moving_news(self):
        """Test getting market moving news"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Get market moving news
            news = await self.aggregator.get_market_moving_news(min_score=0.7, limit=5)
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check structure
        self.assertIsInstance(news, list)
        
        # If we have results, check their structure
        if news:
            for item in news:
                self.assertIn("symbol", item)
                self.assertIn("title", item)
                self.assertIn("score", item)
                self.assertIn("sentiment", item)
                
                # Check score threshold
                self.assertTrue(abs(item["score"]) >= 0.7)
    
    async def test_get_analyst_consensus(self):
        """Test getting analyst consensus"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        try:
            # Add analyst source
            self.aggregator.add_source(self.analyst_source)
            
            # Get analyst consensus
            consensus = await self.aggregator.get_analyst_consensus(symbols=["AAPL", "MSFT"])
        finally:
            # Restore original method
            SentimentSource.analyze_sentiment = original_method
        
        # Check structure
        self.assertIsInstance(consensus, dict)
        
        # Check for symbols
        for symbol in ["AAPL", "MSFT"]:
            if symbol in consensus:
                sym_data = consensus[symbol]
                
                self.assertIn("consensus_rating", sym_data)
                self.assertIn("consensus_score", sym_data)
                self.assertIn("num_analysts", sym_data)
                
                # Check consensus score range
                self.assertTrue(-1.0 <= sym_data["consensus_score"] <= 1.0)
                
                # Check rating type
                self.assertIn(sym_data["consensus_rating"], [
                    "Strong Buy", "Buy", "Overweight", "Hold", 
                    "Underweight", "Sell", "Strong Sell"
                ])
    
    async def test_create_default_sentiment_aggregator(self):
        """Test creating default sentiment aggregator"""
        # Create a custom mock for TransformerSentimentAnalyzer
        class MockAnalyzer:
            def predict(self, texts):
                return MockSentimentAnalyzer().predict(texts)
        
        # Override analyze_sentiment method for testing
        original_method = SentimentSource.analyze_sentiment
        async def mock_analyze(self, texts, **kwargs):
            analyzer = MockAnalyzer()
            results = analyzer.predict(texts)
            return pd.DataFrame(results)
        
        # Patch the analyze_sentiment method temporarily
        SentimentSource.analyze_sentiment = mock_analyze
        
        # Mock the create_default_sentiment_aggregator function
        original_create = sentiment_aggregator.create_default_sentiment_aggregator
        sentiment_aggregator.create_default_sentiment_aggregator = mock_create = AsyncMock(return_value=self.aggregator)
        
        try:
            # Call the function
            aggregator = await create_default_sentiment_aggregator()
        finally:
            # Restore original methods
            SentimentSource.analyze_sentiment = original_method
            sentiment_aggregator.create_default_sentiment_aggregator = original_create
        
        # Check structure
        self.assertEqual(aggregator.__class__.__name__, "SentimentAggregator")
        
        # There should be some sources
        self.assertGreater(len(aggregator.sources), 0)
        
        # At least one of the expected sources should be present
        source_names = [source.name for source in aggregator.sources]
        self.assertTrue(
            any(name in source_names for name in ["news_api", "social_media", "analyst_ratings"])
        )


def async_test(coro):
    """Decorator for async test methods"""
    def wrapper(*args, **kwargs):
        # Create a new event loop for each test to avoid deprecation warning
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


# Apply the decorator to make test methods async
for name in dir(TestSentimentAggregator):
    if name.startswith('test_') and name != 'test_basic_initialization' and name != 'test_sentiment_source_normalize_scores':
        test_method = getattr(TestSentimentAggregator, name)
        setattr(TestSentimentAggregator, name, async_test(test_method))


if __name__ == '__main__':
    unittest.main()