from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)

    # Asset identification
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)  # stock, crypto, bond, etf, option
    exchange = Column(String(100), nullable=True)

    # Asset details
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)

    # Status
    is_tradable = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)

    # Asset reference
    symbol = Column(String(20), nullable=False, index=True)

    # Price data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Additional metrics
    vwap = Column(Float, nullable=True)  # Volume Weighted Average Price
    previous_close = Column(Float, nullable=True)
    change = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)

    # Data source and timing
    data_source = Column(String(50), nullable=False)  # alpha_vantage, polygon, etc.
    timestamp = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String(20), nullable=False)  # 1min, 5min, 1hour, 1day

    # Data quality
    is_adjusted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Create composite index for efficient queries
    __table_args__ = (
        Index("idx_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_symbol_timeframe_timestamp", "symbol", "timeframe", "timestamp"),
    )


class MarketSentiment(Base):
    __tablename__ = "market_sentiment"

    id = Column(Integer, primary_key=True, index=True)

    # Asset reference
    symbol = Column(String(20), nullable=True, index=True)  # None for overall market

    # Sentiment metrics
    sentiment_score = Column(
        Float, nullable=False
    )  # -1 (very negative) to 1 (very positive)
    confidence_score = Column(Float, nullable=False)  # 0 to 1

    # Source information
    source = Column(String(100), nullable=False)  # news, social_media, analyst_reports
    headline = Column(Text, nullable=True)
    content_summary = Column(Text, nullable=True)

    # Analysis details
    keywords = Column(Text, nullable=True)  # JSON array of relevant keywords
    entities = Column(Text, nullable=True)  # JSON array of detected entities

    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for sentiment analysis queries
    __table_args__ = (Index("idx_symbol_timestamp_sentiment", "symbol", "timestamp"),)


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)

    # Asset reference
    symbol = Column(String(20), nullable=False, index=True)

    # Indicator details
    indicator_name = Column(String(50), nullable=False)  # RSI, MACD, SMA, etc.
    timeframe = Column(String(20), nullable=False)  # 1day, 1hour, etc.

    # Indicator values (flexible schema for different indicators)
    value = Column(Float, nullable=True)
    signal_line = Column(Float, nullable=True)
    histogram = Column(Float, nullable=True)
    upper_band = Column(Float, nullable=True)
    lower_band = Column(Float, nullable=True)

    # Additional metadata
    parameters = Column(Text, nullable=True)  # JSON string of indicator parameters

    # Signal interpretation
    signal = Column(String(20), nullable=True)  # buy, sell, hold, neutral
    strength = Column(Float, nullable=True)  # Signal strength 0-1

    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for technical analysis queries
    __table_args__ = (
        Index(
            "idx_symbol_indicator_timestamp", "symbol", "indicator_name", "timestamp"
        ),
    )
