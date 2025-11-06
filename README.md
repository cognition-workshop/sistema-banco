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

+ celery==5.5.3
+ Django==5.0
+ django-celery-beat==2.8.1
+ django-redis==5.4.0
+ djangorestframework==3.16.1
+ djangorestframework-simplejwt==5.5.1
+ drf-spectacular==0.29.0
+ psycopg2-binary
+ python-dateutil==2.9.0.post0
+ redis==7.0.1

## Install PostgreSQL

### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

### On macOS:
```bash
brew install postgresql
brew services start postgresql
```

### Setup Database:
```bash
# Create database
sudo -u postgres createdb banking_system_db

# Set password for postgres user (optional for local dev)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

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

## Migrate from SQLite to PostgreSQL

If you have existing data in SQLite (`db.sqlite3`), run the migration script to transfer your data to PostgreSQL:
```bash
python migrate_sqlite_to_postgres.py
```

This script will:
- Create the PostgreSQL database if it doesn't exist
- Export all data from SQLite
- Import data to PostgreSQL preserving foreign key relationships
- Verify data integrity after migration

If you're starting fresh, the migration script will simply set up an empty PostgreSQL database.

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
