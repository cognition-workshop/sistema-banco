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

## Environment Setup

The application uses environment variables for configuration. Follow these steps:

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and configure the following variables:

**Required for Development:**
- `SECRET_KEY`: Django secret key (use default for dev, generate new for production)
- `DEBUG`: Set to `True` for development, `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CELERY_BROKER_URL`: Redis connection URL (default: `redis://localhost:6379`)
- `CELERY_RESULT_BACKEND`: Redis connection URL (default: `redis://localhost:6379`)

**Production Security Settings:**
For production deployment, enable these security headers:
- `SECURE_SSL_REDIRECT=True`: Redirect HTTP to HTTPS
- `SESSION_COOKIE_SECURE=True`: Send cookies only over HTTPS
- `CSRF_COOKIE_SECURE=True`: Send CSRF cookies only over HTTPS
- `SECURE_HSTS_SECONDS=31536000`: Enable HSTS for 1 year
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`: Apply HSTS to subdomains

**Note:** The application will work with default values if no `.env` file is present, but you should always create one for production deployments with secure values.

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
