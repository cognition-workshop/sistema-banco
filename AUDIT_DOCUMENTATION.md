# Audit Logging System Documentation

## Overview
This banking system implements a comprehensive, immutable audit logging mechanism that tracks all balance-changing operations with cryptographic verification.

## Features

### 1. Immutability
- Transactions cannot be modified after creation
- Transactions cannot be deleted (only soft-deleted with `is_deleted` flag)
- Database-level protection via model constraints using `PROTECT` on foreign keys

### 2. Cryptographic Integrity
- Each transaction has a SHA-256 hash of its data
- Transactions are chained: each transaction references the hash of the previous one
- Hash chain can be verified to detect tampering

### 3. Comprehensive Audit Trail
- **Who**: User who initiated the transaction (or SYSTEM for automated tasks)
- **When**: Precise timestamp (microsecond precision)
- **What**: Transaction type (Deposit, Withdrawal, Interest)
- **Where**: IP address of the request
- **Before/After**: Previous and current balance captured
- **Metadata**: Additional context (user agent, request method, etc.)

## Architecture

### Data Model
```
Transaction:
  - id (PK)
  - account (FK to UserBankAccount, PROTECT)
  - user (FK to User, PROTECT, nullable for system operations)
  - amount
  - previous_balance
  - balance_after_transaction
  - transaction_type (Deposit/Withdrawal/Interest)
  - timestamp
  - ip_address
  - previous_hash (links to previous transaction)
  - current_hash (SHA-256 of this transaction)
  - is_deleted (soft delete flag)
  - metadata (JSON with additional audit info)
```

### Hash Calculation
```python
hash_data = {
    'account_id': transaction.account_id,
    'amount': str(transaction.amount),
    'previous_balance': str(transaction.previous_balance),
    'balance_after_transaction': str(transaction.balance_after_transaction),
    'transaction_type': transaction.transaction_type,
    'timestamp': transaction.timestamp.isoformat(),
    'user_id': transaction.user_id or 'SYSTEM',
    'previous_hash': transaction.previous_hash or '',
}
current_hash = SHA256(JSON.stringify(hash_data))
```

## Querying Audit Logs

### Basic Queries
```python
# Get all transactions for a user
Transaction.audit.for_user(user)

# Get all transactions for an account
Transaction.audit.for_account(account)

# Get transactions by date range
Transaction.audit.by_date_range(start_date, end_date)

# Get transactions by type
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
Transaction.audit.by_type(DEPOSIT)
```

### Advanced Queries
```python
# Find suspicious activity (5+ withdrawals in 24 hours)
Transaction.audit.suspicious_activity()

# Verify all hashes
invalid_txs = Transaction.audit.verify_all_hashes()
```

## Verification Procedures

### Verify Single Transaction
```python
transaction = Transaction.objects.get(id=123)

# Verify hash matches data
is_valid = transaction.verify_hash_integrity()

# Verify chain links to previous transaction
is_chained = transaction.verify_chain_integrity()
```

### Verify Entire Chain
```python
for account in UserBankAccount.objects.all():
    transactions = Transaction.audit.for_account(account).order_by('timestamp')
    for tx in transactions:
        if not tx.verify_hash_integrity():
            print(f"ALERT: Transaction {tx.id} has invalid hash!")
        if not tx.verify_chain_integrity():
            print(f"ALERT: Transaction {tx.id} has broken chain!")
```

## Compliance Notes

### Regulatory Requirements
- ✅ All balance changes are logged
- ✅ Logs include user identification
- ✅ Logs include timestamps with microsecond precision
- ✅ Logs are immutable (cannot be modified or deleted)
- ✅ Logs can be searched efficiently
- ✅ Integrity can be cryptographically verified

### External Audit
For external auditors:
1. Export full transaction history: `python manage.py dumpdata transactions.Transaction > audit_export.json`
2. Verify hash chain integrity: See verification procedures above
3. Query by date range, user, or account as needed
4. All administrative actions are logged in Django's audit trail

## Performance Considerations

### Indexing
The following indexes are automatically created:
- (user, timestamp)
- (account, timestamp)
- (transaction_type, timestamp)
- (timestamp)

### Partitioning (Future Enhancement)
For systems with millions of transactions, consider monthly partitioning:
```sql
-- Example for PostgreSQL
CREATE TABLE transactions_2024_01 PARTITION OF transactions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Security Best Practices

1. **Access Control**: Only authorized personnel should have access to audit logs
2. **Export Security**: Use encrypted exports for external audits
3. **System User**: The SYSTEM user (for automated tasks) cannot login (is_active=False)
4. **IP Logging**: All user-initiated transactions log IP addresses
5. **Metadata**: Additional context captured for forensic analysis
6. **PROTECT on Delete**: Foreign keys use PROTECT to prevent cascading deletions

## Balance-Changing Operations

All operations that modify account balances are captured:

1. **Deposits** (`transactions.views.DepositMoneyView`)
   - User-initiated via web interface
   - Captures user, IP, and metadata

2. **Withdrawals** (`transactions.views.WithdrawMoneyView`)
   - User-initiated via web interface
   - Validates sufficient balance
   - Captures user, IP, and metadata

3. **Interest Calculation** (`transactions.tasks.calculate_interest`)
   - System-initiated via Celery scheduled task
   - Runs monthly based on account type
   - Uses system user (system@banco.internal)

## Maintenance

### Monthly Tasks
1. Verify hash chain integrity for all accounts
2. Review suspicious activity reports
3. Archive old transactions (if needed)

### Annual Tasks
1. Full audit export for compliance
2. Performance optimization review
3. Storage capacity planning

## Testing

Run the comprehensive test suite:
```bash
# Run all tests
python manage.py test transactions

# Run with coverage
coverage run --source='.' manage.py test transactions
coverage report --omit='*/tests.py,*/migrations/*'
```

Test coverage should be ≥95%.

## Migration from Existing System

The new audit fields are added to the existing Transaction model:
- Existing transactions will have NULL values for new audit fields
- System will create a migration that adds all new fields
- New transactions will automatically populate all audit fields
- Consider backfilling existing transactions with system user if needed

## Admin Interface

The Django admin interface provides read-only access to audit logs:
- Cannot create transactions manually through admin
- Cannot delete transactions through admin
- Can view hash verification status with color coding
- Can search by account, user, or IP address
- Can filter by transaction type, date, and deletion status
