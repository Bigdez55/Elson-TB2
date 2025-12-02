#!/bin/bash
#
# Backup and Restore Testing Script for Elson Trading Bot Platform
#
# This script tests the backup and restore functionality by:
# 1. Creating a test database
# 2. Inserting sample data
# 3. Backing up the database
# 4. Corrupting or dropping the database
# 5. Restoring from the backup
# 6. Verifying data integrity
#
# Usage: ./test_backup_restore.sh [--full]
#   --full: Test with a full backup instead of incremental

set -e

# Default settings
TEST_DB_NAME="elson_test_$(date +%Y%m%d%H%M%S)"
TEST_DB_USER="elson"
BACKUP_SCRIPT_PATH="../Elson/backend/app/scripts/backup_database.py"
RESTORE_SCRIPT_PATH="../Elson/backend/app/scripts/restore_database.py"
LOG_FILE="backup_restore_test_$(date +%Y%m%d%H%M%S).log"
BACKUP_TYPE="incremental"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --full)
      BACKUP_TYPE="full"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Elson Trading Bot Platform: Backup & Restore Test ==="
echo "Started at: $(date)"
echo "Test database: $TEST_DB_NAME"
echo "Backup type: $BACKUP_TYPE"
echo

# Check if PostgreSQL is running
if ! pg_isready -q; then
  echo "ERROR: PostgreSQL is not running"
  exit 1
fi

echo "Step 1: Creating test database..."
createdb "$TEST_DB_NAME"

echo "Step 2: Creating sample schema and data..."
psql -d "$TEST_DB_NAME" << EOF
-- Create test tables
CREATE TABLE test_users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_accounts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES test_users(id),
  account_number VARCHAR(50) NOT NULL,
  balance NUMERIC(15,2) DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_trades (
  id SERIAL PRIMARY KEY,
  account_id INTEGER REFERENCES test_accounts(id),
  symbol VARCHAR(20) NOT NULL,
  quantity INTEGER NOT NULL,
  price NUMERIC(15,2) NOT NULL,
  trade_type VARCHAR(10) NOT NULL,
  executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO test_users (username, email)
VALUES 
  ('user1', 'user1@example.com'),
  ('user2', 'user2@example.com'),
  ('user3', 'user3@example.com');

INSERT INTO test_accounts (user_id, account_number, balance)
VALUES 
  (1, 'ACC001', 10000.00),
  (2, 'ACC002', 25000.00),
  (3, 'ACC003', 5000.00);

INSERT INTO test_trades (account_id, symbol, quantity, price, trade_type)
VALUES 
  (1, 'AAPL', 10, 150.00, 'BUY'),
  (2, 'MSFT', 15, 220.00, 'BUY'),
  (3, 'GOOGL', 5, 2500.00, 'BUY'),
  (1, 'TSLA', 8, 800.00, 'BUY'),
  (2, 'AMZN', 3, 3200.00, 'BUY');

-- Create a function to generate a checksum of all data
CREATE OR REPLACE FUNCTION get_data_checksum() 
RETURNS TEXT AS \$\$
DECLARE
  users_checksum TEXT;
  accounts_checksum TEXT;
  trades_checksum TEXT;
BEGIN
  SELECT MD5(STRING_AGG(id || username || email || created_at::TEXT, '')) INTO users_checksum FROM test_users ORDER BY id;
  SELECT MD5(STRING_AGG(id || user_id || account_number || balance || created_at::TEXT, '')) INTO accounts_checksum FROM test_accounts ORDER BY id;
  SELECT MD5(STRING_AGG(id || account_id || symbol || quantity || price || trade_type || executed_at::TEXT, '')) INTO trades_checksum FROM test_trades ORDER BY id;
  
  RETURN MD5(users_checksum || accounts_checksum || trades_checksum);
END;
\$\$ LANGUAGE plpgsql;
EOF

# Calculate original checksum
ORIGINAL_CHECKSUM=$(psql -t -d "$TEST_DB_NAME" -c "SELECT get_data_checksum();")
ORIGINAL_CHECKSUM=$(echo "$ORIGINAL_CHECKSUM" | tr -d '[:space:]')
echo "Original data checksum: $ORIGINAL_CHECKSUM"

# Count records before backup
USERS_COUNT=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_users;")
ACCOUNTS_COUNT=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_accounts;")
TRADES_COUNT=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_trades;")

echo "Original record counts:"
echo "  Users: $USERS_COUNT"
echo "  Accounts: $ACCOUNTS_COUNT"
echo "  Trades: $TRADES_COUNT"

echo "Step 3: Backing up the database..."
# Prepare environment variables for the backup script
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="$TEST_DB_NAME"
export DB_USER="$TEST_DB_USER"
export BACKUP_STORAGE="local"
export BACKUP_DIR="/tmp/elson_test_backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run backup script
if [ "$BACKUP_TYPE" = "full" ]; then
  python "$BACKUP_SCRIPT_PATH" --full
else
  python "$BACKUP_SCRIPT_PATH"
fi

# Get the backup file path
BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.sql* | head -1)
echo "Created backup: $BACKUP_FILE"

echo "Step 4: Corrupting the database..."
psql -d "$TEST_DB_NAME" << EOF
-- Delete some data
DELETE FROM test_trades WHERE account_id = 1;
DELETE FROM test_accounts WHERE user_id = 2;
DELETE FROM test_users WHERE id = 3;

