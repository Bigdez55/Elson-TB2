"""
Accounting Workflow Schemas for Elson Financial AI

These schemas define structured outputs for personal and small business
accounting workflows, budgeting, and financial management.

WARNING: These tools assist with financial organization and education.
They do not replace professional accountants or constitute tax advice.
The AI should NOT perform actual tax calculations or filing instructions.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .base import BaseSchema

# =============================================================================
# ENUMS
# =============================================================================


class AccountTypeEnum(str, Enum):
    """Standard chart of accounts types"""

    # Assets
    ASSET_CASH = "asset_cash"
    ASSET_CHECKING = "asset_checking"
    ASSET_SAVINGS = "asset_savings"
    ASSET_INVESTMENT = "asset_investment"
    ASSET_RECEIVABLE = "asset_receivable"
    ASSET_INVENTORY = "asset_inventory"
    ASSET_PREPAID = "asset_prepaid"
    ASSET_FIXED = "asset_fixed"
    ASSET_OTHER = "asset_other"

    # Liabilities
    LIABILITY_CREDIT_CARD = "liability_credit_card"
    LIABILITY_PAYABLE = "liability_payable"
    LIABILITY_LOAN = "liability_loan"
    LIABILITY_MORTGAGE = "liability_mortgage"
    LIABILITY_OTHER = "liability_other"

    # Equity
    EQUITY_OPENING = "equity_opening"
    EQUITY_RETAINED = "equity_retained"
    EQUITY_OWNER = "equity_owner"

    # Income
    INCOME_SALARY = "income_salary"
    INCOME_BUSINESS = "income_business"
    INCOME_INVESTMENT = "income_investment"
    INCOME_RENTAL = "income_rental"
    INCOME_OTHER = "income_other"

    # Expenses
    EXPENSE_HOUSING = "expense_housing"
    EXPENSE_TRANSPORTATION = "expense_transportation"
    EXPENSE_FOOD = "expense_food"
    EXPENSE_UTILITIES = "expense_utilities"
    EXPENSE_INSURANCE = "expense_insurance"
    EXPENSE_HEALTHCARE = "expense_healthcare"
    EXPENSE_DEBT_PAYMENT = "expense_debt_payment"
    EXPENSE_ENTERTAINMENT = "expense_entertainment"
    EXPENSE_SHOPPING = "expense_shopping"
    EXPENSE_PERSONAL = "expense_personal"
    EXPENSE_EDUCATION = "expense_education"
    EXPENSE_BUSINESS = "expense_business"
    EXPENSE_TAX = "expense_tax"
    EXPENSE_OTHER = "expense_other"


class TransactionStatusEnum(str, Enum):
    """Transaction reconciliation status"""

    PENDING = "pending"
    CLEARED = "cleared"
    RECONCILED = "reconciled"
    VOID = "void"


class BudgetCategoryEnum(str, Enum):
    """Budget category types"""

    NEEDS = "needs"  # 50% rule
    WANTS = "wants"  # 30% rule
    SAVINGS = "savings"  # 20% rule
    DEBT = "debt"
    BUSINESS = "business"


class FrequencyEnum(str, Enum):
    """Recurring transaction frequency"""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"


# =============================================================================
# SCHEMA 1: LEDGER IMPORT / TRANSACTION CATEGORIZATION
# =============================================================================


class Transaction(BaseSchema):
    """Single financial transaction"""

    transaction_id: str
    date: date
    description: str
    amount: Decimal  # Positive for income, negative for expenses
    account: str
    category: Optional[str] = None
    suggested_category: Optional[AccountTypeEnum] = None
    confidence: Optional[Decimal] = None  # Categorization confidence 0-1
    status: TransactionStatusEnum = TransactionStatusEnum.PENDING
    memo: Optional[str] = None
    payee: Optional[str] = None
    check_number: Optional[str] = None
    tags: List[str] = []


class CategorySuggestion(BaseSchema):
    """AI-suggested category for a transaction"""

    transaction_id: str
    original_description: str
    suggested_category: AccountTypeEnum
    confidence: Decimal
    reasoning: str
    alternative_categories: List[AccountTypeEnum] = []


class LedgerImport(BaseSchema):
    """
    Schema 1: Ledger Import and Transaction Categorization

    Used for: Importing and categorizing bank/credit card transactions
    Compliance: Educational; not for tax filing
    """

    # Metadata
    import_id: str
    created_at: datetime
    source: str  # e.g., "bank_csv", "gnucash", "manual"
    account_name: str
    period_start: date
    period_end: date

    # Transactions
    transactions: List[Transaction]
    total_transactions: int

    # Summary
    total_income: Decimal
    total_expenses: Decimal
    net_change: Decimal

    # Categorization
    categorized_count: int
    uncategorized_count: int
    category_suggestions: List[CategorySuggestion]

    # Category breakdown
    income_by_category: Dict[str, Decimal]
    expenses_by_category: Dict[str, Decimal]

    # Anomalies detected
    unusual_transactions: List[str]  # Transaction IDs
    duplicate_warnings: List[str]

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "Transaction categorization is for organizational purposes only.",
            "Verify all categories before using for tax or business purposes.",
            "This does not constitute accounting advice.",
        ]
    )


# =============================================================================
# SCHEMA 2: MONTHLY CLOSE CHECKLIST
# =============================================================================


class CloseCheckItem(BaseSchema):
    """Single item in monthly close checklist"""

    item_id: str
    category: str
    task: str
    status: Literal["not_started", "in_progress", "completed", "not_applicable"]
    due_date: Optional[date] = None
    notes: Optional[str] = None
    responsible: Optional[str] = None


class AccountBalance(BaseSchema):
    """Account balance for reconciliation"""

    account_name: str
    account_type: AccountTypeEnum
    book_balance: Decimal
    statement_balance: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    reconciled: bool = False
    last_reconciled_date: Optional[date] = None


class MonthlyCloseChecklist(BaseSchema):
    """
    Schema 2: Monthly Close Checklist

    Used for: Guiding through month-end financial close process
    Compliance: Educational; standard accounting practices
    """

    # Metadata
    checklist_id: str
    period: str  # e.g., "2026-01"
    created_at: datetime
    status: Literal["not_started", "in_progress", "completed"]

    # Account reconciliation
    accounts_to_reconcile: List[AccountBalance]
    accounts_reconciled: int
    accounts_pending: int
    total_discrepancy: Decimal

    # Checklist items
    checklist_items: List[CloseCheckItem]
    items_completed: int
    items_pending: int

    # Standard monthly tasks
    bank_reconciliation_complete: bool
    credit_card_reconciliation_complete: bool
    receivables_reviewed: bool
    payables_reviewed: bool
    recurring_transactions_posted: bool
    budget_variance_reviewed: bool

    # Financial summary
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
    savings_rate: Decimal

    # Issues found
    issues: List[str]
    action_items: List[str]

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "This checklist is for personal financial organization.",
            "Business accounting may require additional procedures.",
            "Consult a CPA for professional accounting needs.",
        ]
    )


# =============================================================================
# SCHEMA 3: CASH FLOW FORECAST
# =============================================================================


class CashFlowItem(BaseSchema):
    """Single cash flow item (income or expense)"""

    item_id: str
    description: str
    amount: Decimal
    frequency: FrequencyEnum
    category: AccountTypeEnum
    is_fixed: bool  # Fixed vs variable
    confidence: Literal["certain", "likely", "possible", "uncertain"]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class CashFlowPeriod(BaseSchema):
    """Cash flow for a single period (week/month)"""

    period_start: date
    period_end: date
    beginning_balance: Decimal
    projected_income: Decimal
    projected_expenses: Decimal
    net_cash_flow: Decimal
    ending_balance: Decimal
    minimum_balance: Decimal  # Lowest point during period


class CashFlowForecast(BaseSchema):
    """
    Schema 3: Cash Flow Forecast

    Used for: Projecting future cash position
    Compliance: Educational projections only
    """

    # Metadata
    forecast_id: str
    created_at: datetime
    forecast_period: Literal["weekly", "monthly", "quarterly"]
    periods_ahead: int

    # Current position
    current_cash_balance: Decimal
    as_of_date: date

    # Income sources
    income_items: List[CashFlowItem]
    total_monthly_income: Decimal

    # Expense items
    expense_items: List[CashFlowItem]
    total_monthly_expenses: Decimal
    fixed_expenses: Decimal
    variable_expenses: Decimal

    # Projections
    projections: List[CashFlowPeriod]

    # Key metrics
    monthly_surplus_deficit: Decimal
    months_of_runway: Optional[Decimal] = None  # At current burn rate
    projected_low_point: Decimal
    projected_low_point_date: date

    # Alerts
    negative_balance_periods: List[str]  # Period descriptions
    tight_periods: List[str]  # Balance < threshold

    # Sensitivity
    if_income_drops_10_pct: Decimal  # Ending balance
    if_expenses_rise_10_pct: Decimal

    # Recommendations (educational)
    recommendations: List[str]

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "Cash flow projections are estimates based on provided inputs.",
            "Actual results will vary from projections.",
            "Review and update regularly as circumstances change.",
            "This is not financial advice.",
        ]
    )


# =============================================================================
# SCHEMA 4: BUDGET PLAN
# =============================================================================


class BudgetLineItem(BaseSchema):
    """Single budget line item"""

    line_id: str
    category: str
    subcategory: Optional[str] = None
    budget_type: BudgetCategoryEnum
    budgeted_amount: Decimal
    actual_amount: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    variance_percent: Optional[Decimal] = None
    frequency: FrequencyEnum = FrequencyEnum.MONTHLY
    is_essential: bool = False
    notes: Optional[str] = None


class BudgetSummary(BaseSchema):
    """Budget summary by category type"""

    category_type: BudgetCategoryEnum
    budgeted: Decimal
    actual: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    percent_of_income: Decimal
    target_percent: Decimal  # e.g., 50% for needs


class BudgetPlan(BaseSchema):
    """
    Schema 4: Budget Plan (50/30/20 or Custom)

    Used for: Creating and tracking budgets
    Compliance: Educational; personal finance guidance
    """

    # Metadata
    budget_id: str
    name: str
    created_at: datetime
    period: str  # e.g., "2026-01" or "2026"
    budget_method: Literal["50_30_20", "zero_based", "envelope", "custom"]

    # Income
    total_monthly_income: Decimal
    income_sources: List[BudgetLineItem]

    # Expense categories
    needs: List[BudgetLineItem]  # Housing, utilities, food, insurance, etc.
    wants: List[BudgetLineItem]  # Entertainment, dining out, subscriptions
    savings_debt: List[BudgetLineItem]  # Savings, investments, debt payoff

    # Summary
    category_summaries: List[BudgetSummary]

    # Totals
    total_budgeted_expenses: Decimal
    total_budgeted_savings: Decimal
    budgeted_surplus_deficit: Decimal

    # Tracking (if actual data available)
    total_actual_expenses: Optional[Decimal] = None
    total_actual_savings: Optional[Decimal] = None
    actual_surplus_deficit: Optional[Decimal] = None

    # 50/30/20 analysis
    needs_percent: Decimal
    wants_percent: Decimal
    savings_percent: Decimal
    meets_50_30_20: bool

    # Goals alignment
    financial_goals: List[str]
    goals_funded: List[str]
    goals_underfunded: List[str]

    # Recommendations
    areas_to_reduce: List[str]
    areas_on_track: List[str]
    optimization_suggestions: List[str]

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "Budget plans are for personal financial organization.",
            "Adjust categories and amounts to fit your situation.",
            "This does not constitute financial advice.",
        ]
    )


# =============================================================================
# SCHEMA 5: BUSINESS KPIs
# =============================================================================


class KPIMetric(BaseSchema):
    """Single KPI metric"""

    metric_name: str
    current_value: Decimal
    previous_value: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    target: Optional[Decimal] = None
    status: Literal["on_track", "warning", "off_track", "no_target"]
    unit: str  # e.g., "$", "%", "days", "ratio"
    calculation: str  # Formula explanation


class BusinessKPIs(BaseSchema):
    """
    Schema 5: Small Business KPIs

    Used for: Tracking key performance indicators for small businesses
    Compliance: Educational; not professional accounting
    """

    # Metadata
    report_id: str
    business_name: str
    period: str
    created_at: datetime
    period_start: date
    period_end: date

    # Revenue metrics
    total_revenue: Decimal
    revenue_growth: Optional[Decimal] = None
    average_transaction_value: Optional[Decimal] = None
    revenue_per_customer: Optional[Decimal] = None

    # Profitability
    gross_profit: Decimal
    gross_margin: Decimal
    operating_profit: Decimal
    operating_margin: Decimal
    net_profit: Decimal
    net_margin: Decimal

    # Liquidity
    current_ratio: Optional[Decimal] = None
    quick_ratio: Optional[Decimal] = None
    cash_on_hand: Decimal
    days_cash_on_hand: Optional[Decimal] = None

    # Efficiency
    accounts_receivable_days: Optional[Decimal] = None
    accounts_payable_days: Optional[Decimal] = None
    inventory_turnover: Optional[Decimal] = None

    # All KPIs with details
    kpis: List[KPIMetric]

    # Health assessment
    overall_health: Literal["healthy", "stable", "concerning", "critical"]
    strengths: List[str]
    weaknesses: List[str]
    action_items: List[str]

    # Benchmarks
    industry: Optional[str] = None
    benchmark_comparisons: Dict[str, Dict[str, Decimal]] = (
        {}
    )  # metric -> {yours, industry_avg}

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "KPIs are calculated from provided data and may not reflect complete picture.",
            "Industry benchmarks are general estimates.",
            "Consult a CPA or financial advisor for business financial decisions.",
            "This does not constitute accounting or tax advice.",
        ]
    )


# =============================================================================
# GNUCASH IMPORT SCHEMAS
# =============================================================================


class GnuCashAccount(BaseSchema):
    """GnuCash account representation"""

    account_id: str
    name: str
    full_name: str  # Including parent hierarchy
    account_type: str  # GnuCash type
    mapped_type: Optional[AccountTypeEnum] = None
    currency: str = "USD"
    balance: Decimal
    parent_id: Optional[str] = None
    children: List[str] = []


class GnuCashImportResult(BaseSchema):
    """Result of GnuCash file import"""

    import_id: str
    file_path: str
    file_type: Literal["xml", "sqlite"]
    imported_at: datetime

    # Accounts
    accounts: List[GnuCashAccount]
    account_count: int

    # Transactions
    transaction_count: int
    date_range_start: date
    date_range_end: date

    # Balances
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    total_income_ytd: Decimal
    total_expenses_ytd: Decimal

    # Mapping status
    accounts_mapped: int
    accounts_unmapped: int
    mapping_suggestions: Dict[str, AccountTypeEnum]

    # Warnings
    warnings: List[str]

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "Data imported from GnuCash file as-is.",
            "Verify account mappings before generating reports.",
            "Some GnuCash features may not be fully supported.",
        ]
    )
