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

## Prometheus Metrics

This application exposes Prometheus metrics for monitoring performance and system health.

### Django Metrics (HTTP, Database, Cache)

The Django application exposes metrics at the `/metrics/` endpoint:

```bash
# Access metrics
curl http://127.0.0.1:8000/metrics/
```

**Available Django Metrics:**
- **HTTP Requests:**
  - `django_http_requests_total_by_method_total` - Total HTTP requests by method
  - `django_http_requests_total_by_view_transport_method_total` - Requests by view, transport, method
  - `django_http_requests_latency_seconds` - Request latency histogram
  - `django_http_responses_total_by_status_total` - Responses by status code

- **Database:**
  - `django_db_query_duration_seconds` - Database query duration histogram
  - `django_db_execute_total` - Total database queries executed

- **Migrations:**
  - `django_migrations_applied_total` - Total migrations applied
  - `django_migrations_unapplied_total` - Total unapplied migrations

### Celery Metrics (Tasks, Workers)

For Celery task metrics, you need to run `celery-exporter` as a separate service:

```bash
# Install celery-exporter separately (note: some versions have installation issues)
pip install celery-exporter

# If the above fails, try a specific version that works in your environment
# Note: Versions 1.4.0+ require Rust, some earlier versions have setup.py bugs
# You may need to try different versions or install from a wheel

# Run celery-exporter (in a separate terminal)
celery-exporter --broker-url redis://localhost:6379/0
```

The Celery metrics will be available at `http://localhost:9540/metrics`

**Note:** celery-exporter has known installation issues across multiple versions. If you encounter installation errors:
- Versions 1.4.0+ require Rust toolchain
- Some earlier versions (1.2.x, 1.3.x) have malformed setup.py files
- Consider installing from pre-built wheels or using Docker for celery-exporter

**Available Celery Metrics:**
- `celery_tasks_total` - Number of tasks by state (RECEIVED, PENDING, STARTED, RETRY, FAILURE, REVOKED, SUCCESS)
- `celery_tasks_runtime_seconds` - Task runtime histogram
- `celery_tasks_latency_seconds` - Task latency histogram (time between received and started)
- `celery_workers` - Number of alive workers

### Prometheus Configuration

To scrape these metrics with Prometheus, add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'django-banking-system'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/'

  - job_name: 'celery-tasks'
    static_configs:
      - targets: ['localhost:9540']
```

### Important Notes

- **Django metrics** are automatically collected when the Django application is running
- **Celery metrics** require `celery-exporter` to be running as a separate process
- Both metrics endpoints should be configured in your Prometheus scrape configuration
- For production deployments, ensure both services are properly monitored and restarted on failure

## Images:
![alt text](https://i.imgur.com/FvgmEJL.png)
#
![alt text](https://i.imgur.com/aWzj44Y.png)
