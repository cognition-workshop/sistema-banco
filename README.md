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

## PySpark Data Transformation

This repository includes a PySpark script that transforms Django model data from the SQLite database into Spark DataFrames. This is useful for data analysis, batch processing, and exporting data to different formats.

### Prerequisites

The PySpark script requires PySpark to be installed. It's included in `requirements.txt`:

```bash
pip install pyspark==3.5.0
```

### Creating Demo Data

Before running the transformation script, populate the database with demo data:

```bash
python create_demo_data.py
```

This creates:
- 2 bank account types (Savings and Current)
- 1 demo user (email: demo@example.com)
- 1 bank account with initial balance
- 1 user address
- 7 sample transactions (deposits and withdrawals)

### Running the Transformation Script

The `spark_transform.py` script reads data from the Django SQLite database and transforms it into Spark DataFrames. It supports three output formats:

#### 1. Console Output (Display DataFrames)

View all tables in the console:

```bash
python spark_transform.py --output console
```

#### 2. Parquet Output (Columnar Format)

Save all tables as Parquet files in the `data/` directory:

```bash
python spark_transform.py --output parquet
```

#### 3. CSV Output

Save all tables as CSV files in the `data/` directory:

```bash
python spark_transform.py --output csv
```

### Processing Specific Tables

You can process specific tables instead of all tables:

```bash
# Process only users and transactions
python spark_transform.py --output console --tables users transactions

# Save only bank account types and user bank accounts as Parquet
python spark_transform.py --output parquet --tables bank_account_types user_bank_accounts
```

### Available Tables

- `users` - User accounts with authentication
- `bank_account_types` - Bank account types with interest rates
- `user_bank_accounts` - User bank accounts with balances
- `user_addresses` - User addresses
- `transactions` - Financial transactions (includes transaction type labels)

List available tables:

```bash
python spark_transform.py --list-tables
```

### Transaction Types

The script automatically adds human-readable labels to transaction types:
- **1 = Deposit** - Funds added to account
- **2 = Withdrawal** - Funds removed from account
- **3 = Interest** - System-generated interest credits

### Output Directory Structure

When using Parquet or CSV output, files are saved in the `data/` directory:

```
data/
├── users.parquet/
├── bank_account_types.parquet/
├── user_bank_accounts.parquet/
├── user_addresses.parquet/
└── transactions.parquet/
```

The `data/` directory is gitignored and won't be committed to the repository.

### Technical Details

- **Database**: Reads from `db.sqlite3` using PySpark's JDBC connector
- **JDBC Driver**: Uses `sqlite-jdbc` (automatically downloaded by PySpark)
- **Django Tables**: Follows Django's naming convention (`{app}_{model_lowercase}`)
- **Standalone**: Script doesn't require Django to be running

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
