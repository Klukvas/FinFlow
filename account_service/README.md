# Account Service

A microservice for managing user accounts with transaction integration for the accounting application.

## Features

- **Account Management**: CRUD operations for user accounts
- **Account Types**: Support for various account types (cash, bank, crypto, investment, etc.)
- **Multi-Currency**: Support for different currencies
- **Transaction Integration**: Fetch transactions from expense and income services
- **Account Validation**: Validate account ownership and existence
- **Security**: JWT-based authentication and internal service tokens
- **Archiving**: Soft delete functionality for accounts

## Account Types

- `CASH`: Physical cash
- `BANK`: Traditional bank account
- `CRYPTO`: Cryptocurrency wallet
- `INVESTMENT`: Investment account
- `CREDIT`: Credit card or line of credit
- `SAVINGS`: Savings account
- `CHECKING`: Checking account

## API Endpoints

### Public Endpoints (Require Authentication)

- `POST /accounts` - Create a new account
- `GET /accounts` - List user accounts
- `GET /accounts/{account_id}` - Get account details
- `PUT /accounts/{account_id}` - Update account
- `PATCH /accounts/{account_id}/archive` - Archive account
- `GET /accounts/{account_id}/summary` - Get account summary
- `GET /accounts/{account_id}/transactions` - Get account transactions
- `PATCH /accounts/{account_id}/balance` - Update account balance

### Internal Endpoints (For Service-to-Service Communication)

- `GET /internal/accounts/{account_id}/validate` - Validate account ownership
- `GET /internal/accounts/{account_id}` - Get account details for internal use

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/account_service

# External Services
EXPENSE_SERVICE_URL=http://localhost:8003
INCOME_SERVICE_URL=http://localhost:8004
USER_SERVICE_URL=http://localhost:8001

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
INTERNAL_SECRET_TOKEN=your-internal-secret-token-here

# API Settings
API_TITLE=Account Service
API_VERSION=1.0.0
DEBUG=false

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Validation limits
MAX_BALANCE=999999999.99
MAX_NAME_LENGTH=100
MAX_DESCRIPTION_LENGTH=500
MAX_CURRENCY_LENGTH=3

# HTTP Settings
HTTP_TIMEOUT=5.0
HTTP_RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
```

## Database Schema

### Accounts Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Account name |
| type | Enum | Account type |
| currency | String(3) | Currency code (ISO 4217) |
| balance | Float | Account balance |
| description | String(500) | Account description |
| is_active | Boolean | Whether account is active |
| is_archived | Boolean | Whether account is archived |
| owner_id | Integer | User who owns the account |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Running the Service

### Using Docker Compose

```bash
docker-compose up account_service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Integration with Other Services

The account service integrates with:

1. **Expense Service**: Fetches expense transactions for accounts
2. **Income Service**: Fetches income transactions for accounts
3. **User Service**: Validates user authentication

### Cross-Service Validation

When creating expenses or incomes, the client can specify an `account_id`. The expense and income services should validate this account exists and belongs to the user by calling:

```
GET /internal/accounts/{account_id}/validate?user_id={user_id}
X-Internal-Token: {internal_token}
```

## Error Handling

The service provides consistent error responses:

- `400 Bad Request`: Validation errors, archived account operations
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Account ownership errors
- `404 Not Found`: Account not found
- `503 Service Unavailable`: External service errors

## Security

- JWT-based authentication for public endpoints
- Internal service tokens for service-to-service communication
- User isolation (users can only access their own accounts)
- Input validation and sanitization
- Comprehensive logging for security events

## Monitoring

- Health check endpoint: `GET /health`
- Structured logging with operation tracking
- External service call monitoring
- Security event logging
