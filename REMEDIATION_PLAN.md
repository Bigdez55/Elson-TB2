# Elson Financial AI - Remediation Plan v1

**Last Updated:** 2026-01-19
**Status:** Phases 0-3 COMPLETE

## Executive Summary

**Core Insight**: A 14B model with strong tools, retrieval, and rules will beat a 235B model with weak grounding for most real user needs—especially when calculations and market data are involved.

**Priority Order**: Tool integration → Workflow schemas → Domain packs → Model merging (last)

**Current Status**:
| Area | Status | Priority |
|------|--------|----------|
| OpenBB market data | ✅ **COMPLETE** | P0 - Critical |
| FinanceToolkit ratios | ✅ **COMPLETE** | P0 - Critical |
| yfinance endpoints | ✅ **COMPLETE** | P0 - Critical |
| Tool-use training | ✅ **COMPLETE** (2,500 pairs) | P0 - Critical |
| Insurance workflows | ✅ **COMPLETE** (10,000 pairs) | P1 - High |
| Accounting integration | ✅ **COMPLETE** (5,000 pairs) | P1 - High |
| Evaluation benchmark | ✅ **COMPLETE** (431 questions) | P1 - High |
| InvestLM merge | Config exists, not run | P2 - After eval |
| Qwen3-235B / DeepSeek-R1 full | Not started | P3 - Future |

---

## Phase 0: Alignment Decisions (One-Time)

### 0.1 Tool-First Architecture Policy

**Rule**: The model MUST call tools for any question involving:
- Current pricing or market data
- Fundamentals or financial statements
- Portfolio analytics or ratios
- Any computation requiring auditability

**Implementation**: Add system prompt directive + tool-use fine-tuning

```
TOOL-FIRST POLICY:
When answering questions about current prices, market data, financial ratios,
or any quantitative analysis, you MUST use the appropriate tool rather than
answering from memory. Tool outputs are authoritative; memory is not.
```

### 0.2 Structured Output Schemas (7 Core)

| Schema | Purpose | Tool Integration |
|--------|---------|------------------|
| `FinancialPlan` | Comprehensive wealth plan | Calculator tools |
| `PortfolioPolicyStatement` | IPS document | FinanceToolkit ratios |
| `TradePlan` | Position sizing + rationale | OpenBB data |
| `TaxScenarioSummary` | Tax optimization analysis | Calculator tools |
| `ComplianceChecklist` | Regulatory compliance | Rules engine |
| `MarketDataRequest` | **NEW** - Tool call schema | OpenBB |
| `FundamentalAnalysisReport` | **NEW** - Ratio analysis | FinanceToolkit |

### 0.3 Evidence Policy

**Rule**: If a claim depends on live data or computed ratios, it MUST cite tool output, not memory.

```
EVIDENCE POLICY:
- Price claims → cite OpenBB get_quote timestamp
- Ratio claims → cite FinanceToolkit computation
- Historical data → cite OpenBB get_ohlcv range
- No "approximately" or "around" for checkable facts
```

**Absolute Outcome**: Prevents hallucinated numbers and forces institutional behavior.

---

## Phase 1: Integrate OpenBB and FinanceToolkit

### 1.1 OpenBB Integration

**What it provides**: Market data, price history, fundamentals, company info, macro

**Implementation Pattern**:
- FastAPI tool endpoints wrapping OpenBB SDK calls
- Redis cache by symbol + timeframe (TTL: quotes=60s, fundamentals=24h)
- Normalized JSON output schemas

**Minimum Endpoints**:

| Endpoint | OpenBB Function | Cache TTL | Output Schema |
|----------|-----------------|-----------|---------------|
| `GET /tools/openbb/quote/{symbol}` | `obb.equity.price.quote()` | 60s | `QuoteResponse` |
| `GET /tools/openbb/ohlcv/{symbol}` | `obb.equity.price.historical()` | 5min | `OHLCVResponse` |
| `GET /tools/openbb/fundamentals/{symbol}` | `obb.equity.fundamental.overview()` | 24h | `FundamentalsResponse` |
| `GET /tools/openbb/news/{symbol}` | `obb.news.company()` | 15min | `NewsResponse` |
| `GET /tools/openbb/macro/{series}` | `obb.economy.*` | 1h | `MacroResponse` |

**File**: `/backend/app/api/api_v1/endpoints/tools_openbb.py`

### 1.2 FinanceToolkit Integration

**What it provides**: 150+ computed ratios and financial statement-derived metrics

