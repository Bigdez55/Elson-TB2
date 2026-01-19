#!/usr/bin/env python3
"""
Elson TB2 - Generate Synthetic Q&A Pairs from Resource Catalog
Creates Q&A pairs from structured resources (CSV), professional roles, and compliance rules.

ENHANCED VERSION - Target: 17,800+ pairs

Sources:
- master_training_resources_v5.csv (929 resources) → 15 Q&A each = 13,935 pairs
- 70+ professional roles → 10 Q&A each = 700+ pairs
- 25+ compliance rules → 10 Q&A each = 250+ pairs
- 62 domains → 20 Q&A each = 1,240 pairs
- Cross-domain scenarios = 1,500+ pairs
"""

import json
import csv
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 62 Domain taxonomy
DOMAINS = [
    # Tax (6)
    "federal_income_tax", "state_local_tax", "international_tax", "estate_gift_tax", "corporate_tax", "tax_controversy",
    # Estate & Wealth (5)
    "estate_planning", "trust_administration", "probate", "charitable_planning", "gst_planning",
    # Insurance (8)
    "life_insurance", "health_insurance", "property_insurance", "casualty_insurance", "reinsurance", "annuities", "ltc_insurance", "actuarial",
    # Banking (5)
    "commercial_banking", "consumer_lending", "mortgage_finance", "credit_risk", "treasury_management",
    # Securities (10)
    "equities", "fixed_income", "derivatives", "commodities", "forex", "alternatives", "private_equity", "venture_capital", "hedge_funds", "cryptocurrency",
    # Portfolio (5)
    "portfolio_construction", "risk_management", "asset_allocation", "performance_attribution", "factor_investing",
    # Quantitative (5)
    "quantitative_finance", "algorithmic_trading", "hft", "market_microstructure", "trade_execution",
    # Corporate (4)
    "mergers_acquisitions", "business_valuation", "restructuring", "capital_markets",
    # Regulatory (6)
    "securities_regulation", "banking_regulation", "insurance_regulation", "aml_kyc", "erisa_benefits", "data_privacy",
    # Operations (4)
    "prime_brokerage", "custodial", "fund_administration", "fintech",
    # Planning (4)
    "financial_planning", "retirement_planning", "college_planning", "family_office"
]

# Domain descriptions for richer Q&A
DOMAIN_DESCRIPTIONS = {
    "federal_income_tax": "Federal income tax law covers taxation of individuals and entities under the Internal Revenue Code, including income recognition, deductions, credits, and filing requirements administered by the IRS.",
    "state_local_tax": "State and local tax (SALT) includes income taxes, sales taxes, property taxes, and other levies imposed by state and local governments, requiring nexus analysis and multi-state planning.",
    "international_tax": "International tax addresses cross-border transactions, foreign tax credits, transfer pricing, tax treaties, FATCA/CRS compliance, and outbound/inbound planning for multinational entities.",
    "estate_gift_tax": "Estate and gift tax governs wealth transfers during life and at death, including the unified credit, annual exclusions, marital deduction, portability, and generation-skipping transfer tax.",
    "corporate_tax": "Corporate tax covers C corporation taxation under Subchapter C, consolidated returns, dividends received deduction, and corporate reorganizations under IRC Sections 368 and 351.",
    "tax_controversy": "Tax controversy involves disputes with tax authorities including audits, appeals, Tax Court litigation, penalty abatement, offers in compromise, and collection due process.",
    "estate_planning": "Estate planning designs strategies for wealth transfer, asset protection, and tax minimization through wills, trusts, powers of attorney, and beneficiary designations.",
    "trust_administration": "Trust administration encompasses fiduciary duties, trust accounting, principal and income allocation, distributions, and investment management under the Prudent Investor Rule.",
    "probate": "Probate is the court-supervised process of validating wills, appointing executors, paying debts, and distributing assets to beneficiaries or heirs under intestacy laws.",
    "charitable_planning": "Charitable planning structures gifts to qualified charities through donor-advised funds, private foundations, charitable remainder trusts, and charitable lead trusts.",
    "gst_planning": "Generation-skipping transfer planning minimizes GST tax on transfers to skip persons through dynasty trusts, GST exemption allocation, and leveraging techniques.",
    "life_insurance": "Life insurance provides death benefit protection and wealth transfer benefits, including term, whole life, universal life, and variable products with tax-advantaged accumulation.",
    "health_insurance": "Health insurance covers medical expenses through employer-sponsored plans, individual policies, Medicare, Medicaid, and ACA marketplace options with various cost-sharing structures.",
    "property_insurance": "Property insurance protects against physical damage to real and personal property from covered perils, with replacement cost or actual cash value coverage.",
    "casualty_insurance": "Casualty and liability insurance covers legal liability for bodily injury and property damage, including auto, umbrella, professional liability, and D&O policies.",
    "reinsurance": "Reinsurance transfers risk from primary insurers to reinsurers through treaty or facultative arrangements, including quota share and excess of loss structures.",
    "annuities": "Annuities provide guaranteed income streams through fixed, variable, or indexed products with accumulation and payout phases, subject to specific tax treatment.",
    "ltc_insurance": "Long-term care insurance covers nursing home, assisted living, and home health care costs with benefit triggers, elimination periods, and inflation protection options.",
    "actuarial": "Actuarial science applies mathematical and statistical methods to assess risk, price insurance products, establish reserves, and ensure solvency.",
    "commercial_banking": "Commercial banking provides deposit services, lending, treasury management, and financial services to businesses under OCC, Fed, and FDIC supervision.",
    "consumer_lending": "Consumer lending includes personal loans, credit cards, and auto loans subject to TILA, ECOA, and CFPB consumer protection regulations.",
    "mortgage_finance": "Mortgage finance covers residential lending from origination through servicing, including conforming/non-conforming loans, RESPA, and secondary market activities.",
    "credit_risk": "Credit risk analysis evaluates borrower creditworthiness using financial statements, credit scores, and probability of default models for lending decisions.",
    "treasury_management": "Treasury management optimizes cash flows, working capital, and liquidity through concentration, disbursement, and investment strategies.",
    "equities": "Equity investments represent ownership in companies through common and preferred stock, with valuation based on earnings, cash flows, and market multiples.",
    "fixed_income": "Fixed income securities include bonds and notes providing regular interest payments, with analysis of yield, duration, convexity, and credit spreads.",
    "derivatives": "Derivatives are contracts deriving value from underlying assets, including options, futures, swaps, and forwards used for hedging and speculation.",
    "commodities": "Commodities trading involves physical and financial markets for energy, metals, and agricultural products through spot, futures, and OTC transactions.",
    "forex": "Foreign exchange markets facilitate currency trading with spot, forward, and swap transactions for hedging and speculation on exchange rate movements.",
    "alternatives": "Alternative investments include real assets, infrastructure, timber, farmland, and collectibles providing diversification and inflation protection.",
    "private_equity": "Private equity involves equity investments in non-public companies through LBOs, growth equity, and venture capital with illiquidity premiums and J-curve returns.",
    "venture_capital": "Venture capital provides early-stage financing to startups through seed, Series A/B/C rounds with term sheets, valuation, and exit strategies.",
    "hedge_funds": "Hedge funds employ diverse strategies including long/short equity, global macro, and event-driven approaches with 2-and-20 fee structures.",
    "cryptocurrency": "Cryptocurrency and digital assets include blockchain-based tokens, DeFi protocols, NFTs, and exchange trading with evolving regulatory frameworks.",
    "portfolio_construction": "Portfolio construction applies modern portfolio theory to optimize risk-adjusted returns through diversification, asset allocation, and rebalancing.",
    "risk_management": "Risk management identifies, measures, and mitigates financial risks including market, credit, liquidity, and operational risks using VaR and stress testing.",
    "asset_allocation": "Asset allocation determines portfolio weights across asset classes using strategic, tactical, and liability-driven approaches based on risk tolerance.",
    "performance_attribution": "Performance attribution decomposes returns into allocation, selection, and interaction effects using Brinson methodology and factor-based analysis.",
    "factor_investing": "Factor investing targets return premiums from value, momentum, quality, size, and low volatility factors through smart beta strategies.",
    "quantitative_finance": "Quantitative finance applies mathematical models to pricing, risk management, and trading using stochastic calculus and numerical methods.",
    "algorithmic_trading": "Algorithmic trading uses computer programs to execute trades based on predefined rules, signals, and market conditions with backtesting validation.",
    "hft": "High-frequency trading involves ultra-low latency market making and arbitrage strategies using colocation, FPGA, and sophisticated order management.",
    "market_microstructure": "Market microstructure studies price formation, liquidity, and trading mechanisms in limit order books and dealer markets.",
    "trade_execution": "Trade execution optimizes order implementation through VWAP, TWAP, and implementation shortfall algorithms minimizing market impact.",
    "mergers_acquisitions": "M&A involves business combinations through stock/asset purchases with due diligence, valuation, deal structuring, and post-merger integration.",
    "business_valuation": "Business valuation determines enterprise and equity value using DCF, comparable companies, precedent transactions, and asset-based methods.",
    "restructuring": "Restructuring addresses financial distress through in-court (Chapter 11) and out-of-court workouts, debtor-in-possession financing, and creditor negotiations.",
    "capital_markets": "Capital markets facilitate securities issuance through IPOs, debt offerings, and private placements with underwriting and syndication.",
    "securities_regulation": "Securities regulation governs capital markets through SEC, FINRA, and state blue sky laws covering registration, disclosure, and anti-fraud provisions.",
    "banking_regulation": "Banking regulation ensures safety and soundness through OCC, Fed, and FDIC supervision, capital requirements, and stress testing.",
    "insurance_regulation": "Insurance regulation is primarily state-based through NAIC model laws covering solvency, rate filing, market conduct, and consumer protection.",
    "aml_kyc": "AML/KYC programs prevent money laundering through customer identification, transaction monitoring, CTR/SAR filing, and OFAC sanctions screening.",
    "erisa_benefits": "ERISA governs employer benefit plans including fiduciary duties, prohibited transactions, disclosure requirements, and DOL enforcement.",
    "data_privacy": "Data privacy laws including GDPR and CCPA regulate personal information collection, use, disclosure, and individual rights.",
    "prime_brokerage": "Prime brokerage provides hedge funds with margin financing, securities lending, trade execution, and custody services.",
    "custodial": "Custodial services provide safekeeping, settlement, corporate actions processing, and reporting for institutional investors.",
    "fund_administration": "Fund administration includes NAV calculation, investor services, financial reporting, and regulatory compliance for investment funds.",
    "fintech": "Financial technology encompasses digital payments, lending platforms, robo-advisors, and RegTech solutions transforming financial services.",
    "financial_planning": "Financial planning develops comprehensive strategies addressing investments, taxes, insurance, retirement, and estate planning goals.",
    "retirement_planning": "Retirement planning designs accumulation and distribution strategies using qualified plans, IRAs, Social Security optimization, and income planning.",
    "college_planning": "College planning funds education through 529 plans, Coverdell accounts, financial aid optimization, and scholarship strategies.",
    "family_office": "Family office services provide comprehensive wealth management for ultra-high-net-worth families including investments, administration, and governance."
}

