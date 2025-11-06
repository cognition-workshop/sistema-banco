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

### Enterprise Features

* Environment-based configuration with `.env` support
* Structured JSON logging for production
* Custom error handling middleware
* User-friendly error pages in Portuguese (404, 500, 403)
* Comprehensive input validation (client and server-side)
* Health check endpoints (`/health/`, `/health/db/`, `/health/redis/`)
* Performance monitoring with system metrics
* CI/CD pipeline with GitHub Actions
* Automated linting (flake8, black)
* Security checks (bandit, safety)
* Automated testing with pytest
* Migration management documentation
* Database backup scripts


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
+ python-decouple==3.8
+ python-json-logger==2.0.7
+ psutil==5.9.5
+ pytest==7.4.3
+ pytest-django==4.7.0
+ flake8==6.1.0
+ black==23.12.0
+ bandit==1.7.5
+ safety==2.3.5

## Install Redis Server

[Redis Quick Start](https://redis.io/topics/quickstart)

Run Redis server
```bash
redis-server
```

## Environment Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:
- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `REDIS_URL`: Redis server URL

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
