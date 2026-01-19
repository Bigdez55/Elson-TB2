#!/usr/bin/env python3
"""
Elson TB2 - Q&A Extraction from Strategic Documents

Extracts Q&A training pairs from strategic markdown documents:
- Building AGI_ASI Investment System.md (~500 pairs)
- Comprehensive Trading Knowledge Compilation.md (~400 pairs)
- Other strategic documents (~300 pairs)

Usage:
    python scripts/extract_qa_from_docs.py
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class QAPair:
    """A single Q&A training pair."""
    instruction: str
    input: str
    output: str
    category: str
    source: str
    difficulty: str = "medium"


# Category mappings for different sections
SECTION_CATEGORIES = {
    "fpga": "high_frequency_trading",
    "kernel bypass": "high_frequency_trading",
    "hft": "high_frequency_trading",
    "latency": "high_frequency_trading",
    "kdb": "data_engineering",
    "tickerplant": "data_engineering",
    "time-series": "data_engineering",
    "security master": "data_engineering",
    "fix protocol": "trading_infrastructure",
    "rough volatility": "quantitative_finance",
    "rfsv": "quantitative_finance",
    "deep hedging": "quantitative_finance",
    "heston": "quantitative_finance",
    "malliavin": "quantitative_finance",
    "black-scholes": "quantitative_finance",
    "monte carlo": "quantitative_finance",
    "almgren": "algorithmic_trading",
    "vwap": "algorithmic_trading",
    "twap": "algorithmic_trading",
    "market making": "algorithmic_trading",
    "avellaneda": "algorithmic_trading",
    "execution": "algorithmic_trading",
    "llm": "ai_ml",
    "finGPT": "ai_ml",
    "bloombergGPT": "ai_ml",
    "causal": "ai_ml",
    "gnn": "ai_ml",
    "neural network": "ai_ml",
    "ldi": "portfolio_management",
    "liability": "portfolio_management",
    "asset allocation": "portfolio_management",
    "risk parity": "portfolio_management",
    "kelly": "portfolio_management",
    "black-litterman": "portfolio_management",
    "aladdin": "market_infrastructure",
    "ibor": "market_infrastructure",
    "charles river": "market_infrastructure",
    "simcorp": "market_infrastructure",
    "murex": "market_infrastructure",
}


def get_category(text: str) -> str:
    """Determine category based on text content."""
    text_lower = text.lower()
    for keyword, category in SECTION_CATEGORIES.items():
        if keyword in text_lower:
            return category
    return "general_finance"


def extract_from_section(title: str, content: str, source: str) -> List[QAPair]:
    """Extract Q&A pairs from a section."""
    pairs = []

    # Clean the content
    content = re.sub(r'\[\d+\]', '', content)  # Remove citations
    content = re.sub(r'\n{3,}', '\n\n', content)  # Normalize newlines

    # Extract the category
    category = get_category(f"{title} {content}")

    # Generate question from section title
    if title:
        # Create a "What is" question from section title
        clean_title = re.sub(r'^[\d.]+\s*', '', title)  # Remove numbering
        clean_title = clean_title.strip()

        if clean_title:
            question = f"What is {clean_title}?"
            if "?" not in clean_title.lower():
                # Truncate content for answer (first 500 chars of substantive content)
                answer_content = content.strip()[:1500]
                if answer_content:
                    pairs.append(QAPair(
                        instruction=question,
                        input="",
                        output=answer_content.strip(),
                        category=category,
                        source=source,
                        difficulty="medium"
                    ))

    # Look for bullet points that define concepts
    bullet_pattern = r'\*\s*\*\*([^*]+)\*\*:?\s*(.+?)(?=\n\*|\n\n|\Z)'
    for match in re.finditer(bullet_pattern, content, re.DOTALL):
        term = match.group(1).strip()
        definition = match.group(2).strip()

        if len(term) < 100 and len(definition) > 50:
            pairs.append(QAPair(
                instruction=f"Explain {term} in financial systems.",
                input="",
                output=definition[:1000],
                category=category,
                source=source,
                difficulty="medium"
            ))

    return pairs


def parse_markdown_sections(content: str) -> List[Tuple[str, str]]:
    """Parse markdown into sections with titles and content."""
    sections = []

    # Split by headers (## or ###)
    header_pattern = r'^(#{2,3})\s*(.+?)$'
    parts = re.split(header_pattern, content, flags=re.MULTILINE)

    current_title = ""
    current_content = ""

    i = 0
    while i < len(parts):
        part = parts[i].strip()

        if part.startswith('#'):
            # This is a header marker, next part is title, then content
            if current_title or current_content:
                sections.append((current_title, current_content))
            current_title = parts[i + 1].strip() if i + 1 < len(parts) else ""
            current_content = parts[i + 2].strip() if i + 2 < len(parts) else ""
            i += 3
        else:
            current_content += "\n" + part
            i += 1

    if current_title or current_content:
        sections.append((current_title, current_content))

    return sections


# Pre-defined Q&A pairs based on document analysis
STRATEGIC_QA_PAIRS = [
    # FPGA and HFT
    QAPair(
        instruction="What is FPGA acceleration in high-frequency trading?",
        input="",
        output="""FPGA (Field-Programmable Gate Array) acceleration implements trading logic directly in hardware rather than software. Unlike CPUs that execute sequential instructions, FPGAs are physically reconfigured via a bitstream to represent the logic circuit itself.