-- Corrupt some data
UPDATE test_users SET email = 'corrupted@example.com' WHERE id = 1;
UPDATE test_accounts SET balance = 999999.99 WHERE id = 1;
EOF

# Calculate corrupted checksum
CORRUPTED_CHECKSUM=$(psql -t -d "$TEST_DB_NAME" -c "SELECT get_data_checksum();")
CORRUPTED_CHECKSUM=$(echo "$CORRUPTED_CHECKSUM" | tr -d '[:space:]')
echo "Corrupted data checksum: $CORRUPTED_CHECKSUM"

# Count records after corruption
USERS_AFTER_CORRUPTION=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_users;")
ACCOUNTS_AFTER_CORRUPTION=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_accounts;")
TRADES_AFTER_CORRUPTION=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_trades;")

echo "Record counts after corruption:"
echo "  Users: $USERS_AFTER_CORRUPTION"
echo "  Accounts: $ACCOUNTS_AFTER_CORRUPTION"
echo "  Trades: $TRADES_AFTER_CORRUPTION"

echo "Step 5: Restoring the database..."
# Drop the corrupted database and create an empty one
dropdb "$TEST_DB_NAME"
createdb "$TEST_DB_NAME"

# Run restore script
python "$RESTORE_SCRIPT_PATH" --latest --target-db "$TEST_DB_NAME"

# Wait for restoration to complete
sleep 2

echo "Step 6: Verifying data integrity after restore..."
# Re-create the checksum function (it would have been lost in the database drop)
psql -d "$TEST_DB_NAME" << EOF
-- Create a function to generate a checksum of all data
CREATE OR REPLACE FUNCTION get_data_checksum() 
RETURNS TEXT AS \$\$
DECLARE
  users_checksum TEXT;
  accounts_checksum TEXT;
  trades_checksum TEXT;
BEGIN
  SELECT MD5(STRING_AGG(id || username || email || created_at::TEXT, '')) INTO users_checksum FROM test_users ORDER BY id;
  SELECT MD5(STRING_AGG(id || user_id || account_number || balance || created_at::TEXT, '')) INTO accounts_checksum FROM test_accounts ORDER BY id;
  SELECT MD5(STRING_AGG(id || account_id || symbol || quantity || price || trade_type || executed_at::TEXT, '')) INTO trades_checksum FROM test_trades ORDER BY id;
  
  RETURN MD5(users_checksum || accounts_checksum || trades_checksum);
END;
\$\$ LANGUAGE plpgsql;
EOF

# Calculate restored checksum
RESTORED_CHECKSUM=$(psql -t -d "$TEST_DB_NAME" -c "SELECT get_data_checksum();")
RESTORED_CHECKSUM=$(echo "$RESTORED_CHECKSUM" | tr -d '[:space:]')
echo "Restored data checksum: $RESTORED_CHECKSUM"

# Count records after restore
USERS_AFTER_RESTORE=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_users;")
ACCOUNTS_AFTER_RESTORE=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_accounts;")
TRADES_AFTER_RESTORE=$(psql -t -d "$TEST_DB_NAME" -c "SELECT COUNT(*) FROM test_trades;")

echo "Record counts after restore:"
echo "  Users: $USERS_AFTER_RESTORE"
echo "  Accounts: $ACCOUNTS_AFTER_RESTORE"
echo "  Trades: $TRADES_AFTER_RESTORE"

# Verify integrity
if [ "$ORIGINAL_CHECKSUM" = "$RESTORED_CHECKSUM" ]; then
  echo "SUCCESS: Data integrity verified! The restored database matches the original."
  TEST_RESULT="PASSED"
else
  echo "FAILURE: Data integrity check failed! The restored database does not match the original."
  echo "Original checksum: $ORIGINAL_CHECKSUM"
  echo "Restored checksum: $RESTORED_CHECKSUM"
  TEST_RESULT="FAILED"
fi

# Check record counts
if [ "$USERS_COUNT" = "$USERS_AFTER_RESTORE" ] && 
   [ "$ACCOUNTS_COUNT" = "$ACCOUNTS_AFTER_RESTORE" ] && 
   [ "$TRADES_COUNT" = "$TRADES_AFTER_RESTORE" ]; then
  echo "Record count check passed!"
else
  echo "Record count check failed!"
  echo "Original counts: Users=$USERS_COUNT, Accounts=$ACCOUNTS_COUNT, Trades=$TRADES_COUNT"
  echo "Restored counts: Users=$USERS_AFTER_RESTORE, Accounts=$ACCOUNTS_AFTER_RESTORE, Trades=$TRADES_AFTER_RESTORE"
  TEST_RESULT="FAILED"
fi

echo "Step 7: Cleanup..."
dropdb "$TEST_DB_NAME"

# Calculate test duration
END_TIME=$(date +%s)
START_TIME=$(date -r "$LOG_FILE" +%s)
DURATION=$((END_TIME - START_TIME))

echo
echo "=== Test Summary ==="
echo "Test completed at: $(date)"
echo "Duration: $DURATION seconds"
echo "Result: $TEST_RESULT"
echo "Log file: $LOG_FILE"
echo

# Exit with appropriate status code
if [ "$TEST_RESULT" = "PASSED" ]; then
  exit 0
else
  exit 1
fi