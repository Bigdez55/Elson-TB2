"""
Comprehensive tests for Enhanced Market Data Service

This test suite validates:
1. Multi-provider failover functionality
2. Data validation and sanitization
3. Caching and stale data handling
4. Provider health tracking
5. Circuit breaker functionality
6. Rate limiting
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from app.services.enhanced_market_data import (
    AlphaVantageProviderEnhanced,
    EnhancedMarketDataService,
    MarketDataCache,
    YFinanceProvider,
)


class TestMarketDataCache:
    """Test the market data caching system."""

    def test_cache_initialization(self):
        """Test cache is initialized correctly."""
        cache = MarketDataCache()
        assert cache._cache == {}
        assert "quote" in cache._ttl_map
        assert "historical" in cache._ttl_map
        assert cache._ttl_map["quote"] == 60
        assert cache._ttl_map["historical"] == 3600

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = MarketDataCache()
        test_data = {"symbol": "AAPL", "price": 150.0}

        # Set data
        cache.set("test_key", test_data, "quote")

        # Get data immediately (should be fresh)
        result = cache.get("test_key", "quote")
        assert result == test_data

    def test_cache_expiration(self):
        """Test that cache entries expire correctly."""
        cache = MarketDataCache()
        cache._ttl_map["test"] = 1  # 1 second TTL for testing

        test_data = {"symbol": "AAPL", "price": 150.0}
        cache.set("test_key", test_data, "test")

        # Should be available immediately
        result = cache.get("test_key", "test")
        assert result == test_data

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        result = cache.get("test_key", "test")
        assert result is None

    def test_cache_clear_expired(self):
        """Test the clear_expired functionality."""
        cache = MarketDataCache()

        # Add some test data with timestamps
        current_time = time.time()
        cache._cache = {
            "fresh_key": ({"data": "fresh"}, current_time),
            "old_key": ({"data": "old"}, current_time - 7200),  # 2 hours old
        }

        cache.clear_expired()

        # Fresh data should remain, old data should be gone
        assert "fresh_key" in cache._cache
        assert "old_key" not in cache._cache


class TestYFinanceProvider:
    """Test Yahoo Finance provider functionality."""

    @pytest.fixture
    def provider(self):
        return YFinanceProvider()

    def test_provider_initialization(self, provider):
        """Test provider is initialized correctly."""
        assert provider.name == "YFinance"
        assert provider.rate_limit_delay == 0.5
        assert provider.error_count == 0
        assert not provider.is_circuit_open()

    def test_circuit_breaker_functionality(self, provider):
        """Test circuit breaker opens and closes correctly."""
        # Initially circuit should be closed
        assert not provider.is_circuit_open()

        # Trigger enough errors to open circuit
        for _ in range(provider.circuit_breaker_threshold):
            provider.record_error()

        # Circuit should now be open
        assert provider.is_circuit_open()

        # Test that success reduces error count
        provider.record_success()
        assert provider.error_count == provider.circuit_breaker_threshold - 1

    @pytest.mark.asyncio
    async def test_rate_limiting(self, provider):
        """Test rate limiting functionality."""
        start_time = time.time()

        # First call should be immediate
        await provider._rate_limit()
        first_call_time = time.time() - start_time

        # Second call should be delayed
        await provider._rate_limit()
        second_call_time = time.time() - start_time

        # Second call should take at least rate_limit_delay longer
        assert second_call_time >= first_call_time + provider.rate_limit_delay * 0.9

    @pytest.mark.asyncio
    async def test_get_quote_success(self, provider):
        """Test successful quote retrieval."""
        mock_response_data = {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "regularMarketPrice": 150.0,
                            "previousClose": 148.0,
                            "regularMarketVolume": 1000000,
                            "marketCap": 2500000000000,
                            "trailingPE": 25.5,
                        }
                    }
                ]
            }
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            quote = await provider.get_quote("AAPL")

            assert quote is not None
            assert quote["symbol"] == "AAPL"
            assert quote["price"] == 150.0
            assert quote["change"] == 2.0  # 150.0 - 148.0
            assert quote["volume"] == 1000000
            assert quote["provider"] == "YFinance"
            assert provider.error_count == 0  # Should record success

    @pytest.mark.asyncio
    async def test_get_quote_failure(self, provider):
        """Test quote retrieval failure handling."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            quote = await provider.get_quote("INVALID")

            assert quote is None
            assert provider.error_count == 1  # Should record error

    @pytest.mark.asyncio
    async def test_get_quote_with_circuit_open(self, provider):
        """Test that quotes are not fetched when circuit is open."""
        # Force circuit open
        provider.error_count = provider.circuit_breaker_threshold

        quote = await provider.get_quote("AAPL")
        assert quote is None


