# Banking System - FastAPI Version

This is a FastAPI conversion of the Django banking system.

## Features

- REST API with JSON responses
- JWT authentication
- SQLAlchemy ORM with SQLite database
- Celery for background tasks (interest calculation)
- Automatic API documentation with Swagger UI

## Installation

1. Install dependencies:
```bash
pip install -r requirements-fastapi.txt
```

2. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your SECRET_KEY
# Generate a secure secret key with: openssl rand -hex 32
nano .env
```

**Important**: Make sure to set a secure `SECRET_KEY` in your `.env` file before running the application.

## Running the Application

### Start FastAPI Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Celery Worker

```bash
celery -A app.tasks.celery_app worker -l info
```

### Start Celery Beat Scheduler

```bash
celery -A app.tasks.celery_app beat -l info
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /accounts/register/` - Register a new user
- `POST /accounts/login/` - Login and get JWT token
- `POST /accounts/logout/` - Logout (client-side token deletion)
- `GET /accounts/me/` - Get current user info
- `GET /accounts/me/account/` - Get current user's bank account

### Transactions
- `POST /transactions/deposit/` - Deposit money (requires authentication)
- `POST /transactions/withdraw/` - Withdraw money (requires authentication)
- `GET /transactions/report/` - Get transaction report with optional date filter (requires authentication)

### General
- `GET /` - API info
- `GET /health` - Health check

## Authentication

All transaction endpoints require JWT authentication. To use them:

1. Register a new user via `POST /accounts/register/`
2. Login via `POST /accounts/login/` to get an access token
3. In Swagger UI, click the "Authorize" button and enter the token
4. Or include the token in requests: `Authorization: Bearer <token>`

## Key Changes from Django Version

1. **Architecture**: Pure REST API with JSON responses (no HTML templates)
2. **Authentication**: JWT-based instead of session-based
3. **ORM**: SQLAlchemy instead of Django ORM
4. **Bug Fix**: Added validation to prevent withdrawals that result in negative balance
5. **Removed**: Demo user bypass - all endpoints now require proper authentication

## Database

The application uses the same SQLite database (`db.sqlite3`) as the Django version. The SQLAlchemy models use the same table names for compatibility.

## Celery Task

The interest calculation task runs on the 1st of every month at midnight (UTC), same as the Django version.
