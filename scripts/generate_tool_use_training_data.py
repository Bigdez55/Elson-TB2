"""
Generate Tool-Use Training Data for Elson Financial AI

This script generates training examples that teach the model to:
1. Recognize when a tool should be called
2. Format the correct tool call
3. Analyze and respond using tool output

Target: 2,000 - 5,000 tool-use examples
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOLS = {
    "openbb_quote": {
        "description": "Get real-time quote for a stock symbol",
        "params": ["symbol"],
        "triggers": [
            "current price", "price now", "trading at", "stock price",
            "how much is", "what is the price", "quote for", "today's price"
        ]
    },
    "openbb_ohlcv": {
        "description": "Get historical price data (OHLCV)",
        "params": ["symbol", "start_date", "end_date"],
        "triggers": [
            "historical price", "price history", "performance over",
            "chart", "trend", "past month", "past year", "52 week"
        ]
    },
    "openbb_fundamentals": {
        "description": "Get company fundamentals overview",
        "params": ["symbol"],
        "triggers": [
            "company info", "fundamentals", "about the company",
            "revenue", "earnings", "market cap", "employees"
        ]
    },
    "openbb_news": {
        "description": "Get company news headlines",
        "params": ["symbol", "limit"],
        "triggers": [
            "news about", "headlines", "latest news", "what's happening",
            "recent developments", "announcements"
        ]
    },
    "openbb_macro": {
        "description": "Get macroeconomic data series",
        "params": ["series", "country"],
        "triggers": [
            "gdp", "inflation", "unemployment", "interest rates",
            "economic", "fed", "economy"
        ]
    },
    "financetoolkit_statements": {
        "description": "Get financial statements",
        "params": ["symbol", "period", "limit"],
        "triggers": [
            "income statement", "balance sheet", "cash flow",
            "financial statements", "quarterly results", "annual report"
        ]
    },
    "financetoolkit_ratios": {
        "description": "Get comprehensive financial ratios",
        "params": ["symbol", "period"],
        "triggers": [
            "p/e ratio", "roe", "roa", "profit margin", "debt ratio",
            "valuation", "financial health", "ratios"
        ]
    },
    "financetoolkit_category": {
        "description": "Get detailed ratios for a category with trends",
        "params": ["symbol", "category", "periods"],
        "triggers": [
            "profitability trend", "liquidity trend", "solvency",
            "historical ratios", "ratio history"
        ]
    },
    "financetoolkit_compare": {
        "description": "Compare ratios across multiple tickers",
        "params": ["symbols", "category"],
        "triggers": [
            "compare", "vs", "versus", "which is better",
            "peer comparison", "side by side"
        ]
    }
}


# =============================================================================
# SAMPLE STOCK UNIVERSE
# =============================================================================

STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financial"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive"},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Defensive"},
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy"},
    {"symbol": "HD", "name": "Home Depot Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financial"},
    {"symbol": "DIS", "name": "Walt Disney Co.", "sector": "Communication"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication"},
    {"symbol": "KO", "name": "Coca-Cola Co.", "sector": "Consumer Defensive"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology"},
]


# =============================================================================
# QUESTION TEMPLATES
# =============================================================================

QUOTE_QUESTIONS = [
    "What is {symbol}'s current stock price?",
    "How much is {symbol} trading at right now?",
    "Can you give me a quote for {symbol}?",
    "What's the current price of {name}?",
    "How is {symbol} doing today?",
    "What's {symbol} at?",
    "Give me the latest price for {symbol}",
    "I want to know {symbol}'s stock price",
    "Price check on {symbol}",
    "What's {name} ({symbol}) trading at?",
]

OHLCV_QUESTIONS = [
    "Show me {symbol}'s price history for the past month",
    "How has {symbol} performed over the last year?",
    "What's {symbol}'s 52-week high and low?",
    "Can you show me {symbol}'s historical price data?",
    "I want to see {name}'s stock chart data",
    "What was {symbol}'s price trend this quarter?",
    "Give me {symbol}'s historical performance",
    "How has {symbol} stock moved in the past 6 months?",
]

FUNDAMENTALS_QUESTIONS = [
    "Tell me about {name}",
    "What are {symbol}'s fundamentals?",
    "Give me an overview of {symbol}",
    "What's {symbol}'s market cap and P/E ratio?",
    "I want to know about {name}'s business",
    "What does {symbol} do and how big is it?",
    "Give me the company profile for {symbol}",
    "What's {symbol}'s revenue and profit margin?",
]

NEWS_QUESTIONS = [
    "What's the latest news on {symbol}?",
    "Any recent headlines about {name}?",
    "What's happening with {symbol}?",
    "Give me news updates for {symbol}",
    "Are there any announcements from {name}?",
    "What are people saying about {symbol}?",
]

RATIOS_QUESTIONS = [
    "What's {symbol}'s P/E ratio?",
    "Give me {symbol}'s financial ratios",
    "What's the ROE for {name}?",
    "How profitable is {symbol}?",
    "What's {symbol}'s debt-to-equity ratio?",
    "Is {symbol} financially healthy?",
    "What are {symbol}'s valuation metrics?",
    "Give me the liquidity ratios for {symbol}",
    "What's {symbol}'s profit margin?",
    "How does {symbol} score on profitability?",
]

COMPARE_QUESTIONS = [
    "Compare {symbol1} and {symbol2}",
    "Which is better: {symbol1} or {symbol2}?",
    "{symbol1} vs {symbol2} - which has better valuation?",
    "How does {symbol1} compare to {symbol2} financially?",
    "Compare the profitability of {symbol1}, {symbol2}, and {symbol3}",
    "Which has better ratios: {symbol1} or {symbol2}?",
]

MACRO_QUESTIONS = [
    "What's the current inflation rate?",
    "What's the US GDP growth?",
    "What's the unemployment rate?",
    "Where are interest rates right now?",
    "What's the Fed funds rate?",
    "Give me the latest economic indicators",
    "How is the economy doing?",
]


# =============================================================================
# MOCK TOOL RESPONSES
# =============================================================================

def generate_quote_response(symbol: str) -> Dict:
    """Generate mock quote response"""
    base_price = random.uniform(50, 500)
    change = random.uniform(-5, 5)
    return {
        "symbol": symbol,
        "price": str(round(base_price, 2)),
        "open": str(round(base_price - random.uniform(0, 3), 2)),
        "high": str(round(base_price + random.uniform(0, 5), 2)),
        "low": str(round(base_price - random.uniform(0, 5), 2)),
        "close": str(round(base_price - change, 2)),
        "volume": random.randint(10000000, 100000000),
        "change": str(round(change, 2)),
        "change_percent": str(round(change / base_price * 100, 2)),
        "market_cap": str(random.randint(100, 3000)) + "000000000",
        "pe_ratio": str(round(random.uniform(10, 40), 1)),
        "timestamp": datetime.utcnow().isoformat(),
        "source": "openbb"
    }


def generate_ratios_response(symbol: str) -> Dict:
    """Generate mock ratios response"""
    return {
        "symbol": symbol,
        "period": "annual",
        "period_end": "2025-12-31",
        "categories": [
            {
                "category": "profitability",
                "ratios": [
                    {"name": "return_on_equity", "value": str(round(random.uniform(0.10, 0.35), 3)),
                     "formula": "Net Income / Shareholders' Equity", "interpretation": "Higher is better"},
                    {"name": "net_profit_margin", "value": str(round(random.uniform(0.05, 0.30), 3)),
                     "formula": "Net Income / Revenue", "interpretation": "Higher is better"},
                ]
            },
            {
                "category": "valuation",
                "ratios": [
                    {"name": "pe_ratio", "value": str(round(random.uniform(15, 35), 1)),
                     "formula": "Price / EPS", "interpretation": "Context-dependent"},
                    {"name": "price_to_book", "value": str(round(random.uniform(2, 15), 1)),
                     "formula": "Price / Book Value", "interpretation": "Lower may indicate value"},
                ]
            }
        ],
        "source": "financetoolkit"
    }


def generate_compare_response(symbols: List[str]) -> Dict:
    """Generate mock comparison response"""
    comparison = {}
    for sym in symbols:
        comparison[sym] = {
            "pe_ratio": str(round(random.uniform(15, 35), 1)),
            "return_on_equity": str(round(random.uniform(0.10, 0.35), 3)),
            "debt_to_equity": str(round(random.uniform(0.5, 2.0), 2)),
        }

    # Generate rankings
    rankings = {
        "pe_ratio": sorted(symbols, key=lambda x: float(comparison[x]["pe_ratio"])),
        "return_on_equity": sorted(symbols, key=lambda x: float(comparison[x]["return_on_equity"]), reverse=True),
    }

    return {
        "symbols": symbols,
        "category": "all",
        "comparison": comparison,
        "rankings": rankings,
        "source": "financetoolkit"
    }


# =============================================================================
# TRAINING EXAMPLE GENERATORS
# =============================================================================

def generate_quote_example() -> Dict:
    """Generate a quote tool-use example"""
    stock = random.choice(STOCKS)
    question = random.choice(QUOTE_QUESTIONS).format(
        symbol=stock["symbol"],
        name=stock["name"]
    )

    tool_response = generate_quote_response(stock["symbol"])

    # Generate analysis based on tool output
    price = float(tool_response["price"])
    change = float(tool_response["change"])
    change_pct = float(tool_response["change_percent"])
    pe = float(tool_response["pe_ratio"])

    direction = "up" if change > 0 else "down"
    sentiment = "positive" if change > 0 else "negative"

    analysis = f"""{stock['name']} ({stock['symbol']}) is currently trading at ${price:.2f}, {direction} ${abs(change):.2f} ({abs(change_pct):.2f}%) today.

