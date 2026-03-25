import os

# SET ENVIRONMENT VARIABLES BEFORE ANY APP IMPORTS
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-internal-token")
os.environ.setdefault("CATEGORY_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("SUBSCRIPTION_SERVICE_URL", "http://localhost:8080")

import pytest
from datetime import date
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user_id
from app.models.transaction import (
    ParsedTransaction,
    BankType,
    TransactionType,
    PDFParseResponse,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

TEST_USER_ID = 42

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
connection = engine.connect()
Base.metadata.create_all(bind=connection)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=connection
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user_id():
    return TEST_USER_ID


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_current_user_id


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def mock_subscription_client():
    """Mock SubscriptionClient with permissive defaults."""
    with patch(
        "app.routers.pdf_parser.subscription_client"
    ) as mock_client:
        mock_client.check_pdf_upload_limit.return_value = True
        mock_client.check_pdf_records_limit.return_value = True
        mock_client.get_user_features.return_value = {
            "pdf_uploads_per_month": {
                "feature_code": "pdf_uploads_per_month",
                "enabled": True,
                "limit_value": 10,
                "plan_code": "professional",
            },
            "pdf_records_per_upload": {
                "feature_code": "pdf_records_per_upload",
                "enabled": True,
                "limit_value": 100,
                "plan_code": "professional",
            },
        }
        yield mock_client


@pytest.fixture
def mock_upload_repo():
    """Mock PDFUploadRepository."""
    with patch(
        "app.routers.pdf_parser.PDFUploadRepository"
    ) as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo.get_monthly_upload_count.return_value = 0
        mock_repo.create_upload_record.return_value = MagicMock(id=1)
        mock_repo_cls.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def mock_pdf_parser_service():
    """Mock PDFParserService."""
    with patch(
        "app.routers.pdf_parser.pdf_parser_service"
    ) as mock_service:
        yield mock_service


@pytest.fixture
def sample_transactions():
    """Create a list of sample parsed transactions for testing."""
    return [
        ParsedTransaction(
            amount=100.50,
            description="Test payment",
            transaction_date=date(2025, 1, 15),
            transaction_type=TransactionType.EXPENSE,
            bank_type=BankType.MONOBANK,
            raw_text="15.01.2025 | Test payment | MCC:5411 | -100.50",
            confidence_score=0.9,
            mcc_code=5411,
            mcc_category_name="Grocery Stores",
            mcc_category_translation=None,
            category_exists=False,
            category_id=None,
        ),
        ParsedTransaction(
            amount=5000.00,
            description="Salary payment",
            transaction_date=date(2025, 1, 10),
            transaction_type=TransactionType.INCOME,
            bank_type=BankType.MONOBANK,
            raw_text="10.01.2025 | Salary payment | MCC:None | 5000.00",
            confidence_score=0.85,
            mcc_code=None,
            mcc_category_name=None,
            mcc_category_translation=None,
            category_exists=False,
            category_id=None,
        ),
    ]


@pytest.fixture
def sample_parse_response(sample_transactions):
    """Create a sample PDFParseResponse for testing."""
    return PDFParseResponse(
        transactions=sample_transactions,
        bank_detected=BankType.MONOBANK,
        total_transactions=2,
        successful_parses=2,
        failed_parses=0,
        parsing_metadata={
            "file_size": 1024,
            "parsing_method": "monobank_parser",
            "confidence_threshold": 0.7,
        },
    )


@pytest.fixture
def valid_pdf_content():
    """Return minimal valid PDF bytes for testing."""
    return b"%PDF-1.4 fake content for testing"


@pytest.fixture
def valid_xlsx_content():
    """Return minimal valid XLSX (ZIP) bytes for testing."""
    return b"PK\x03\x04 fake xlsx content"


@pytest.fixture
def valid_csv_content():
    """Return minimal valid CSV bytes for testing."""
    return (
        b"Date Requested,Transaction Status,Transaction Type,"
        b"Currency,Transaction Amount,Client,Withdraw Method\n"
        b"2025-01-15 10:00:00,completed,client_payment,EUR,1000.00,ACME Corp,\n"
    )