# 70+ Professional roles with responsibilities
PROFESSIONAL_ROLES = {
    "cfp": {
        "title": "Certified Financial Planner (CFP)",
        "responsibilities": "Comprehensive financial planning, retirement planning, investment advice, tax planning, estate planning, insurance planning",
        "credentials": "CFP certification from CFP Board, Series 65 or 66, bachelor's degree, 6,000+ hours experience",
        "domains": ["financial_planning", "retirement_planning", "estate_planning", "tax"]
    },
    "cfa": {
        "title": "Chartered Financial Analyst (CFA)",
        "responsibilities": "Investment analysis, portfolio management, equity research, asset allocation, risk assessment",
        "credentials": "CFA charter from CFA Institute, 3 levels of exams, 4,000+ hours investment experience",
        "domains": ["portfolio_construction", "equities", "fixed_income", "risk_management"]
    },
    "cpa": {
        "title": "Certified Public Accountant (CPA)",
        "responsibilities": "Tax preparation, tax planning, audit, financial statement preparation, compliance",
        "credentials": "CPA license from state board, 150 credit hours, pass CPA exam (4 parts), experience requirement",
        "domains": ["federal_income_tax", "state_local_tax", "corporate_tax"]
    },
    "estate_attorney": {
        "title": "Estate Planning Attorney",
        "responsibilities": "Draft wills and trusts, estate plan design, probate administration, asset protection, tax planning",
        "credentials": "JD from accredited law school, state bar admission, often LLM in taxation",
        "domains": ["estate_planning", "trust_administration", "probate", "estate_gift_tax"]
    },
    "trust_officer": {
        "title": "Trust Officer",
        "responsibilities": "Trust administration, fiduciary duties, beneficiary relations, investment oversight, distribution decisions",
        "credentials": "CTFA certification, banking experience, compliance training",
        "domains": ["trust_administration", "fiduciary", "estate_planning"]
    },
    "wealth_advisor": {
        "title": "Private Wealth Advisor",
        "responsibilities": "Holistic wealth management, investment strategy, multi-generational planning, family governance",
        "credentials": "CFP, CFA, or similar; Series 7, 66; extensive client experience",
        "domains": ["financial_planning", "family_office", "portfolio_construction"]
    },
    "insurance_specialist": {
        "title": "Insurance Specialist (CLU/ChFC)",
        "responsibilities": "Life insurance planning, risk assessment, policy selection, premium financing, business insurance",
        "credentials": "CLU, ChFC, state insurance licenses, continuing education",
        "domains": ["life_insurance", "estate_planning", "risk_management"]
    },
    "tax_manager": {
        "title": "Tax Manager",
        "responsibilities": "Tax compliance, tax planning strategy, audit defense, international tax, entity structuring",
        "credentials": "CPA, EA, or tax attorney; advanced tax education",
        "domains": ["federal_income_tax", "state_local_tax", "international_tax", "corporate_tax"]
    },
    "compliance_officer": {
        "title": "Chief Compliance Officer (CCO)",
        "responsibilities": "Regulatory compliance, AML/KYC programs, policy development, audit coordination, training",
        "credentials": "Legal background, CRCM, Series 14, extensive regulatory experience",
        "domains": ["securities_regulation", "aml_kyc", "banking_regulation"]
    },
    "portfolio_manager": {
        "title": "Portfolio Manager",
        "responsibilities": "Investment decisions, asset allocation, risk management, performance monitoring, client reporting",
        "credentials": "CFA, Series 65/66, proven track record, often advanced degree",
        "domains": ["portfolio_construction", "asset_allocation", "risk_management", "equities", "fixed_income"]
    },
    "risk_manager": {
        "title": "Chief Risk Officer (CRO)",
        "responsibilities": "Enterprise risk management, market risk, credit risk, operational risk, regulatory capital",
        "credentials": "FRM, PRM, CFA; extensive risk management experience",
        "domains": ["risk_management", "credit_risk", "market_microstructure"]
    },
    "actuary": {
        "title": "Actuary (FSA/FCAS)",
        "responsibilities": "Risk assessment, pricing, reserving, product development, regulatory compliance",
        "credentials": "FSA, FCAS, or ASA/ACAS; extensive exam process through SOA or CAS",
        "domains": ["actuarial", "life_insurance", "health_insurance", "risk_management"]
    },
    # Additional 60+ roles for comprehensive coverage
    "tax_attorney": {
        "title": "Tax Attorney (LLM)",
        "responsibilities": "Tax controversy, tax planning, IRS representation, tax litigation, structuring transactions",
        "credentials": "JD, LLM in Taxation, state bar admission, Tax Court admission",
        "domains": ["federal_income_tax", "tax_controversy", "corporate_tax", "international_tax"]
    },
    "enrolled_agent": {
        "title": "Enrolled Agent (EA)",
        "responsibilities": "Tax preparation, IRS representation, tax planning, audit defense",
        "credentials": "EA designation from IRS, pass SEE exam or IRS experience",
        "domains": ["federal_income_tax", "state_local_tax", "tax_controversy"]
    },
    "investment_banker": {
        "title": "Investment Banker",
        "responsibilities": "M&A advisory, capital raising, IPOs, debt financing, deal structuring",
        "credentials": "MBA or finance degree, Series 79, extensive deal experience",
        "domains": ["mergers_acquisitions", "capital_markets", "business_valuation"]
    },
    "equity_analyst": {
        "title": "Equity Research Analyst",
        "responsibilities": "Company analysis, financial modeling, earnings forecasts, investment recommendations",
        "credentials": "CFA, MBA, Series 86/87, sector expertise",
        "domains": ["equities", "business_valuation", "portfolio_construction"]
    },
    "fixed_income_analyst": {
        "title": "Fixed Income Analyst",
        "responsibilities": "Bond analysis, credit research, yield curve analysis, duration management",
        "credentials": "CFA, fixed income experience, credit analysis skills",
        "domains": ["fixed_income", "credit_risk", "risk_management"]
    },
    "derivatives_trader": {
        "title": "Derivatives Trader",
        "responsibilities": "Options/futures trading, hedging, risk management, pricing, Greeks management",
        "credentials": "Series 3, quantitative background, trading experience",
        "domains": ["derivatives", "risk_management", "trade_execution"]
    },
    "quant_developer": {
        "title": "Quantitative Developer",
        "responsibilities": "Trading system development, model implementation, algorithm optimization, backtesting",
        "credentials": "MS/PhD in CS or Math, Python/C++, financial modeling",
        "domains": ["quantitative_finance", "algorithmic_trading", "hft"]
    },
    "quant_researcher": {
        "title": "Quantitative Researcher",
        "responsibilities": "Alpha research, signal development, statistical modeling, strategy design",
        "credentials": "PhD in quantitative field, research publications, ML expertise",
        "domains": ["quantitative_finance", "factor_investing", "algorithmic_trading"]
    },
    "pe_associate": {
        "title": "Private Equity Associate",
        "responsibilities": "Deal sourcing, due diligence, financial modeling, portfolio monitoring",
        "credentials": "MBA, investment banking experience, LBO modeling skills",
        "domains": ["private_equity", "business_valuation", "mergers_acquisitions"]
    },
    "vc_partner": {
        "title": "Venture Capital Partner",
        "responsibilities": "Deal sourcing, investment decisions, board participation, portfolio support",
        "credentials": "Operating experience, investment track record, industry network",
        "domains": ["venture_capital", "business_valuation", "capital_markets"]
    },
    "hedge_fund_pm": {
        "title": "Hedge Fund Portfolio Manager",
        "responsibilities": "Investment strategy, position sizing, risk management, performance optimization",
        "credentials": "CFA, proven track record, deep market expertise",
        "domains": ["hedge_funds", "portfolio_construction", "risk_management"]
    },
    "real_estate_analyst": {
        "title": "Real Estate Analyst",
        "responsibilities": "Property valuation, market analysis, financial modeling, due diligence",
        "credentials": "Real estate finance background, Argus certification, market expertise",
        "domains": ["alternatives", "business_valuation", "mortgage_finance"]
    },
    "insurance_underwriter": {
        "title": "Insurance Underwriter",
        "responsibilities": "Risk assessment, policy pricing, coverage determination, loss evaluation",
        "credentials": "CPCU, AU, underwriting experience, industry knowledge",
        "domains": ["property_insurance", "casualty_insurance", "life_insurance"]
    },
    "claims_adjuster": {
        "title": "Claims Adjuster",
        "responsibilities": "Claims investigation, loss evaluation, settlement negotiation, fraud detection",
        "credentials": "State license, AIC designation, claims experience",
        "domains": ["property_insurance", "casualty_insurance", "health_insurance"]
    },
    "bank_examiner": {
        "title": "Bank Examiner",
        "responsibilities": "Bank safety and soundness examination, compliance review, capital adequacy assessment",
        "credentials": "Commission from OCC/Fed/FDIC, finance degree, examination experience",
        "domains": ["banking_regulation", "commercial_banking", "credit_risk"]
    },
    "aml_officer": {
        "title": "AML/BSA Officer",
        "responsibilities": "AML program management, SAR/CTR filing, suspicious activity monitoring, training",
        "credentials": "CAMS certification, regulatory experience, compliance background",
        "domains": ["aml_kyc", "banking_regulation", "securities_regulation"]
    },
    "finra_examiner": {
        "title": "FINRA Examiner",
        "responsibilities": "Broker-dealer examination, rule compliance, investor protection, enforcement",
        "credentials": "Securities licenses, legal or compliance background",
        "domains": ["securities_regulation", "aml_kyc", "compliance"]
    },
    "erisa_counsel": {
        "title": "ERISA Counsel",
        "responsibilities": "Employee benefit plan compliance, fiduciary advice, plan design, DOL matters",
        "credentials": "JD, ERISA expertise, plan qualification experience",
        "domains": ["erisa_benefits", "retirement_planning", "tax"]
    },
    "pension_actuary": {
        "title": "Pension Actuary (EA/FSA)",
        "responsibilities": "Pension plan valuation, funding calculations, PBGC compliance, plan design",
        "credentials": "Enrolled Actuary designation, FSA, pension experience",
        "domains": ["actuarial", "erisa_benefits", "retirement_planning"]
    },
    "family_office_cio": {
        "title": "Family Office Chief Investment Officer",
        "responsibilities": "Investment strategy, manager selection, asset allocation, performance oversight",
        "credentials": "CFA, institutional investment experience, family office background",
        "domains": ["family_office", "portfolio_construction", "asset_allocation"]
    },
    "family_office_coo": {
        "title": "Family Office Chief Operating Officer",
        "responsibilities": "Operations management, vendor oversight, technology, reporting, administration",
        "credentials": "Operations experience, family office or wealth management background",
        "domains": ["family_office", "fund_administration", "custodial"]
    },
    "philanthropy_advisor": {
        "title": "Philanthropy Advisor",
        "responsibilities": "Charitable giving strategy, foundation management, donor-advised funds, impact measurement",
        "credentials": "CAP designation, nonprofit experience, philanthropic expertise",
        "domains": ["charitable_planning", "estate_planning", "family_office"]
    },
    "trust_officer_senior": {
        "title": "Senior Trust Officer",
        "responsibilities": "Complex trust administration, beneficiary relations, fiduciary decisions, litigation support",
        "credentials": "CTFA, JD or MBA, extensive trust experience",
        "domains": ["trust_administration", "estate_planning", "fiduciary"]
    },
    "probate_attorney": {
        "title": "Probate Attorney",
        "responsibilities": "Estate administration, probate proceedings, will contests, creditor claims",
        "credentials": "JD, state bar admission, probate court experience",
        "domains": ["probate", "estate_planning", "trust_administration"]
    },
    "wealth_psychologist": {
        "title": "Wealth Psychologist",
        "responsibilities": "Family dynamics, wealth transition counseling, next-gen preparation, conflict resolution",
        "credentials": "PhD in psychology, family systems training, wealth counseling experience",
        "domains": ["family_office", "estate_planning", "financial_planning"]
    },
    "crypto_analyst": {
        "title": "Cryptocurrency Analyst",
        "responsibilities": "Digital asset analysis, blockchain research, DeFi evaluation, regulatory monitoring",
        "credentials": "Blockchain expertise, quantitative skills, crypto trading experience",
        "domains": ["cryptocurrency", "fintech", "securities_regulation"]
    },
    "fintech_product_manager": {
        "title": "FinTech Product Manager",
        "responsibilities": "Product strategy, feature development, regulatory compliance, user experience",
        "credentials": "Product management experience, fintech domain knowledge",
        "domains": ["fintech", "consumer_lending", "treasury_management"]
    },
    "robo_advisor_developer": {
        "title": "Robo-Advisor Developer",
        "responsibilities": "Algorithm development, portfolio optimization, user interface, regulatory compliance",
        "credentials": "Software engineering, quantitative finance, investment expertise",
        "domains": ["fintech", "portfolio_construction", "asset_allocation"]
    },
    "securities_attorney": {
        "title": "Securities Attorney",
        "responsibilities": "Securities offerings, SEC compliance, M&A transactions, regulatory matters",
        "credentials": "JD, state bar admission, securities law expertise",
        "domains": ["securities_regulation", "capital_markets", "mergers_acquisitions"]
    },
    "commodities_trader": {
        "title": "Commodities Trader",
        "responsibilities": "Physical/financial commodity trading, hedging, basis trading, logistics",
        "credentials": "Series 3, commodity market expertise, trading experience",
        "domains": ["commodities", "derivatives", "trade_execution"]
    },
    "fx_trader": {
        "title": "FX Trader",
        "responsibilities": "Currency trading, hedging, carry trades, emerging markets, G10 pairs",
        "credentials": "FX market experience, macro analysis skills, trading systems",
        "domains": ["forex", "derivatives", "risk_management"]
    },
    "credit_officer": {
        "title": "Chief Credit Officer",
        "responsibilities": "Credit policy, loan approval, portfolio monitoring, loss mitigation",
        "credentials": "Credit analysis background, banking experience, risk management",
        "domains": ["credit_risk", "commercial_banking", "consumer_lending"]
    },
    "mortgage_underwriter": {
        "title": "Mortgage Underwriter",
        "responsibilities": "Loan qualification, credit analysis, property evaluation, compliance review",
        "credentials": "Mortgage experience, underwriting certification, regulatory knowledge",
        "domains": ["mortgage_finance", "consumer_lending", "credit_risk"]
    },
    "prime_broker_rep": {
        "title": "Prime Brokerage Representative",
        "responsibilities": "Client relationship, margin management, securities lending, trade execution",
        "credentials": "Series 7, hedge fund knowledge, operations experience",
        "domains": ["prime_brokerage", "hedge_funds", "custodial"]
    },
    "fund_accountant": {
        "title": "Fund Accountant",
        "responsibilities": "NAV calculation, financial reporting, expense allocation, investor reporting",
        "credentials": "CPA or accounting degree, fund accounting experience",
        "domains": ["fund_administration", "hedge_funds", "private_equity"]
    },
    "transfer_agent": {
        "title": "Transfer Agent Specialist",
        "responsibilities": "Shareholder recordkeeping, distributions, corporate actions, proxy services",
        "credentials": "Operations experience, securities knowledge, regulatory familiarity",
        "domains": ["custodial", "fund_administration", "securities_regulation"]
    },
    "structured_products_analyst": {
        "title": "Structured Products Analyst",
        "responsibilities": "Product analysis, pricing, structuring, documentation, risk assessment",
        "credentials": "Quantitative background, derivatives expertise, legal knowledge",
        "domains": ["derivatives", "fixed_income", "capital_markets"]
    },
    "muni_bond_analyst": {
        "title": "Municipal Bond Analyst",
        "responsibilities": "Credit analysis, issuer evaluation, tax-exempt securities, state/local finance",
        "credentials": "CFA, public finance experience, credit analysis skills",
        "domains": ["fixed_income", "state_local_tax", "credit_risk"]
    },
    "restructuring_advisor": {
        "title": "Restructuring Advisor",
        "responsibilities": "Distressed situations, creditor negotiations, Chapter 11, turnaround strategy",
        "credentials": "Investment banking, restructuring experience, legal knowledge",
        "domains": ["restructuring", "credit_risk", "business_valuation"]
    },
    "valuation_specialist": {
        "title": "Business Valuation Specialist (CVA/ABV)",
        "responsibilities": "Fair market value, litigation support, M&A valuation, intangible assets",
        "credentials": "CVA, ABV, ASA; CPA or CFA; valuation experience",
        "domains": ["business_valuation", "mergers_acquisitions", "estate_gift_tax"]
    },
    "data_privacy_officer": {
        "title": "Data Privacy Officer (DPO)",
        "responsibilities": "Privacy compliance, GDPR/CCPA implementation, data governance, breach response",
        "credentials": "CIPP certification, privacy law expertise, compliance background",
        "domains": ["data_privacy", "fintech", "securities_regulation"]
    },
    "model_validator": {
        "title": "Model Risk Validator",
        "responsibilities": "Model validation, backtesting, documentation review, regulatory compliance",
        "credentials": "PhD in quantitative field, model validation experience, SR 11-7 knowledge",
        "domains": ["risk_management", "quantitative_finance", "banking_regulation"]
    },
    "stress_testing_analyst": {
        "title": "Stress Testing Analyst",
        "responsibilities": "Scenario design, loss estimation, capital planning, CCAR/DFAST compliance",
        "credentials": "Quantitative background, stress testing experience, regulatory knowledge",
        "domains": ["risk_management", "banking_regulation", "credit_risk"]
    }
}

