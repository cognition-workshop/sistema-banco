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

## Testing

Run the test suite:
```bash
python manage.py test
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run linting:
```bash
flake8 .
black --check .
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment. The pipeline includes:

- **Linting**: Runs flake8 and black to ensure code quality
- **Testing**: Runs the full test suite with PostgreSQL and Redis services
- **Coverage**: Generates and uploads test coverage reports
- **Deployment**: Automatically deploys to production on merge to master

The CI pipeline runs on:
- All pushes to `master` and `develop` branches
- All pull requests to `master`

### Viewing CI Results

Check the "Actions" tab in GitHub to view CI results. All checks must pass before merging.

## Migration Management

### Running Migrations

```bash
python manage.py migrate
```

### Creating New Migrations

```bash
python manage.py makemigrations
```

### Rolling Back Migrations

Use the rollback script to revert to a specific migration:

```bash
./scripts/rollback_migration.sh <app_name> <migration_name>
```

Examples:
```bash
# Rollback transactions to initial migration
./scripts/rollback_migration.sh transactions 0001_initial

# Rollback accounts to initial migration
./scripts/rollback_migration.sh accounts 0001_initial
```

### Important Migration Notes

- Always create a backup before running migrations in production
- Test migrations in a staging environment first
- Use `--fake` flag carefully - it marks migrations as applied without running them
- Use `--fake-initial` when the database state matches the initial migration

### Migration Dependencies

The migrations have the following dependencies:
1. `accounts.0001_initial` - Creates User and BankAccount models
2. `transactions.0001_initial` - Depends on accounts, creates Transaction model

## Production Deployment

### Environment Variables

Set the following environment variables for production:

- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to `False`
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: PostgreSQL database URL
- `REDIS_URL`: Redis connection URL

### Pre-Deployment Checklist

1. Run all tests: `python manage.py test`
2. Run linting: `flake8 . && black --check .`
3. Check for migrations: `python manage.py makemigrations --check`
4. Collect static files: `python manage.py collectstatic`
5. Review security settings

### Database Setup for Production

Switch from SQLite to PostgreSQL in production by updating `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### Health Check

The application includes a health check endpoint at `/health/` that verifies:
- Database connectivity
- Redis/Celery connectivity

Use this endpoint for monitoring and load balancer health checks.

## Logging

The application uses structured logging with JSON format for production. Logs are written to:
- Console (verbose format)
- File: `logs/banking_system.log` (JSON format, rotated at 15MB, keeps 10 backups)

Log levels by module:
- `django`: INFO
- `transactions`: INFO
- `accounts`: INFO
- `core`: INFO

To view logs:
```bash
tail -f logs/banking_system.log
```

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
