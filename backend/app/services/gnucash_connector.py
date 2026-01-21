"""
GnuCash Connector for Elson Financial AI

Reads GnuCash files (XML or SQLite format) and extracts:
- Chart of accounts
- Account balances
- Transactions
- Budget data

This is READ-ONLY - we never modify GnuCash files.
"""

import gzip
import logging
import sqlite3
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class GnuCashAccount:
    """Represents a GnuCash account"""

    guid: str
    name: str
    account_type: str
    commodity: str = "USD"
    parent_guid: Optional[str] = None
    description: str = ""
    balance: Decimal = Decimal("0")
    full_path: str = ""
    children: List[str] = field(default_factory=list)


@dataclass
class GnuCashTransaction:
    """Represents a GnuCash transaction"""

    guid: str
    date_posted: date
    description: str
    splits: List[Dict] = field(default_factory=list)
    num: str = ""  # Check number
    notes: str = ""


@dataclass
class GnuCashSplit:
    """Represents a split within a transaction"""

    guid: str
    account_guid: str
    value: Decimal
    memo: str = ""
    reconciled_state: str = "n"


# =============================================================================
# GNUCASH TYPE MAPPING
# =============================================================================

# Map GnuCash account types to our standard types
GNUCASH_TYPE_MAPPING = {
    # Assets
    "ASSET": "asset_other",
    "BANK": "asset_checking",
    "CASH": "asset_cash",
    "CHECKING": "asset_checking",
    "SAVINGS": "asset_savings",
    "MONEYMRKT": "asset_savings",
    "STOCK": "asset_investment",
    "MUTUAL": "asset_investment",
    "RECEIVABLE": "asset_receivable",
    "INVESTMENT": "asset_investment",
    # Liabilities
    "LIABILITY": "liability_other",
    "CREDIT": "liability_credit_card",
    "CREDITLINE": "liability_credit_card",
    "PAYABLE": "liability_payable",
    # Equity
    "EQUITY": "equity_owner",
    # Income
    "INCOME": "income_other",
    # Expenses
    "EXPENSE": "expense_other",
    # Special
    "ROOT": None,
    "TRADING": None,
}


# =============================================================================
# XML PARSER
# =============================================================================