Key metrics:
- Trading volume: {tool_response['volume']:,} shares
- Market cap: ${int(tool_response['market_cap']):,}
- P/E ratio: {pe:.1f}x

The stock is showing {sentiment} momentum today. The P/E of {pe:.1f}x should be compared to sector peers and historical averages for context.

Note: This data is from {tool_response['timestamp'][:10]}. Always verify with your broker before making trading decisions."""

    return {
        "instruction": question,
        "input": "",
        "output": f"<tool_call>\n{{\"tool\": \"openbb_quote\", \"params\": {{\"symbol\": \"{stock['symbol']}\"}}}}\n</tool_call>",
        "tool_response": json.dumps(tool_response),
        "final_response": analysis,
        "category": "tool_use_quote"
    }


def generate_ratios_example() -> Dict:
    """Generate a ratios tool-use example"""
    stock = random.choice(STOCKS)
    question = random.choice(RATIOS_QUESTIONS).format(
        symbol=stock["symbol"],
        name=stock["name"]
    )

    tool_response = generate_ratios_response(stock["symbol"])

    # Extract values for analysis
    roe = float(tool_response["categories"][0]["ratios"][0]["value"])
    npm = float(tool_response["categories"][0]["ratios"][1]["value"])
    pe = float(tool_response["categories"][1]["ratios"][0]["value"])
    pb = float(tool_response["categories"][1]["ratios"][1]["value"])

    health = "strong" if roe > 0.20 and npm > 0.15 else "moderate" if roe > 0.10 else "weak"

    analysis = f"""Based on {stock['name']}'s ({stock['symbol']}) financial ratios:

