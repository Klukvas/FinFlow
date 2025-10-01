# Debt Service

Microservice for managing user debts and debt payments with contact management.

## Features

- **Debt Management**: Create, read, update, and delete debt accounts
- **Contact Management**: Manage creditors and lenders associated with debts
- **Payment Tracking**: Record and track debt payments with principal/interest breakdown
- **Debt Types**: Support for various debt types (credit cards, loans, mortgages, etc.)
- **Summary Statistics**: Get debt summaries and payment history

## API Endpoints

### Debt Endpoints
- `POST /debts/` - Create a new debt
- `GET /debts/` - Get all debts (with filtering options)
- `GET /debts/{debt_id}` - Get a specific debt
- `PUT /debts/{debt_id}` - Update a debt
- `DELETE /debts/{debt_id}` - Delete a debt
- `GET /debts/summary/` - Get debt summary statistics

### Payment Endpoints
- `POST /debts/{debt_id}/payments/` - Create a debt payment
- `GET /debts/{debt_id}/payments/` - Get all payments for a debt

### Contact Endpoints
- `POST /contacts/` - Create a new contact
- `GET /contacts/` - Get all contacts
- `GET /contacts/{contact_id}` - Get a specific contact
- `PUT /contacts/{contact_id}` - Update a contact
- `DELETE /contacts/{contact_id}` - Delete a contact
- `GET /contacts/summaries/` - Get contact summaries with debt information

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Poetry (recommended) or pip

### Installation

1. **Using Poetry (Recommended)**:
   ```bash
   poetry install
   poetry shell
   ```

2. **Using pip**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Environment Configuration

Create a `.env` file with the following variables:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5433/accounting_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
INTERNAL_SECRET_TOKEN=your-internal-secret-token-here
CORS_ORIGINS=*
```

### Database Setup

1. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

2. **Create initial migration** (if needed):
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```

### Running the Service

1. **Using the startup script**:
   ```bash
   ./startup.sh
   ```

2. **Direct command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
   ```

3. **Using Docker**:
   ```bash
   docker-compose up debt_service
   ```

## API Documentation

Once the service is running, visit:
- **Swagger UI**: http://localhost:8008/docs
- **ReDoc**: http://localhost:8008/redoc

## Testing

Run tests using pytest:
```bash
pytest
```

## Project Structure

```
debt_service/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── routers/         # API endpoints
│   ├── exceptions/      # Custom exceptions
│   ├── utils/           # Utility functions
│   └── main.py          # FastAPI application
├── alembic/             # Database migrations
├── tests/               # Test files
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Poetry configuration
├── alembic.ini          # Alembic configuration
├── dockerfile           # Docker configuration
└── startup.sh           # Startup script
```

## Dependencies

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **PostgreSQL**: Database
- **Uvicorn**: ASGI server

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Use type hints throughout
5. Follow PEP 8 style guidelines