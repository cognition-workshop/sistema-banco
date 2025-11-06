# Sistema Banco - Modern Banking System

A Django-based banking system with modern technology stack.

## Technology Stack

- **Backend:** Django 5.0, Django REST Framework 3.14
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Task Queue:** Celery with Redis broker
- **Frontend:** HTMX, Tailwind CSS v4
- **Python:** 3.8+

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js 18 or higher
- Docker and Docker Compose (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sistema-banco
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start database and cache services:
```bash
docker-compose up -d
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Install Node.js dependencies and build CSS:
```bash
npm install
npm run build:css
```

8. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

9. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Development

To watch for CSS changes during development:
```bash
npm run watch:css
```

## API Documentation

REST API is available at `/api/`:
- `/api/users/` - User information
- `/api/accounts/` - Bank account information  
- `/api/transactions/` - Transaction history

All endpoints require authentication. Use session authentication or obtain an API token.

## Features (Updated)

- User registration and authentication
- Bank account management
- Deposit and withdrawal transactions
- Transaction history with date filtering
- REST API for programmatic access
- Redis caching for improved performance
- Modern UI with HTMX and Tailwind CSS v4

## Migration Guide

If upgrading from an older version, see [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for detailed migration instructions.

---

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

+ Python >= 3.7
+ Redis Server
+ Git
+ pip
+ Virtualenv (virtualenvwrapper is recommended)

## Requirements

+ celery==4.4.7
+ Django==3.2
+ django-celery-beat==2.0.0
+ python-dateutil==2.8.1
+ redis==3.5.3

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

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
