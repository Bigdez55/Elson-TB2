#!/usr/bin/env python3
"""
Expanded Quiz Templates V3 for Elson Financial AI

Final batch of questions to reach the 1000 question target.
Focus on comprehensive coverage across all financial planning areas.
"""

EXPANDED_QUIZZES_V3 = {
    # More basic personal finance
    "personal_finance_fundamentals": {
        "weight": 0.10,
        "questions": [
            # Savings and banking
            {"subdomain": "savings", "difficulty": "easy", "question_type": "factual",
             "question": "What is the difference between a savings account and a money market account?",
             "expected_elements": ["interest rates", "check writing", "minimum balance"],
             "prohibited_elements": ["always better", "guaranteed"]},
            {"subdomain": "savings", "difficulty": "easy", "question_type": "factual",
             "question": "What is FDIC insurance and what does it cover?",
             "expected_elements": ["$250,000", "deposit insurance", "per depositor"],
             "prohibited_elements": ["all money safe", "unlimited"]},
            {"subdomain": "savings", "difficulty": "easy", "question_type": "comparison",
             "question": "Compare CDs to high-yield savings accounts.",
             "expected_elements": ["term", "early withdrawal penalty", "interest rate"],
             "prohibited_elements": ["always CD", "always savings"]},
            {"subdomain": "checking", "difficulty": "easy", "question_type": "factual",
             "question": "What is overdraft protection and how does it work?",
             "expected_elements": ["linked account", "fees", "automatic transfer"],
             "prohibited_elements": ["free", "no cost"]},
            {"subdomain": "banking", "difficulty": "medium", "question_type": "comparison",
             "question": "Compare online banks to traditional brick-and-mortar banks.",
             "expected_elements": ["interest rates", "fees", "convenience", "services"],
             "prohibited_elements": ["always better", "no differences"]},

            # Emergency fund
            {"subdomain": "emergency_fund", "difficulty": "easy", "question_type": "factual",
             "question": "What is an emergency fund and how much should you have?",
             "expected_elements": ["3-6 months", "liquid", "unexpected expenses"],
             "prohibited_elements": ["exact amount", "guaranteed safe"]},
            {"subdomain": "emergency_fund", "difficulty": "medium", "question_type": "explanation",
             "question": "Where should you keep your emergency fund?",
             "expected_elements": ["accessible", "liquid", "FDIC insured"],
             "prohibited_elements": ["invest in stocks", "CD only"]},

            # Spending and cash flow
            {"subdomain": "cash_flow", "difficulty": "easy", "question_type": "factual",
             "question": "What is the difference between gross income and net income?",
             "expected_elements": ["before taxes", "after deductions", "take-home"],
             "prohibited_elements": ["same thing", "interchangeable"]},
            {"subdomain": "cash_flow", "difficulty": "medium", "question_type": "calculation",
             "question": "How do you calculate your savings rate?",
             "expected_elements": ["savings divided by income", "percentage", "gross vs net"],
             "prohibited_elements": ["exact target", "everyone should"]},
            {"subdomain": "spending", "difficulty": "medium", "question_type": "explanation",
             "question": "What is discretionary vs non-discretionary spending?",
             "expected_elements": ["essential", "optional", "needs vs wants"],
             "prohibited_elements": ["eliminate all discretionary", "always"]},

            # Financial goals
            {"subdomain": "goals", "difficulty": "easy", "question_type": "factual",
             "question": "What are SMART financial goals?",
             "expected_elements": ["Specific", "Measurable", "Achievable", "Relevant", "Time-bound"],
             "prohibited_elements": ["guaranteed success", "only method"]},
            {"subdomain": "goals", "difficulty": "medium", "question_type": "procedural",
             "question": "How should you prioritize multiple financial goals?",
             "expected_elements": ["emergency fund", "high-interest debt", "retirement", "timeline"],
             "prohibited_elements": ["one order for all", "simple answer"]},
            {"subdomain": "goals", "difficulty": "hard", "question_type": "scenario",
             "question": "Create a financial priority plan for a 35-year-old with $20,000 debt and no retirement savings.",
             "expected_elements": ["debt vs savings", "employer match", "interest rates"],
             "prohibited_elements": ["simple answer", "one approach"]},
        ]
    },

    # Debt Management Extended
    "debt_management_extended": {
        "weight": 0.06,
        "questions": [
            {"subdomain": "strategies", "difficulty": "easy", "question_type": "comparison",
             "question": "Compare the debt avalanche method to the debt snowball method.",
             "expected_elements": ["highest interest", "smallest balance", "psychological", "mathematical"],
             "prohibited_elements": ["always better", "only method"]},
            {"subdomain": "strategies", "difficulty": "medium", "question_type": "calculation",
             "question": "Calculate the interest savings of paying extra on a mortgage.",
             "expected_elements": ["amortization", "principal", "interest saved", "term reduction"],
             "prohibited_elements": ["always prepay", "guaranteed"]},
            {"subdomain": "mortgages", "difficulty": "medium", "question_type": "explanation",
             "question": "What is the difference between mortgage refinancing and recasting?",
             "expected_elements": ["new loan", "lump sum", "payment reduction", "closing costs"],
             "prohibited_elements": ["always refinance", "no cost"]},
            {"subdomain": "student_loans", "difficulty": "medium", "question_type": "comparison",
             "question": "Compare federal student loan repayment plans: standard, graduated, income-driven.",
             "expected_elements": ["payment amounts", "total cost", "forgiveness"],
             "prohibited_elements": ["always choose", "best for everyone"]},
            {"subdomain": "student_loans", "difficulty": "hard", "question_type": "explanation",
             "question": "What is Public Service Loan Forgiveness (PSLF) and who qualifies?",
             "expected_elements": ["qualifying employer", "120 payments", "Direct Loans"],
             "prohibited_elements": ["guaranteed forgiveness", "easy"]},
            {"subdomain": "consolidation", "difficulty": "medium", "question_type": "explanation",
             "question": "When does debt consolidation make sense?",
             "expected_elements": ["lower rate", "single payment", "total cost"],
             "prohibited_elements": ["always good", "no downside"]},
            {"subdomain": "bankruptcy", "difficulty": "hard", "question_type": "explanation",
             "question": "What is the difference between Chapter 7 and Chapter 13 bankruptcy?",
             "expected_elements": ["liquidation", "repayment plan", "eligibility", "impact"],
             "prohibited_elements": ["easy solution", "no consequences"]},
            {"subdomain": "collections", "difficulty": "medium", "question_type": "procedural",
             "question": "What are your rights when dealing with debt collectors?",
             "expected_elements": ["FDCPA", "validation", "cease contact", "time-barred debt"],
             "prohibited_elements": ["ignore them", "don't pay"]},
        ]
    },

    # Financial Planning Process
    "financial_planning_process": {
        "weight": 0.05,
        "questions": [
            {"subdomain": "process", "difficulty": "easy", "question_type": "factual",
             "question": "What are the six steps of the financial planning process?",
             "expected_elements": ["establish relationship", "gather data", "analyze", "present recommendations", "implement", "monitor"],
             "prohibited_elements": ["one-time", "simple"]},
            {"subdomain": "net_worth", "difficulty": "easy", "question_type": "calculation",
             "question": "How do you calculate net worth?",
             "expected_elements": ["assets minus liabilities", "snapshot", "balance sheet"],
             "prohibited_elements": ["income based", "complex"]},
            {"subdomain": "documents", "difficulty": "medium", "question_type": "factual",
             "question": "What financial documents should everyone keep organized?",
             "expected_elements": ["tax returns", "insurance policies", "estate documents", "investment statements"],
             "prohibited_elements": ["everything", "nothing"]},
            {"subdomain": "professionals", "difficulty": "medium", "question_type": "comparison",
             "question": "Compare CFP, CFA, and CPA credentials.",
             "expected_elements": ["financial planning", "investment analysis", "accounting"],
             "prohibited_elements": ["best", "always choose"]},
            {"subdomain": "fees", "difficulty": "medium", "question_type": "explanation",
             "question": "What are the different ways financial advisors charge for their services?",
             "expected_elements": ["fee-only", "commission", "AUM", "hourly"],
             "prohibited_elements": ["fee-only always best", "commissions always bad"]},
            {"subdomain": "review", "difficulty": "medium", "question_type": "explanation",
             "question": "How often should you review your financial plan?",
             "expected_elements": ["annually", "life changes", "market changes"],
             "prohibited_elements": ["never change", "daily"]},
        ]
    },

    # Risk Management Extended
    "risk_management_extended": {
        "weight": 0.04,
        "questions": [
            {"subdomain": "risk_tolerance", "difficulty": "easy", "question_type": "factual",
             "question": "What is risk tolerance and how is it different from risk capacity?",
             "expected_elements": ["willingness", "ability", "emotional", "financial"],
             "prohibited_elements": ["same thing", "simple"]},
            {"subdomain": "insurance", "difficulty": "medium", "question_type": "explanation",
             "question": "What types of risk should be insured vs self-insured?",
             "expected_elements": ["catastrophic", "affordable premium", "frequency vs severity"],
             "prohibited_elements": ["insure everything", "insure nothing"]},
            {"subdomain": "emergency", "difficulty": "medium", "question_type": "scenario",
             "question": "How should someone with a variable income approach risk management?",
             "expected_elements": ["larger emergency fund", "disability insurance", "income smoothing"],
             "prohibited_elements": ["same as W-2", "simple"]},
            {"subdomain": "diversification", "difficulty": "hard", "question_type": "explanation",
             "question": "What is correlation and why does it matter for diversification?",
             "expected_elements": ["movement together", "-1 to 1", "reduces risk"],
             "prohibited_elements": ["eliminates risk", "perfect protection"]},
            {"subdomain": "hedging", "difficulty": "hard", "question_type": "explanation",
             "question": "What is the difference between diversification and hedging?",
             "expected_elements": ["spreading risk", "offsetting risk", "cost", "goal"],
             "prohibited_elements": ["same thing", "no difference"]},
        ]
    },

    # Tax Planning Extended
    "tax_planning_extended": {
        "weight": 0.05,
        "questions": [
            {"subdomain": "strategies", "difficulty": "medium", "question_type": "explanation",
             "question": "What is tax-loss harvesting and when is it beneficial?",
             "expected_elements": ["realize losses", "offset gains", "wash sale rule"],
             "prohibited_elements": ["always harvest", "free tax savings"]},
            {"subdomain": "strategies", "difficulty": "hard", "question_type": "comparison",
             "question": "Compare tax-deferred, tax-exempt, and taxable accounts for different types of investments.",
             "expected_elements": ["asset location", "growth vs income", "tax efficiency"],
             "prohibited_elements": ["one best answer", "simple"]},
            {"subdomain": "strategies", "difficulty": "hard", "question_type": "scenario",
             "question": "Design a tax-efficient charitable giving strategy for someone with appreciated stock.",
             "expected_elements": ["donate stock directly", "avoid capital gains", "fair market value"],
             "prohibited_elements": ["always donate", "simple"]},
            {"subdomain": "business", "difficulty": "hard", "question_type": "explanation",
             "question": "What tax strategies are available for high-income W-2 employees?",
             "expected_elements": ["maximize retirement", "HSA", "charitable", "limited deductions"],
             "prohibited_elements": ["avoid taxes", "simple"]},
            {"subdomain": "timing", "difficulty": "extremely_complex", "question_type": "scenario",
             "question": "Analyze the tax implications of exercising incentive stock options (ISOs).",
             "expected_elements": ["AMT", "holding period", "disqualifying disposition"],
             "prohibited_elements": ["simple", "no tax"]},
        ]
    },

    # More Calculation-Heavy Questions
    "calculation_scenarios": {
        "weight": 0.06,
        "questions": [
            {"subdomain": "compound_interest", "difficulty": "medium", "question_type": "calculation",
             "question": "Calculate the future value of $500/month invested for 30 years at 7% annual return.",
             "expected_elements": ["future value", "compound growth", "time value of money"],
             "prohibited_elements": ["guaranteed return", "exact prediction"]},
            {"subdomain": "mortgage", "difficulty": "medium", "question_type": "calculation",
             "question": "Calculate the monthly payment on a $400,000 mortgage at 6.5% for 30 years.",
             "expected_elements": ["PMT formula", "principal and interest", "amortization"],
             "prohibited_elements": ["exact rate", "guaranteed"]},
            {"subdomain": "retirement", "difficulty": "hard", "question_type": "calculation",
             "question": "How much does a 35-year-old need to save monthly to have $2M by age 65 at 7% return?",
             "expected_elements": ["PMT", "future value", "time horizon"],
             "prohibited_elements": ["guaranteed", "exact prediction"]},
            {"subdomain": "inflation", "difficulty": "medium", "question_type": "calculation",
             "question": "If inflation averages 3%, what will $100,000 be worth in purchasing power in 20 years?",
             "expected_elements": ["purchasing power", "present value", "inflation factor"],
             "prohibited_elements": ["exact inflation", "guaranteed"]},
            {"subdomain": "withdrawal", "difficulty": "hard", "question_type": "calculation",
             "question": "Using the 4% rule, how much can someone withdraw annually from a $1.5M portfolio?",
             "expected_elements": ["$60,000", "sustainable withdrawal", "limitations"],
             "prohibited_elements": ["guaranteed safe", "always works"]},
            {"subdomain": "bonds", "difficulty": "hard", "question_type": "calculation",
             "question": "Calculate the current yield and yield to maturity for a bond trading at a discount.",
             "expected_elements": ["coupon/price", "time to maturity", "total return"],
             "prohibited_elements": ["simple", "guaranteed"]},
        ]
    },

    # Scenario-Based Questions
    "complex_scenarios": {
        "weight": 0.08,
        "questions": [
            {"subdomain": "young_professional", "difficulty": "medium", "question_type": "scenario",
             "question": "Create a financial plan for a 25-year-old making $60,000 with $30,000 in student loans.",
             "expected_elements": ["emergency fund", "employer match", "debt strategy"],
             "prohibited_elements": ["one right answer", "guaranteed"]},
            {"subdomain": "mid_career", "difficulty": "hard", "question_type": "scenario",
             "question": "A 45-year-old has $500,000 saved but needs $3M for retirement. What adjustments should they consider?",
             "expected_elements": ["savings rate", "asset allocation", "retirement age"],
             "prohibited_elements": ["simple solution", "guaranteed"]},
            {"subdomain": "pre_retirement", "difficulty": "hard", "question_type": "scenario",
             "question": "How should a 58-year-old consider sequence of returns risk as they approach retirement?",
             "expected_elements": ["glide path", "bucket strategy", "flexibility"],
             "prohibited_elements": ["100% stocks", "simple answer"]},
            {"subdomain": "inheritance", "difficulty": "hard", "question_type": "scenario",
             "question": "What should someone consider when receiving a $500,000 inheritance?",
             "expected_elements": ["no rush", "tax implications", "goals", "windfalls"],
             "prohibited_elements": ["spend it", "invest all immediately"]},
            {"subdomain": "job_loss", "difficulty": "medium", "question_type": "scenario",
             "question": "What financial steps should someone take after losing their job?",
             "expected_elements": ["emergency fund", "COBRA", "unemployment", "budget"],
             "prohibited_elements": ["panic", "withdraw retirement"]},
            {"subdomain": "windfall", "difficulty": "medium", "question_type": "scenario",
             "question": "How should someone handle a $100,000 bonus?",
             "expected_elements": ["tax withholding", "goals", "don't rush"],
             "prohibited_elements": ["spend immediately", "all to one place"]},
            {"subdomain": "divorce", "difficulty": "hard", "question_type": "scenario",
             "question": "What financial considerations are important during divorce proceedings?",
             "expected_elements": ["asset division", "tax implications", "budget adjustment"],
             "prohibited_elements": ["simple", "one approach"]},
            {"subdomain": "business_owner", "difficulty": "extremely_complex", "question_type": "scenario",
             "question": "How should a business owner coordinate personal and business financial planning?",
             "expected_elements": ["separation", "exit planning", "tax optimization"],
             "prohibited_elements": ["simple", "one strategy"]},
        ]
    },

    # Comparison Questions
    "product_comparisons": {
        "weight": 0.04,
        "questions": [
            {"subdomain": "retirement", "difficulty": "medium", "question_type": "comparison",
             "question": "Compare Traditional vs Roth for a high-income earner vs a low-income earner.",
             "expected_elements": ["tax bracket now vs later", "income limits", "flexibility"],
             "prohibited_elements": ["always Roth", "always Traditional"]},
            {"subdomain": "loans", "difficulty": "medium", "question_type": "comparison",
             "question": "Compare personal loans, home equity loans, and 401(k) loans.",
             "expected_elements": ["rates", "collateral", "tax implications", "risks"],
             "prohibited_elements": ["best option", "always choose"]},
            {"subdomain": "annuities", "difficulty": "hard", "question_type": "comparison",
             "question": "Compare annuities to bond ladders for retirement income.",
             "expected_elements": ["guaranteed income", "flexibility", "fees", "longevity"],
             "prohibited_elements": ["always annuity", "never annuity"]},
            {"subdomain": "advisors", "difficulty": "medium", "question_type": "comparison",
             "question": "Compare robo-advisors to human financial advisors.",
             "expected_elements": ["cost", "personalization", "complexity", "access"],
             "prohibited_elements": ["always robo", "never robo"]},
        ]
    },

    # Market and Economic Concepts
    "market_concepts": {
        "weight": 0.04,
        "questions": [
            {"subdomain": "cycles", "difficulty": "medium", "question_type": "explanation",
             "question": "What are the phases of a business cycle and how do they affect investments?",
             "expected_elements": ["expansion", "peak", "contraction", "trough"],
             "prohibited_elements": ["predict perfectly", "timing"]},
            {"subdomain": "inflation", "difficulty": "medium", "question_type": "explanation",
             "question": "How does inflation affect different types of investments?",
             "expected_elements": ["bonds hurt", "TIPS", "real assets", "purchasing power"],
             "prohibited_elements": ["always bad", "simple protection"]},
            {"subdomain": "interest_rates", "difficulty": "hard", "question_type": "explanation",
             "question": "How do Federal Reserve interest rate changes affect the economy and markets?",
             "expected_elements": ["borrowing costs", "bond prices", "currency", "lag"],
             "prohibited_elements": ["immediate impact", "predict market"]},
            {"subdomain": "valuation", "difficulty": "hard", "question_type": "explanation",
             "question": "What does it mean when the stock market is 'overvalued' or 'undervalued'?",
             "expected_elements": ["metrics", "historical comparison", "forward returns"],
             "prohibited_elements": ["time market", "predict crash"]},
        ]
    },

    # Special Situations
    "special_situations": {
        "weight": 0.03,
        "questions": [
            {"subdomain": "expats", "difficulty": "hard", "question_type": "explanation",
             "question": "What financial planning challenges do US expats face?",
             "expected_elements": ["FBAR", "PFIC", "tax filing", "banking challenges"],
             "prohibited_elements": ["simple", "no issues"],
             "compliance_sensitive": True},
            {"subdomain": "military", "difficulty": "medium", "question_type": "explanation",
             "question": "What unique financial benefits are available to military members?",
             "expected_elements": ["TSP", "Roth TSP", "tax benefits", "SGLI"],
             "prohibited_elements": ["same as civilian", "no benefits"]},
            {"subdomain": "disability", "difficulty": "hard", "question_type": "scenario",
             "question": "What financial planning considerations apply to someone with a disability?",
             "expected_elements": ["SSDI", "ABLE account", "special needs trust"],
             "prohibited_elements": ["simple", "same as everyone"]},
            {"subdomain": "self_employed", "difficulty": "hard", "question_type": "explanation",
             "question": "What unique financial challenges do self-employed individuals face?",
             "expected_elements": ["irregular income", "self-employment tax", "insurance", "retirement"],
             "prohibited_elements": ["simple", "same as employee"]},
        ]
    },
}


def get_expanded_quizzes_v3():
    """Return the expanded quiz dictionary version 3"""
    return EXPANDED_QUIZZES_V3
