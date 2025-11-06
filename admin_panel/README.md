# Admin Panel API

The Admin Panel provides a comprehensive REST API for managing the banking system, monitoring transactions, detecting fraud, and maintaining system health.

## Architecture

The admin panel is built using:
- **Django REST Framework** for API endpoints
- **JWT Authentication** (djangorestframework-simplejwt) for secure access
- **Role-Based Access Control** (Senior Admin, Operational Admin, Viewer)
- **Celery** for asynchronous fraud detection
- **ReportLab** for PDF generation
- **psutil** for system health monitoring

## Key Components

### Models
- `AdminUser`: Extends User with admin-specific fields and role
- `AuditLog`: Records all admin actions for compliance
- `FraudRule`: Configurable fraud detection rules
- `FraudAlert`: Generated alerts from fraud detection
- `SystemHealthMetric`: System health monitoring data

### Fraud Detection

The fraud detection system runs automatically on new transactions and checks against active rules:

1. **Suspicious Withdrawals**: Large amounts or high percentage of account balance
   ```python
   {
     "amount_threshold": 5000,
     "percentage_of_balance": 80
   }
   ```

2. **Unusual Hours**: Transactions during specified time ranges
   ```python
   {
     "start_hour": 22,
     "end_hour": 6
   }
   ```

3. **Repeated Transactions**: Multiple identical transactions in a time window
   ```python
   {
     "time_window_minutes": 30,
     "count_threshold": 3,
     "amount_threshold": 100
   }
   ```

4. **Exceeds Maximum Amount**: Transactions above threshold during restricted hours
   ```python
   {
     "max_amount": 10000,
     "time_restriction_start": 22,
     "time_restriction_end": 6
   }
   ```

### Analytics

The analytics module provides:
- Transaction volume by type (deposit, withdrawal, interest)
- Daily transaction trends
- User statistics (total, active, inactive, balances)
- Fraud statistics (alerts, pending, reviewed)

### System Health Monitoring

Monitors:
- **CPU Usage**: Percentage utilization
- **Memory Usage**: Percentage and absolute values
- **Network**: Bytes sent/received
- **Database**: Response time for health check query
- **Redis**: Cache availability
- **Celery**: Worker status

## Security

- JWT tokens with 1-hour access token lifetime
- Role-based permissions at viewset level
- Audit logging of all admin actions
- IP address tracking for admin actions
- Separate authentication for admin users

## Performance Considerations

- Database query optimization with `select_related` and `prefetch_related`
- Pagination on list endpoints (50 items per page)
- Indexes on frequently queried fields
- Asynchronous fraud detection using Celery
- Health metrics cleanup task to prevent database bloat

## Testing

Comprehensive test suite covering:
- Unit tests for models and utilities
- Integration tests for API endpoints
- Permission tests for authorization
- Fraud detection algorithm tests
- Analytics calculation tests
- Report generation tests

Target: >90% code coverage for business logic

## Deployment Considerations

1. Set strong `SECRET_KEY` in production
2. Configure proper `ALLOWED_HOSTS`
3. Use environment variables for sensitive settings
4. Set up HTTPS for API endpoints
5. Configure CORS if frontend is on different domain
6. Set up monitoring and alerting for health metrics
7. Regular backups of audit logs
8. Rotate JWT secret keys periodically

## Future Enhancements

- Real-time WebSocket updates for fraud alerts
- Machine learning-based fraud detection
- Geographic location-based rules
- Multi-factor authentication for admin users
- Advanced analytics with data visualization
- Scheduled reports via email
- Integration with external fraud detection services