class GnuCashXMLParser:
    """Parse GnuCash XML files (compressed or uncompressed)"""

    # GnuCash XML namespaces
    NAMESPACES = {
        "gnc": "http://www.gnucash.org/XML/gnc",
        "act": "http://www.gnucash.org/XML/act",
        "book": "http://www.gnucash.org/XML/book",
        "cd": "http://www.gnucash.org/XML/cd",
        "cmdty": "http://www.gnucash.org/XML/cmdty",
        "price": "http://www.gnucash.org/XML/price",
        "slot": "http://www.gnucash.org/XML/slot",
        "split": "http://www.gnucash.org/XML/split",
        "sx": "http://www.gnucash.org/XML/sx",
        "trn": "http://www.gnucash.org/XML/trn",
        "ts": "http://www.gnucash.org/XML/ts",
        "fs": "http://www.gnucash.org/XML/fs",
        "bgt": "http://www.gnucash.org/XML/bgt",
        "recurrence": "http://www.gnucash.org/XML/recurrence",
        "lot": "http://www.gnucash.org/XML/lot",
        "cust": "http://www.gnucash.org/XML/cust",
        "job": "http://www.gnucash.org/XML/job",
        "addr": "http://www.gnucash.org/XML/addr",
        "owner": "http://www.gnucash.org/XML/owner",
        "taxtable": "http://www.gnucash.org/XML/taxtable",
        "tte": "http://www.gnucash.org/XML/tte",
        "employee": "http://www.gnucash.org/XML/employee",
        "order": "http://www.gnucash.org/XML/order",
        "billterm": "http://www.gnucash.org/XML/billterm",
        "bt-days": "http://www.gnucash.org/XML/bt-days",
        "bt-prox": "http://www.gnucash.org/XML/bt-prox",
        "invoice": "http://www.gnucash.org/XML/invoice",
        "entry": "http://www.gnucash.org/XML/entry",
        "vendor": "http://www.gnucash.org/XML/vendor",
    }

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.accounts: Dict[str, GnuCashAccount] = {}
        self.transactions: List[GnuCashTransaction] = []
        self.root = None

    def parse(self) -> Tuple[Dict[str, GnuCashAccount], List[GnuCashTransaction]]:
        """Parse the GnuCash file and return accounts and transactions"""
        try:
            # Try to open as gzipped file first
            if self.file_path.suffix == ".gnucash" or self._is_gzipped():
                with gzip.open(self.file_path, "rt", encoding="utf-8") as f:
                    content = f.read()
            else:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            # Register namespaces
            for prefix, uri in self.NAMESPACES.items():
                ET.register_namespace(prefix, uri)

            self.root = ET.fromstring(content)
            self._parse_accounts()
            self._parse_transactions()
            self._calculate_balances()
            self._build_full_paths()

            return self.accounts, self.transactions

        except gzip.BadGzipFile:
            # Try as plain XML
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.root = ET.fromstring(content)
            self._parse_accounts()
            self._parse_transactions()
            self._calculate_balances()
            self._build_full_paths()
            return self.accounts, self.transactions

        except Exception as e:
            logger.error(f"Failed to parse GnuCash XML: {e}")
            raise

    def _is_gzipped(self) -> bool:
        """Check if file is gzipped"""
        try:
            with open(self.file_path, "rb") as f:
                return f.read(2) == b"\x1f\x8b"
        except Exception:
            return False

    def _parse_accounts(self):
        """Parse all accounts from XML"""
        # Find all account elements
        for account_elem in self.root.iter("{http://www.gnucash.org/XML/gnc}account"):
            try:
                guid = self._get_text(account_elem, "act:id")
                name = self._get_text(account_elem, "act:name")
                account_type = self._get_text(account_elem, "act:type")
                parent_elem = account_elem.find("act:parent", self.NAMESPACES)
                parent_guid = parent_elem.text if parent_elem is not None else None

                # Get commodity (currency)
                cmdty_elem = account_elem.find("act:commodity", self.NAMESPACES)
                commodity = "USD"
                if cmdty_elem is not None:
                    space = self._get_text(cmdty_elem, "cmdty:space")
                    cid = self._get_text(cmdty_elem, "cmdty:id")
                    if space == "CURRENCY":
                        commodity = cid or "USD"

                description = self._get_text(account_elem, "act:description") or ""

                account = GnuCashAccount(
                    guid=guid,
                    name=name,
                    account_type=account_type,
                    commodity=commodity,
                    parent_guid=parent_guid,
                    description=description,
                )

                self.accounts[guid] = account

                # Track children
                if parent_guid and parent_guid in self.accounts:
                    self.accounts[parent_guid].children.append(guid)

            except Exception as e:
                logger.warning(f"Failed to parse account: {e}")
                continue

    def _parse_transactions(self):
        """Parse all transactions from XML"""
        for trn_elem in self.root.iter("{http://www.gnucash.org/XML/gnc}transaction"):
            try:
                guid = self._get_text(trn_elem, "trn:id")
                description = self._get_text(trn_elem, "trn:description") or ""
                num = self._get_text(trn_elem, "trn:num") or ""

                # Parse date
                date_elem = trn_elem.find("trn:date-posted", self.NAMESPACES)
                date_posted = date.today()
                if date_elem is not None:
                    ts_date = self._get_text(date_elem, "ts:date")
                    if ts_date:
                        date_posted = datetime.fromisoformat(ts_date.split()[0]).date()

                # Parse splits
                splits = []
                splits_elem = trn_elem.find("trn:splits", self.NAMESPACES)
                if splits_elem is not None:
                    for split_elem in splits_elem.findall("trn:split", self.NAMESPACES):
                        split_data = self._parse_split(split_elem)
                        if split_data:
                            splits.append(split_data)

                transaction = GnuCashTransaction(
                    guid=guid,
                    date_posted=date_posted,
                    description=description,
                    splits=splits,
                    num=num,
                )

                self.transactions.append(transaction)

            except Exception as e:
                logger.warning(f"Failed to parse transaction: {e}")
                continue

    def _parse_split(self, split_elem) -> Optional[Dict]:
        """Parse a transaction split"""
        try:
            split_guid = self._get_text(split_elem, "split:id")
            account_guid = self._get_text(split_elem, "split:account")
            value_str = self._get_text(split_elem, "split:value") or "0/1"
            memo = self._get_text(split_elem, "split:memo") or ""
            reconciled = self._get_text(split_elem, "split:reconciled-state") or "n"

            # Parse fractional value (e.g., "10000/100" = 100.00)
            if "/" in value_str:
                num, denom = value_str.split("/")
                value = Decimal(num) / Decimal(denom)
            else:
                value = Decimal(value_str)

            return {
                "guid": split_guid,
                "account_guid": account_guid,
                "value": value,
                "memo": memo,
                "reconciled_state": reconciled,
            }

        except Exception as e:
            logger.warning(f"Failed to parse split: {e}")
            return None

    def _get_text(self, elem, tag: str) -> Optional[str]:
        """Get text content of a child element"""
        child = elem.find(tag, self.NAMESPACES)
        return child.text if child is not None else None

    def _calculate_balances(self):
        """Calculate account balances from transactions"""
        for trn in self.transactions:
            for split in trn.splits:
                account_guid = split.get("account_guid")
                value = split.get("value", Decimal("0"))
                if account_guid in self.accounts:
                    self.accounts[account_guid].balance += value

    def _build_full_paths(self):
        """Build full account paths (e.g., 'Assets:Bank:Checking')"""
        for guid, account in self.accounts.items():
            path_parts = [account.name]
            parent_guid = account.parent_guid

            while parent_guid and parent_guid in self.accounts:
                parent = self.accounts[parent_guid]
                if parent.account_type == "ROOT":
                    break
                path_parts.insert(0, parent.name)
                parent_guid = parent.parent_guid

            account.full_path = ":".join(path_parts)