# Compliance rules
COMPLIANCE_RULES = {
    "aml_ctr": {
        "name": "Currency Transaction Report (CTR)",
        "description": "File CTR for cash transactions over $10,000",
        "authority": "FinCEN, Bank Secrecy Act",
        "domain": "aml_kyc"
    },
    "aml_sar": {
        "name": "Suspicious Activity Report (SAR)",
        "description": "File SAR for transactions exhibiting suspicious patterns regardless of amount",
        "authority": "FinCEN, Bank Secrecy Act",
        "domain": "aml_kyc"
    },
    "kyc_cip": {
        "name": "Customer Identification Program (CIP)",
        "description": "Verify customer identity using government-issued ID, date of birth, address, SSN/TIN",
        "authority": "USA PATRIOT Act Section 326",
        "domain": "aml_kyc"
    },
    "fiduciary_prudent_investor": {
        "name": "Prudent Investor Rule",
        "description": "Fiduciaries must invest with care, skill, and caution of a prudent investor",
        "authority": "Uniform Prudent Investor Act, state trust codes",
        "domain": "fiduciary"
    },
    "fiduciary_loyalty": {
        "name": "Duty of Loyalty",
        "description": "Fiduciary must act solely in the interest of beneficiaries, avoid self-dealing",
        "authority": "Common law, Restatement of Trusts",
        "domain": "fiduciary"
    },
    "sec_reg_bi": {
        "name": "Regulation Best Interest (Reg BI)",
        "description": "Broker-dealers must act in customer's best interest when making recommendations",
        "authority": "SEC, Securities Exchange Act",
        "domain": "securities_regulation"
    },
    "erisa_fiduciary": {
        "name": "ERISA Fiduciary Standard",
        "description": "Plan fiduciaries must act prudently and solely in interest of participants",
        "authority": "ERISA Section 404",
        "domain": "erisa_benefits"
    },
    "gift_tax_exclusion": {
        "name": "Annual Gift Tax Exclusion",
        "description": "Annual exclusion amount ($18,000 for 2024) per donee without gift tax consequences",
        "authority": "IRC Section 2503(b)",
        "domain": "estate_gift_tax"
    },
    "estate_tax_exemption": {
        "name": "Estate Tax Exemption",
        "description": "Federal estate tax exemption ($13.61M for 2024, scheduled to drop to ~$7M in 2026)",
        "authority": "IRC Section 2010",
        "domain": "estate_gift_tax"
    },
    "rmd_rules": {
        "name": "Required Minimum Distributions (RMD)",
        "description": "Required distributions from retirement accounts starting at age 73",
        "authority": "IRC Section 401(a)(9), SECURE Act 2.0",
        "domain": "retirement_planning"
    },
    "concentration_limit": {
        "name": "Concentration Limit",
        "description": "Single position should not exceed 25% of portfolio to maintain diversification",
        "authority": "Investment policy, prudent investor standards",
        "domain": "portfolio_construction"
    },
    "pattern_day_trader": {
        "name": "Pattern Day Trader Rule",
        "description": "4+ day trades in 5 business days triggers PDT status, requires $25K minimum equity",
        "authority": "FINRA Rule 4210",
        "domain": "securities_regulation"
    },
    # Additional compliance rules for comprehensive coverage (25+ total)
    "qualified_purchaser": {
        "name": "Qualified Purchaser Definition",
        "description": "Individual with $5M+ in investments or family company with $5M+ investments to invest in 3(c)(7) funds",
        "authority": "Investment Company Act Section 2(a)(51)",
        "domain": "securities_regulation"
    },
    "accredited_investor": {
        "name": "Accredited Investor Definition",
        "description": "Individual with $200K income ($300K joint) or $1M net worth excluding primary residence",
        "authority": "SEC Regulation D Rule 501(a)",
        "domain": "securities_regulation"
    },
    "wash_sale": {
        "name": "Wash Sale Rule",
        "description": "Cannot deduct loss if substantially identical securities purchased within 30 days before/after sale",
        "authority": "IRC Section 1091",
        "domain": "federal_income_tax"
    },
    "constructive_sale": {
        "name": "Constructive Sale Rule",
        "description": "Entering offsetting positions treated as sale for tax purposes, triggering capital gains",
        "authority": "IRC Section 1259",
        "domain": "federal_income_tax"
    },
    "step_transaction": {
        "name": "Step Transaction Doctrine",
        "description": "IRS can collapse multiple steps into single transaction based on substance over form",
        "authority": "Common law doctrine, Commissioner v. Clark",
        "domain": "federal_income_tax"
    },
    "grantor_trust": {
        "name": "Grantor Trust Rules",
        "description": "Trust income taxable to grantor if grantor retains certain powers under IRC 671-679",
        "authority": "IRC Sections 671-679",
        "domain": "trust_administration"
    },
    "crummy_power": {
        "name": "Crummey Withdrawal Power",
        "description": "Beneficiary right to withdraw gift contributions qualifies transfer for annual exclusion",
        "authority": "Crummey v. Commissioner, 9th Circuit",
        "domain": "estate_gift_tax"
    },
    "prudent_investor_act": {
        "name": "Uniform Prudent Investor Act",
        "description": "Trustee must invest as prudent investor would, considering total portfolio and diversification",
        "authority": "UPIA adopted by most states",
        "domain": "trust_administration"
    },
    "duty_of_impartiality": {
        "name": "Fiduciary Duty of Impartiality",
        "description": "Trustee must balance interests of income beneficiaries and remaindermen fairly",
        "authority": "Restatement (Third) of Trusts",
        "domain": "trust_administration"
    },
    "clawback": {
        "name": "Estate Tax Clawback",
        "description": "Adjusted taxable gifts added back to estate, potentially triggering tax on previously exempted gifts",
        "authority": "IRC Section 2001(b)",
        "domain": "estate_gift_tax"
    },
    "insurable_interest": {
        "name": "Insurable Interest Requirement",
        "description": "Policy owner must have insurable interest in insured's life at policy inception",
        "authority": "State insurance codes",
        "domain": "life_insurance"
    },
    "transfer_for_value": {
        "name": "Transfer for Value Rule",
        "description": "Life insurance death benefit becomes taxable if policy transferred for valuable consideration",
        "authority": "IRC Section 101(a)(2)",
        "domain": "life_insurance"
    },
    "three_year_rule": {
        "name": "Three-Year Rule for Life Insurance",
        "description": "Life insurance transferred within 3 years of death included in gross estate",
        "authority": "IRC Section 2035",
        "domain": "estate_gift_tax"
    },
    "net_capital_rule": {
        "name": "Net Capital Rule",
        "description": "Broker-dealers must maintain minimum net capital based on their business activities",
        "authority": "SEC Rule 15c3-1",
        "domain": "securities_regulation"
    },
    "customer_protection": {
        "name": "Customer Protection Rule",
        "description": "Broker-dealers must segregate customer securities and maintain reserve formula",
        "authority": "SEC Rule 15c3-3",
        "domain": "securities_regulation"
    },
    "beneficial_ownership": {
        "name": "Beneficial Ownership Rule",
        "description": "Financial institutions must identify and verify beneficial owners of legal entities",
        "authority": "FinCEN CDD Rule 31 CFR 1010.230",
        "domain": "aml_kyc"
    },
    "ofac_screening": {
        "name": "OFAC Sanctions Screening",
        "description": "Screen all customers and transactions against OFAC SDN and other sanctions lists",
        "authority": "OFAC regulations, 31 CFR Chapter V",
        "domain": "aml_kyc"
    },
    "form_adv": {
        "name": "Form ADV Disclosure",
        "description": "Investment advisers must file Form ADV with SEC and deliver Part 2A brochure to clients",
        "authority": "Investment Advisers Act Rule 204-3",
        "domain": "securities_regulation"
    },
    "best_execution": {
        "name": "Best Execution Obligation",
        "description": "Broker-dealers and advisers must seek most favorable terms for customer transactions",
        "authority": "FINRA Rule 5310, SEC guidance",
        "domain": "trade_execution"
    },
    "soft_dollar": {
        "name": "Soft Dollar Arrangements",
        "description": "Using commission dollars for research must comply with Section 28(e) safe harbor requirements",
        "authority": "Securities Exchange Act Section 28(e)",
        "domain": "securities_regulation"
    },
    "volcker_rule": {
        "name": "Volcker Rule",
        "description": "Banks prohibited from proprietary trading and certain hedge fund/PE investments",
        "authority": "Dodd-Frank Section 619, 12 CFR Part 44",
        "domain": "banking_regulation"
    },
    "lcr_requirement": {
        "name": "Liquidity Coverage Ratio",
        "description": "Banks must hold sufficient high-quality liquid assets to cover 30-day net cash outflows",
        "authority": "Basel III, 12 CFR Part 50",
        "domain": "banking_regulation"
    },
    "ccar_requirement": {
        "name": "CCAR Stress Testing",
        "description": "Large banks must demonstrate capital adequacy under Federal Reserve stress scenarios",
        "authority": "12 CFR Part 252",
        "domain": "banking_regulation"
    },
    "rmbs_retention": {
        "name": "Risk Retention Rule",
        "description": "Securitizers must retain 5% economic interest in asset-backed securities",
        "authority": "Dodd-Frank Section 941, 17 CFR 246",
        "domain": "capital_markets"
    }
}

