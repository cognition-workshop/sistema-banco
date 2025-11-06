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

## CI/CD Pipeline

This project includes a complete CI/CD pipeline that automatically runs on every push and pull request.

### Pipeline Stages

The pipeline executes the following stages sequentially:

1. **Linting** - Code quality checks using flake8
2. **Testing** - Django tests and database migrations
3. **Security** - Security scanning with bandit and pip-audit
4. **Deploy** - Automatic deployment to Heroku (only on master branch)

### Pipeline Configuration

The pipeline is configured in `.github/workflows/ci-cd.yml` and runs automatically on:
- Push to `master` branch
- Pull requests to `master` branch

Each stage must pass before the next stage runs. If any stage fails, the pipeline stops and deployment is blocked.

### Tools Used

- **flake8**: Python code linting (configured in `.flake8`)
- **bandit**: Security vulnerability scanning (configured in `bandit.yaml`)
- **pip-audit**: Dependency vulnerability checking
- **Django tests**: Runs all project tests with `python manage.py test`

### Deployment

The deploy stage only runs when:
- All previous stages (lint, test, security) pass successfully
- The push is to the `master` branch
- Heroku credentials are configured

#### Heroku Deployment Setup

To enable automatic deployment to Heroku, configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

- `HEROKU_API_KEY`: Your Heroku API key
- `HEROKU_APP_NAME`: Name of your Heroku app
- `HEROKU_EMAIL`: Email associated with your Heroku account

The deployment uses the files:
- `Procfile`: Defines the web dyno command
- `runtime.txt`: Specifies Python version for Heroku

#### Managing Celery Workers on Heroku

The `Procfile` includes commented-out configurations for Celery workers. To run background tasks:

1. Uncomment the worker and beat lines in `Procfile`
2. Add Redis addon to your Heroku app: `heroku addons:create heroku-redis:hobby-dev`
3. Scale the worker dynos: `heroku ps:scale worker=1 beat=1`

### Local Development with CI Tools

You can run the CI checks locally before pushing:

```bash
# Linting
pip install flake8
flake8 .

# Security scanning
pip install bandit pip-audit
bandit -r -c bandit.yaml .
pip-audit -r requirements.txt

# Tests
python manage.py test
```

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
