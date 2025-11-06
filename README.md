# Online Banking System V3.0.0 - Modernized Edition

A modern online banking system built with Django 5.0, Django REST Framework, HTMX, Tailwind CSS v4, PostgreSQL, and Redis. This system provides a comprehensive banking solution with REST API endpoints, real-time caching, and a modern interactive UI.


## Features

### Core Banking Features
* Create Bank Account with user registration
* Deposit & Withdraw Money with validation
* Bank Account Type Support (e.g. Current Account, Savings Account)
* Interest calculation depending on the Bank Account type
* Transaction report with date range filter
* See balance after every transaction in the Transaction Report
* Calculate Monthly Interest Using Celery Scheduled tasks
* More efficient and accurate interest calculation and balance update
* Ability to add Minimum and Maximum Transaction amount restriction

### Modern Technology Stack
* **REST API**: Full-featured REST API with Django REST Framework
* **Modern UI**: HTMX v2.0.3 + Tailwind CSS v4 for interactive, responsive design
* **Database**: PostgreSQL for production-grade data storage
* **Caching**: Redis cache layer for improved performance
* **Task Queue**: Celery with Redis broker for background jobs
* **Comprehensive Testing**: Full unit test coverage for all components


## Prerequisites

Be sure you have the following installed on your development machine:

+ Python >= 3.7
+ PostgreSQL >= 12
+ Redis Server
+ Git
+ pip
+ Virtualenv (virtualenvwrapper is recommended)

## Requirements

+ Django==5.0.13
+ djangorestframework==3.15.2
+ celery==5.4.0
+ django-celery-beat==2.7.0
+ redis==5.2.1
+ python-dateutil==2.9.0
+ psycopg2-binary==2.9.10
+ django-redis==5.4.0

## API Endpoints

The system provides a comprehensive REST API with authentication and full CRUD operations:

### Authentication
* `/api/token/` - Token authentication endpoint
* `/api-auth/` - Session authentication (browsable API)

### Account Management
* `/api/accounts/users/` - User management (list, retrieve)
* `/api/accounts/users/me/` - Current authenticated user profile
* `/api/accounts/bank-accounts/` - Bank account management
* `/api/accounts/account-types/` - Account type information
* `/api/accounts/addresses/` - User address management

### Transaction Management
* `/api/transactions/transactions/` - Transaction history and details
* `/api/transactions/transactions/deposit/` - Perform deposits via API
* `/api/transactions/transactions/withdraw/` - Perform withdrawals via API

**Authentication Methods:**
1. **Session Authentication**: Login via Django's auth system, then access API endpoints
2. **Token Authentication**: POST credentials to `/api/token/` to receive a token, then include `Authorization: Token <token>` header in requests

For detailed API documentation and migration information, see [MODERNIZATION.md](MODERNIZATION.md).

## Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**Create Database:**
```bash
sudo -u postgres createdb banking_system
```

**Configure Database Credentials (optional):**

The system uses environment variables for database configuration. If not set, it defaults to:
```bash
export DB_NAME=banking_system
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432
```

## Install Redis Server

[Redis Quick Start](https://redis.io/topics/quickstart)

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
```

**Run Redis server:**
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

Migrate Database (ensure PostgreSQL is running and configured),
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

Run Celery
(Different Terminal Window with Virtual Environment Activated)
```bash
celery -A banking_system worker -l info

celery -A banking_system beat -l info
```

## Modern Tech Stack

This system has been completely modernized with the following technology stack:

- **Backend Framework:** Django 5.0.13 with Django REST Framework 3.15.2
- **Frontend:** HTMX v2.0.3 + Tailwind CSS v4 (no jQuery dependencies)
- **Database:** PostgreSQL with psycopg2-binary 2.9.10
- **Cache Layer:** Redis 5.2.1 with django-redis 5.4.0 (15-minute TTL)
- **Task Queue:** Celery 5.4.0 with Redis broker and django-celery-beat 2.7.0
- **Testing:** Comprehensive unit tests covering models, forms, views, APIs, and tasks

## Architecture

For a detailed architecture diagram and component overview, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Technical Documentation

For detailed information about the modernization process, migration steps, and technical changes, see [MODERNIZATION.md](MODERNIZATION.md).

### Key Improvements
- **Performance:** Redis caching reduces database queries and improves response times
- **API-First:** RESTful API endpoints enable mobile and third-party integrations
- **Modern UI:** HTMX provides dynamic interactions without heavy JavaScript frameworks
- **Scalability:** PostgreSQL and Redis provide production-grade data management
- **Maintainability:** Django 5.0 LTS ensures long-term support and security updates
- **Testing:** Comprehensive test suite ensures code quality and catches regressions

## Testing

Run the full test suite:
```bash
python manage.py test
```

Test specific apps:
```bash
python manage.py test accounts
python manage.py test transactions
```

Verify Django configuration:
```bash
python manage.py check
```

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