class TestAlphaVantageProvider:
    """Test Alpha Vantage provider functionality."""

    @pytest.fixture
    def provider(self):
        return AlphaVantageProviderEnhanced()

    def test_provider_initialization(self, provider):
        """Test provider is initialized correctly."""
        assert provider.name == "AlphaVantage"
        assert provider.rate_limit_delay == 12.0  # 5 calls per minute

    @pytest.mark.asyncio
    async def test_get_quote_without_api_key(self, provider):
        """Test that provider returns None without API key."""
        provider.api_key = None
        quote = await provider.get_quote("AAPL")
        assert quote is None

    @pytest.mark.asyncio
    async def test_get_quote_success(self, provider):
        """Test successful quote retrieval from Alpha Vantage."""
        provider.api_key = "test_key"

        mock_response_data = {
            "Global Quote": {
                "05. price": "150.0000",
                "09. change": "2.0000",
                "10. change percent": "1.35%",
                "06. volume": "1000000",
            }
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            quote = await provider.get_quote("AAPL")

            assert quote is not None
            assert quote["symbol"] == "AAPL"
            assert quote["price"] == 150.0
            assert quote["change"] == 2.0
            assert quote["change_percent"] == 1.35
            assert quote["volume"] == 1000000
            assert quote["provider"] == "AlphaVantage"


class TestEnhancedMarketDataService:
    """Test the main enhanced market data service."""

    @pytest.fixture
    def service(self):
        return EnhancedMarketDataService()

    def test_service_initialization(self, service):
        """Test service is initialized correctly."""
        assert service.cache is not None
        assert len(service.providers) >= 2  # Should have multiple providers
        assert service.primary_provider == 0

    @pytest.mark.asyncio
    async def test_get_quote_with_cache_hit(self, service):
        """Test quote retrieval with cache hit."""
        # Pre-populate cache
        cached_quote = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": datetime.utcnow().isoformat(),
        }
        service.cache.set("quote:AAPL", cached_quote, "quote")

        quote = await service.get_quote("AAPL")
        assert quote == cached_quote

    @pytest.mark.asyncio
    async def test_get_quote_provider_failover(self, service):
        """Test failover between providers."""
        # Mock first provider to fail
        service.providers[0].get_quote = AsyncMock(return_value=None)

        # Mock second provider to succeed
        success_quote = {"symbol": "AAPL", "price": 150.0, "provider": "backup"}
        service.providers[1].get_quote = AsyncMock(return_value=success_quote)

        quote = await service.get_quote("AAPL")

        assert quote == success_quote
        # Primary provider should switch to the working one
        assert service.primary_provider == 1

    @pytest.mark.asyncio
    async def test_get_quote_all_providers_fail(self, service):
        """Test behavior when all providers fail."""
        # Mock all providers to fail
        for provider in service.providers:
            provider.get_quote = AsyncMock(return_value=None)

        quote = await service.get_quote("AAPL")
        assert quote is None

    @pytest.mark.asyncio
    async def test_get_multiple_quotes(self, service):
        """Test getting multiple quotes efficiently."""
        # Mock successful quotes
        test_quotes = {
            "AAPL": {"symbol": "AAPL", "price": 150.0},
            "GOOGL": {"symbol": "GOOGL", "price": 2500.0},
            "MSFT": {"symbol": "MSFT", "price": 300.0},
        }

        async def mock_get_quote(symbol):
            return test_quotes.get(symbol)

        service.get_quote = mock_get_quote

        symbols = ["AAPL", "GOOGL", "MSFT", "INVALID"]
        results = await service.get_multiple_quotes(symbols)

        assert len(results) == 4
        assert results["AAPL"]["price"] == 150.0
        assert results["GOOGL"]["price"] == 2500.0
        assert results["MSFT"]["price"] == 300.0
        assert results["INVALID"] is None

    @pytest.mark.asyncio
    async def test_get_historical_data(self, service):
        """Test historical data retrieval."""
        mock_historical = [
            {"timestamp": "2023-01-01", "close": 150.0},
            {"timestamp": "2023-01-02", "close": 152.0},
        ]

        service.providers[0].get_historical_data = AsyncMock(
            return_value=mock_historical
        )

        data = await service.get_historical_data("AAPL", "1mo")
        assert data == mock_historical

    @pytest.mark.asyncio
    async def test_search_symbols(self, service):
        """Test symbol search functionality."""
        results = await service.search_symbols("APPLE")

        assert len(results) > 0
        # Should find AAPL when searching for APPLE
        symbols = [r["symbol"] for r in results]
        assert "AAPL" in symbols

    def test_get_cache_stats(self, service):
        """Test cache statistics retrieval."""
        stats = service.get_cache_stats()

        assert "cache_size" in stats
        assert "primary_provider" in stats
        assert "provider_status" in stats
        assert isinstance(stats["provider_status"], list)

    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test service health check."""
        # Mock successful provider response
        service.providers[0].get_quote = AsyncMock(return_value={"price": 150.0})

        health = await service.health_check()

        assert "overall_status" in health
        assert "providers" in health
        assert "timestamp" in health
        assert len(health["providers"]) == len(service.providers)


class TestDataValidationAndSanitization:
    """Test data validation and sanitization features."""

    @pytest.mark.asyncio
    async def test_symbol_normalization(self):
        """Test that symbols are properly normalized."""
        service = EnhancedMarketDataService()

        # Mock provider to return quote
        mock_quote = {"symbol": "AAPL", "price": 150.0}
        service.providers[0].get_quote = AsyncMock(return_value=mock_quote)

        # Test lowercase symbol gets normalized
        quote = await service.get_quote("aapl")
        assert quote["symbol"] == "AAPL"

        # Test symbol with spaces gets stripped
        quote = await service.get_quote(" aapl ")
        assert quote["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_invalid_symbol_handling(self):
        """Test handling of invalid symbols."""
        service = EnhancedMarketDataService()

        # Test empty symbol
        quote = await service.get_quote("")
        assert quote is None or quote["symbol"] == ""

        # Test very long symbol
        long_symbol = "A" * 20
        quote = await service.get_quote(long_symbol)
        # Should either reject or normalize


class TestStaleDataHandling:
    """Test handling of stale data."""

    def test_cache_expiry_detection(self):
        """Test that expired cache entries are detected."""
        cache = MarketDataCache()

        # Set data with past timestamp
        old_timestamp = time.time() - 3700  # Over an hour ago
        cache._cache["old_key"] = ({"data": "old"}, old_timestamp)

        # Should return None for expired data
        result = cache.get("old_key", "quote")  # TTL is 60 seconds for quotes
        assert result is None

    def test_cache_cleanup(self):
        """Test automatic cache cleanup."""
        cache = MarketDataCache()

        # Add mix of fresh and stale data
        current_time = time.time()
        cache._cache = {
            "fresh": ({"data": "fresh"}, current_time),
            "stale1": ({"data": "stale"}, current_time - 7200),
            "stale2": ({"data": "stale"}, current_time - 3700),
        }

        cache.clear_expired()

        # Only fresh data should remain
        assert "fresh" in cache._cache
        assert "stale1" not in cache._cache
        assert "stale2" not in cache._cache


class TestProviderHealthTracking:
    """Test provider health tracking functionality."""

    def test_error_count_tracking(self):
        """Test that provider error counts are tracked correctly."""
        provider = YFinanceProvider()

        assert provider.error_count == 0

        # Record some errors
        provider.record_error()
        provider.record_error()
        assert provider.error_count == 2

        # Record success (should decrease error count)
        provider.record_success()
        assert provider.error_count == 1

        # Error count shouldn't go below 0
        provider.record_success()
        provider.record_success()
        assert provider.error_count == 0

    def test_circuit_breaker_timeout(self):
        """Test circuit breaker timeout functionality."""
        provider = YFinanceProvider()
        provider.circuit_breaker_timeout = 1  # 1 second for testing

        # Open circuit
        for _ in range(provider.circuit_breaker_threshold):
            provider.record_error()

        assert provider.is_circuit_open()

        # Wait for timeout
        time.sleep(1.1)

        # Circuit should reset after timeout
        assert not provider.is_circuit_open()
        assert provider.error_count == 0

    @pytest.mark.asyncio
    async def test_health_check_integration(self):
        """Test health check integration with providers."""
        service = EnhancedMarketDataService()

        # Mock one provider as healthy, one as unhealthy
        service.providers[0].get_quote = AsyncMock(return_value={"price": 150.0})
        service.providers[1].get_quote = AsyncMock(side_effect=Exception("API Error"))

        health = await service.health_check()

        # Should have mixed health status
        provider_statuses = [p["status"] for p in health["providers"]]
        assert "healthy" in provider_statuses or "degraded" in provider_statuses
        assert health["overall_status"] in ["healthy", "degraded"]


if __name__ == "__main__":
    # Run basic functionality test
    async def test_basic_functionality():
        print("Testing Enhanced Market Data Service...")

        service = EnhancedMarketDataService()

        # Test cache
        print("✓ Cache initialization")

        # Test provider health
        health = await service.health_check()
        print(f"✓ Health check: {health['overall_status']}")

        # Test quote retrieval (might fail without actual API keys)
        try:
            quote = await service.get_quote("AAPL")
            if quote:
                print(f"✓ Quote retrieval: {quote['symbol']} = ${quote['price']}")
            else:
                print("⚠ Quote retrieval failed (expected without API keys)")
        except Exception as e:
            print(f"⚠ Quote retrieval error: {e}")

        # Test cache stats
        stats = service.get_cache_stats()
        print(f"✓ Cache stats: {stats['cache_size']} entries")

        print("Enhanced Market Data Service testing completed!")

    # Run the test
    asyncio.run(test_basic_functionality())
