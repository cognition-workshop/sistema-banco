# Banking System - Spring Boot 3.5.x Migration

This is a complete rewrite of the Django banking system application using Spring Boot 3.5.x with Java 24.

## Technology Stack

- **Framework**: Spring Boot 3.5.0
- **Java Version**: 24
- **Database**: H2 (in-memory/file-based)
- **Template Engine**: Thymeleaf
- **Security**: Spring Security
- **ORM**: JPA/Hibernate with Jakarta EE
- **Migration Tool**: Flyway
- **Build Tool**: Maven

## Features

- User authentication with demo mode
- Deposit money to bank account
- Withdraw money from bank account
- Transaction reporting with date range filtering
- Automated interest calculation (scheduled task)
- Multiple bank account types (Savings, Current)
- Responsive UI with Tailwind CSS

## Project Structure

```
src/
├── main/
│   ├── java/com/banking/system/
│   │   ├── config/          # Security and app configuration
│   │   ├── constant/        # Constants (TransactionType, Gender)
│   │   ├── controller/      # Web controllers
│   │   ├── dto/             # Data transfer objects
│   │   ├── initializer/     # Demo data initializer
│   │   ├── model/           # JPA entities
│   │   ├── repository/      # Data repositories
│   │   ├── service/         # Business logic services
│   │   └── BankingSystemApplication.java
│   └── resources/
│       ├── db/migration/    # Flyway migration scripts
│       ├── templates/       # Thymeleaf templates
│       │   ├── layout/      # Base layouts (navbar, footer, messages)
│       │   └── transactions/ # Transaction views
│       ├── application.properties
│       └── application-demo.properties
└── test/                    # Unit tests
```

## Running the Application

### Prerequisites

- Java 24 or higher
- Maven 3.8+

### Build

```bash
./mvnw clean install
```

### Run

```bash
./mvnw spring-boot:run
```

The application will start on `http://localhost:8080`

### Demo Mode

The application runs in demo mode by default (`spring.profiles.active=demo`), which:
- Disables authentication (allows direct access)
- Uses a fixed demo user: `demo@example.com`
- Creates sample data on startup

Demo credentials (if authentication is enabled):
- Email: demo@example.com
- Password: demo123

## Key Differences from Django Version

### Models (Entities)

- Django ORM models → JPA entities with Jakarta EE annotations
- `@Entity`, `@Table`, `@OneToOne`, `@ManyToOne`, etc.
- Lombok used for boilerplate reduction (`@Data`, `@NoArgsConstructor`, etc.)

### Views (Controllers)

- Django class-based views → Spring `@Controller`
- Django's `ListView`/`CreateView` → `@GetMapping`/`@PostMapping` methods
- Template rendering via `Model` object

### Templates

- Django template language → Thymeleaf
- `{% extends %}` → `th:replace` with fragments
- `{{ variable }}` → `${variable}`
- `{% url %}` → `@{/path}`

### Authentication

- Django authentication → Spring Security
- Demo mode uses custom `SecurityFilterChain` that permits all requests
- Production mode would use form-based authentication

### Async Tasks

- Celery + Redis → Spring `@Scheduled`
- `@task(name="calculate_interest")` → `@Scheduled(cron = "0 0 0 1 * ?")`
- Runs on first day of each month at midnight

### Database

- Django migrations → Flyway migrations
- SQLite → H2 (similar lightweight database)
- Schema defined in `V1__Initial_schema.sql`

### Configuration

- Django settings.py → application.properties
- Profile-based configuration (demo, production)
- Environment-specific properties

## API Endpoints

- `GET /` - Redirects to transaction report
- `GET /transactions/report` - View all transactions with optional date filtering
- `GET /transactions/deposit` - Deposit form
- `POST /transactions/deposit` - Process deposit
- `GET /transactions/withdraw` - Withdrawal form
- `POST /transactions/withdraw` - Process withdrawal

## Database

The application uses H2 database with file storage at `./data/bankingdb`.

### H2 Console

Access the H2 console at: `http://localhost:8080/h2-console`

Connection details:
- JDBC URL: `jdbc:h2:file:./data/bankingdb`
- Username: `sa`
- Password: (empty)

## Business Logic

### Deposit
- Validates minimum deposit amount ($10)
- Updates account balance
- Sets initial deposit date and interest start date on first deposit
- Creates transaction record

### Withdrawal
- Validates minimum withdrawal amount ($10)
- Validates maximum withdrawal amount (based on account type)
- Updates account balance
- Creates transaction record
- **Note**: Current implementation does not prevent negative balances (same as Django version)

### Interest Calculation
- Scheduled task runs monthly (first day of month)
- Calculates interest based on account type settings
- Updates account balance
- Creates interest transaction records
- Formula: `interest = principal × (1 + (rate/100) / n) - principal`
  - Where `n` = interest_calculation_per_year

## Configuration Properties

| Property | Default | Description |
|----------|---------|-------------|
| `banking.account.starting-number` | 1000000000 | Starting account number |
| `banking.transaction.minimum-deposit` | 10.00 | Minimum deposit amount |
| `banking.transaction.minimum-withdrawal` | 10.00 | Minimum withdrawal amount |
| `banking.demo.enabled` | true | Enable demo mode |
| `banking.demo.user.email` | demo@example.com | Demo user email |

## Development

### Adding New Features

1. Create entity in `model/` package
2. Create repository in `repository/` package
3. Implement business logic in `service/` package
4. Create controller in `controller/` package
5. Create Thymeleaf templates in `templates/`
6. Add Flyway migration if schema changes needed

### Running Tests

```bash
./mvnw test
```

## Migration Notes

This Spring Boot application provides functional equivalence to the original Django application with the following improvements:

1. **Type Safety**: Java's strong typing catches errors at compile time
2. **Performance**: Spring Boot with JPA provides excellent performance
3. **Enterprise Ready**: Built on proven enterprise technologies
4. **Scalability**: Easy to scale with Spring Boot's ecosystem
5. **Maintainability**: Clean separation of concerns with MVC pattern

## License

Same as original Django application.