**Key Benefits:**
- **Massive Parallelism**: All logic executes simultaneously
- **Deterministic Latency**: No thread scheduling or context switching
- **Ultra-Low Latency**: 20-30 nanoseconds for message parsing vs microseconds for software

**Applications in Trading:**
1. **Market Data Parsing**: Decode NASDAQ ITCH or CME FIX/FAST at line rate (10Gbps+)
2. **Pre-Trade Risk Checks**: Rule 15c3-5 compliance with zero latency penalty
3. **Order Generation**: Direct market access without software overhead

This is essential for firms where microsecond advantages translate to millions in profits.""",
        category="high_frequency_trading",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="Explain kernel bypass networking for trading systems.",
        input="",
        output="""Kernel bypass networking eliminates the overhead of the operating system's TCP/IP stack, allowing trading applications to access network interface cards directly.

**Traditional Path (High Latency):**
NIC -> Kernel Space -> TCP/IP Stack -> Buffer Copy -> User Space Application

**Kernel Bypass Path (Low Latency):**
NIC -> Direct User Space Access (Zero-Copy)

**Technologies:**
- **DPDK** (Data Plane Development Kit): Intel's framework for packet processing
- **Solarflare OpenOnload**: Accelerated TCP/IP in user space
- **RDMA** (Remote Direct Memory Access): Memory-to-memory transfer without CPU
- **ef_vi/TCPDirect**: Direct hardware queue access for lowest latency

**Performance:**
- Reduces end-to-end latency from microseconds to sub-microsecond range
- Eliminates expensive context switches between kernel and user space
- Enables deterministic performance required for market making""",
        category="high_frequency_trading",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="What is kdb+/q and why is it used in finance?",
        input="",
        output="""kdb+ is a high-performance time-series database developed by KX Systems, with its integrated programming language called q. It's the industry standard for quantitative finance.

**Architecture Components:**

1. **Tickerplant (TP)**: Entry point receiving normalized market data, logging to journal, publishing to subscribers. Uses -25! for zero-latency broadcast.

2. **Real-Time Database (RDB)**: In-memory storage of current day's data. Supports queries like: `select vwap: size wsum price % sum size by sym from trade`

3. **Historical Database (HDB)**: End-of-day data written to disk, partitioned by date, columns stored as separate files (splayed).

**Why Finance Uses kdb+:**
- Column-oriented storage optimal for analytical queries
- Can ingest millions of ticks per second
- Microsecond-latency queries on real-time data
- Compact syntax: complex analytics in single lines
- Proven at scale across major banks and hedge funds

**Cost**: Expensive licensing ($50K-100K+ per core/year) but unmatched performance for tick data.""",
        category="data_engineering",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="What is Rough Volatility (RFSV)?",
        input="",
        output="""Rough Fractional Stochastic Volatility (RFSV) is a modern volatility model that captures the "roughness" of real market volatility that classical models miss.

**Discovery (Gatheral, Bayer, Friz, 2014):**
Log-volatility behaves like fractional Brownian motion with Hurst parameter H ≈ 0.1, far "rougher" than the standard Brownian motion (H=0.5) assumed in Black-Scholes/Heston.

**Key Properties:**
- Non-Markovian (path-dependent, has memory)
- Captures steep short-dated implied volatility skew
- More accurate pricing of options, especially short expiries

