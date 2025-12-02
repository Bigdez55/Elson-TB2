#!/usr/bin/env python
"""
Database Integrity Checker for Elson Trading Bot Platform.

This script performs thorough integrity checks on the database to identify potential issues
such as corrupted data, constraint violations, orphaned records, and data inconsistencies.

Usage:
    python check_data_integrity.py [--database DATABASE] [--config CONFIG_FILE] [--output OUTPUT_FILE]
    
Options:
    --database    The name of the database to check (defaults to the one in config)
    --config      Path to a configuration file
    --output      Output report file (defaults to integrity_report_TIMESTAMP.html)
    --quiet       Only output on errors
    --verbose     Increase output verbosity
"""

import os
import sys
import argparse
import logging
import json
import datetime
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/elson/data-integrity.log", mode='a+')
    ]
)
logger = logging.getLogger("data-integrity")

# Default configuration
DEFAULT_CONFIG = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "elson_production",
        "user": "elson"
    },
    "checks": {
        "run_all": True,
        "reference_integrity": True,
        "constraint_validation": True,
        "null_checks": True,
        "data_type_validation": True,
        "duplicate_detection": True,
        "business_rules": True,
        "sequence_checks": True,
        "index_consistency": True,
        "database_statistics": True
    },
    "tables": {
        "critical": [
            "users",
            "accounts",
            "trades",
            "portfolios",
            "positions",
            "market_data",
            "trade_executions"
        ],
        "exclude": [
            "alembic_version",
            "spatial_ref_sys"
        ]
    },
    "business_rules": [
        {
            "name": "Portfolio balance matches position sum",
            "description": "The portfolio balance should equal the sum of all position values",
            "query": """
                SELECT 
                    p.id, 
                    p.user_id,
                    p.balance,
                    COALESCE(SUM(pos.quantity * pos.price), 0) as position_sum,
                    p.balance - COALESCE(SUM(pos.quantity * pos.price), 0) as difference
                FROM portfolios p
                LEFT JOIN positions pos ON p.id = pos.portfolio_id
                GROUP BY p.id, p.user_id, p.balance
                HAVING ABS(p.balance - COALESCE(SUM(pos.quantity * pos.price), 0)) > 0.01
            """
        },
        {
            "name": "Trade execution price within market range",
            "description": "Trade execution prices should be within +/- 10% of market price at execution time",
            "query": """
                SELECT 
                    te.id,
                    te.trade_id,
                    te.symbol,
                    te.executed_price,
                    md.price as market_price,
                    ((te.executed_price / md.price) - 1) * 100 as price_difference_pct
                FROM trade_executions te
                JOIN market_data md ON te.symbol = md.symbol 
                    AND md.timestamp <= te.executed_at
                    AND md.timestamp >= te.executed_at - INTERVAL '5 minutes'
                WHERE ABS(((te.executed_price / md.price) - 1) * 100) > 10
                ORDER BY ABS(((te.executed_price / md.price) - 1) * 100) DESC
            """
        },
        {
            "name": "Custodial account approval flow",
            "description": "For minor accounts, all trades must have guardian approval",
            "query": """
                SELECT 
                    t.id,
                    t.account_id,
                    t.created_at,
                    u.id as user_id,
                    u.is_minor
                FROM trades t
                JOIN accounts a ON t.account_id = a.id
                JOIN users u ON a.user_id = u.id
                LEFT JOIN guardian_approvals ga ON t.id = ga.trade_id
                WHERE u.is_minor = TRUE AND ga.id IS NULL
            """
        }
    ]
}

@dataclass
class CheckResult:
    """Result of a data integrity check."""
    name: str
    description: str
    status: str  # "passed", "warning", "failed", "skipped"
    details: List[Dict[str, Any]]
    records_checked: int
    records_with_issues: int
    execution_time: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "details": self.details,
            "records_checked": self.records_checked,
            "records_with_issues": self.records_with_issues,
            "execution_time": self.execution_time,
            "error_message": self.error_message
        }

