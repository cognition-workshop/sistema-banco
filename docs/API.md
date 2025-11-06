# API Documentation

## Health Check Endpoints

### GET /health/
Basic health check to verify the application is running.

**Response:**
```json
{
  "status": "OK",
  "message": "Sistema bancário está funcionando",
  "timestamp": 1234567890.123
}
```

### GET /readiness/
Readiness check to verify all dependencies are working.

**Response:**
```json
{
  "status": "OK",
  "checks": {
    "database": true,
    "redis": true,
    "overall": true
  },
  "timestamp": 1234567890.123
}
```

## Transaction Endpoints

### POST /transactions/deposit/
Create a deposit transaction.

**Parameters:**
- `amount`: Decimal (required, minimum: 10)
- `transaction_type`: Integer (required, value: 1)

### POST /transactions/withdraw/
Create a withdrawal transaction.

**Parameters:**
- `amount`: Decimal (required, minimum: 10)
- `transaction_type`: Integer (required, value: 2)

**Validation:**
- Amount must not exceed account balance
- Amount must not exceed maximum withdrawal limit

### GET /transactions/report/
View transaction history with optional date range filter.

**Query Parameters:**
- `daterange`: String (optional, format: "YYYY-MM-DD - YYYY-MM-DD")