**Implementation Pattern**:
- Compute service taking ticker + period
- Returns categorized ratio bundles
- All calculations auditable (show formula)

**Minimum Endpoints**:

| Endpoint | Function | Output |
|----------|----------|--------|
| `GET /tools/ratios/statements/{symbol}` | Income, Balance, Cash Flow | `FinancialStatements` |
| `GET /tools/ratios/summary/{symbol}` | All ratio categories | `RatioSummary` |
| `GET /tools/ratios/category/{symbol}/{category}` | Single category deep dive | `RatioCategoryDetail` |
| `GET /tools/ratios/compare` | Multi-ticker comparison | `RatioComparison` |

**Ratio Categories**:
- Profitability (ROE, ROA, margins)
- Liquidity (current, quick, cash)
- Solvency (debt/equity, interest coverage)
- Valuation (P/E, P/B, EV/EBITDA)
- Growth (revenue, earnings, dividend)

**File**: `/backend/app/api/api_v1/endpoints/tools_financetoolkit.py`

### 1.3 Tool-Use Training Data

**Critical**: Model must learn to CALL tools, not explain them.

**Target**: 2,000 - 5,000 tool-use examples

**Format** (extends Alpaca):
```json
{
  "instruction": "What is Apple's current P/E ratio?",
  "input": "",
  "output": "<tool_call>\n{\"tool\": \"financetoolkit_ratios\", \"params\": {\"symbol\": \"AAPL\", \"category\": \"valuation\"}}\n</tool_call>",
  "tool_response": "{\"pe_ratio\": 28.5, \"pe_ttm\": 29.1, \"forward_pe\": 26.2, \"as_of\": \"2026-01-19\"}",
  "final_response": "Apple's current P/E ratio is 28.5 (TTM: 29.1, Forward: 26.2) as of January 19, 2026. This is [analysis based on tool output]...",
  "category": "tool_use_valuation"
}
```

**Distribution**:
| Category | Examples | Tool |
|----------|----------|------|
| Quote/price queries | 500 | OpenBB |
| Historical price analysis | 400 | OpenBB |
| Fundamental overview | 400 | OpenBB |
| Ratio calculations | 800 | FinanceToolkit |
| Multi-ticker comparison | 400 | FinanceToolkit |
| News-driven analysis | 300 | OpenBB |
| Macro/economic queries | 200 | OpenBB |

**Absolute Outcome**: Model stops improvising financial metrics.

---

## Phase 2: Insurance Workflow Pack

**Approach**: Build capability surface area FIRST, then consider specialized models.

### 2.1 Insurance Domain Taxonomy

Expand knowledge base with:
- Life insurance (term, whole, universal, variable)
- Health insurance (ACA, Medicare, Medicaid, HSA/FSA)
- Property & Casualty (auto, home, umbrella, liability)
- Annuities (fixed, variable, indexed, immediate)
- Long-term care (traditional, hybrid)
- Disability (short-term, long-term, own-occupation)
- Reinsurance basics
- Actuarial concepts (mortality tables, loss ratios)
- State-by-state regulatory variations

### 2.2 Insurance Schemas

| Schema | Purpose |
|--------|---------|
| `PolicyComparison` | Side-by-side policy analysis |
| `SuitabilityAssessment` | Needs-based recommendation |
| `NeedsAnalysis` | Coverage gap identification |
| `PremiumIllustrationSummary` | Projection summary with caveats |
| `ClaimsScenarioChecklist` | What-if claims analysis |

### 2.3 Insurance Rules Engine

Add to `/backend/app/services/compliance_rules.py`:

| Rule | Authority | Action |
|------|-----------|--------|
| `INS_SUITABILITY_CHECK` | Compliance | Require suitability assessment |
| `INS_REPLACEMENT_WARNING` | Compliance | Flag 1035 exchange risks |
| `INS_ILLUSTRATION_CAVEAT` | Legal | Mandate "not guaranteed" language |
| `INS_STATE_SPECIFIC` | Compliance | Route to state-specific rules |
| `INS_NO_GUARANTEED_OUTCOMES` | Legal | Block guarantee language |

### 2.4 Insurance Dataset

**Target**: 10,000 - 30,000 insurance-specific Q&A pairs

**Sources**:
- NAIC guidelines extraction
- State insurance department FAQs
- Product type comparisons (synthetic, validated)
- Claims scenarios
- Suitability case studies

**Absolute Outcome**: Real insurance workflows on 14B model without giant model merge.

---

## Phase 3: Accounting and GnuCash Integration

**Approach**: General ledger schema FIRST, then GnuCash as data source.