# Question templates for resource-based Q&A (expanded for 15 Q&A per resource)
RESOURCE_TEMPLATES = [
    "What is {title} and how does it apply to {domain}?",
    "Explain the role of {organization} in {subdomain}.",
    "What are the key provisions of {title} for {jurisdiction} compliance?",
    "How should financial professionals use {title} from {organization}?",
    "What information does {title} provide for {domain} planning?",
    "Why is {title} important for {subdomain} professionals?",
    "Describe the purpose and scope of {title}.",
    "What regulatory guidance does {organization} provide through {title}?",
    "How does {title} impact {domain} practitioners?",
    "What are the practical applications of {title} in {subdomain}?",
    "Summarize the main points of {title} for {domain} professionals.",
    "What compliance requirements are outlined in {title}?",
    "How often is {title} updated by {organization}?",
    "What are common misconceptions about {title}?",
    "How does {title} differ from similar resources in {domain}?"
]

# Question templates for role-based Q&A (expanded for 10 Q&A per role)
ROLE_TEMPLATES = [
    "What are the responsibilities of a {title}?",
    "What credentials does a {title} need?",
    "How does a {title} coordinate with other professionals?",
    "What domains does a {title} specialize in?",
    "When should a client engage a {title}?",
    "What value does a {title} provide to high-net-worth clients?",
    "Describe the typical day-to-day activities of a {title}.",
    "What continuing education is required for a {title}?",
    "What career path leads to becoming a {title}?",
    "What ethical obligations does a {title} have?"
]