# =============================================================================
# SQLITE PARSER
# =============================================================================


class GnuCashSQLiteParser:
    """Parse GnuCash SQLite database files"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.accounts: Dict[str, GnuCashAccount] = {}
        self.transactions: List[GnuCashTransaction] = []

    def parse(self) -> Tuple[Dict[str, GnuCashAccount], List[GnuCashTransaction]]:
        """Parse the GnuCash SQLite database"""
        try:
            conn = sqlite3.connect(str(self.file_path))
            conn.row_factory = sqlite3.Row

            self._parse_accounts(conn)
            self._parse_transactions(conn)
            self._build_full_paths()

            conn.close()

            return self.accounts, self.transactions

        except Exception as e:
            logger.error(f"Failed to parse GnuCash SQLite: {e}")
            raise

    def _parse_accounts(self, conn: sqlite3.Connection):
        """Parse accounts from SQLite database"""
        cursor = conn.execute(
            """
            SELECT
                a.guid,
                a.name,
                a.account_type,
                a.parent_guid,
                a.description,
                c.mnemonic as currency
            FROM accounts a
            LEFT JOIN commodities c ON a.commodity_guid = c.guid
        """
        )

        for row in cursor:
            account = GnuCashAccount(
                guid=row["guid"],
                name=row["name"],
                account_type=row["account_type"],
                parent_guid=row["parent_guid"],
                description=row["description"] or "",
                commodity=row["currency"] or "USD",
            )
            self.accounts[account.guid] = account

        # Calculate balances
        cursor = conn.execute(
            """
            SELECT
                s.account_guid,
                SUM(CAST(s.value_num AS REAL) / s.value_denom) as balance
            FROM splits s
            GROUP BY s.account_guid
        """
        )

        for row in cursor:
            account_guid = row["account_guid"]
            if account_guid in self.accounts:
                try:
                    self.accounts[account_guid].balance = Decimal(
                        str(row["balance"] or 0)
                    )
                except InvalidOperation:
                    self.accounts[account_guid].balance = Decimal("0")

    def _parse_transactions(self, conn: sqlite3.Connection):
        """Parse transactions from SQLite database"""
        cursor = conn.execute(
            """
            SELECT
                t.guid,
                t.post_date,
                t.description,
                t.num
            FROM transactions t
            ORDER BY t.post_date DESC
            LIMIT 10000
        """
        )

        for row in cursor:
            # Parse date
            date_str = row["post_date"]
            if date_str:
                try:
                    # GnuCash stores dates as "YYYYMMDDHHMMSS"
                    date_posted = datetime.strptime(date_str[:8], "%Y%m%d").date()
                except ValueError:
                    date_posted = date.today()
            else:
                date_posted = date.today()

            # Get splits for this transaction
            split_cursor = conn.execute(
                """
                SELECT
                    s.guid,
                    s.account_guid,
                    CAST(s.value_num AS REAL) / s.value_denom as value,
                    s.memo,
                    s.reconcile_state
                FROM splits s
                WHERE s.tx_guid = ?
            """,
                (row["guid"],),
            )

            splits = []
            for split_row in split_cursor:
                splits.append(
                    {
                        "guid": split_row["guid"],
                        "account_guid": split_row["account_guid"],
                        "value": Decimal(str(split_row["value"] or 0)),
                        "memo": split_row["memo"] or "",
                        "reconciled_state": split_row["reconcile_state"] or "n",
                    }
                )

            transaction = GnuCashTransaction(
                guid=row["guid"],
                date_posted=date_posted,
                description=row["description"] or "",
                splits=splits,
                num=row["num"] or "",
            )

            self.transactions.append(transaction)

    def _build_full_paths(self):
        """Build full account paths"""
        for guid, account in self.accounts.items():
            path_parts = [account.name]
            parent_guid = account.parent_guid

            while parent_guid and parent_guid in self.accounts:
                parent = self.accounts[parent_guid]
                if parent.account_type == "ROOT":
                    break
                path_parts.insert(0, parent.name)
                parent_guid = parent.parent_guid

            account.full_path = ":".join(path_parts)


# =============================================================================
# MAIN CONNECTOR CLASS
# =============================================================================


class GnuCashConnector:
    """
    Main connector class for reading GnuCash files.

    Supports both XML (.gnucash) and SQLite (.gnucash) formats.
    This is READ-ONLY - we never modify the source files.
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.accounts: Dict[str, GnuCashAccount] = {}
        self.transactions: List[GnuCashTransaction] = []
        self.file_type: str = "unknown"

    def load(self) -> Dict:
        """
        Load and parse the GnuCash file.

        Returns a summary dictionary.
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"GnuCash file not found: {self.file_path}")

        # Determine file type
        self.file_type = self._detect_file_type()

        # Parse based on type
        if self.file_type == "xml":
            parser = GnuCashXMLParser(str(self.file_path))
        elif self.file_type == "sqlite":
            parser = GnuCashSQLiteParser(str(self.file_path))
        else:
            raise ValueError(f"Unknown GnuCash file type: {self.file_type}")

        self.accounts, self.transactions = parser.parse()

        return self.get_summary()

    def _detect_file_type(self) -> str:
        """Detect whether file is XML or SQLite"""
        try:
            # Check for SQLite magic bytes
            with open(self.file_path, "rb") as f:
                header = f.read(16)
                if header[:6] == b"SQLite":
                    return "sqlite"
                elif header[:2] == b"\x1f\x8b":  # gzip
                    return "xml"
                elif header[:5] == b"<?xml":
                    return "xml"

            # Try to open as gzip
            try:
                with gzip.open(self.file_path, "rt") as f:
                    first_line = f.readline()
                    if "<?xml" in first_line:
                        return "xml"
            except gzip.BadGzipFile:
                pass

            # Default to XML for .gnucash extension
            if self.file_path.suffix == ".gnucash":
                return "xml"

            return "unknown"

        except Exception as e:
            logger.warning(f"Could not detect file type: {e}")
            return "unknown"

    def get_summary(self) -> Dict:
        """Get summary of loaded data"""
        # Calculate totals
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        total_income = Decimal("0")
        total_expenses = Decimal("0")

        for account in self.accounts.values():
            atype = account.account_type.upper()
            if atype in [
                "ASSET",
                "BANK",
                "CASH",
                "CHECKING",
                "SAVINGS",
                "STOCK",
                "MUTUAL",
            ]:
                total_assets += account.balance
            elif atype in ["LIABILITY", "CREDIT", "CREDITLINE", "PAYABLE"]:
                total_liabilities += abs(account.balance)
            elif atype == "INCOME":
                total_income += abs(account.balance)
            elif atype == "EXPENSE":
                total_expenses += abs(account.balance)

        # Date range
        dates = [t.date_posted for t in self.transactions if t.date_posted]
        date_start = min(dates) if dates else date.today()
        date_end = max(dates) if dates else date.today()

        return {
            "file_path": str(self.file_path),
            "file_type": self.file_type,
            "account_count": len(self.accounts),
            "transaction_count": len(self.transactions),
            "date_range_start": date_start,
            "date_range_end": date_end,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": total_assets - total_liabilities,
            "total_income_ytd": total_income,
            "total_expenses_ytd": total_expenses,
        }

    def get_account_list(self) -> List[Dict]:
        """Get list of accounts with mapped types"""
        result = []
        for account in self.accounts.values():
            if account.account_type == "ROOT":
                continue

            mapped_type = GNUCASH_TYPE_MAPPING.get(
                account.account_type.upper(), "expense_other"
            )

            result.append(
                {
                    "guid": account.guid,
                    "name": account.name,
                    "full_path": account.full_path,
                    "gnucash_type": account.account_type,
                    "mapped_type": mapped_type,
                    "balance": account.balance,
                    "currency": account.commodity,
                }
            )

        return sorted(result, key=lambda x: x["full_path"])

    def get_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_guid: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """Get transactions with optional filters"""
        result = []

        for trn in self.transactions:
            # Date filter
            if start_date and trn.date_posted < start_date:
                continue
            if end_date and trn.date_posted > end_date:
                continue

            # Account filter
            if account_guid:
                account_guids = [s["account_guid"] for s in trn.splits]
                if account_guid not in account_guids:
                    continue

            # Build transaction dict
            trn_dict = {
                "guid": trn.guid,
                "date": trn.date_posted,
                "description": trn.description,
                "num": trn.num,
                "splits": [],
            }

            for split in trn.splits:
                account = self.accounts.get(split["account_guid"])
                account_name = account.full_path if account else "Unknown"

                trn_dict["splits"].append(
                    {
                        "account": account_name,
                        "amount": split["value"],
                        "memo": split["memo"],
                        "reconciled": split["reconciled_state"],
                    }
                )

            result.append(trn_dict)

            if len(result) >= limit:
                break

        return result

    def get_balance_sheet(self) -> Dict:
        """Generate a simple balance sheet"""
        assets = {}
        liabilities = {}
        equity = {}

        for account in self.accounts.values():
            atype = account.account_type.upper()

            if atype in [
                "ASSET",
                "BANK",
                "CASH",
                "CHECKING",
                "SAVINGS",
                "STOCK",
                "MUTUAL",
                "RECEIVABLE",
            ]:
                assets[account.full_path] = account.balance
            elif atype in ["LIABILITY", "CREDIT", "CREDITLINE", "PAYABLE"]:
                liabilities[account.full_path] = abs(account.balance)
            elif atype == "EQUITY":
                equity[account.full_path] = account.balance

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        total_equity = sum(equity.values())

        return {
            "as_of": date.today(),
            "assets": assets,
            "total_assets": total_assets,
            "liabilities": liabilities,
            "total_liabilities": total_liabilities,
            "equity": equity,
            "total_equity": total_equity,
            "net_worth": total_assets - total_liabilities,
        }

    def get_income_statement(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """Generate a simple income statement for a period"""
        income = {}
        expenses = {}

        # Filter transactions by date
        for trn in self.transactions:
            if start_date and trn.date_posted < start_date:
                continue
            if end_date and trn.date_posted > end_date:
                continue

            for split in trn.splits:
                account = self.accounts.get(split["account_guid"])
                if not account:
                    continue

                atype = account.account_type.upper()
                value = split["value"]

                if atype == "INCOME":
                    income[account.full_path] = income.get(
                        account.full_path, Decimal("0")
                    ) + abs(value)
                elif atype == "EXPENSE":
                    expenses[account.full_path] = expenses.get(
                        account.full_path, Decimal("0")
                    ) + abs(value)

        total_income = sum(income.values())
        total_expenses = sum(expenses.values())

        return {
            "period_start": start_date or date.today().replace(month=1, day=1),
            "period_end": end_date or date.today(),
            "income": income,
            "total_income": total_income,
            "expenses": expenses,
            "total_expenses": total_expenses,
            "net_income": total_income - total_expenses,
        }
