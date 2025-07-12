# Volatility Regime Testing Framework

This directory contains the framework for testing trading models across different volatility regimes for the Elson Wealth Trading Platform.

## Overview

The volatility regime testing framework allows comprehensive evaluation of quantum and classical trading models under varying market conditions, from low to extreme volatility. This ensures that models maintain performance regardless of market conditions.

## Key Features

- **Volatility Classification**: Automatically segments historical data into volatility regimes
- **Comprehensive Testing**: Tests models across all regimes with the same evaluation criteria
- **Performance Visualization**: Creates charts showing performance by volatility regime
- **Robustness Metrics**: Calculates volatility robustness scores to measure consistency
- **Hybrid Model Testing**: Includes specialized models designed for high volatility conditions

## Volatility Regimes

The framework classifies market data into four volatility regimes:

1. **LOW**: 0-15% annualized volatility (calm markets)
2. **NORMAL**: 15-25% annualized volatility (typical market conditions)
3. **HIGH**: 25-40% annualized volatility (stressed markets)
4. **EXTREME**: >40% annualized volatility (crisis conditions)

## Usage

Run the testing framework with:

```bash
# Basic usage with default symbols
python quantum_model_evaluation.py

# Extended testing with more symbols
python quantum_model_evaluation.py --extended_symbols

# Test with specific date range
python quantum_model_evaluation.py --start_date 2020-01-01 --end_date 2022-12-31

# Disable volatility regime testing (tests on full dataset only)
python quantum_model_evaluation.py --no_volatility_test
```

## Output

The framework produces:

1. **JSON Results**: Detailed performance metrics for each model by regime
2. **Performance Charts**: Visual comparison of models across regimes
3. **Volatility Robustness Chart**: Shows consistency of model performance
4. **Win Rate Comparisons**: Compares quantum vs classical models

## Interpretation

A successful model should:

1. Maintain win rate >60% across all volatility regimes
2. Show performance differential ≤10 percentage points between regimes
3. Outperform classical models in high and extreme volatility regimes

## Implementation Details

The framework:

1. Calculates 20-day rolling volatility for classification
2. Identifies continuous periods within each regime for testing
3. Runs models with regime-specific parameter adjustments
4. Aggregates results and calculates robustness metrics

## Advanced Features

- **Parameter Optimization**: Automatically adjusts model parameters by regime
- **Circuit Breaker Testing**: Verifies models correctly reduce position sizing
- **Extended Symbol Set**: Tests across diverse assets including ETFs, sectors, and volatility indices

For more details on the implementation, see the code documentation in `quantum_model_evaluation.py`.