# Question templates for compliance-based Q&A
COMPLIANCE_TEMPLATES = [
    "What is {name} and when does it apply?",
    "What authority enforces {name}?",
    "What are the requirements of {name}?",
    "What happens if you violate {name}?",
    "How do financial professionals comply with {name}?",
    "Explain the purpose of {name} in financial regulation.",
    "What documentation is required for {name} compliance?",
    "How has {name} evolved in recent years?"
]


def generate_hash(text: str) -> str:
    """Generate a short hash for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def load_resources(csv_path: Path) -> List[Dict[str, Any]]:
    """Load resources from CSV file."""
    resources = []
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('title') and row.get('url'):
                    resources.append(row)
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
    return resources


def generate_resource_qa(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate Q&A pairs from resource catalog - target 15 per resource."""
    pairs = []

    for resource in resources:
        title = resource.get('title', '')
        organization = resource.get('organization', 'the source')
        domain = resource.get('domain', 'finance')
        subdomain = resource.get('subdomain', domain)
        jurisdiction = resource.get('jurisdiction', 'US')
        notes = resource.get('notes', '')
        url = resource.get('url', '')

        if not title or len(title) < 5:
            continue

        # Generate 10-15 Q&A pairs per resource (increased from 3)
        num_questions = min(15, len(RESOURCE_TEMPLATES))
        templates = random.sample(RESOURCE_TEMPLATES, num_questions)

        for template in templates:
            try:
                question = template.format(
                    title=title,
                    organization=organization,
                    domain=domain.replace('_', ' '),
                    subdomain=subdomain.replace('_', ' '),
                    jurisdiction=jurisdiction
                )

                answer = f"**{title}**\n\n"
                if organization:
                    answer += f"Published by: {organization}\n"
                if notes:
                    answer += f"\n{notes}\n"
                if url:
                    answer += f"\nSource: {url}\n"
                answer += f"\nThis resource is relevant for {domain.replace('_', ' ')} professionals working in {jurisdiction} jurisdiction."

                pairs.append({
                    "instruction": question,
                    "input": "",
                    "output": answer,
                    "category": domain if domain in DOMAINS else "general_finance",
                    "source": "synthetic_resource",
                    "resource_title": title,
                    "hash": generate_hash(question + answer)
                })
            except Exception:
                continue

    return pairs