**Implications for Trading:**
1. Standard PDE solvers don't work (non-Markovian)
2. Requires advanced Monte Carlo and asymptotic expansions
3. Provides pricing advantage in options markets
4. Better hedging through more accurate delta/gamma

**Academic Foundation:**
- "Volatility is Rough" paper (2014)
- Work by Gatheral, Bayer, Friz at Baruch/TU Berlin""",
        category="quantitative_finance",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="Explain the Deep Hedging framework.",
        input="",
        output="""Deep Hedging, pioneered by Hans Buehler at J.P. Morgan and researchers at ETH Zurich, replaces traditional Greek-based hedging with neural networks that learn optimal hedging strategies.

**Traditional Hedging Problems:**
- Depends on model being correct
- Ignores transaction costs
- Fails for exotic payoffs without analytical Greeks

**Deep Hedging Approach:**
1. Train neural networks to output optimal hedge ratios directly
2. Minimize specific risk measures (not just variance)
3. Include explicit transaction costs in loss function
4. Learn "patience" - avoid over-trading in illiquid markets

**Risk Measures Optimized:**
- Expected Shortfall (CVaR)
- Entropic Risk
- General Convex Risk Measures

**Architecture:**
- Typically RNNs or LSTMs
- Input: history of asset prices and hedging errors
- Output: optimal trading action for the hedge

**Advantage:**
- Model-free approach works for exotic derivatives
- Automatically adapts to market conditions
- Can hedge instruments with no analytical formula""",
        category="quantitative_finance",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="What is the Almgren-Chriss optimal execution framework?",
        input="",
        output="""Almgren-Chriss (2000) is the foundational framework for optimal execution of large orders, balancing speed vs. market impact.

**The Problem:**
When executing a large order (e.g., $100M of AAPL), you face a tradeoff:
- Trade fast: High market impact (your trades move the price against you)
- Trade slow: Volatility risk (price may move while you wait)

**The Solution:**
Solve a stochastic control problem that minimizes Implementation Shortfall (difference between decision price and execution price).

**Key Parameters:**
- σ (volatility): Risk of waiting
- η (temporary impact): Price moves due to your trade
- γ (permanent impact): Lasting price change from information
- λ (risk aversion): Your tolerance for execution uncertainty

**Optimal Trading Trajectory:**
The model produces a trading schedule that tells you:
- How many shares to trade each period
- How to balance urgency vs. patience
- When to be more aggressive vs. passive

**Extensions:**
- VWAP/TWAP algorithms build on this foundation
- Modern versions use ML to forecast volume profiles
- Real-time adaptation based on market conditions""",
        category="algorithmic_trading",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="What is the Avellaneda-Stoikov market making model?",
        input="",
        output="""Avellaneda-Stoikov is the foundational model for high-frequency market making, dynamically adjusting quotes based on inventory.

**Core Concept:**
Market makers earn the bid-ask spread but face inventory risk. If you accumulate too much inventory, adverse price moves cause losses.

**The Model:**
Dynamically adjust bid and ask prices based on:
- Current inventory position (q)
- Risk aversion (γ)
- Time to end of trading (T-t)
- Volatility (σ)

**Reservation Price:**
r(s,t) = s - q × γ × σ² × (T-t)

The "fair price" shifts based on inventory. If long, lower both bid and ask to attract buyers and discourage sellers.

**Optimal Spread:**
δ = γ × σ² × (T-t) + (2/γ) × ln(1 + γ/k)

Where k relates to order arrival intensity.

**Practical Application:**
- Skew quotes to manage inventory toward zero
- Widen spreads when inventory is extreme
- Account for adverse selection (toxic flow)

**Related: VPIN (Volume-Synchronized Probability of Informed Trading)**
Monitors for toxic flow to avoid trading against informed insiders.""",
        category="algorithmic_trading",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    QAPair(
        instruction="Compare BlackRock Aladdin with other institutional platforms.",
        input="",
        output="""Major institutional investment platforms and their characteristics:

**BlackRock Aladdin** ($21.6T AUM managed on platform)
- "Whole Portfolio" philosophy unifying public and private markets
- Integrated eFront for private markets
- Aladdin Studio for custom applications via REST APIs
- Strengths: Scale, ecosystem, comprehensive risk analytics
- Weaknesses: High cost, vendor lock-in, legacy architecture

**State Street Alpha / Charles River IMS**
- Centralized data model harmonizing front/middle/back office
- IBOR as single source of truth
- Strong compliance and pre-trade risk checks
- Focus on institutional asset managers

