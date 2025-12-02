"""
Tests for external API client implementations.

These tests validate that all API client implementations conform to the expected interface
and provide standardized responses for common operations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.external_api.factory import ApiProvider, api_factory
from app.services.external_api.base import BaseApiClient, ApiError
from app.services.external_api.alpha_vantage import AlphaVantageClient
from app.services.external_api.finnhub import FinnhubClient
from app.services.external_api.fmp import FMPClient
from app.services.external_api.polygon import PolygonClient
from app.services.external_api.coinbase import CoinbaseClient


# Common test data
TEST_SYMBOL = "AAPL"
CRYPTO_SYMBOL = "BTC"


@pytest.fixture
def mock_response():
    """Create a mock response for client tests."""
    return MagicMock()


@pytest.mark.asyncio
@pytest.mark.parametrize("client_class", [
    AlphaVantageClient,
    FinnhubClient,
    FMPClient,
    PolygonClient
])
async def test_get_stock_quote_interface(client_class, mock_response):
    """Test that stock quote method returns expected fields."""
    # Mock the client's get method
    with patch.object(client_class, "get", new_callable=AsyncMock) as mock_get:
        # Setup mock response
        # Each client has a different response format, but we're testing the output format
        mock_get.return_value = mock_response
        
        # Create client instance
        client = client_class(api_key="test_key")
        
        # Customize mock response for each client to allow proper processing
        if client_class == AlphaVantageClient:
            mock_response.get.side_effect = lambda key, default=None: {
                "Global Quote": {
                    "01. symbol": TEST_SYMBOL,
                    "05. price": "150.0",
                    "02. open": "149.0",
                    "03. high": "151.0",
                    "04. low": "148.0",
                    "06. volume": "1000000",
                    "07. latest trading day": "2023-01-01",
                    "08. previous close": "148.5",
                    "09. change": "1.5",
                    "10. change percent": "1.0%"
                }
            }.get(key, default)
        elif client_class == FinnhubClient:
            mock_response.get.side_effect = lambda key, default=None: {
                "c": 150.0,
                "o": 149.0,
                "h": 151.0,
                "l": 148.0,
                "pc": 148.5,
                "t": 1672531200
            }.get(key, default)
        elif client_class == FMPClient:
            mock_get.return_value = [{
                "symbol": TEST_SYMBOL,
                "price": 150.0,
                "open": 149.0,
                "dayHigh": 151.0,
                "dayLow": 148.0,
                "volume": 1000000,
                "previousClose": 148.5,
                "change": 1.5,
                "changesPercentage": 1.0
            }]
        elif client_class == PolygonClient:
            mock_response.get.side_effect = lambda key, default=None: {
                "status": "OK",
                "ticker": {
                    "day": {"o": 149.0, "h": 151.0, "l": 148.0, "v": 1000000},
                    "prevDay": {"c": 148.5},
                    "lastQuote": {"b": 149.9, "a": 150.1, "bs": 100, "as": 100, "t": 1672531200000},
                    "lastTrade": {"p": 150.0, "s": 100, "t": 1672531200000}
                }
            }.get(key, default)
        
        # Call the method
        result = await client.get_stock_quote(TEST_SYMBOL)
        
        # Check common fields that all implementations should provide
        assert isinstance(result, dict)
        assert "symbol" in result
        assert "price" in result
        assert isinstance(result["price"], (int, float))
        
        # Check that at least some of these common fields are present
        common_fields = ["open", "high", "low", "volume", "change", "change_percent", "previous_close"]
        assert any(field in result for field in common_fields)


@pytest.mark.asyncio
@pytest.mark.parametrize("client_class", [
    AlphaVantageClient,
    FinnhubClient,
    FMPClient,
    PolygonClient
])
async def test_get_historical_data_interface(client_class, mock_response):
    """Test that historical data method returns expected fields."""
    # Mock the client's get method
    with patch.object(client_class, "get", new_callable=AsyncMock) as mock_get:
        # Setup mock response based on client class
        if client_class == AlphaVantageClient:
            mock_get.return_value = {
                "Meta Data": {"2. Symbol": TEST_SYMBOL},
                "Time Series (Daily)": {
                    "2023-01-01": {
                        "1. open": "149.0",
                        "2. high": "151.0",
                        "3. low": "148.0",
                        "4. close": "150.0",
                        "5. volume": "1000000"
                    },
                    "2023-01-02": {
                        "1. open": "150.0",
                        "2. high": "152.0",
                        "3. low": "149.0",
                        "4. close": "151.0",
                        "5. volume": "1100000"
                    }
                }
            }
        elif client_class == FinnhubClient:
            mock_get.return_value = {
                "s": "ok",
                "t": [1672531200, 1672617600],
                "o": [149.0, 150.0],
                "h": [151.0, 152.0],
                "l": [148.0, 149.0],
                "c": [150.0, 151.0],
                "v": [1000000, 1100000]
            }
        elif client_class == FMPClient:
            mock_get.return_value = {
                "symbol": TEST_SYMBOL,
                "historical": [
                    {
                        "date": "2023-01-01",
                        "open": 149.0,
                        "high": 151.0,
                        "low": 148.0,
                        "close": 150.0,
                        "volume": 1000000
                    },
                    {
                        "date": "2023-01-02",
                        "open": 150.0,
                        "high": 152.0,
                        "low": 149.0,
                        "close": 151.0,
                        "volume": 1100000
                    }
                ]
            }
        elif client_class == PolygonClient:
            mock_get.return_value = {
                "status": "OK",
                "results": [
                    {
                        "t": 1672531200000,
                        "o": 149.0,
                        "h": 151.0,
                        "l": 148.0,
                        "c": 150.0,
                        "v": 1000000
                    },
                    {
                        "t": 1672617600000,
                        "o": 150.0,
                        "h": 152.0,
                        "l": 149.0,
                        "c": 151.0,
                        "v": 1100000
                    }
                ]
            }
        
        # Create client instance
        client = client_class(api_key="test_key")
        
        # Call the method
        result = await client.get_historical_data(
            TEST_SYMBOL,
            start_date="2023-01-01",
            end_date="2023-01-10",
            interval="daily"
        )
        
        # Check common structure
        assert isinstance(result, dict)
        assert "symbol" in result
        assert "interval" in result
        assert "data" in result
        assert isinstance(result["data"], list)
        
        # Check data points if there are any
        if result["data"]:
            data_point = result["data"][0]
            assert "date" in data_point
            assert "open" in data_point
            assert "high" in data_point
            assert "low" in data_point
            assert "close" in data_point
            assert "volume" in data_point


@pytest.mark.asyncio
@pytest.mark.parametrize("client_class", [
    AlphaVantageClient,
    FinnhubClient,
    FMPClient,
    PolygonClient
])
async def test_get_company_profile_interface(client_class, mock_response):
    """Test that company profile method returns expected fields."""
    # Mock the client's get method(s)
    with patch.object(client_class, "get", new_callable=AsyncMock) as mock_get:
        # Setup mock response based on client class
        if client_class == AlphaVantageClient:
            # For AlphaVantage, we'll need to mock both get_company_overview and get
            with patch.object(client_class, "get_company_overview", new_callable=AsyncMock) as mock_overview:
                mock_overview.return_value = {
                    "Symbol": TEST_SYMBOL,
                    "Name": "Apple Inc",
                    "Description": "Apple Inc. designs, manufactures, and markets smartphones...",
                    "Exchange": "NASDAQ",
                    "Sector": "Technology",
                    "Industry": "Consumer Electronics",
                    "MarketCapitalization": "2500000000000",
                    "PERatio": "30.5",
                    "DividendYield": "0.5",
                    "52WeekHigh": "180.0",
                    "52WeekLow": "120.0"
                }
                
                # Create client instance
                client = client_class(api_key="test_key")
                
                # Call the method
                result = await client.get_company_profile(TEST_SYMBOL)
        else:
            # For other clients, we'll mock the regular get method
            if client_class == FinnhubClient:
                mock_get.return_value = {
                    "ticker": TEST_SYMBOL,
                    "name": "Apple Inc",
                    "finnhubIndustry": "Technology",
                    "exchange": "NASDAQ",
                    "marketCapitalization": 2500,
                    "shareOutstanding": 16000,
                    "weburl": "https://www.apple.com",
                    "logo": "https://example.com/apple.png",
                    "phone": "1-800-275-2273",
                    "country": "US"
                }
            elif client_class == FMPClient:
                mock_get.return_value = [{
                    "symbol": TEST_SYMBOL,
                    "companyName": "Apple Inc",
                    "description": "Apple Inc. designs, manufactures, and markets smartphones...",
                    "exchange": "NASDAQ",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "mktCap": 2500000000000,
                    "pe": 30.5,
                    "lastDiv": 0.5,
                    "beta": 1.2,
                    "range": "120.0-180.0",
                    "country": "US",
                    "fullTimeEmployees": 150000,
                    "ceo": "Tim Cook",
                    "website": "https://www.apple.com",
                    "image": "https://example.com/apple.png",
                    "price": 150.0,
                    "changes": 1.5
                }]
            elif client_class == PolygonClient:
                # Polygon makes multiple requests, so we need a more complex mock
                mock_get.side_effect = [
                    {
                        "status": "OK",
                        "results": {
                            "ticker": TEST_SYMBOL,
                            "name": "Apple Inc",
                            "description": "Apple Inc. designs, manufactures, and markets smartphones...",
                            "primary_exchange": "NASDAQ",
                            "sic_description": "Electronic Computers",
                            "market_cap": 2500000000000,
                            "total_employees": 150000,
                            "homepage_url": "https://www.apple.com",
                            "branding": {"logo_url": "https://example.com/apple.png"},
                            "locale": "US",
                            "address": {"city": "Cupertino", "state": "CA"},
                            "type": "CS",
                            "currency_name": "USD",
                            "share_class_shares_outstanding": 16000000000
                        }
                    },
                    {
                        "status": "OK",
                        "results": [{
                            "ratios": {"pe": 30.5}
                        }]
                    }
                ]
            
            # Create client instance
            client = client_class(api_key="test_key")
            
            # Call the method
            result = await client.get_company_profile(TEST_SYMBOL)
        
        # Check common structure
        assert isinstance(result, dict)
        assert "symbol" in result
        assert "name" in result
        assert "provider" in result
        
        # Check for some common fields
        common_fields = ["description", "exchange", "sector", "industry", "market_cap", "website"]
        assert any(field in result for field in common_fields)


@pytest.mark.asyncio
async def test_coinbase_crypto_quote():
    """Test Coinbase client crypto quote method."""
    # Mock the client's get method
    with patch.object(CoinbaseClient, "get", new_callable=AsyncMock) as mock_get:
        # Setup mock response
        mock_get.return_value = {
            "data": {
                "base": "BTC",
                "currency": "USD",
                "amount": "50000"
            }
        }
        
        # Create client instance
        client = CoinbaseClient(api_key="test_key", api_secret="test_secret")
        
        # Call the method
        result = await client.get_stock_quote(CRYPTO_SYMBOL)
        
        # Check response structure
        assert isinstance(result, dict)
        assert "symbol" in result
        assert "price" in result
        assert "currency" in result
        assert result["symbol"] == "BTC"
        assert result["price"] == 50000.0
        assert result["currency"] == "USD"


@pytest.mark.asyncio
async def test_factory_provider_registration():
    """Test that all providers are properly registered in the factory."""
    # Import register to ensure all registrations happen
    from app.services.external_api import register
    
    # Check that all expected providers are available
    for provider in [
        ApiProvider.ALPHA_VANTAGE,
        ApiProvider.FINNHUB,
        ApiProvider.FMP,
        ApiProvider.POLYGON,
        ApiProvider.COINBASE
    ]:
        # This will raise an error if the provider is not registered
        assert provider in api_factory._registry