# Online Banking System V2.0.2

This is an Online Banking Concept created using Django Web Framework.


## Features

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


## Prerequisites

Be sure you have the following installed on your development machine:

+ Python >= 3.10
+ Redis Server
+ Git
+ pip
+ Virtualenv (virtualenvwrapper is recommended)

## Requirements

+ celery==5.4.0
+ Django==5.0.10
+ django-celery-beat==2.7.0
+ djangorestframework==3.15.2
+ python-dateutil==2.9.0
+ redis==5.2.0
+ psycopg[binary]==3.2.3
+ dj-database-url==2.2.0
+ python-decouple==3.8

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

Run Celery
(Different Terminal Window with Virtual Environment Activated)
```bash
celery -A banking_system worker -l info

celery -A banking_system beat -l info
```

## Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database Configuration (optional - defaults to SQLite)
DATABASE_URL=postgresql://user:password@localhost:5432/banking_system

# Redis Configuration
REDIS_URL=redis://localhost:6379/1
```

## PostgreSQL Setup (Production)

For production environments, use PostgreSQL instead of SQLite:

1. Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. Create database and user:
```bash
sudo -u postgres psql
CREATE DATABASE banking_system;
CREATE USER banking_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE banking_system TO banking_user;
\q
```

3. Set DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://banking_user:your_password@localhost:5432/banking_system"
```

4. Run migrations:
```bash
python manage.py migrate
```

## API Endpoints

The system now includes RESTful API endpoints with full CRUD operations:

### Account Types
- `GET /api/account-types/` - List all account types
- `POST /api/account-types/` - Create new account type
- `GET /api/account-types/{id}/` - Retrieve account type details
- `PUT /api/account-types/{id}/` - Update account type
- `DELETE /api/account-types/{id}/` - Delete account type

### Bank Accounts
- `GET /api/accounts/` - List all bank accounts
- `POST /api/accounts/` - Create new bank account
- `GET /api/accounts/{id}/` - Retrieve account details
- `PUT /api/accounts/{id}/` - Update account
- `DELETE /api/accounts/{id}/` - Delete account
- `GET /api/accounts/{id}/balance/` - Get account balance

### Users
- `GET /api/users/` - List all users
- `POST /api/users/` - Create new user
- `GET /api/users/{id}/` - Retrieve user details
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user

### Transactions
- `GET /api/transactions/` - List all transactions
- `POST /api/transactions/` - Create new transaction
- `GET /api/transactions/{id}/` - Retrieve transaction details
- `PUT /api/transactions/{id}/` - Update transaction
- `DELETE /api/transactions/{id}/` - Delete transaction

Browse the interactive API documentation at: http://localhost:8000/api/

## Redis Caching

Redis is now used for both Celery message broker and Django caching. The cache timeout is set to 5 minutes by default and can be configured in settings.

## Modern Frontend

The system now uses:
- **HTMX 2.0** - Modern interactivity without jQuery
- **Tailwind CSS v4** - Latest utility-first CSS framework
- **Native HTML5 date inputs** - No external date picker libraries needed

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
