# Sistema Bancário - Solution Architecture

## System Overview

The Online Banking System is a modern, scalable web application built with Django 5.0, designed to handle banking operations with high performance, security, and maintainability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Web Browser                                                          │  │
│  │  • HTMX v2.0.3 (Dynamic interactions)                                │  │
│  │  • Tailwind CSS v4 (Modern, responsive UI)                           │  │
│  │  • HTML5 date inputs                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
└───────────────────────────────────┼──────────────────────────────────────────┘
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Django 5.0.13                                     │  │
│  │  ┌────────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │  │
│  │  │   Web Interface    │  │   REST API       │  │   Admin Panel   │ │  │
│  │  │   (Templates)      │  │   (DRF 3.15.2)   │  │   (Django Admin)│ │  │
│  │  └────────────────────┘  └──────────────────┘  └─────────────────┘ │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │              Business Logic Layer                              │ │  │
│  │  │  • Account Management (accounts app)                           │ │  │
│  │  │  • Transaction Processing (transactions app)                   │ │  │
│  │  │  • Interest Calculation                                        │ │  │
│  │  │  • Form Validation & Business Rules                           │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │              Authentication & Authorization                    │ │  │
│  │  │  • Session Authentication                                      │ │  │
│  │  │  • Token Authentication (DRF)                                  │ │  │
│  │  │  • Permission Classes                                          │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                          │                    │                             │
└──────────────────────────┼────────────────────┼─────────────────────────────┘
                           │                    │
                           ▼                    ▼
         ┌─────────────────────────┐  ┌─────────────────────────┐
         │    CACHE LAYER          │  │   TASK QUEUE            │
         │                         │  │                         │
         │  Redis 5.2.1            │  │  Celery 5.4.0           │
         │  • django-redis 5.4.0   │  │  • Redis Broker         │
         │  • 15-min TTL           │  │  • Periodic Tasks       │
         │  • Query caching        │  │  • Interest Calculation │
         │  • Session storage      │  │  • django-celery-beat   │
         └─────────────────────────┘  └─────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────────────┐
         │           DATA LAYER                        │
         │                                             │
         │  PostgreSQL (psycopg2-binary 2.9.10)       │
         │  ┌───────────────────────────────────────┐ │
         │  │  Tables:                              │ │
         │  │  • auth_user (Users)                  │ │
         │  │  • accounts_bankaccounttype           │ │
         │  │  • accounts_userbankaccount           │ │
         │  │  • accounts_useraddress               │ │
         │  │  • transactions_transaction           │ │
         │  │  • django_celery_beat_*               │ │
         │  └───────────────────────────────────────┘ │
         └─────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer

**Technology:** HTMX v2.0.3 + Tailwind CSS v4

**Responsibilities:**
- Render responsive, modern UI
- Handle user interactions without full page reloads
- Display real-time feedback and validation
- Support mobile and desktop browsers

**Key Features:**
- HTMX enables AJAX requests with minimal JavaScript
- Tailwind CSS v4 provides utility-first styling
- HTML5 date inputs replace jQuery daterangepicker
- Progressive enhancement for accessibility

### 2. Application Layer

**Technology:** Django 5.0.13 + Django REST Framework 3.15.2

**Responsibilities:**
- Handle HTTP requests and routing
- Process business logic
- Enforce authentication and authorization
- Provide both web interface and REST API
- Manage form validation

**Key Components:**

#### Web Interface
- Template-based views for user-facing pages
- Form handling with Django Forms
- Session-based authentication
- HTMX-enhanced interactions

#### REST API
- RESTful endpoints for programmatic access
- Token and session authentication
- Serializers for data validation
- ViewSets for CRUD operations
- API browsability through DRF

#### Business Logic
- **accounts app:**
  - User registration and management
  - Bank account creation and management
  - Account type definitions (Savings, Current)
  - Address management
  
- **transactions app:**
  - Deposit and withdrawal processing
  - Transaction history and reporting
  - Balance calculations
  - Date range filtering
  - Interest rate management

### 3. Cache Layer

**Technology:** Redis 5.2.1 + django-redis 5.4.0

**Responsibilities:**
- Cache frequently accessed data
- Reduce database load
- Improve response times
- Store session data

**Configuration:**
- 15-minute TTL (Time To Live)
- Used for transaction report caching
- Celery task result backend
- Session storage backend

### 4. Task Queue

**Technology:** Celery 5.4.0 + Redis broker + django-celery-beat 2.7.0

**Responsibilities:**
- Process background tasks asynchronously
- Schedule periodic tasks
- Calculate monthly interest
- Handle long-running operations

**Key Tasks:**
- Monthly interest calculation for all accounts
- Scheduled batch operations
- Configurable via Django Admin (django-celery-beat)

### 5. Data Layer

**Technology:** PostgreSQL + psycopg2-binary 2.9.10

**Responsibilities:**
- Store persistent data
- Ensure data integrity
- Support transactions
- Enable complex queries

**Schema:**
- **Users:** Authentication and user profiles
- **BankAccountType:** Account type definitions with interest rates
- **UserBankAccount:** Customer bank accounts with balances
- **UserAddress:** Customer address information
- **Transaction:** All banking transactions (deposits, withdrawals, interest)
- **Celery Beat:** Scheduled task management

## Data Flow

