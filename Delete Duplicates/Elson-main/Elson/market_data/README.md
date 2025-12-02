# Market Data for Hybrid Model Testing and Training

This directory contains historical market data files used for testing and training the Elson Wealth Trading Platform hybrid models.

## Data Protocol

As per our updated protocol, we now ALWAYS test and train with real market data and historical data. Synthetic data should only be used as a fallback during development when real data is unavailable.

## Data Sources

1. Historical data CSV files should be placed in this directory with the naming convention:
   - `{SYMBOL}_historical.csv` (e.g., "SPY_historical.csv")

2. Data can be obtained from various sources:
   - Yahoo Finance (recommended for testing)
   - Alpha Vantage
   - IEX Cloud
   - Polygon.io
   - Other market data providers with appropriate licensing

## CSV Format

The expected CSV format is:

```
date,open,high,low,close,volume
2023-01-01,100.0,102.0,99.0,101.5,1000000
2023-01-02,101.5,103.0,100.5,102.0,1200000
...
```

Additional columns like 'adj_close' or 'returns' may be included but are not required.

## Performance Targets

Our updated performance targets are:

1. Minimum targets (required):
   - High Volatility Win Rate: ≥ 60%
   - Extreme Volatility Win Rate: ≥ 60%
   - Volatility Robustness: ≤ 10pp

2. Aspirational goal (target):
   - Average Win Rate: ≥ 70% across all regimes

## Historical Periods of Interest

For thorough testing, include data from these specific historical periods of high volatility:

1. March 2020 (COVID-19 market crash)
2. October 2022 (inflation/rate hike volatility)
3. March 2023 (banking crisis volatility)
4. Any periods with VIX > 30

## Data Loading

The live_test/run_live_market_test.py script is designed to automatically load historical data from this directory. It will calculate volatility if not already included in the dataset.

## Notes

- Do not commit large data files to the repository
- Consider using a .gitignore pattern for large CSV files
- For CI/CD environments, ensure data is available through an automated download process