### 3.1 Accounting Schemas

| Schema | Purpose |
|--------|---------|
| `LedgerImport` | Transaction categorization |
| `MonthlyCloseChecklist` | Period-end procedures |
| `CashFlowForecast` | Forward-looking projections |
| `BudgetPlan` | Income/expense allocation |
| `BusinessKPIs` | Small business metrics |

### 3.2 GnuCash Connector

- Read GnuCash XML/SQLite files
- Map accounts to standard chart of accounts
- Generate reports without modifying source

### 3.3 Accounting Rules

| Rule | Action |
|------|--------|
| `ACCT_NO_TAX_FILING` | Block specific tax filing instructions |
| `ACCT_AUDIT_TRAIL` | Require source documentation |
| `ACCT_SEPARATION` | Enforce personal/business separation |

**Absolute Outcome**: TB2 becomes a real money manager, not only an investing assistant.

---

## Phase 4: Multi-Model Merge (After Tools & Eval Mature)

**Prerequisites**:
1. ✅ Measured deficits that cannot be fixed with data, tools, or routing
2. ✅ Locked benchmark showing where the model fails
3. ✅ Clean ablation setup for attribution

**Only Then Consider**:
- InvestLM-7B merge (config exists at `/mergekit_configs/advanced_stage2_expanded.yaml`)
- AdaptLLM/finance-chat merge

**Do NOT merge if**:
- Tool integration is incomplete
- Benchmark < 500 items
- Cannot attribute improvements

**Absolute Outcome**: Avoid unstable merges and moving targets.

---

## Phase 5: Scaling Models (Future)

**When to scale to DeepSeek-R1 full or Qwen3-235B**:
1. Need deeper reasoning under long contexts (>8K tokens)
2. Need multilingual institutional support
3. Have enough grounded data and tool-use patterns that scaling amplifies correct behavior

**Current bottleneck is NOT parameter count. It is**:
- Truth grounding
- Domain balance
- Tool-use training

---

## Implementation Timeline

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **Phase 0** | Policy docs, 7 schemas | ✅ COMPLETE |
| **Phase 1a** | OpenBB endpoints | ✅ COMPLETE |
| **Phase 1b** | FinanceToolkit endpoints | ✅ COMPLETE |
| **Phase 1c** | 2,500 tool-use training pairs | ✅ COMPLETE |
| **Phase 1d** | yfinance endpoints (free data) | ✅ COMPLETE |
| **Phase 2** | Insurance pack (10,000 pairs) | ✅ COMPLETE |
| **Phase 3** | Accounting integration (5,000 pairs) | ✅ COMPLETE |
| **Phase 4** | Model merge evaluation | Pending (benchmark > 431) |
| **Phase 5** | Scale to 70B+ | Phase 4 complete |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Tool-use accuracy | 95%+ correct tool calls |
| Hallucination rate on checkable facts | < 2% |
| Benchmark accuracy (500+ items) | 90%+ |
| Insurance workflow completion | 85%+ |
| Accounting task accuracy | 90%+ |
| Latency P95 | < 2000ms |

---

## Files to Create

| File | Purpose |
|------|---------|
| `/backend/app/api/api_v1/endpoints/tools_openbb.py` | OpenBB integration |
| `/backend/app/api/api_v1/endpoints/tools_financetoolkit.py` | FinanceToolkit integration |
| `/backend/app/schemas/tool_schemas.py` | Tool I/O schemas |
| `/backend/app/schemas/output_schemas.py` | 7 structured output schemas |
| `/backend/app/services/insurance_rules.py` | Insurance compliance rules |
| `/backend/app/services/accounting_rules.py` | Accounting compliance rules |
| `/backend/training_data/tool_use_examples.json` | Tool-use training data |
| `/backend/app/knowledge_base/insurance/` | Insurance domain content |
| `/backend/app/knowledge_base/accounting/` | Accounting domain content |

---

## Next Immediate Actions

1. ~~**Implement OpenBB endpoints** (5 endpoints)~~ ✅ COMPLETE
2. ~~**Implement FinanceToolkit endpoints** (4 endpoints)~~ ✅ COMPLETE
3. ~~**Define 7 structured output schemas**~~ ✅ COMPLETE
4. ~~**Generate 2,500 tool-use training examples**~~ ✅ COMPLETE
5. ~~**Expand benchmark to 431 questions**~~ ✅ COMPLETE
6. **Deploy vLLM on L4 with DoRA adapter** (NEXT)
7. **Run 431-question evaluation benchmark**
8. **Retrain with full 40,993 pairs**
