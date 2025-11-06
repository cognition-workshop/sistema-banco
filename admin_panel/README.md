# Admin Panel

## Overview

The Admin Panel is a comprehensive administrative interface for the Banking System, providing tools for user management, transaction monitoring, analytics, fraud detection, and system health monitoring.

## Features

### 1. User Management
- **Dashboard**: View all users with pagination and advanced filtering
- **Search**: Search by email or account number
- **Filters**: Filter by account status, balance range, account type
- **Bulk Actions**: Suspend or reactivate multiple accounts
- **User Details**: View complete user profiles with transaction history
- **Edit Users**: Update user information (name, email, address)
- **Export**: Export user data to CSV

### 2. Transaction Monitoring
- **Real-time Metrics**: View today's total, count, and average transaction values
- **Advanced Filters**: Filter by date range, transaction type, amount range
- **Transaction List**: Paginated list with account details
- **Suspicious Transaction Detection**: Automatic alerts for unusual patterns

### 3. Analytics Dashboard
- **KPIs**: User growth rate, average transaction value, active accounts, total balance
- **Charts**: User growth trends, account type distribution, transaction volume by type
- **Top Accounts**: View top 10 accounts by balance
- **Exports**: Generate PDF and CSV reports

### 4. Fraud Detection
- **Fraud Rules**: Configurable rules for detecting suspicious activity
  - High value transactions
  - High frequency transactions
  - Suspicious timing patterns
- **Alert Management**: View and investigate fraud alerts
- **Priority Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Investigation Tracking**: Assign alerts to admins, add notes, mark as resolved
- **Whitelist**: Add trusted accounts to whitelist

### 5. System Health Monitoring
- **Resource Monitoring**: CPU, memory, and disk usage
- **Service Status**: Check Django, Celery, Redis, Database health
- **Health Score**: Overall system health percentage
- **Celery Monitoring**: Track worker status and task queues
- **Error Tracking**: View recent system errors

## Roles and Permissions

### Super Admin
- Full access to all features
- User and account management
- Fraud rule configuration
- System settings access
- All analytics and reports

### Manager
- User management (view, edit, suspend/reactivate)
- Transaction monitoring
- Fraud alert investigation
- Analytics access
- Export reports

### Analyst
- View-only access to analytics
- Transaction monitoring (read-only)
- Fraud alert viewing
- Generate reports

### Support
- User account lookup
- View transaction history
- Limited edit capabilities
- Basic reporting

## Installation

1. The admin_panel app is already added to INSTALLED_APPS in settings.py
2. Run migrations:
```bash
python manage.py makemigrations admin_panel
python manage.py migrate
```

3. Create an admin user and set their role:
```bash
python manage.py createsuperuser
```

4. In Django admin or shell, update the user's role:
```python
from accounts.models import User
user = User.objects.get(email='admin@example.com')
user.role = 'SUPER_ADMIN'
user.save()
```

## Access

- URL: http://localhost:8000/admin-portal/
- Login URL: http://localhost:8000/admin-portal/login/

## Security

- All admin actions are logged in AdminAuditLog
- Middleware validates admin permissions on all requests
- IP addresses are recorded for audit trail
- Regular users cannot access admin panel
- Session-based authentication

## Models

### FraudRule
Defines rules for detecting fraudulent activity:
- `name`: Rule name
- `rule_type`: HIGH_VALUE, HIGH_FREQUENCY, SUSPICIOUS_TIMING
- `threshold_value`: For high value rules
- `time_window_minutes`: For frequency rules
- `is_active`: Enable/disable rule

### FraudAlert
Records detected suspicious activity:
- `account`: Related bank account
- `rule`: Fraud rule that triggered alert
- `severity`: LOW, MEDIUM, HIGH, CRITICAL
- `status`: PENDING, INVESTIGATING, RESOLVED, FALSE_POSITIVE
- `investigated_by`: Admin handling the case
- `notes`: Investigation notes

### AdminAuditLog
Tracks all administrative actions:
- `user`: Admin who performed action
- `action`: Description of action
- `target_model`: Model affected (if applicable)
- `ip_address`: IP address of request
- `timestamp`: When action occurred

### AccountWhitelist
Trusted accounts exempt from certain fraud checks:
- `account`: Whitelisted account
- `reason`: Justification for whitelisting
- `added_by`: Admin who added to whitelist

## API Endpoints

All endpoints require admin authentication:

- `/admin-portal/` - Main dashboard
- `/admin-portal/login/` - Admin login
- `/admin-portal/logout/` - Admin logout
- `/admin-portal/users/` - Users dashboard
- `/admin-portal/users/<id>/` - User detail
- `/admin-portal/users/<id>/edit/` - Edit user
- `/admin-portal/users/bulk-action/` - Bulk user actions
- `/admin-portal/users/export/` - Export users CSV
- `/admin-portal/transactions/` - Transactions dashboard
- `/admin-portal/analytics/` - Analytics dashboard
- `/admin-portal/analytics/export/` - Export analytics
- `/admin-portal/fraud/` - Fraud dashboard
- `/admin-portal/fraud/alerts/<id>/` - Fraud alert detail
- `/admin-portal/health/` - System health dashboard

## Testing

Run tests:
```bash
python manage.py test admin_panel
```

Test coverage includes:
- Authentication and authorization
- Middleware permission checks
- Model creation and validation
- View access control
- Audit log creation

## Dependencies

- Django 3.2+
- psutil (for system monitoring)
- reportlab (for PDF exports)
- Chart.js (frontend charts)
- DataTables (interactive tables)
- Tailwind CSS (styling)

## Troubleshooting

### Cannot access admin panel
- Ensure user has admin role (not REGULAR_USER)
- Check middleware is in MIDDLEWARE list in settings.py
- Verify user is authenticated

### Charts not displaying
- Check JavaScript console for errors
- Ensure Chart.js is loading from CDN
- Verify data is being passed to templates

### Export not working
- Check file permissions
- Verify reportlab is installed
- Check for sufficient disk space

### Health monitoring showing errors
- Ensure psutil is installed
- Check service configurations (Redis, Celery)
- Verify database connectivity

## Future Enhancements

- Email alerts for critical fraud cases
- Advanced fraud detection with machine learning
- Real-time dashboard updates with WebSockets
- Custom report builder
- Role-based field-level permissions
- Two-factor authentication for admin access
- API for external integrations