**SimCorp Dimension**
- Integrated, modular design
- Tightly coupled IBOR and ABOR
- Handles complex multi-asset portfolios
- Single database schema for all instruments

**Murex MX.3**
- Layered architecture (Presentation, Business, Orchestration, Database)
- Event-driven processing for high volumes
- MxML workflow for external integration
- Strong cross-asset derivatives coverage

**Key Architectural Elements:**
1. Investment Book of Record (IBOR): Real-time position view
2. Security Master: Unified instrument ontology
3. Risk Engine: Real-time analytics
4. Execution Management: Order routing and execution""",
        category="market_infrastructure",
        source="Building AGI_ASI Investment System.md",
        difficulty="medium"
    ),
    QAPair(
        instruction="What is the Investment Book of Record (IBOR)?",
        input="",
        output="""The Investment Book of Record (IBOR) is the single source of truth for real-time positions in institutional investment platforms.

**IBOR vs. ABOR:**
- **IBOR** (Investment): Real-time, supports intraday trading decisions
- **ABOR** (Accounting): T+1 settlement focus, tax reporting

**Core Functions:**
1. **Real-Time Position Tracking**: Updates immediately upon trade execution
2. **Air Trade Prevention**: Prevents selling assets you don't own
3. **Pre-Trade Compliance**: Checks against investment guidelines
4. **Cash Management**: Real-time cash position across accounts
5. **Exposure Monitoring**: Aggregated risk views

**Modern IBOR Requirements:**
- Streaming, event-sourced architecture
- Every tick/execution triggers state transition
- Instantaneous propagation to risk engines
- Move from batch to real-time processing
- Time-series and in-memory data stores

**Implementation:**
- Database: kdb+, InfluxDB, or specialized IBOR platforms
- Updates: Sub-second latency for position changes
- Integration: Feeds risk engines, compliance, trading systems

The IBOR enables institutions to make trading decisions with confidence in their actual positions.""",
        category="market_infrastructure",
        source="Building AGI_ASI Investment System.md",
        difficulty="medium"
    ),
    QAPair(
        instruction="What is Risk Parity portfolio construction?",
        input="",
        output="""Risk Parity constructs portfolios where each asset class contributes equally to total portfolio risk, rather than equal capital allocation.

**Traditional 60/40 Problem:**
A 60% stocks / 40% bonds portfolio actually has ~90% of its risk coming from stocks because equities are much more volatile than bonds.

**Risk Parity Solution:**
Weight assets inversely proportional to their volatility:
w_i ∝ 1/σ_i

**Implementation:**
1. Calculate volatility of each asset class
2. Weight inversely to volatility
3. Often use leverage to achieve target return
4. Rebalance as volatilities change

**Example Weights:**
- Stocks (σ=15%): Lower weight
- Bonds (σ=5%): Higher weight
- Commodities (σ=20%): Lower weight

**Benefits:**
- True diversification across risk factors
- More balanced performance across economic regimes
- Reduces concentration risk
- Smoother return stream

**Famous Implementation:**
Bridgewater's "All Weather" fund uses Risk Parity principles to perform across growth/recession and inflation/deflation environments.

**Considerations:**
- Requires leverage to meet return targets
- Volatility estimates must be accurate
- Correlation assumptions matter""",
        category="portfolio_management",
        source="Building AGI_ASI Investment System.md",
        difficulty="medium"
    ),
    QAPair(
        instruction="Explain the Kelly Criterion for position sizing.",
        input="",
        output="""The Kelly Criterion determines optimal bet size to maximize long-term geometric growth rate of capital.

**Formula:**
f* = μ / σ²

Where:
- f* = optimal fraction of capital to bet
- μ = expected excess return
- σ² = variance of returns

**Interpretation:**
Bet more when:
- Higher expected return (μ)
- Lower variance (σ²)
- Higher confidence in your edge

**Practical Issues:**

1. **Parameter Uncertainty**: Small errors in μ or σ estimates cause large errors in optimal sizing
2. **Ruin Risk**: Full Kelly can lead to large drawdowns
3. **Non-Normal Returns**: Formula assumes normal distribution

**Solution: Fractional Kelly**
Use a fraction of Kelly (commonly 1/2 or 1/4):
- Half Kelly: More conservative, smoother ride
- Quarter Kelly: Very conservative
- Full Kelly: Maximum growth but high volatility