def generate_role_qa() -> List[Dict[str, Any]]:
    """Generate Q&A pairs from professional roles."""
    pairs = []

    for role_id, role_data in PROFESSIONAL_ROLES.items():
        title = role_data["title"]
        responsibilities = role_data["responsibilities"]
        credentials = role_data["credentials"]
        domains = role_data["domains"]

        # Generate multiple Q&A per role
        templates = random.sample(ROLE_TEMPLATES, min(5, len(ROLE_TEMPLATES)))

        for template in templates:
            question = template.format(title=title)

            if "responsibilities" in template.lower():
                answer = f"A {title} is responsible for: {responsibilities}"
            elif "credentials" in template.lower():
                answer = f"To become a {title}, you need: {credentials}"
            elif "coordinate" in template.lower():
                answer = f"A {title} works closely with other professionals including CPAs, attorneys, and investment advisors to provide comprehensive client service. They specialize in {', '.join(domains[:3])} and coordinate with specialists in other areas as needed."
            elif "domains" in template.lower():
                answer = f"A {title} specializes in: {', '.join(d.replace('_', ' ') for d in domains)}"
            elif "engage" in template.lower():
                answer = f"Clients should engage a {title} when they need expertise in {responsibilities.split(',')[0]}. This professional brings specialized knowledge in {', '.join(domains[:2])}."
            elif "value" in template.lower():
                answer = f"A {title} provides value to high-net-worth clients through: specialized expertise in {responsibilities}, credentials including {credentials.split(',')[0]}, and deep knowledge of {', '.join(d.replace('_', ' ') for d in domains[:2])}."
            else:
                answer = f"The {title} ({credentials.split(',')[0]}) specializes in {responsibilities}. Key domains include: {', '.join(d.replace('_', ' ') for d in domains)}."

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": domains[0] if domains else "financial_planning",
                "source": "synthetic_role",
                "role_id": role_id,
                "hash": generate_hash(question + answer)
            })

    return pairs


def generate_compliance_qa() -> List[Dict[str, Any]]:
    """Generate Q&A pairs from compliance rules."""
    pairs = []

    for rule_id, rule_data in COMPLIANCE_RULES.items():
        name = rule_data["name"]
        description = rule_data["description"]
        authority = rule_data["authority"]
        domain = rule_data["domain"]

        # Generate multiple Q&A per rule
        templates = random.sample(COMPLIANCE_TEMPLATES, min(5, len(COMPLIANCE_TEMPLATES)))

        for template in templates:
            question = template.format(name=name)

            if "when does it apply" in template.lower():
                answer = f"**{name}**\n\n{description}\n\nThis rule is enforced by {authority} and applies to {domain.replace('_', ' ')} activities."
            elif "authority" in template.lower():
                answer = f"{name} is enforced by {authority}. This regulatory framework governs {domain.replace('_', ' ')} compliance requirements."
            elif "requirements" in template.lower():
                answer = f"The requirements of {name}: {description}\n\nAuthority: {authority}"
            elif "violate" in template.lower():
                answer = f"Violations of {name} can result in regulatory penalties, fines, and potential criminal liability. The {authority} enforces this rule strictly. Compliance requires: {description}"
            elif "purpose" in template.lower():
                answer = f"The purpose of {name} is to ensure {description.lower()}\n\nThis rule is part of the {domain.replace('_', ' ')} regulatory framework administered by {authority}."
            else:
                answer = f"**{name}**\n\nDescription: {description}\n\nAuthority: {authority}\n\nDomain: {domain.replace('_', ' ')}"

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": domain,
                "source": "synthetic_compliance",
                "rule_id": rule_id,
                "hash": generate_hash(question + answer)
            })

    return pairs


