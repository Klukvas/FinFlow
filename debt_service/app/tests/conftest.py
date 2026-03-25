"""
Test configuration and fixtures for debt service tests.
"""
import os
import tempfile

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
# This must happen before importing anything from app.*
os.environ["TESTING"] = "1"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("INTERNAL_SECRET_TOKEN", "test-internal-token-for-testing")
os.environ.setdefault("USER_SERVICE_URL", "http://localhost:8000")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("CURRENCY_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("WORKSPACE_SERVICE_URL", "http://localhost:8003")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import create_engine, event, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base
from app.models.debt import Debt, Contact, DebtPayment


# ==================== SQLite UUID Workaround ====================
# PostgreSQL UUID columns cannot be rendered by SQLite.
# We swap them to String(36) and auto-convert UUID <-> str.

class SQLiteUUID(TypeDecorator):
    """Store UUID as a 36-char string in SQLite."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return str(value)  # keep as string for SQLite compat
        return value


_uuid_patched = False


def _patch_uuid_columns_for_sqlite():
    """Replace PostgreSQL UUID column types with SQLiteUUID for testing."""
    global _uuid_patched
    if _uuid_patched:
        return
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PG_UUID):
                column.type = SQLiteUUID()
    _uuid_patched = True


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test using a temp file."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    _patch_uuid_columns_for_sqlite()
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


# ==================== FastAPI Test Client ====================

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden dependencies."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    from shared.auth.dependencies import get_current_user_id, get_workspace_id, verify_internal_token

    test_workspace_id = uuid4()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user_id():
        return 1

    def override_get_workspace_id():
        return test_workspace_id

    def override_verify_internal_token():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_workspace_id] = override_get_workspace_id
    app.dependency_overrides[verify_internal_token] = override_verify_internal_token

    with TestClient(app) as test_client:
        # Store workspace_id on client for test use
        test_client.workspace_id = test_workspace_id
        yield test_client

    app.dependency_overrides.clear()


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_workspace_client():
    """Create a mock WorkspaceClient that authorizes all requests."""
    mock = Mock()
    mock.authorize.return_value = (True, "member")
    return mock


@pytest.fixture
def mock_subscription_client():
    """Create a mock SubscriptionClient."""
    mock = Mock()
    mock.check_limit.return_value = (True, None)
    mock.check_modify_allowed.return_value = True
    mock.get_user_features.return_value = {}
    mock.get_read_only_ids.return_value = set()
    return mock


@pytest.fixture
def mock_user_client():
    """Create a mock UserServiceClient."""
    mock = Mock()
    mock.get_user_base_currency.return_value = "USD"
    return mock


@pytest.fixture
def mock_currency_client():
    """Create a mock CurrencyServiceClient."""
    mock = Mock()
    mock.get_rates.return_value = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}
    mock.convert_amount.return_value = 100.0
    return mock


# ==================== Service Fixtures ====================

@pytest.fixture
def debt_service(db_session, mock_workspace_client, mock_subscription_client, mock_user_client, mock_currency_client):
    """Create DebtService with mocked external dependencies."""
    from app.services.debt import DebtService
    from app.services.contact import ContactService
    from app.utils.logger import get_logger
    from fastapi import HTTPException, status

    service = DebtService.__new__(DebtService)
    service.db = db_session
    service.workspace_client = mock_workspace_client
    service.subscription_client = mock_subscription_client
    service.user_client = mock_user_client
    service.currency_client = mock_currency_client
    service._access_denied_error = lambda msg: HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    service._workspace_mismatch_error = lambda msg: HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    service.logger = get_logger(__name__)

    contact_svc = ContactService.__new__(ContactService)
    contact_svc.db = db_session
    contact_svc.workspace_client = mock_workspace_client
    contact_svc._access_denied_error = lambda msg: HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    contact_svc._workspace_mismatch_error = lambda msg: HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    contact_svc.logger = get_logger(__name__)
    service.contact_service = contact_svc

    return service


@pytest.fixture
def contact_service(db_session, mock_workspace_client):
    """Create ContactService with mocked external dependencies."""
    from app.services.contact import ContactService
    from app.utils.logger import get_logger
    from fastapi import HTTPException, status

    service = ContactService.__new__(ContactService)
    service.db = db_session
    service.workspace_client = mock_workspace_client
    service._access_denied_error = lambda msg: HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    service._workspace_mismatch_error = lambda msg: HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    service.logger = get_logger(__name__)

    return service


# ==================== Data Fixtures ====================

@pytest.fixture
def workspace_id():
    """Return a fixed workspace UUID for tests."""
    return uuid4()


@pytest.fixture
def user_id():
    """Return a fixed user ID for tests."""
    return 1


@pytest.fixture
def sample_contact(db_session, workspace_id, user_id):
    """Create a sample contact in the database."""
    contact = Contact(
        user_id=user_id,
        workspace_id=str(workspace_id),
        name="John Smith",
        email="john@bank.com",
        phone="+1-555-0123",
        company="First National Bank",
        address="123 Main St",
        notes="Primary loan officer",
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture
def sample_debt(db_session, workspace_id, user_id, sample_contact):
    """Create a sample debt in the database."""
    debt = Debt(
        user_id=user_id,
        workspace_id=str(workspace_id),
        contact_id=sample_contact.id,
        name="Credit Card - Visa",
        description="Personal credit card debt",
        debt_type="CREDIT_CARD",
        currency="USD",
        initial_amount=Decimal("5000.00"),
        current_balance=Decimal("5000.00"),
        interest_rate=Decimal("18.99"),
        minimum_payment=Decimal("150.00"),
        start_date=date(2024, 1, 1),
        due_date=date(2025, 1, 1),
        is_active=True,
        is_paid_off=False,
    )
    db_session.add(debt)
    db_session.commit()
    db_session.refresh(debt)
    return debt


@pytest.fixture
def sample_debt_no_contact(db_session, workspace_id, user_id):
    """Create a sample debt without a contact."""
    debt = Debt(
        user_id=user_id,
        workspace_id=str(workspace_id),
        contact_id=None,
        name="Student Loan",
        description="Federal student loan",
        debt_type="STUDENT_LOAN",
        currency="USD",
        initial_amount=Decimal("20000.00"),
        current_balance=Decimal("18000.00"),
        interest_rate=Decimal("4.50"),
        minimum_payment=Decimal("250.00"),
        start_date=date(2023, 6, 1),
        due_date=date(2033, 6, 1),
        is_active=True,
        is_paid_off=False,
    )
    db_session.add(debt)
    db_session.commit()
    db_session.refresh(debt)
    return debt


@pytest.fixture
def paid_off_debt(db_session, workspace_id, user_id):
    """Create a paid-off debt."""
    debt = Debt(
        user_id=user_id,
        workspace_id=str(workspace_id),
        name="Old Car Loan",
        debt_type="AUTO_LOAN",
        currency="USD",
        initial_amount=Decimal("10000.00"),
        current_balance=Decimal("0.00"),
        start_date=date(2022, 1, 1),
        is_active=False,
        is_paid_off=True,
    )
    db_session.add(debt)
    db_session.commit()
    db_session.refresh(debt)
    return debt


@pytest.fixture
def sample_payment(db_session, sample_debt, user_id):
    """Create a sample debt payment."""
    payment = DebtPayment(
        debt_id=sample_debt.id,
        user_id=user_id,
        amount=Decimal("200.00"),
        principal_amount=Decimal("150.00"),
        interest_amount=Decimal("50.00"),
        payment_date=date(2024, 2, 1),
        description="Monthly payment",
        payment_method="TRANSFER",
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def multiple_contacts(db_session, workspace_id, user_id):
    """Create multiple contacts."""
    contacts = []
    for i in range(5):
        contact = Contact(
            user_id=user_id,
            workspace_id=str(workspace_id),
            name=f"Contact {i + 1}",
            email=f"contact{i + 1}@test.com",
            company=f"Company {i + 1}",
        )
        db_session.add(contact)
        contacts.append(contact)
    db_session.commit()
    for c in contacts:
        db_session.refresh(c)
    return contacts


@pytest.fixture
def multiple_debts(db_session, workspace_id, user_id):
    """Create multiple debts with varied attributes."""
    debts = []
    debt_configs = [
        ("Credit Card", "CREDIT_CARD", Decimal("5000"), Decimal("4500"), True, False, "USD"),
        ("Mortgage", "MORTGAGE", Decimal("200000"), Decimal("195000"), True, False, "USD"),
        ("Car Loan", "AUTO_LOAN", Decimal("15000"), Decimal("0"), False, True, "EUR"),
        ("Student Loan", "STUDENT_LOAN", Decimal("30000"), Decimal("28000"), True, False, "GBP"),
    ]
    for name, dtype, initial, balance, active, paid, currency in debt_configs:
        debt = Debt(
            user_id=user_id,
            workspace_id=str(workspace_id),
            name=name,
            debt_type=dtype,
            currency=currency,
            initial_amount=initial,
            current_balance=balance,
            start_date=date(2024, 1, 1),
            is_active=active,
            is_paid_off=paid,
        )
        db_session.add(debt)
        debts.append(debt)
    db_session.commit()
    for d in debts:
        db_session.refresh(d)
    return debts


# ==================== Helper Fixtures ====================

@pytest.fixture
def auth_headers():
    """Return authorization headers for testing."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def internal_headers():
    """Return internal service headers."""
    return {"X-Internal-Token": "test-internal-token-for-testing"}