### 1. User Registration Flow
```
Browser → Django Views → Form Validation → PostgreSQL (User + Address)
                                        ↓
                                   Session Created
```

### 2. Deposit/Withdrawal Flow
```
Browser → Django Views → Form Validation → Transaction Creation
                              ↓                    ↓
                      Balance Check          PostgreSQL
                              ↓                    ↓
                      Update Balance         Transaction Record
                              ↓
                      Clear Cache
```

### 3. Transaction Report Flow
```
Browser → Django Views → Check Cache → Return Cached Data
                              ↓
                         Cache Miss
                              ↓
                      Query PostgreSQL → Store in Cache → Return Data
```

### 4. Interest Calculation Flow (Scheduled)
```
Celery Beat → Trigger Task → Calculate Interest for All Accounts
                                        ↓
                              Create Interest Transactions
                                        ↓
                                Update Account Balances
                                        ↓
                                   PostgreSQL
```

### 5. API Request Flow
```
API Client → DRF Views → Authentication → Authorization → Business Logic
                              ↓               ↓                ↓
                         Token/Session   Permissions    Serializers
                                                              ↓
                                                        PostgreSQL
                                                              ↓
                                                      JSON Response
```

## Security Features

1. **Authentication:**
   - Session-based authentication for web interface
   - Token authentication for API access
   - Password hashing with Django's PBKDF2 algorithm

2. **Authorization:**
   - Permission-based access control
   - User-level data isolation (users see only their own accounts)
   - Admin-level permissions for staff users

3. **Data Protection:**
   - CSRF protection on all forms
   - SQL injection prevention via ORM
   - XSS protection via template auto-escaping
   - Input validation at form and serializer levels

4. **Transaction Integrity:**
   - Database transactions for atomic operations
   - Balance validation before withdrawals
   - Transaction history immutability

## Scalability Considerations

1. **Horizontal Scaling:**
   - Stateless application servers (Django)
   - Shared cache layer (Redis)
   - Centralized database (PostgreSQL with replication possible)
   - Distributed task processing (multiple Celery workers)

2. **Performance Optimization:**
   - Database query optimization with select_related and prefetch_related
   - Redis caching for frequently accessed data
   - Connection pooling for database connections
   - Asynchronous task processing

3. **Monitoring & Maintenance:**
   - Django Admin for data management
   - Celery flower for task monitoring (optional)
   - PostgreSQL logging for query analysis
   - Redis monitoring for cache hit rates

## Technology Choices

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Web Framework | Django | 5.0.13 | LTS version, mature ecosystem, ORM, admin panel |
| API Framework | Django REST Framework | 3.15.2 | Industry standard for Django APIs |
| Frontend | HTMX | 2.0.3 | Modern interactions without heavy JS frameworks |
| Styling | Tailwind CSS | v4 | Utility-first, responsive, modern design |
| Database | PostgreSQL | 12+ | Production-grade, ACID compliance, scalability |
| Cache | Redis | 5.2.1 | High performance, widely adopted, multi-purpose |
| Task Queue | Celery | 5.4.0 | Async processing, scheduling, Django integration |
| DB Driver | psycopg2-binary | 2.9.10 | PostgreSQL adapter for Python |
| Cache Integration | django-redis | 5.4.0 | Django cache backend for Redis |
| Task Scheduling | django-celery-beat | 2.7.0 | Database-backed periodic tasks |

## Deployment Considerations

### Development Environment
- SQLite can be used for local development (though PostgreSQL is recommended)
- Redis can run locally
- Celery can run in a separate terminal
- Django development server for testing

### Production Environment
- PostgreSQL with connection pooling
- Redis with persistence and replication
- Multiple Celery workers for task processing
- WSGI server (gunicorn, uWSGI) behind reverse proxy (nginx)
- Static file serving via CDN or web server
- Environment variables for sensitive configuration
- HTTPS/TLS encryption
- Database backups and monitoring

## API Integration Examples

### Authentication
```bash
curl -X POST http://localhost:8000/api/token/ \
  -d "username=user&password=pass"
```

### Get Current User
```bash
curl http://localhost:8000/api/accounts/users/me/ \
  -H "Authorization: Token <token>"
```

### List Bank Accounts
```bash
curl http://localhost:8000/api/accounts/bank-accounts/ \
  -H "Authorization: Token <token>"
```

### Create Deposit
```bash
curl -X POST http://localhost:8000/api/transactions/transactions/deposit/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"account_id": 1, "amount": 100.00}'
```

## Future Enhancements

1. **API Documentation:** Add Swagger/OpenAPI documentation
2. **Monitoring:** Implement application performance monitoring (APM)
3. **Logging:** Structured logging with correlation IDs
4. **Testing:** Add integration and end-to-end tests
5. **CI/CD:** Automated testing and deployment pipeline
6. **Security:** Move secrets to environment variables
7. **Features:** Two-factor authentication, transaction notifications
8. **Analytics:** Business intelligence dashboards

## References

- [MODERNIZATION.md](MODERNIZATION.md) - Detailed modernization process and changes
- [README.md](README.md) - Installation and setup instructions
- Django Documentation: https://docs.djangoproject.com/en/5.0/
- Django REST Framework: https://www.django-rest-framework.org/
- HTMX Documentation: https://htmx.org/
- Celery Documentation: https://docs.celeryproject.org/
