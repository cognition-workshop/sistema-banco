# Online Banking System V2.0.0

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
* **NEW:** Production-ready with comprehensive validation and error handling
* **NEW:** Health check endpoints for monitoring
* **NEW:** Comprehensive test suite (>80% coverage)
* **NEW:** Security configurations for production deployment


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
+ python-dateutil==2.8.2
+ redis==3.5.3
+ django-crispy-forms==2.1
+ crispy-tailwind==0.5.0
+ django-environ==0.11.2
+ coverage==7.3.2
+ flake8==6.1.0
+ black==23.12.0

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

## Running Tests

Run tests with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## Environment Variables

For production deployment, copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

See `docs/DEPLOYMENT.md` for full deployment instructions.

## Health Checks

Monitor application health:
```bash
curl http://localhost:8000/health/
curl http://localhost:8000/readiness/
```

## Code Quality

Run linting and formatting:
```bash
flake8 --exclude=venv,migrations --max-line-length=100
black --check --exclude=venv .
```

## Documentation

- **API Documentation:** See `docs/API.md`
- **Deployment Guide:** See `docs/DEPLOYMENT.md`
- **Changelog:** See `CHANGELOG.md`

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
