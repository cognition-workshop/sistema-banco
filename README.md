# Online Banking System V2.0.2

This is an Online Banking Concept created using Django Web Framework.


## Features

### Core Banking Features
* Create Bank Account.
* Deposit & Withdraw Money
* Bank Account Type Support (e.g. Current Account, Savings Account)
* Interest calculation depending on the Bank Account type
* Transaction report with a date range filter 
* See balance after every transaction in the Transaction Report
* Calculate Monthly Interest Using Celery Scheduled tasks
* More efficient and accurate interest calculation and balance update
* Ability to add Minimum and Maximum Transaction amount restriction
* Modern UI with Tailwind CSS

### Admin Panel Features (NEW)
* **JWT Authentication**: Secure authentication for admin users with role-based access control
* **User Management**: Search, view, edit, suspend/reactivate user accounts
* **Transaction Monitoring**: Real-time transaction monitoring with advanced filters
* **Analytics Dashboard**: Transaction volume by type, daily trends, user statistics
* **Fraud Detection**: Configurable fraud detection rules with automatic alerts
  - Suspicious withdrawals (large amounts or high percentage of balance)
  - Unusual hours transactions
  - Repeated transaction patterns
  - Transactions exceeding maximum amounts during restricted hours
* **System Health Monitoring**: CPU, memory, network, database response time, Redis and Celery status
* **Report Generation**: Export transaction and fraud alert reports in CSV and PDF formats
* **Audit Logging**: Complete audit trail of all admin actions


## Prerequisites

Be sure you have the following installed on your development machine:

+ Python >= 3.7
+ Redis Server
+ Git
+ pip
+ Virtualenv (virtualenvwrapper is recommended)

## Requirements

+ celery==4.4.7
+ Django==3.2.9
+ django-celery-beat==2.1.0
+ djangorestframework==3.14.0
+ djangorestframework-simplejwt==5.2.0
+ python-dateutil==2.8.2
+ redis==3.5.3
+ reportlab==3.6.12
+ psutil==5.9.4

## Install Redis Server