**Profitability:**
- Return on Equity: {roe:.1%} (Formula: Net Income / Shareholders' Equity)
- Net Profit Margin: {npm:.1%} (Formula: Net Income / Revenue)

**Valuation:**
- P/E Ratio: {pe:.1f}x (Formula: Price / EPS)
- Price-to-Book: {pb:.1f}x (Formula: Price / Book Value)

**Assessment:** {stock['symbol']} shows {health} profitability metrics. The ROE of {roe:.1%} indicates {'efficient' if roe > 0.15 else 'moderate'} use of shareholder capital.

Valuation appears {'elevated' if pe > 25 else 'reasonable' if pe > 15 else 'attractive'} with a P/E of {pe:.1f}x. Compare these ratios to industry peers for a complete picture.

*Data as of {tool_response['period_end']}. This is educational analysis, not investment advice.*"""

    return {
        "instruction": question,
        "input": "",
        "output": f"<tool_call>\n{{\"tool\": \"financetoolkit_ratios\", \"params\": {{\"symbol\": \"{stock['symbol']}\", \"period\": \"annual\"}}}}\n</tool_call>",
        "tool_response": json.dumps(tool_response),
        "final_response": analysis,
        "category": "tool_use_ratios"
    }


def generate_compare_example() -> Dict:
    """Generate a comparison tool-use example"""
    stocks = random.sample(STOCKS, 3)
    symbols = [s["symbol"] for s in stocks]

    question = f"Compare {symbols[0]}, {symbols[1]}, and {symbols[2]} - which has the best financial metrics?"

    tool_response = generate_compare_response(symbols)

    # Build comparison analysis
    comp = tool_response["comparison"]
    rankings = tool_response["rankings"]

    analysis = f"""Comparing {', '.join(symbols)}:

| Metric | {symbols[0]} | {symbols[1]} | {symbols[2]} | Best |
|--------|{'|'.join(['-'*8 for _ in symbols])}|------|
| P/E Ratio | {comp[symbols[0]]['pe_ratio']}x | {comp[symbols[1]]['pe_ratio']}x | {comp[symbols[2]]['pe_ratio']}x | {rankings['pe_ratio'][0]} (lowest) |
| ROE | {float(comp[symbols[0]]['return_on_equity']):.1%} | {float(comp[symbols[1]]['return_on_equity']):.1%} | {float(comp[symbols[2]]['return_on_equity']):.1%} | {rankings['return_on_equity'][0]} (highest) |
| Debt/Equity | {comp[symbols[0]]['debt_to_equity']} | {comp[symbols[1]]['debt_to_equity']} | {comp[symbols[2]]['debt_to_equity']} | - |

**Summary:**
- **Best Value (lowest P/E):** {rankings['pe_ratio'][0]}
- **Most Profitable (highest ROE):** {rankings['return_on_equity'][0]}

Different investors may prefer different stocks based on their priorities. Value investors might favor {rankings['pe_ratio'][0]}, while those seeking profitability might prefer {rankings['return_on_equity'][0]}.

*This comparison is for educational purposes. Consider all factors before investing.*"""

    return {
        "instruction": question,
        "input": "",
        "output": f"<tool_call>\n{{\"tool\": \"financetoolkit_compare\", \"params\": {{\"symbols\": {json.dumps(symbols)}, \"category\": \"all\"}}}}\n</tool_call>",
        "tool_response": json.dumps(tool_response),
        "final_response": analysis,
        "category": "tool_use_compare"
    }


def generate_fundamentals_example() -> Dict:
    """Generate a fundamentals tool-use example"""
    stock = random.choice(STOCKS)
    question = random.choice(FUNDAMENTALS_QUESTIONS).format(
        symbol=stock["symbol"],
        name=stock["name"]
    )

    market_cap = random.randint(100, 3000) * 1000000000
    revenue = random.randint(50, 400) * 1000000000
    employees = random.randint(10000, 200000)

    tool_response = {
        "symbol": stock["symbol"],
        "name": stock["name"],
        "sector": stock["sector"],
        "industry": f"{stock['sector']} - Diversified",
        "description": f"{stock['name']} is a leading company in the {stock['sector']} sector.",
        "employees": employees,
        "market_cap": str(market_cap),
        "pe_ratio": str(round(random.uniform(15, 35), 1)),
        "revenue_ttm": str(revenue),
        "net_income_ttm": str(int(revenue * random.uniform(0.10, 0.25))),
        "profit_margin": str(round(random.uniform(0.10, 0.25), 3)),
        "dividend_yield": str(round(random.uniform(0, 0.03), 4)),
        "source": "openbb"
    }

    mc_b = market_cap / 1e9
    rev_b = revenue / 1e9
    ni_b = int(tool_response["net_income_ttm"]) / 1e9

    analysis = f"""{stock['name']} ({stock['symbol']}) - Company Overview

**Business:**
- Sector: {stock['sector']}
- Employees: {employees:,}
- {tool_response['description']}

**Financials (TTM):**
- Market Cap: ${mc_b:.1f}B
- Revenue: ${rev_b:.1f}B
- Net Income: ${ni_b:.1f}B
- Profit Margin: {float(tool_response['profit_margin']):.1%}

**Valuation:**
- P/E Ratio: {tool_response['pe_ratio']}x
- Dividend Yield: {float(tool_response['dividend_yield']):.2%}

{stock['name']} is a {'large-cap' if mc_b > 100 else 'mid-cap' if mc_b > 10 else 'small-cap'} company with {'strong' if float(tool_response['profit_margin']) > 0.15 else 'moderate'} profitability.

*Data sourced from OpenBB. Verify with official filings before making investment decisions.*"""

    return {
        "instruction": question,
        "input": "",
        "output": f"<tool_call>\n{{\"tool\": \"openbb_fundamentals\", \"params\": {{\"symbol\": \"{stock['symbol']}\"}}}}\n</tool_call>",
        "tool_response": json.dumps(tool_response),
        "final_response": analysis,
        "category": "tool_use_fundamentals"
    }


def generate_macro_example() -> Dict:
    """Generate a macro data tool-use example"""
    question = random.choice(MACRO_QUESTIONS)

    series = random.choice(["gdp", "inflation", "unemployment", "interest_rates"])

    if series == "gdp":
        value = round(random.uniform(2, 4), 1)
        unit = "percent growth"
        interpretation = f"The US GDP grew at {value}% annualized rate, indicating {'strong' if value > 3 else 'moderate'} economic expansion."
    elif series == "inflation":
        value = round(random.uniform(2, 5), 1)
        unit = "percent (CPI)"
        interpretation = f"Inflation at {value}% is {'above' if value > 3 else 'near'} the Fed's 2% target, {'suggesting potential rate hikes' if value > 3 else 'within acceptable range'}."
    elif series == "unemployment":
        value = round(random.uniform(3.5, 5.5), 1)
        unit = "percent"
        interpretation = f"Unemployment at {value}% is {'low' if value < 4 else 'moderate'}, indicating a {'tight' if value < 4 else 'balanced'} labor market."
    else:
        value = round(random.uniform(4, 6), 2)
        unit = "percent"
        interpretation = f"The Fed funds rate at {value}% reflects {'restrictive' if value > 5 else 'neutral'} monetary policy."

    tool_response = {
        "series": series,
        "country": "US",
        "unit": unit,
        "data": [{"date": "2025-12-01", "value": str(value)}],
        "source": "openbb"
    }

    analysis = f"""**{series.replace('_', ' ').title()}**: {value}% ({unit})

{interpretation}

This is a key economic indicator that affects:
- Federal Reserve policy decisions
- Stock and bond market valuations
- Consumer and business confidence

*Data as of December 2025. Economic conditions change; verify with official sources.*"""

    return {
        "instruction": question,
        "input": "",
        "output": f"<tool_call>\n{{\"tool\": \"openbb_macro\", \"params\": {{\"series\": \"{series}\", \"country\": \"US\"}}}}\n</tool_call>",
        "tool_response": json.dumps(tool_response),
        "final_response": analysis,
        "category": "tool_use_macro"
    }


def generate_no_tool_example() -> Dict:
    """Generate examples where NO tool should be called (general knowledge)"""
    questions_no_tool = [
        ("What is a P/E ratio?", "A P/E (Price-to-Earnings) ratio is a valuation metric that compares a company's stock price to its earnings per share (EPS). Formula: P/E = Stock Price / EPS. A higher P/E may indicate growth expectations, while a lower P/E may suggest value or concerns. Always compare to industry peers and historical averages."),
        ("Explain dollar-cost averaging", "Dollar-cost averaging (DCA) is an investment strategy where you invest a fixed amount at regular intervals, regardless of price. Benefits: reduces timing risk, builds discipline, and smooths out volatility impact. Example: investing $500 monthly into an index fund. This strategy works best for long-term investors."),
        ("What's the difference between stocks and bonds?", "Stocks represent ownership in a company (equity), while bonds are loans to companies or governments (debt). Stocks offer higher potential returns but more risk; bonds provide fixed income with lower risk. A balanced portfolio often includes both based on risk tolerance and time horizon."),
        ("How do dividends work?", "Dividends are payments companies make to shareholders from profits. Key dates: declaration date (announced), ex-dividend date (must own before), record date (ownership verified), payment date (received). Dividend yield = Annual dividend / Stock price. Not all companies pay dividends; growth companies often reinvest profits instead."),
        ("What is an ETF?", "An ETF (Exchange-Traded Fund) is a basket of securities that trades on an exchange like a stock. Benefits: diversification, low costs, tax efficiency, liquidity. Types include index ETFs, sector ETFs, bond ETFs, and thematic ETFs. Popular examples: SPY (S&P 500), QQQ (Nasdaq 100), VTI (total market)."),
    ]

    q, a = random.choice(questions_no_tool)
    return {
        "instruction": q,
        "input": "",
        "output": a,
        "category": "general_finance_no_tool"
    }


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_tool_use_dataset(n_examples: int = 2500) -> List[Dict]:
    """Generate full tool-use training dataset"""
    examples = []

    # Distribution of example types
    distribution = {
        "quote": 0.20,           # 20% quote examples
        "ratios": 0.25,          # 25% ratio examples
        "compare": 0.10,         # 10% comparison examples
        "fundamentals": 0.15,    # 15% fundamentals examples
        "macro": 0.10,           # 10% macro examples
        "no_tool": 0.20,         # 20% no-tool examples (prevents over-tooling)
    }

    generators = {
        "quote": generate_quote_example,
        "ratios": generate_ratios_example,
        "compare": generate_compare_example,
        "fundamentals": generate_fundamentals_example,
        "macro": generate_macro_example,
        "no_tool": generate_no_tool_example,
    }

    for example_type, ratio in distribution.items():
        count = int(n_examples * ratio)
        print(f"Generating {count} {example_type} examples...")

        for _ in range(count):
            try:
                example = generators[example_type]()
                examples.append(example)
            except Exception as e:
                print(f"Error generating {example_type}: {e}")

    random.shuffle(examples)

    return examples


def save_dataset(examples: List[Dict], output_path: str):
    """Save dataset to JSON file"""
    with open(output_path, "w") as f:
        json.dump(examples, f, indent=2)

    print(f"Saved {len(examples)} examples to {output_path}")

    # Print statistics
    categories = {}
    for ex in examples:
        cat = ex.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate tool-use training data")
    parser.add_argument("--n", type=int, default=2500, help="Number of examples to generate")
    parser.add_argument("--output", type=str, default="backend/training_data/tool_use_training_data.json",
                        help="Output file path")
    args = parser.parse_args()

    print(f"Generating {args.n} tool-use training examples...")
    examples = generate_tool_use_dataset(args.n)
    save_dataset(examples, args.output)

    print("\nDone! The model should now learn to:")
    print("1. Recognize when a tool call is needed")
    print("2. Format the correct tool call with parameters")
    print("3. Analyze tool output and provide grounded responses")
    print("4. Know when NOT to use a tool (general knowledge)")
