"""
Data Engine for the trading bot.
Handles data collection, preprocessing, and feature engineering.
"""

from .data_sources import (
    DataSource, 
    MarketDataSource, 
    NewsDataSource, 
    EconomicDataSource,
    OrderBookDataSource,
    create_data_source
)

from .feature_engineering import (
    FeatureEngineering,
    SentimentFeatures,
    DataCombiner,
    prepare_ml_features
)

__all__ = [
    'DataSource',
    'MarketDataSource',
    'NewsDataSource',
    'EconomicDataSource',
    'OrderBookDataSource',
    'create_data_source',
    'FeatureEngineering',
    'SentimentFeatures',
    'DataCombiner',
    'prepare_ml_features'
]