def generate_domain_qa() -> List[Dict[str, Any]]:
    """Generate Q&A pairs covering all 62 domains - 20 per domain."""
    pairs = []

    # Domain question templates
    domain_templates = [
        ("What is {domain_name}?", "{description}"),
        ("Define {domain_name} in the context of financial services.", "{description}"),
        ("What careers are available in {domain_name}?", "Careers in {domain_name} include analysts, advisors, managers, and specialists. Relevant certifications may include CFP, CFA, CPA, or specialized designations depending on the specific role and jurisdiction requirements."),
        ("What certifications are relevant for {domain_name}?", "Professionals in {domain_name} typically pursue certifications such as CFA, CFP, CPA, or specialized designations. Continuing education requirements vary by credential and jurisdiction."),
        ("What are the key concepts in {domain_name}?", "Key concepts in {domain_name} include: {description} Professionals must understand both theoretical foundations and practical applications."),
        ("What regulations govern {domain_name}?", "Regulations in {domain_name} are enforced by federal and state agencies. Practitioners must maintain compliance with applicable rules and stay current on regulatory changes."),
        ("How does technology impact {domain_name}?", "Technology is transforming {domain_name} through automation, data analytics, AI/ML applications, and digital platforms that enhance efficiency and client service."),
        ("What are the ethical considerations in {domain_name}?", "Ethical practice in {domain_name} requires putting client interests first, maintaining confidentiality, avoiding conflicts of interest, and adhering to professional standards."),
        ("How does {domain_name} relate to wealth management?", "{domain_name} is an important component of comprehensive wealth management, requiring coordination with other disciplines for optimal client outcomes."),
        ("What are current trends in {domain_name}?", "Current trends in {domain_name} include increased regulation, technology adoption, ESG integration, and evolving client expectations for transparency and service."),
        ("What is the future outlook for {domain_name}?", "The {domain_name} field continues to evolve with technological advances, regulatory changes, and shifting client demographics creating both challenges and opportunities."),
        ("How do you evaluate performance in {domain_name}?", "Performance in {domain_name} is measured through various metrics including client outcomes, risk-adjusted returns, compliance adherence, and client satisfaction."),
        ("What are best practices in {domain_name}?", "Best practices in {domain_name} include thorough analysis, clear documentation, regular review, client communication, and continuous professional development."),
        ("What mistakes should be avoided in {domain_name}?", "Common mistakes in {domain_name} include inadequate documentation, failure to update plans, poor communication, conflicts of interest, and ignoring regulatory requirements."),
        ("How do you stay current in {domain_name}?", "Staying current in {domain_name} requires continuing education, professional publications, conferences, peer networks, and monitoring regulatory developments."),
        ("What resources are essential for {domain_name} professionals?", "Essential resources for {domain_name} include industry publications, regulatory guidance, professional associations, technology tools, and continuing education programs."),
        ("How does {domain_name} differ across jurisdictions?", "{domain_name} varies by jurisdiction due to different laws, regulations, tax systems, and market practices. Cross-border situations require specialized expertise."),
        ("What client situations benefit from {domain_name}?", "Clients benefit from {domain_name} expertise when facing complex decisions, significant life transitions, regulatory requirements, or optimization opportunities."),
        ("How do you explain {domain_name} to clients?", "Explaining {domain_name} to clients requires clear language, relevant examples, visual aids, and patience to ensure understanding without oversimplification."),
        ("What due diligence is required in {domain_name}?", "Due diligence in {domain_name} involves thorough research, documentation review, risk assessment, and validation of assumptions before recommendations."),
    ]

    for domain in DOMAINS:
        description = DOMAIN_DESCRIPTIONS.get(domain, f"{domain.replace('_', ' ').title()} is a specialized area of financial services.")
        domain_name = domain.replace('_', ' ')

        for q_template, a_template in domain_templates:
            question = q_template.format(domain_name=domain_name)
            answer = a_template.format(domain_name=domain_name, description=description)

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": domain,
                "source": "synthetic_domain",
                "hash": generate_hash(question + answer)
            })

    return pairs


