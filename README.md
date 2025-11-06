# Sistema Bancário Online v2.0.2

A modern online banking system built with Django, featuring account management, transactions, automated interest calculations, and real-time UI updates with HTMX.

## Technology Stack

- **Backend Framework**: Django 5.0.9
- **Database**: PostgreSQL
- **Cache & Message Broker**: Redis
- **Task Queue**: Celery 5.5.3
- **Frontend**: HTMX, Tailwind CSS
- **API**: Django REST Framework 3.14.0

## Features

### Account Management
- Create and manage bank accounts with email-based authentication
- Multiple bank account types (Savings, Current, etc.)
- Customizable account parameters (interest rates, withdrawal limits)
- User profile management with address information

### Transaction System
- Deposit and withdraw money
- Transaction history with date range filtering
- Real-time balance updates after each transaction
- Transaction type filtering and search
- Balance validation to prevent overdrafts

### Interest Calculation
- Automated monthly interest calculation using Celery scheduled tasks
- Configurable interest rates per account type
- Flexible interest calculation periods (monthly, quarterly, etc.)
- Accurate compound interest calculations

### Performance & Caching
- Redis-based caching for improved performance
- Optimized transaction history queries
- Database indexing for faster lookups

### Modern UI/UX
- Dynamic page updates with HTMX (no full page reloads)
- Responsive design with Tailwind CSS
- Date picker for transaction filtering
- Clean and intuitive interface

## Prerequisites

Ensure you have the following installed on your development machine:

- **Python** >= 3.12
- **PostgreSQL** >= 12
- **Redis Server** >= 4.5
- **Git**
- **pip**
- **virtualenv** or **venv**

## PostgreSQL Setup

1. Install PostgreSQL if not already installed:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql
```

2. Start PostgreSQL service:
```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew services start postgresql
```

3. Create the database and user:
```bash
sudo -u postgres psql
```

Then run these SQL commands:
```sql
CREATE DATABASE banking_system;
CREATE USER banking_user;
ALTER ROLE banking_user SET client_encoding TO 'utf8';
ALTER ROLE banking_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE banking_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE banking_system TO banking_user;
\q
```

**Important:** After creating the user, you need to set a password for `banking_user`. Use the PostgreSQL `ALTER USER` command with the password option (consult PostgreSQL documentation for syntax). Then update the same password in the `PASSWORD` field of `banking_system/settings.py` database configuration.

## Redis Setup

Install and start Redis server:

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS (using Homebrew)
brew install redis
brew services start redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

## Project Installation

1. Clone the repository:
```bash
git clone https://github.com/cognition-workshop/sistema-banco.git
cd sistema-banco
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
python manage.py migrate
```

5. Create a superuser account:
```bash
python manage.py createsuperuser
```

6. (Optional) Create demo data:
```bash
python create_demo_data.py
```

## Running the Application

### Start the Django Development Server

```bash
source venv/bin/activate  # If not already activated
python manage.py runserver 0.0.0.0:8000
```

Access the application at: http://localhost:8000

### Start Celery Worker (for background tasks)

Open a new terminal window:
```bash
cd sistema-banco
source venv/bin/activate
celery -A banking_system worker -l info
```

### Start Celery Beat (for scheduled tasks)

Open another terminal window:
```bash
cd sistema-banco
source venv/bin/activate
celery -A banking_system beat -l info
```

## Development Commands

### Run Lint Check
```bash
python manage.py check
```

### Run Tests
```bash
python manage.py test
```

### Create Migrations
```bash
python manage.py makemigrations
```

### Apply Migrations
```bash
python manage.py migrate
```

## Project Structure

```
sistema-banco/
├── accounts/           # User authentication and bank account management
│   ├── models.py      # User, BankAccountType, UserBankAccount, UserAddress
│   ├── views.py       # Account creation, login, registration views
│   └── forms.py       # User registration and account forms
│
├── transactions/      # Transaction management
│   ├── models.py      # Transaction model
│   ├── views.py       # Deposit, withdraw, transaction report views
│   ├── forms.py       # Transaction forms
│   └── tasks.py       # Celery tasks for interest calculation
│
├── core/              # Core functionality and home page
│   └── views.py       # Home page view
│
├── banking_system/    # Project settings and configuration
│   ├── settings.py    # Django settings
│   ├── urls.py        # URL configuration
│   └── celery.py      # Celery configuration
│
├── templates/         # HTML templates
├── static/            # Static files (CSS, JS, images)
├── requirements.txt   # Python dependencies
└── manage.py          # Django management script
```

## Dependencies

- **celery** 5.5.3 - Distributed task queue
- **Django** 5.0.9 - Web framework
- **django-celery-beat** 2.7.0 - Periodic task scheduler
- **django-redis** 5.0.0 - Redis cache backend
- **djangorestframework** 3.14.0 - API framework
- **python-dateutil** 2.8.2 - Date utilities
- **redis** 4.5.0 - Redis client
- **psycopg2-binary** - PostgreSQL adapter

## Configuration

Key settings in `banking_system/settings.py`:

- **Database**: PostgreSQL (banking_system)
- **Cache**: Redis (localhost:6379/1)
- **Celery Broker**: Redis (localhost:6379)
- **Time Zone**: UTC
- **Account Number Start**: 1000000000
- **Minimum Transaction Amount**: 10

## Admin Panel

Access the Django admin panel at: http://localhost:8000/admin

Use the superuser credentials you created during installation to:
- Manage users and bank accounts
- Configure bank account types and interest rates
- View and manage transactions
- Monitor system settings

## Contributing

This project is part of the Cognition Workshop. For contributions, please follow the standard Git workflow:

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

See LICENSE file for details.