[Redis Quick Start](https://redis.io/topics/quickstart)

Run Redis server
```bash
redis-server
```

## Project Installation

To setup a local development environment:

Create a virtual environment in which to install Python pip packages. With [virtualenv](https://pypi.python.org/pypi/virtualenv),
```bash
virtualenv venv            # create a virtualenv
source venv/bin/activate   # activate the Python virtualenv 
```

or with [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/),
```bash
mkvirtualenv -p python3 {{project_name}}   # create and activate environment
workon {{project_name}}   # reactivate existing environment
```

Clone GitHub Project,
```bash
git@github.com:saadmk11/banking-system.git

cd banking-system
```

Install development dependencies,
```bash
pip install -r requirements.txt
```

Migrate Database,
```bash
python manage.py migrate
```

Run the web application locally,
```bash
python manage.py runserver # 127.0.0.1:8000
```

Create Superuser,
```bash
python manage.py createsuperuser
```

Create Admin User for Admin Panel,
```bash
python manage.py create_admin_user admin@example.com --password yourpassword --role SENIOR
```

Create Default Fraud Rules,
```bash
python manage.py create_default_fraud_rules
```

Run Celery
(Different Terminal Window with Virtual Environment Activated)
```bash
celery -A banking_system worker -l info

celery -A banking_system beat -l info
```

## Admin Panel API Documentation

### Authentication

**Obtain JWT Token**
```bash
POST /api/admin/auth/login/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "yourpassword"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "role": "SENIOR",
  "email": "admin@example.com"
}
```

**Refresh Token**
```bash
POST /api/admin/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### User Management

**List Users** (with search and filters)
```bash
GET /api/admin/users/
GET /api/admin/users/?name=John
GET /api/admin/users/?email=john@example.com
GET /api/admin/users/?is_active=true
Authorization: Bearer <access_token>
```

**Get User Details**
```bash
GET /api/admin/users/{id}/
Authorization: Bearer <access_token>
```

**Suspend User** (Senior Admin only)
```bash
POST /api/admin/users/{id}/suspend/
Authorization: Bearer <access_token>
```

**Reactivate User** (Senior Admin only)
```bash
POST /api/admin/users/{id}/reactivate/
Authorization: Bearer <access_token>
```

### Transaction Monitoring

**List Transactions** (with filters)
```bash
GET /api/admin/transactions/
GET /api/admin/transactions/?date_from=2024-01-01
GET /api/admin/transactions/?date_to=2024-12-31
GET /api/admin/transactions/?type=1
GET /api/admin/transactions/?min_amount=100&max_amount=1000
GET /api/admin/transactions/?user_email=john@example.com
Authorization: Bearer <access_token>
```

**Get Transaction Details**
```bash
GET /api/admin/transactions/{id}/
Authorization: Bearer <access_token>
```

### Fraud Detection

**List Fraud Rules**
```bash
GET /api/admin/fraud-rules/
Authorization: Bearer <access_token>
```

**Create Fraud Rule** (Senior Admin only)
```bash
POST /api/admin/fraud-rules/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Large Withdrawal Detection",
  "rule_type": "SUSPICIOUS_WITHDRAWAL",
  "parameters": {
    "amount_threshold": 5000,
    "percentage_of_balance": 80
  },
  "is_active": true,
  "severity": "HIGH"
}
```

**List Fraud Alerts**
```bash
GET /api/admin/fraud-alerts/
GET /api/admin/fraud-alerts/?status=PENDING
Authorization: Bearer <access_token>
```

**Review Fraud Alert**
```bash
POST /api/admin/fraud-alerts/{id}/review/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "REVIEWED",
  "notes": "Investigated and confirmed as legitimate"
}
```

### Analytics

**Transaction Volume by Type**
```bash
GET /api/admin/analytics/transaction_volume/
GET /api/admin/analytics/transaction_volume/?date_from=2024-01-01&date_to=2024-12-31
Authorization: Bearer <access_token>
```

**Daily Trends**
```bash
GET /api/admin/analytics/daily_trends/
GET /api/admin/analytics/daily_trends/?days=30
Authorization: Bearer <access_token>
```

**User Statistics**
```bash
GET /api/admin/analytics/user_statistics/
Authorization: Bearer <access_token>
```

**Fraud Statistics**
```bash
GET /api/admin/analytics/fraud_statistics/
Authorization: Bearer <access_token>
```

### Reports

**Export Transactions**
```bash
GET /api/admin/reports/transactions/?format=csv
GET /api/admin/reports/transactions/?format=pdf
Authorization: Bearer <access_token>
```

**Export Fraud Alerts**
```bash
GET /api/admin/reports/fraud_alerts/
Authorization: Bearer <access_token>
```

### System Health

**Current System Health**
```bash
GET /api/admin/health/current/
Authorization: Bearer <access_token>

Response:
{
  "cpu": {
    "usage_percent": 45.2,
    "status": "HEALTHY"
  },
  "memory": {
    "usage_percent": 62.5,
    "used_mb": 4096.0,
    "total_mb": 8192.0,
    "status": "HEALTHY"
  },
  "database": {
    "response_time_ms": 12.5,
    "status": "HEALTHY"
  },
  "redis": {
    "is_available": true,
    "status": "HEALTHY"
  },
  "celery": {
    "is_available": true,
    "status": "HEALTHY"
  }
}
```

**Health History**
```bash
GET /api/admin/health/history/
GET /api/admin/health/history/?hours=24
Authorization: Bearer <access_token>
```

### Audit Logs

**List Audit Logs** (Senior Admin only)
```bash
GET /api/admin/audit-logs/
GET /api/admin/audit-logs/?action_type=SUSPEND
GET /api/admin/audit-logs/?target_model=User
GET /api/admin/audit-logs/?admin_email=admin@example.com
Authorization: Bearer <access_token>
```

## Admin Roles

* **SENIOR**: Full access to all features including user management, fraud rules, and audit logs
* **OPERATIONAL**: Access to user management, transactions, and fraud alerts
* **VIEWER**: Read-only access to dashboards and reports

## Testing

Run all tests:
```bash
python manage.py test
```

Run specific test modules:
```bash
python manage.py test admin_panel.tests.test_views
python manage.py test admin_panel.tests.test_fraud_detection
```

Check test coverage:
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