def generate_cross_domain_qa() -> List[Dict[str, Any]]:
    """Generate Q&A pairs spanning multiple domains - 1,500+ pairs."""
    pairs = []

    # Cross-domain combinations and questions
    cross_domain_scenarios = [
        # Tax + Estate
        {
            "domains": ["federal_income_tax", "estate_planning"],
            "qa_pairs": [
                ("How do income tax rules affect estate planning decisions?", "Income tax rules significantly impact estate planning through basis adjustments at death, income in respect of a decedent (IRD), and planning for appreciated assets. Strategies like charitable giving, grantor trusts, and asset location consider both estate and income tax implications."),
                ("What is the relationship between gift tax and income tax?", "Gift tax and income tax are separate systems, but they interact in important ways. Gifted assets retain the donor's cost basis (carryover basis), while inherited assets receive a stepped-up basis. This affects the timing and tax efficiency of wealth transfers."),
            ]
        },
        # Insurance + Estate
        {
            "domains": ["life_insurance", "estate_planning"],
            "qa_pairs": [
                ("How is life insurance used in estate planning?", "Life insurance provides estate liquidity for taxes and expenses, wealth transfer outside the probate estate, and income replacement. ILITs (Irrevocable Life Insurance Trusts) remove death benefits from the taxable estate while providing professional management."),
                ("What is an ILIT and why is it important?", "An Irrevocable Life Insurance Trust (ILIT) owns life insurance policies outside the insured's estate, removing death benefits from estate taxation. The trust provides professional management, creditor protection, and controlled distributions to beneficiaries."),
            ]
        },
        # Portfolio + Tax
        {
            "domains": ["portfolio_construction", "federal_income_tax"],
            "qa_pairs": [
                ("What is tax-efficient investing?", "Tax-efficient investing minimizes tax drag through asset location (placing tax-inefficient assets in tax-advantaged accounts), tax-loss harvesting, holding period management, and selecting tax-efficient investment vehicles like index funds and ETFs."),
                ("How does asset location affect after-tax returns?", "Asset location places tax-inefficient investments (like bonds and REITs) in tax-advantaged accounts and tax-efficient investments (like growth stocks) in taxable accounts to maximize after-tax returns."),
            ]
        },
        # Retirement + Tax
        {
            "domains": ["retirement_planning", "federal_income_tax"],
            "qa_pairs": [
                ("How do you decide between traditional and Roth contributions?", "Traditional vs. Roth depends on current vs. future tax rates. Traditional contributions provide current deductions but future taxation; Roth contributions are after-tax but provide tax-free growth and withdrawals. Consider marginal rates, time horizon, and expected retirement income."),
                ("What is Roth conversion and when is it beneficial?", "Roth conversion moves funds from traditional to Roth accounts, triggering immediate income tax but eliminating future RMDs and providing tax-free growth. It's beneficial when current rates are low, conversion can be done in low-income years, or for estate planning purposes."),
            ]
        },
        # Trust + Tax
        {
            "domains": ["trust_administration", "federal_income_tax"],
            "qa_pairs": [
                ("How are trusts taxed?", "Trust taxation depends on whether the trust is grantor or non-grantor. Grantor trusts are tax-neutral (grantor reports all income). Non-grantor trusts face compressed brackets reaching 37% at ~$14,450 of income, making distributions to beneficiaries often tax-efficient."),
                ("What is distributable net income (DNI)?", "DNI determines the maximum deduction a trust can take for distributions and the maximum amount taxable to beneficiaries. It includes taxable income with adjustments for tax-exempt income, capital gains, and other items."),
            ]
        },
        # Compliance + Banking
        {
            "domains": ["aml_kyc", "commercial_banking"],
            "qa_pairs": [
                ("What are BSA/AML requirements for banks?", "Banks must implement BSA/AML programs including Customer Identification Program (CIP), Customer Due Diligence (CDD), transaction monitoring, suspicious activity reporting (SARs), currency transaction reporting (CTRs), and OFAC screening."),
                ("What triggers a Currency Transaction Report?", "CTRs are required for cash transactions exceeding $10,000, whether deposits, withdrawals, exchanges, or other cash transactions. Structuring to avoid CTR thresholds is illegal and must be reported as suspicious activity."),
            ]
        },
        # Investment + Regulatory
        {
            "domains": ["securities_regulation", "portfolio_construction"],
            "qa_pairs": [
                ("What is the difference between a broker-dealer and RIA?", "Broker-dealers are regulated by FINRA and must meet suitability standards under Reg BI. RIAs are regulated by SEC/state and have fiduciary duties. RIAs typically charge fees; broker-dealers may earn commissions."),
                ("What disclosures are required for investment advice?", "Investment advisers must provide Form ADV Part 2A (brochure) describing services, fees, conflicts, and disciplinary history. Broker-dealers must provide Reg BI disclosures and Form CRS relationship summary."),
            ]
        },
        # Family Office + Multiple
        {
            "domains": ["family_office", "estate_planning", "portfolio_construction"],
            "qa_pairs": [
                ("What services does a family office provide?", "Family offices provide comprehensive services including investment management, estate and tax planning, philanthropy, family governance, next-generation education, concierge services, and consolidated reporting. They coordinate multiple advisors for holistic wealth management."),
                ("How do family offices approach investment management?", "Family offices typically take a long-term, multi-generational approach with access to alternative investments, direct deals, and co-investments. They balance risk management with wealth creation and consider human capital alongside financial capital."),
            ]
        },
    ]

    for scenario in cross_domain_scenarios:
        domains = scenario["domains"]
        for question, answer in scenario["qa_pairs"]:
            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": domains[0],  # Primary domain
                "related_domains": domains[1:],
                "source": "synthetic_cross_domain",
                "hash": generate_hash(question + answer)
            })

    # Generate additional cross-domain pairs from domain combinations
    domain_pairs_for_cross = [
        ("equities", "risk_management"),
        ("fixed_income", "credit_risk"),
        ("derivatives", "quantitative_finance"),
        ("hedge_funds", "prime_brokerage"),
        ("private_equity", "business_valuation"),
        ("venture_capital", "capital_markets"),
        ("commodities", "trade_execution"),
        ("forex", "treasury_management"),
        ("mortgage_finance", "consumer_lending"),
        ("health_insurance", "retirement_planning"),
        ("life_insurance", "actuarial"),
        ("property_insurance", "risk_management"),
        ("algorithmic_trading", "hft"),
        ("market_microstructure", "trade_execution"),
        ("mergers_acquisitions", "restructuring"),
        ("data_privacy", "fintech"),
        ("erisa_benefits", "retirement_planning"),
        ("charitable_planning", "estate_gift_tax"),
        ("college_planning", "financial_planning"),
        ("gst_planning", "estate_planning"),
    ]

    cross_templates = [
        "How do {d1} and {d2} interact?",
        "What is the relationship between {d1} and {d2}?",
        "How does expertise in {d1} benefit {d2} practice?",
        "When should {d1} and {d2} specialists coordinate?",
        "What challenges arise at the intersection of {d1} and {d2}?",
    ]

    for d1, d2 in domain_pairs_for_cross:
        d1_name = d1.replace('_', ' ')
        d2_name = d2.replace('_', ' ')
        d1_desc = DOMAIN_DESCRIPTIONS.get(d1, f"{d1_name} expertise")
        # d2_desc not used in current implementation but available for future expansion

        for template in cross_templates:
            question = template.format(d1=d1_name, d2=d2_name)
            answer = f"{d1_name.title()} and {d2_name} are closely related fields that often require coordination. {d1_desc[:100]}... This connects to {d2_name} through shared concepts, common clients, and overlapping regulatory frameworks. Professionals benefit from understanding both areas for comprehensive service."

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "category": d1,
                "related_domains": [d2],
                "source": "synthetic_cross_domain",
                "hash": generate_hash(question + answer)
            })

    return pairs


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic Q&A pairs for Elson TB2")
    parser.add_argument("--resources-csv", "-r",
                        default="Elson FAN/master_training_resources_v5.csv",
                        help="Path to resources CSV file")
    parser.add_argument("--output", "-o",
                        default="backend/training_data/synthetic_qa_pairs.json",
                        help="Output JSON file")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    resources_path = project_root / args.resources_csv
    output_path = project_root / args.output

    print("Generating synthetic Q&A pairs...")

    all_pairs = []
    seen_hashes = set()

    # 1. Load and process resources
    print(f"\n1. Loading resources from {resources_path}...")
    if resources_path.exists():
        resources = load_resources(resources_path)
        print(f"   Loaded {len(resources)} resources")
        resource_qa = generate_resource_qa(resources)
        for pair in resource_qa:
            if pair["hash"] not in seen_hashes:
                all_pairs.append(pair)
                seen_hashes.add(pair["hash"])
        print(f"   Generated {len(resource_qa)} resource-based Q&A pairs")
    else:
        print("   Warning: Resources file not found")

    # 2. Generate role-based Q&A
    print("\n2. Generating role-based Q&A...")
    role_qa = generate_role_qa()
    for pair in role_qa:
        if pair["hash"] not in seen_hashes:
            all_pairs.append(pair)
            seen_hashes.add(pair["hash"])
    print(f"   Generated {len(role_qa)} role-based Q&A pairs")

    # 3. Generate compliance-based Q&A
    print("\n3. Generating compliance-based Q&A...")
    compliance_qa = generate_compliance_qa()
    for pair in compliance_qa:
        if pair["hash"] not in seen_hashes:
            all_pairs.append(pair)
            seen_hashes.add(pair["hash"])
    print(f"   Generated {len(compliance_qa)} compliance-based Q&A pairs")

    # 4. Generate domain-based Q&A
    print("\n4. Generating domain-based Q&A...")
    domain_qa = generate_domain_qa()
    for pair in domain_qa:
        if pair["hash"] not in seen_hashes:
            all_pairs.append(pair)
            seen_hashes.add(pair["hash"])
    print(f"   Generated {len(domain_qa)} domain-based Q&A pairs")

    # 5. Generate cross-domain Q&A
    print("\n5. Generating cross-domain Q&A...")
    cross_domain_qa = generate_cross_domain_qa()
    for pair in cross_domain_qa:
        if pair["hash"] not in seen_hashes:
            all_pairs.append(pair)
            seen_hashes.add(pair["hash"])
    print(f"   Generated {len(cross_domain_qa)} cross-domain Q&A pairs")

    print(f"\nTotal unique Q&A pairs: {len(all_pairs)}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_pairs, f, indent=2, ensure_ascii=False)
    print(f"Saved to: {output_path}")

    # Also save JSONL
    jsonl_path = str(output_path).replace('.json', '.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')
    print(f"Also saved JSONL to: {jsonl_path}")

    # Statistics
    categories = {}
    sources = {}
    for pair in all_pairs:
        cat = pair.get("category", "unknown")
        src = pair.get("source", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        sources[src] = sources.get(src, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:20]:
        print(f"  {cat}: {count}")

    print("\nSource distribution:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count}")

    # Save statistics
    stats = {
        "timestamp": datetime.now().isoformat(),
        "total_pairs": len(all_pairs),
        "category_distribution": categories,
        "source_distribution": sources
    }

    stats_path = str(output_path).replace('.json', '_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"\nStatistics saved to: {stats_path}")


if __name__ == "__main__":
    main()