**Example:**
If Kelly says bet 20% of capital:
- Half Kelly = 10%
- Quarter Kelly = 5%

**Application:**
- Hedge fund position sizing
- Sports betting optimization
- Venture capital allocation
- Any situation with repeated bets and edge""",
        category="portfolio_management",
        source="Building AGI_ASI Investment System.md",
        difficulty="medium"
    ),
    QAPair(
        instruction="What is the Black-Litterman model?",
        input="",
        output="""Black-Litterman is a Bayesian approach to portfolio optimization that combines market equilibrium weights with investor views.

**The Problem with Mean-Variance:**
- Highly sensitive to expected return estimates
- Small changes in inputs create wildly different portfolios
- Often produces extreme, unintuitive weights

**Black-Litterman Solution:**

1. **Prior (Market Equilibrium)**:
Start with market capitalization weights as the "neutral" portfolio. These imply equilibrium expected returns.

2. **Views**:
Express your investment views with confidence levels:
- "I believe Tech will outperform by 2%"
- "I'm 60% confident in this view"

3. **Posterior (Combined)**:
Bayesian update combines prior (market) with views to produce tilted expected returns, then optimize.

**Mathematics:**
E[R] = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ × [(τΣ)⁻¹π + P'Ω⁻¹Q]

Where:
- π = implied equilibrium returns
- P = view matrix
- Q = view returns
- Ω = view uncertainty

**Benefits:**
- More stable portfolios
- Intuitive way to express views
- Respects market wisdom as baseline
- Confidence-weighted tilts

**Usage:**
Standard at institutional investors for combining alpha signals with market-neutral benchmarks.""",
        category="portfolio_management",
        source="Building AGI_ASI Investment System.md",
        difficulty="hard"
    ),
    # Trading Knowledge Compilation pairs
    QAPair(
        instruction="What is the difference between agency and principal trading?",
        input="",
        output="""Agency and principal trading represent fundamentally different ways brokers execute client orders:

**Agency Trading:**
- Broker acts as agent, executing on client's behalf
- No principal risk - broker doesn't take position
- Earns commission on execution
- Best execution obligation to client
- Common for: Institutional equities, retail orders

**Principal Trading:**
- Broker uses own capital to trade with client
- Takes position risk (can profit or lose)
- Earns bid-ask spread
- Must disclose principal capacity
- Common for: Bonds, OTC derivatives, market making

**Risk/Reward:**
- Agency: Low risk, fixed commission income
- Principal: Higher risk, potential for larger profits

**Regulatory Considerations:**
- Principal trades require disclosure (FINRA Rule 2232)
- Different best execution obligations
- Conflict of interest management required

**Hybrid: Riskless Principal:**
Broker executes matching trade simultaneously, earning spread without actual market risk. Common in fixed income markets.""",
        category="trading_infrastructure",
        source="Comprehensive Trading Knowledge Compilation.md",
        difficulty="medium"
    ),
    QAPair(
        instruction="Explain the trade lifecycle from execution to settlement.",
        input="",
        output="""The trade lifecycle encompasses all stages from order to final settlement:

**1. Pre-Trade**
- Investment decision and order generation
- Pre-trade compliance checks
- Order routing decision

**2. Execution**
- Order sent to venue (exchange, dark pool, dealer)
- Matching with counterparty
- Trade confirmation/execution report

**3. Post-Trade (T+0)**
- Trade capture in OMS/EMS
- Real-time position update
- Allocation to accounts

**4. Clearing (T+0 to T+1)**
- Trade submitted to clearinghouse (e.g., NSCC, LCH)
- Novation: CCP becomes counterparty to both sides
- Netting of obligations
- Margin calculation

**5. Settlement (T+2 for equities)**
- DVP (Delivery vs. Payment)
- Securities delivered via depository (e.g., DTC)
- Cash transferred between custodians
- Final position update

**Key Infrastructure:**
- OMS/EMS: Order management
- DTCC/Euroclear: Clearing and settlement
- Custodian banks: Asset safekeeping
- SWIFT: Messaging between parties

**T+1 Transition (2024):**
US moving from T+2 to T+1 settlement for equities.""",
        category="trading_infrastructure",
        source="Comprehensive Trading Knowledge Compilation.md",
        difficulty="medium"
    ),
    QAPair(
        instruction="What are the main quantitative trading strategies?",
        input="",
        output="""Major quantitative trading strategies employed by systematic funds:

**1. Statistical Arbitrage**
- Pairs trading: Long/short correlated securities
- Mean reversion on spreads
- Cointegration-based signals
- Holding period: Days to weeks

**2. Factor Investing**
- Systematic exposure to risk factors
- Common factors: Value, Momentum, Size, Quality, Low Vol
- Academic foundation: Fama-French
- Long-only or long-short

**3. Market Making**
- Provide liquidity, earn spread
- Inventory management critical
- Avellaneda-Stoikov models
- Very short holding period (seconds)

**4. Trend Following / CTA**
- Momentum across asset classes
- Managed futures
- Diversified across markets
- Holding period: Weeks to months

**5. Machine Learning Strategies**
- Alternative data (satellite, NLP, social)
- Neural network alpha signals
- Reinforcement learning for execution
- Feature engineering critical

**6. High-Frequency Trading (HFT)**
- Sub-millisecond execution
- Latency arbitrage
- Rebate capture
- Co-location essential

**Risk Management:**
All strategies require position limits, stop losses, and correlation monitoring across the portfolio.""",
        category="algorithmic_trading",
        source="Comprehensive Trading Knowledge Compilation.md",
        difficulty="medium"
    ),
]


def generate_qa_from_document(doc_path: str) -> List[QAPair]:
    """Generate Q&A pairs from a markdown document."""
    pairs = []

    if not os.path.exists(doc_path):
        return pairs

    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    source = os.path.basename(doc_path)
    sections = parse_markdown_sections(content)

    for title, section_content in sections:
        section_pairs = extract_from_section(title, section_content, source)
        pairs.extend(section_pairs)

    return pairs


def save_training_data(pairs: List[QAPair], output_path: str):
    """Save Q&A pairs to JSON format."""
    data = [asdict(p) for p in pairs]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(pairs)} Q&A pairs to {output_path}")


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent
    fan_path = base_path / "Elson FAN"
    output_path = base_path / "backend" / "training_data" / "strategic_qa_pairs.json"

    print("=" * 60)
    print("Elson TB2 - Q&A Extraction from Strategic Documents")
    print("=" * 60)

    all_pairs = []

    # Add pre-defined strategic Q&A pairs
    print(f"\nAdding {len(STRATEGIC_QA_PAIRS)} pre-defined strategic Q&A pairs...")
    all_pairs.extend(STRATEGIC_QA_PAIRS)

    # Process strategic documents
    strategic_docs = [
        fan_path / "Building AGI_ASI Investment System.md",
        fan_path / "Comprehensive Trading Knowledge Compilation.md",
        fan_path / "BLACKROCK & VANGUARD RIVALRY MASTER PLAN.txt",
        fan_path / "FINANCIAL PROJECTIONS & INVESTOR PRESENTATION.txt",
        fan_path / "LLM FINE-TUNING & RAG IMPLEMENTATION ROADMAP.txt",
    ]

    for doc in strategic_docs:
        if doc.exists():
            print(f"\nProcessing: {doc.name}")
            doc_pairs = generate_qa_from_document(str(doc))
            print(f"  Extracted: {len(doc_pairs)} pairs")
            all_pairs.extend(doc_pairs)
        else:
            print(f"\nSkipping (not found): {doc.name}")

    # Remove duplicates based on instruction
    seen = set()
    unique_pairs = []
    for pair in all_pairs:
        if pair.instruction not in seen:
            seen.add(pair.instruction)
            unique_pairs.append(pair)

    print(f"\n{'=' * 60}")
    print(f"Total unique Q&A pairs: {len(unique_pairs)}")

    # Category distribution
    categories: Dict[str, int] = {}
    for pair in unique_pairs:
        categories[pair.category] = categories.get(pair.category, 0) + 1

    print("\nCategory Distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Save output
    save_training_data(unique_pairs, str(output_path))

    # Also save in Alpaca format for fine-tuning
    alpaca_output = base_path / "backend" / "training_data" / "strategic_qa_alpaca.json"
    alpaca_data = [
        {
            "instruction": p.instruction,
            "input": p.input,
            "output": p.output
        }
        for p in unique_pairs
    ]
    with open(alpaca_output, 'w', encoding='utf-8') as f:
        json.dump(alpaca_data, f, indent=2, ensure_ascii=False)
    print(f"Saved Alpaca format to {alpaca_output}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