class DataIntegrityChecker:
    """Data integrity checker for PostgreSQL databases."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conn = None
        self.cursor = None
        self.results = []
    
    def connect(self) -> None:
        """Connect to the database."""
        try:
            # Check if running in Kubernetes
            in_kubernetes = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount")
            
            # Get PostgreSQL connection parameters from environment or config
            db_host = os.environ.get("DB_HOST") or self.config["database"]["host"]
            db_port = os.environ.get("DB_PORT") or self.config["database"]["port"]
            db_name = os.environ.get("DB_NAME") or self.config["database"]["name"]
            db_user = os.environ.get("DB_USER") or self.config["database"]["user"]
            db_password = os.environ.get("PGPASSWORD") or ""
            
            # Connect to PostgreSQL
            # Fix for SQL query execution issues
            self.conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
                application_name="elson_data_integrity_checker"
            )
            
            # Set a statement timeout to avoid hanging queries
            self.conn.cursor().execute("SET statement_timeout = 30000")  # 30 seconds
            
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            logger.info(f"Connected to database {self.config['database']['name']} on {self.config['database']['host']}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def get_table_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about database tables."""
        query = """
            SELECT 
                c.relname as table_name,
                n.nspname as schema_name,
                c.reltuples as estimated_row_count,
                pg_size_pretty(pg_total_relation_size(c.oid)) as total_size,
                obj_description(c.oid) as description
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY c.relname
        """
        
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        
        tables = {}
        for row in result:
            table_name = row["table_name"]
            if table_name in self.config["tables"]["exclude"]:
                continue
                
            tables[table_name] = {
                "schema": row["schema_name"],
                "estimated_row_count": int(row["estimated_row_count"]),
                "total_size": row["total_size"],
                "description": row["description"],
                "is_critical": table_name in self.config["tables"]["critical"]
            }
        
        logger.info(f"Found {len(tables)} tables in database")
        return tables
    
    def get_column_info(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get information about table columns."""
        query = """
            SELECT 
                a.attname as column_name,
                format_type(a.atttypid, a.atttypmod) as data_type,
                a.attnotnull as not_null,
                pg_get_expr(d.adbin, d.adrelid) as default_value,
                col_description(a.attrelid, a.attnum) as description
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
            WHERE c.relname = %s AND n.nspname = %s AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum
        """
        
        self.cursor.execute(query, (table_name, schema))
        result = self.cursor.fetchall()
        
        columns = []
        for row in result:
            columns.append({
                "name": row["column_name"],
                "data_type": row["data_type"],
                "not_null": row["not_null"],
                "default_value": row["default_value"],
                "description": row["description"]
            })
        
        return columns
    
    def get_constraints(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get constraints for a table."""
        query = """
            SELECT 
                con.conname as constraint_name,
                con.contype as constraint_type,
                CASE
                    WHEN con.contype = 'p' THEN 'PRIMARY KEY'
                    WHEN con.contype = 'u' THEN 'UNIQUE'
                    WHEN con.contype = 'f' THEN 'FOREIGN KEY'
                    WHEN con.contype = 'c' THEN 'CHECK'
                    ELSE con.contype::text
                END as constraint_type_desc,
                pg_get_constraintdef(con.oid) as definition
            FROM pg_constraint con
            JOIN pg_class c ON con.conrelid = c.oid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = %s AND n.nspname = %s
            ORDER BY con.contype, con.conname
        """
        
        self.cursor.execute(query, (table_name, schema))
        result = self.cursor.fetchall()
        
        constraints = []
        for row in result:
            constraints.append({
                "name": row["constraint_name"],
                "type": row["constraint_type"],
                "type_desc": row["constraint_type_desc"],
                "definition": row["definition"]
            })
        
        return constraints
    
    def get_foreign_keys(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """Get foreign keys for a table."""
        query = """
            SELECT
                con.conname as constraint_name,
                pg_get_constraintdef(con.oid) as definition,
                c2.relname as referenced_table,
                n2.nspname as referenced_schema
            FROM pg_constraint con
            JOIN pg_class c ON con.conrelid = c.oid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_class c2 ON con.confrelid = c2.oid
            JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
            WHERE c.relname = %s AND n.nspname = %s AND con.contype = 'f'
            ORDER BY con.conname
        """
        
        self.cursor.execute(query, (table_name, schema))
        result = self.cursor.fetchall()
        
        foreign_keys = []
        for row in result:
            foreign_keys.append({
                "name": row["constraint_name"],
                "definition": row["definition"],
                "referenced_table": row["referenced_table"],
                "referenced_schema": row["referenced_schema"]
            })
        
        return foreign_keys
    
    def run_checks(self) -> List[CheckResult]:
        """Run all configured integrity checks."""
        try:
            self.connect()
            
            # Get database information
            tables = self.get_table_info()
            
            # Run checks
            if self.config["checks"]["database_statistics"]:
                self.check_database_statistics()
            
            if self.config["checks"]["reference_integrity"]:
                for table_name, table_info in tables.items():
                    self.check_reference_integrity(table_name, table_info["schema"])
            
            if self.config["checks"]["constraint_validation"]:
                for table_name, table_info in tables.items():
                    self.check_constraint_validation(table_name, table_info["schema"])
            
            if self.config["checks"]["null_checks"]:
                for table_name, table_info in tables.items():
                    self.check_null_values(table_name, table_info["schema"])
            
            if self.config["checks"]["data_type_validation"]:
                for table_name, table_info in tables.items():
                    self.check_data_type_validation(table_name, table_info["schema"])
            
            if self.config["checks"]["duplicate_detection"]:
                for table_name, table_info in tables.items():
                    self.check_duplicate_records(table_name, table_info["schema"])
            
            if self.config["checks"]["sequence_checks"]:
                for table_name, table_info in tables.items():
                    self.check_sequence_values(table_name, table_info["schema"])
            
            if self.config["checks"]["index_consistency"]:
                for table_name, table_info in tables.items():
                    self.check_index_consistency(table_name, table_info["schema"])
            
            if self.config["checks"]["business_rules"]:
                self.check_business_rules()
            
            logger.info(f"Completed all integrity checks with {len(self.results)} results")
            return self.results
            
        except Exception as e:
            logger.error(f"Error running checks: {e}")
            raise
        finally:
            self.close()
    
    def check_reference_integrity(self, table_name: str, schema: str = "public") -> None:
        """Check for foreign key constraint violations."""
        import time
        start_time = time.time()
        
        # Get foreign keys for the table
        foreign_keys = self.get_foreign_keys(table_name, schema)
        
        if not foreign_keys:
            # Skip this check if no foreign keys exist
            self.results.append(CheckResult(
                name=f"Reference Integrity: {table_name}",
                description=f"Check for foreign key constraint violations in {table_name}",
                status="skipped",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message="No foreign keys found for this table"
            ))
            return
        
        issues = []
        records_checked = 0
        
        try:
            for fk in foreign_keys:
                # Extract column names from the foreign key definition
                # Example definition: "FOREIGN KEY (user_id) REFERENCES users(id)"
                fk_def = fk["definition"]
                if "REFERENCES" not in fk_def:
                    continue
                
                # Simple parsing to extract column names
                local_cols_part = fk_def.split("(")[1].split(")")[0]
                local_cols = [col.strip() for col in local_cols_part.split(",")]
                
                ref_table_part = fk_def.split("REFERENCES")[1].strip()
                ref_table = ref_table_part.split("(")[0].strip()
                ref_cols_part = ref_table_part.split("(")[1].split(")")[0]
                ref_cols = [col.strip() for col in ref_cols_part.split(",")]
                
                # Build the query to count records for this foreign key
                conditions = []
                for i, local_col in enumerate(local_cols):
                    conditions.append(f"{local_col} IS NOT NULL")
                
                query = f"""
                    SELECT COUNT(*) as total
                    FROM {schema}.{table_name}
                    WHERE {' AND '.join(conditions)}
                """
                self.cursor.execute(query)
                total_count = self.cursor.fetchone()[0]
                records_checked += total_count
                
                # Skip if no non-null values
                if total_count == 0:
                    continue
                
                # Build the query to check for orphaned records
                join_conditions = []
                for i, local_col in enumerate(local_cols):
                    ref_col = ref_cols[i]
                    join_conditions.append(f"t1.{local_col} = t2.{ref_col}")
                
                query = f"""
                    SELECT t1.*
                    FROM {schema}.{table_name} t1
                    LEFT JOIN {ref_table} t2 ON {' AND '.join(join_conditions)}
                    WHERE {' AND '.join([f"t1.{col} IS NOT NULL" for col in local_cols])}
                    AND t2.{ref_cols[0]} IS NULL
                    LIMIT 100
                """
                
                self.cursor.execute(query)
                orphaned_records = self.cursor.fetchall()
                
                # Count total orphaned records
                if orphaned_records:
                    count_query = f"""
                        SELECT COUNT(*) as count
                        FROM {schema}.{table_name} t1
                        LEFT JOIN {ref_table} t2 ON {' AND '.join(join_conditions)}
                        WHERE {' AND '.join([f"t1.{col} IS NOT NULL" for col in local_cols])}
                        AND t2.{ref_cols[0]} IS NULL
                    """
                    self.cursor.execute(count_query)
                    orphaned_count = self.cursor.fetchone()[0]
                    
                    issues.append({
                        "foreign_key": fk["name"],
                        "definition": fk_def,
                        "orphaned_count": orphaned_count,
                        "sample_records": [dict(record) for record in orphaned_records]
                    })
            
            # Create result
            records_with_issues = sum(issue["orphaned_count"] for issue in issues)
            status = "passed" if not issues else "failed"
            
            self.results.append(CheckResult(
                name=f"Reference Integrity: {table_name}",
                description=f"Check for foreign key constraint violations in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking reference integrity for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"Reference Integrity: {table_name}",
                description=f"Check for foreign key constraint violations in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_constraint_validation(self, table_name: str, schema: str = "public") -> None:
        """Check for constraint violations."""
        import time
        start_time = time.time()
        
        # Get constraints for the table
        constraints = self.get_constraints(table_name, schema)
        check_constraints = [c for c in constraints if c["type"] == "c"]
        
        if not check_constraints:
            # Skip this check if no check constraints exist
            self.results.append(CheckResult(
                name=f"Constraint Validation: {table_name}",
                description=f"Check for constraint violations in {table_name}",
                status="skipped",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message="No check constraints found for this table"
            ))
            return
        
        issues = []
        records_checked = 0
        
        try:
            # Get row count for the table
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            records_checked = self.cursor.fetchone()[0]
            
            for constraint in check_constraints:
                # Extract the check condition from the definition
                # Example: "CHECK ((price > 0::numeric))"
                check_def = constraint["definition"]
                condition = check_def.replace("CHECK (", "").rstrip(")")
                
                # Build the query to find violations
                query = f"""
                    SELECT *
                    FROM {schema}.{table_name}
                    WHERE NOT ({condition})
                    LIMIT 100
                """
                
                self.cursor.execute(query)
                violations = self.cursor.fetchall()
                
                # Count total violations
                if violations:
                    count_query = f"""
                        SELECT COUNT(*) as count
                        FROM {schema}.{table_name}
                        WHERE NOT ({condition})
                    """
                    self.cursor.execute(count_query)
                    violation_count = self.cursor.fetchone()[0]
                    
                    issues.append({
                        "constraint": constraint["name"],
                        "definition": check_def,
                        "violation_count": violation_count,
                        "sample_records": [dict(record) for record in violations]
                    })
            
            # Create result
            records_with_issues = sum(issue["violation_count"] for issue in issues)
            status = "passed" if not issues else "failed"
            
            self.results.append(CheckResult(
                name=f"Constraint Validation: {table_name}",
                description=f"Check for constraint violations in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking constraint validation for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"Constraint Validation: {table_name}",
                description=f"Check for constraint violations in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_null_values(self, table_name: str, schema: str = "public") -> None:
        """Check for unexpected NULL values."""
        import time
        start_time = time.time()
        
        # Get column information for the table
        columns = self.get_column_info(table_name, schema)
        not_null_columns = [col for col in columns if col["not_null"]]
        
        if not not_null_columns:
            # Skip this check if no NOT NULL columns exist
            self.results.append(CheckResult(
                name=f"NULL Value Check: {table_name}",
                description=f"Check for unexpected NULL values in {table_name}",
                status="skipped",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message="No NOT NULL columns found for this table"
            ))
            return
        
        issues = []
        records_checked = 0
        
        try:
            # Get row count for the table
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            records_checked = self.cursor.fetchone()[0]
            
            # Check for NULL values in NOT NULL columns
            for column in not_null_columns:
                query = f"""
                    SELECT *
                    FROM {schema}.{table_name}
                    WHERE {column["name"]} IS NULL
                    LIMIT 100
                """
                
                self.cursor.execute(query)
                null_records = self.cursor.fetchall()
                
                # Count total NULL values
                if null_records:
                    count_query = f"""
                        SELECT COUNT(*) as count
                        FROM {schema}.{table_name}
                        WHERE {column["name"]} IS NULL
                    """
                    self.cursor.execute(count_query)
                    null_count = self.cursor.fetchone()[0]
                    
                    issues.append({
                        "column": column["name"],
                        "data_type": column["data_type"],
                        "null_count": null_count,
                        "sample_records": [dict(record) for record in null_records]
                    })
            
            # Create result
            records_with_issues = sum(issue["null_count"] for issue in issues)
            status = "passed" if not issues else "failed"
            
            self.results.append(CheckResult(
                name=f"NULL Value Check: {table_name}",
                description=f"Check for unexpected NULL values in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking NULL values for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"NULL Value Check: {table_name}",
                description=f"Check for unexpected NULL values in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_data_type_validation(self, table_name: str, schema: str = "public") -> None:
        """Check for data type validation issues."""
        import time
        start_time = time.time()
        
        # Get column information for the table
        columns = self.get_column_info(table_name, schema)
        
        issues = []
        records_checked = 0
        
        try:
            # Get row count for the table
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            records_checked = self.cursor.fetchone()[0]
            
            # Check for suspicious values in specific data types
            for column in columns:
                data_type = column["data_type"].lower()
                column_name = column["name"]
                
                if "numeric" in data_type or "int" in data_type or "float" in data_type or "double" in data_type:
                    # Fix: Use CAST for safer numeric type checking
                    query = f"""
                        SELECT *
                        FROM {schema}.{table_name}
                        WHERE {column_name} IS NOT NULL
                        AND (
                            CAST({column_name} AS TEXT) = 'Infinity'
                            OR CAST({column_name} AS TEXT) = '-Infinity'
                            OR CAST({column_name} AS TEXT) = 'NaN'
                            OR {column_name} < -1e12
                            OR {column_name} > 1e12
                        )
                        LIMIT 100
                    """
                    
                    try:
                        self.cursor.execute(query)
                        extreme_records = self.cursor.fetchall()
                        
                        # Count total extreme values
                        if extreme_records:
                            count_query = f"""
                                SELECT COUNT(*) as count
                                FROM {schema}.{table_name}
                                WHERE {column_name} IS NOT NULL
                                AND (
                                    CAST({column_name} AS TEXT) = 'Infinity'
                                    OR CAST({column_name} AS TEXT) = '-Infinity'
                                    OR CAST({column_name} AS TEXT) = 'NaN'
                                    OR {column_name} < -1e12
                                    OR {column_name} > 1e12
                                )
                            """
                            self.cursor.execute(count_query)
                            extreme_count = self.cursor.fetchone()[0]
                            
                            issues.append({
                                "column": column_name,
                                "data_type": data_type,
                                "issue_type": "extreme_values",
                                "count": extreme_count,
                                "sample_records": [dict(record) for record in extreme_records]
                            })
                    except Exception as e:
                        # Some data type conversions might fail, which is okay
                        logger.debug(f"Skipping extreme value check for {column_name}: {e}")
                
                elif "date" in data_type or "time" in data_type:
                    # Fix: Use CAST for safer timestamp checking
                    query = f"""
                        SELECT *
                        FROM {schema}.{table_name}
                        WHERE {column_name} IS NOT NULL
                        AND (
                            {column_name} < CAST('1900-01-01' AS TIMESTAMP)
                            OR {column_name} > CAST('2100-01-01' AS TIMESTAMP)
                        )
                        LIMIT 100
                    """
                    
                    try:
                        self.cursor.execute(query)
                        extreme_dates = self.cursor.fetchall()
                        
                        # Count total extreme dates
                        if extreme_dates:
                            count_query = f"""
                                SELECT COUNT(*) as count
                                FROM {schema}.{table_name}
                                WHERE {column_name} IS NOT NULL
                                AND (
                                    {column_name} < CAST('1900-01-01' AS TIMESTAMP)
                                    OR {column_name} > CAST('2100-01-01' AS TIMESTAMP)
                                )
                            """
                            self.cursor.execute(count_query)
                            extreme_count = self.cursor.fetchone()[0]
                            
                            issues.append({
                                "column": column_name,
                                "data_type": data_type,
                                "issue_type": "extreme_dates",
                                "count": extreme_count,
                                "sample_records": [dict(record) for record in extreme_dates]
                            })
                    except Exception as e:
                        # Some data type conversions might fail, which is okay
                        logger.debug(f"Skipping date check for {column_name}: {e}")
            
            # Create result
            records_with_issues = sum(issue["count"] for issue in issues)
            status = "passed" if not issues else "failed"
            
            self.results.append(CheckResult(
                name=f"Data Type Validation: {table_name}",
                description=f"Check for data type validation issues in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking data type validation for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"Data Type Validation: {table_name}",
                description=f"Check for data type validation issues in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_duplicate_records(self, table_name: str, schema: str = "public") -> None:
        """Check for duplicate records."""
        import time
        start_time = time.time()
        
        # Get column information for the table
        columns = self.get_column_info(table_name, schema)
        
        # Get constraints for the table
        constraints = self.get_constraints(table_name, schema)
        unique_constraints = [c for c in constraints if c["type"] in ["p", "u"]]
        
        if not unique_constraints:
            # Skip this check if no unique constraints exist
            self.results.append(CheckResult(
                name=f"Duplicate Record Check: {table_name}",
                description=f"Check for duplicate records in {table_name}",
                status="skipped",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message="No unique constraints found for this table"
            ))
            return
        
        issues = []
        records_checked = 0
        
        try:
            # Get row count for the table
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            records_checked = self.cursor.fetchone()[0]
            
            # Check for duplicate values in columns that should be unique
            for constraint in unique_constraints:
                # Extract columns from the constraint definition
                # Example: "PRIMARY KEY (id)" or "UNIQUE (email)"
                constraint_def = constraint["definition"]
                cols_part = constraint_def.split("(")[1].split(")")[0]
                cols = [col.strip() for col in cols_part.split(",")]
                
                # Build the query to find duplicates
                select_cols = ", ".join(cols)
                group_by_cols = select_cols
                having_clause = " COUNT(*) > 1"
                
                query = f"""
                    SELECT {select_cols}, COUNT(*) as duplicate_count
                    FROM {schema}.{table_name}
                    GROUP BY {group_by_cols}
                    HAVING {having_clause}
                    LIMIT 100
                """
                
                self.cursor.execute(query)
                duplicates = self.cursor.fetchall()
                
                # Count total duplicate records
                if duplicates:
                    # We need to count all records that are duplicates, not just the groups
                    duplicate_groups = duplicates
                    
                    # For each duplicate group, we need to find the actual records
                    sample_records = []
                    total_duplicate_records = 0
                    
                    for group in duplicate_groups[:5]:  # Limit to 5 groups for samples
                        conditions = []
                        for i, col in enumerate(cols):
                            val = group[i]
                            if val is None:
                                conditions.append(f"{col} IS NULL")
                            else:
                                conditions.append(f"{col} = %s")
                        
                        where_clause = " AND ".join(conditions)
                        sample_query = f"""
                            SELECT *
                            FROM {schema}.{table_name}
                            WHERE {where_clause}
                            LIMIT 10
                        """
                        
                        # Get the parameter values (exclude the last column which is the count)
                        params = [val for val in group[:-1] if val is not None]
                        
                        self.cursor.execute(sample_query, params)
                        group_records = self.cursor.fetchall()
                        sample_records.extend([dict(record) for record in group_records])
                        
                        # The duplicate count is the last column in the group record
                        total_duplicate_records += group["duplicate_count"]
                    
                    issues.append({
                        "constraint": constraint["name"],
                        "columns": cols,
                        "duplicate_groups": len(duplicate_groups),
                        "duplicate_records": total_duplicate_records,
                        "sample_records": sample_records
                    })
            
            # Create result
            records_with_issues = sum(issue["duplicate_records"] for issue in issues)
            status = "passed" if not issues else "failed"
            
            self.results.append(CheckResult(
                name=f"Duplicate Record Check: {table_name}",
                description=f"Check for duplicate records in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking duplicate records for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"Duplicate Record Check: {table_name}",
                description=f"Check for duplicate records in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_sequence_values(self, table_name: str, schema: str = "public") -> None:
        """Check for sequence value issues."""
        import time
        start_time = time.time()
        
        # Get column information for the table
        columns = self.get_column_info(table_name, schema)
        
        # Find columns with default values that use sequences
        sequence_columns = []
        for column in columns:
            if column["default_value"] and "nextval" in column["default_value"]:
                sequence_columns.append(column)
        
        if not sequence_columns:
            # Skip this check if no sequence columns exist
            self.results.append(CheckResult(
                name=f"Sequence Value Check: {table_name}",
                description=f"Check for sequence value issues in {table_name}",
                status="skipped",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message="No sequence columns found for this table"
            ))
            return
        
        issues = []
        records_checked = 0
        
        try:
            # For each sequence column, check if there are any issues
            for column in sequence_columns:
                column_name = column["name"]
                
                # Extract sequence name from default value
                # Example: "nextval('users_id_seq'::regclass)"
                default_value = column["default_value"]
                sequence_name = default_value.split("'")[1]
                
                # Get the current sequence value
                self.cursor.execute(f"SELECT last_value, is_called FROM {sequence_name}")
                seq_info = self.cursor.fetchone()
                current_seq_value = seq_info["last_value"]
                
                # Get the maximum value in the table
                self.cursor.execute(f"SELECT MAX({column_name}) FROM {schema}.{table_name}")
                max_value = self.cursor.fetchone()[0]
                
                # Get row count for the table
                self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                records_checked = self.cursor.fetchone()[0]
                
                # Check for sequence issues
                if max_value is not None and current_seq_value < max_value:
                    issues.append({
                        "column": column_name,
                        "sequence": sequence_name,
                        "current_seq_value": current_seq_value,
                        "max_value": max_value,
                        "difference": max_value - current_seq_value,
                        "issue_type": "sequence_behind"
                    })
                
                # Check for gaps in sequence values using improved query
                query = f"""
                    WITH numbered AS (
                        SELECT {column_name}, 
                               ROW_NUMBER() OVER (ORDER BY {column_name}) as row_num
                        FROM {schema}.{table_name}
                        WHERE {column_name} IS NOT NULL
                    )
                    SELECT {column_name}, row_num, ({column_name} - row_num) as gap
                    FROM numbered
                    WHERE ({column_name} - row_num) > 100
                    ORDER BY {column_name}
                    LIMIT 100
                """
                
                self.cursor.execute(query)
                gaps = self.cursor.fetchall()
                
                if gaps:
                    # Count the total number of gaps
                    gap_count = len(gaps)
                    
                    issues.append({
                        "column": column_name,
                        "sequence": sequence_name,
                        "issue_type": "sequence_gaps",
                        "gap_count": gap_count,
                        "sample_gaps": [dict(gap) for gap in gaps]
                    })
            
            # Create result
            records_with_issues = len(issues)
            status = "passed" if not issues else "warning"  # Sequence issues are usually just warnings
            
            self.results.append(CheckResult(
                name=f"Sequence Value Check: {table_name}",
                description=f"Check for sequence value issues in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking sequence values for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"Sequence Value Check: {table_name}",
                description=f"Check for sequence value issues in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_index_consistency(self, table_name: str, schema: str = "public") -> None:
        """Check for index health and consistency."""
        import time
        start_time = time.time()
        
        # Get indexes for the table
        query = """
            SELECT
                i.relname as index_name,
                a.attname as column_name,
                ix.indisunique as is_unique,
                ix.indisprimary as is_primary,
                pg_size_pretty(pg_relation_size(i.oid)) as index_size,
                pg_stat_get_numscans(i.oid) as index_scans
            FROM pg_index ix
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE t.relname = %s AND n.nspname = %s
            ORDER BY i.relname, a.attnum
        """
        
        self.cursor.execute(query, (table_name, schema))
        indexes = self.cursor.fetchall()
        
        if not indexes:
            # Skip this check if no indexes exist
            self.results.append(CheckResult(
                name=f"Index Consistency: {table_name}",
                description=f"Check for index health and consistency in {table_name}",
                status="skipped",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message="No indexes found for this table"
            ))
            return
        
        issues = []
        records_checked = len(indexes)
        
        try:
            # Group indexes by name
            index_groups = {}
            for idx in indexes:
                name = idx["index_name"]
                if name not in index_groups:
                    index_groups[name] = {
                        "name": name,
                        "columns": [],
                        "is_unique": idx["is_unique"],
                        "is_primary": idx["is_primary"],
                        "size": idx["index_size"],
                        "scans": idx["index_scans"]
                    }
                index_groups[name]["columns"].append(idx["column_name"])
            
            # Check for unused indexes
            for name, idx in index_groups.items():
                if idx["scans"] == 0 and not idx["is_primary"]:
                    issues.append({
                        "index": name,
                        "columns": idx["columns"],
                        "issue_type": "unused_index",
                        "size": idx["size"]
                    })
            
            # Create result
            records_with_issues = len(issues)
            status = "passed" if not issues else "warning"  # Index issues are usually just warnings
            
            self.results.append(CheckResult(
                name=f"Index Consistency: {table_name}",
                description=f"Check for index health and consistency in {table_name}",
                status=status,
                details=issues,
                records_checked=records_checked,
                records_with_issues=records_with_issues,
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error checking index consistency for {table_name}: {e}")
            self.results.append(CheckResult(
                name=f"Index Consistency: {table_name}",
                description=f"Check for index health and consistency in {table_name}",
                status="error",
                details=[],
                records_checked=records_checked,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_database_statistics(self) -> None:
        """Get overall database statistics."""
        import time
        start_time = time.time()
        
        try:
            # Get database size
            self.cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = self.cursor.fetchone()[0]
            
            # Get table counts
            self.cursor.execute("""
                SELECT count(*) FROM pg_stat_user_tables
            """)
            table_count = self.cursor.fetchone()[0]
            
            # Get largest tables
            self.cursor.execute("""
                SELECT
                    relname as table_name,
                    pg_size_pretty(pg_relation_size(c.oid)) as table_size,
                    pg_size_pretty(pg_total_relation_size(c.oid)) as total_size,
                    reltuples::bigint as estimated_rows
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY pg_total_relation_size(c.oid) DESC
                LIMIT 10
            """)
            largest_tables = self.cursor.fetchall()
            
            # Get connection statistics
            self.cursor.execute("""
                SELECT
                    sum(numbackends) as connections,
                    sum(xact_commit) as commits,
                    sum(xact_rollback) as rollbacks,
                    sum(blks_read) as disk_reads,
                    sum(blks_hit) as buffer_hits,
                    CASE
                        WHEN sum(blks_read) + sum(blks_hit) = 0 THEN 0
                        ELSE round(sum(blks_hit) * 100.0 / (sum(blks_read) + sum(blks_hit)), 2)
                    END as cache_hit_ratio
                FROM pg_stat_database
            """)
            db_stats = self.cursor.fetchone()
            
            # Get transaction statistics
            self.cursor.execute("""
                SELECT
                    sum(n_tup_ins) as inserts,
                    sum(n_tup_upd) as updates,
                    sum(n_tup_del) as deletes,
                    sum(n_live_tup) as live_tuples,
                    sum(n_dead_tup) as dead_tuples
                FROM pg_stat_user_tables
            """)
            tx_stats = self.cursor.fetchone()
            
            # Build the result
            details = {
                "database_size": db_size,
                "table_count": table_count,
                "largest_tables": [dict(t) for t in largest_tables],
                "connection_stats": dict(db_stats) if db_stats else {},
                "transaction_stats": dict(tx_stats) if tx_stats else {}
            }
            
            # Check if there are any issues to flag
            issues = []
            
            # Check cache hit ratio
            if db_stats and db_stats["cache_hit_ratio"] < 90:
                issues.append({
                    "issue_type": "low_cache_hit_ratio",
                    "value": f"{db_stats['cache_hit_ratio']}%",
                    "recommendation": "Consider increasing shared_buffers in PostgreSQL configuration"
                })
            
            # Check dead tuple ratio
            if tx_stats and tx_stats["live_tuples"] + tx_stats["dead_tuples"] > 0:
                dead_ratio = tx_stats["dead_tuples"] * 100.0 / (tx_stats["live_tuples"] + tx_stats["dead_tuples"])
                if dead_ratio > 10:
                    issues.append({
                        "issue_type": "high_dead_tuple_ratio",
                        "value": f"{dead_ratio:.2f}%",
                        "recommendation": "Run VACUUM ANALYZE on database"
                    })
            
            # Check connection usage
            if db_stats and db_stats["connections"] > 100:
                issues.append({
                    "issue_type": "high_connection_count",
                    "value": db_stats["connections"],
                    "recommendation": "Check for connection leaks and consider connection pooling"
                })
            
            # Create result
            status = "passed" if not issues else "warning"
            details["issues"] = issues
            
            self.results.append(CheckResult(
                name=f"Database Statistics",
                description=f"Overall database statistics and health check",
                status=status,
                details=[details],
                records_checked=1,
                records_with_issues=len(issues),
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            self.results.append(CheckResult(
                name=f"Database Statistics",
                description=f"Overall database statistics and health check",
                status="error",
                details=[],
                records_checked=0,
                records_with_issues=0,
                execution_time=time.time() - start_time,
                error_message=str(e)
            ))
    
    def check_business_rules(self) -> None:
        """Check business rule validations."""
        import time
        
        # Get business rules from config
        business_rules = self.config.get("business_rules", [])
        
        if not business_rules:
            return
        
        for rule in business_rules:
            start_time = time.time()
            rule_name = rule["name"]
            rule_description = rule["description"]
            rule_query = rule["query"]
            
            try:
                # Execute the rule query with a timeout parameter to prevent hanging
                self.cursor.execute(f"SET statement_timeout = 30000")  # 30 seconds
                self.cursor.execute(rule_query)
                violations = self.cursor.fetchall()
                
                # Create result
                if violations:
                    # Count total violations
                    violation_count = len(violations)
                    
                    # Get sample records
                    sample_records = [dict(record) for record in violations[:100]]
                    
                    self.results.append(CheckResult(
                        name=f"Business Rule: {rule_name}",
                        description=rule_description,
                        status="failed",
                        details=[{"violations": sample_records}],
                        records_checked=violation_count,
                        records_with_issues=violation_count,
                        execution_time=time.time() - start_time
                    ))
                else:
                    self.results.append(CheckResult(
                        name=f"Business Rule: {rule_name}",
                        description=rule_description,
                        status="passed",
                        details=[],
                        records_checked=0,
                        records_with_issues=0,
                        execution_time=time.time() - start_time
                    ))
                
            except Exception as e:
                logger.error(f"Error checking business rule '{rule_name}': {e}")
                self.results.append(CheckResult(
                    name=f"Business Rule: {rule_name}",
                    description=rule_description,
                    status="error",
                    details=[],
                    records_checked=0,
                    records_with_issues=0,
                    execution_time=time.time() - start_time,
                    error_message=str(e)
                ))
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate an HTML report of the integrity check results."""
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"integrity_report_{timestamp}.html"
        
        # Count results by status
        status_counts = {
            "passed": 0,
            "warning": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0
        }
        
        for result in self.results:
            status = result.status
            if status in status_counts:
                status_counts[status] += 1
        
        # Generate HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Database Integrity Report - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }}
                .container {{
                    width: 95%;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3, h4 {{
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                .summary {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    margin: 20px 0;
                }}
                .summary-item {{
                    padding: 10px;
                    border-radius: 5px;
                    flex: 1;
                    min-width: 150px;
                    text-align: center;
                }}
                .passed {{ background-color: #d4edda; color: #155724; }}
                .warning {{ background-color: #fff3cd; color: #856404; }}
                .failed {{ background-color: #f8d7da; color: #721c24; }}
                .error {{ background-color: #f8d7da; color: #721c24; }}
                .skipped {{ background-color: #e2e3e5; color: #383d41; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .details-toggle {{
                    cursor: pointer;
                    color: #007bff;
                }}
                .details-content {{
                    display: none;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    margin-top: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                pre {{
                    margin: 0;
                    white-space: pre-wrap;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Database Integrity Report</h1>
                <p>Report generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>Database: {self.config['database']['name']} on {self.config['database']['host']}</p>
                
                <h2>Summary</h2>
                <div class="summary">
                    <div class="summary-item passed">
                        <h3>Passed</h3>
                        <p>{status_counts['passed']}</p>
                    </div>
                    <div class="summary-item warning">
                        <h3>Warning</h3>
                        <p>{status_counts['warning']}</p>
                    </div>
                    <div class="summary-item failed">
                        <h3>Failed</h3>
                        <p>{status_counts['failed']}</p>
                    </div>
                    <div class="summary-item error">
                        <h3>Error</h3>
                        <p>{status_counts['error']}</p>
                    </div>
                    <div class="summary-item skipped">
                        <h3>Skipped</h3>
                        <p>{status_counts['skipped']}</p>
                    </div>
                </div>
                
                <h2>Check Results</h2>
                <table>
                    <tr>
                        <th>Check</th>
                        <th>Status</th>
                        <th>Records Checked</th>
                        <th>Records with Issues</th>
                        <th>Execution Time</th>
                        <th>Details</th>
                    </tr>
        """
        
        # Add rows for each check result
        for i, result in enumerate(self.results):
            status_class = result.status
            execution_time = f"{result.execution_time:.3f}s"
            
            html += f"""
                <tr class="{status_class}">
                    <td>{result.name}</td>
                    <td>{result.status.upper()}</td>
                    <td>{result.records_checked}</td>
                    <td>{result.records_with_issues}</td>
                    <td>{execution_time}</td>
                    <td>
                        <span class="details-toggle" onclick="toggleDetails({i})">Show Details</span>
                        <div id="details-{i}" class="details-content">
                            <p><strong>Description:</strong> {result.description}</p>
            """
            
            if result.error_message:
                html += f"<p><strong>Error:</strong> {result.error_message}</p>"
            
            if result.details:
                html += f"<pre>{json.dumps(result.details, indent=2, default=str)}</pre>"
            
            html += """
                        </div>
                    </td>
                </tr>
            """
        
        html += """
                </table>
                
                <script>
                    function toggleDetails(id) {
                        var content = document.getElementById('details-' + id);
                        var display = content.style.display;
                        content.style.display = display === 'block' ? 'none' : 'block';
                    }
                </script>
            </div>
        </body>
        </html>
        """
        
        # Write the report to file
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Report generated: {output_file}")
        return output_file

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults."""
    config = DEFAULT_CONFIG.copy()
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
            
            # Update the config with file values
            for key, value in file_config.items():
                if key in config:
                    if isinstance(value, dict) and isinstance(config[key], dict):
                        config[key].update(value)
                    else:
                        config[key] = value
                else:
                    config[key] = value
            
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    # Override with environment variables
    if os.environ.get("DB_HOST"):
        config["database"]["host"] = os.environ.get("DB_HOST")
    if os.environ.get("DB_PORT"):
        config["database"]["port"] = int(os.environ.get("DB_PORT"))
    if os.environ.get("DB_NAME"):
        config["database"]["name"] = os.environ.get("DB_NAME")
    if os.environ.get("DB_USER"):
        config["database"]["user"] = os.environ.get("DB_USER")
    
    return config

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database Integrity Checker for Elson Trading Bot Platform")
    parser.add_argument("--database", help="The name of the database to check (defaults to the one in config)")
    parser.add_argument("--config", help="Path to a configuration file")
    parser.add_argument("--output", help="Output report file (defaults to integrity_report_TIMESTAMP.html)")
    parser.add_argument("--quiet", action="store_true", help="Only output on errors")
    parser.add_argument("--verbose", action="store_true", help="Increase output verbosity")
    args = parser.parse_args()
    
    # Set logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override database name if specified
        if args.database:
            config["database"]["name"] = args.database
        
        # Create and run the checker
        checker = DataIntegrityChecker(config)
        results = checker.run_checks()
        
        # Generate report
        report_file = checker.generate_report(args.output)
        
        # Print summary
        status_counts = {
            "passed": 0,
            "warning": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0
        }
        
        for result in results:
            status = result.status
            if status in status_counts:
                status_counts[status] += 1
        
        print(f"\nDatabase Integrity Check Results:")
        print(f"Database: {config['database']['name']} on {config['database']['host']}")
        print(f"Report file: {report_file}")
        print(f"Checks: {len(results)}")
        print(f"Passed: {status_counts['passed']}")
        print(f"Warning: {status_counts['warning']}")
        print(f"Failed: {status_counts['failed']}")
        print(f"Error: {status_counts['error']}")
        print(f"Skipped: {status_counts['skipped']}")
        
        # Return error code if any checks failed
        if status_counts["failed"] > 0 or status_counts["error"] > 0:
            return 1
        return 0
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())