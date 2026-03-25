"""
Unit tests for Contact API Routers.

Tests cover:
- POST /contacts/ - Create contact
- GET /contacts/ - List contacts
- GET /contacts/{contact_id} - Get contact
- PUT /contacts/{contact_id} - Update contact
- DELETE /contacts/{contact_id} - Delete contact
- GET /contacts/summaries/ - Get contact summaries
- Input validation (422 errors)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4


class TestCreateContactEndpoint:
    """Tests for POST /contacts/"""

    @patch("app.services.contact.ContactService.create_contact", new_callable=AsyncMock)
    def test_create_contact_success(self, mock_create, client):
        """Successfully create a contact via API."""
        from app.schemas.contact import ContactResponse

        mock_response = ContactResponse(
            id=1,
            name="John Smith",
            email="john@bank.com",
            phone="+1-555-0123",
            company="First National Bank",
            address="123 Main St",
            notes="Loan officer",
            user_id=1,
            workspace_id=client.workspace_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_create.return_value = mock_response

        response = client.post(
            "/contacts/",
            json={
                "name": "John Smith",
                "email": "john@bank.com",
                "phone": "+1-555-0123",
                "company": "First National Bank",
                "address": "123 Main St",
                "notes": "Loan officer",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Smith"
        assert data["email"] == "john@bank.com"

    @patch("app.services.contact.ContactService.create_contact", new_callable=AsyncMock)
    def test_create_contact_minimal(self, mock_create, client):
        """Create contact with only name."""
        from app.schemas.contact import ContactResponse

        mock_response = ContactResponse(
            id=2,
            name="Minimal",
            email=None,
            phone=None,
            company=None,
            address=None,
            notes=None,
            user_id=1,
            workspace_id=client.workspace_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_create.return_value = mock_response

        response = client.post(
            "/contacts/",
            json={"name": "Minimal"},
        )

        assert response.status_code == 201

    def test_create_contact_missing_name(self, client):
        """Reject request without name."""
        response = client.post(
            "/contacts/",
            json={"email": "no-name@test.com"},
        )

        assert response.status_code == 422

    def test_create_contact_empty_name(self, client):
        """Reject empty name."""
        response = client.post(
            "/contacts/",
            json={"name": ""},
        )

        assert response.status_code == 422

    def test_create_contact_name_too_long(self, client):
        """Reject name exceeding 255 characters."""
        response = client.post(
            "/contacts/",
            json={"name": "x" * 256},
        )

        assert response.status_code == 422


class TestGetContactsEndpoint:
    """Tests for GET /contacts/"""

    @patch("app.services.contact.ContactService.get_contacts")
    def test_get_contacts_success(self, mock_get, client):
        """Successfully list contacts."""
        mock_get.return_value = []

        response = client.get("/contacts/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("app.services.contact.ContactService.get_contacts")
    def test_get_contacts_with_pagination(self, mock_get, client):
        """List contacts with pagination parameters."""
        mock_get.return_value = []

        response = client.get("/contacts/?skip=5&limit=10")

        assert response.status_code == 200
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][2] == 5   # skip
        assert call_args[0][3] == 10  # limit

    def test_get_contacts_negative_skip(self, client):
        """Reject negative skip parameter."""
        response = client.get("/contacts/?skip=-1")

        assert response.status_code == 422

    def test_get_contacts_limit_too_large(self, client):
        """Reject limit exceeding 1000."""
        response = client.get("/contacts/?limit=1001")

        assert response.status_code == 422

    def test_get_contacts_limit_zero(self, client):
        """Reject zero limit."""
        response = client.get("/contacts/?limit=0")

        assert response.status_code == 422


class TestGetContactEndpoint:
    """Tests for GET /contacts/{contact_id}"""

    @patch("app.services.contact.ContactService.get_contact")
    def test_get_contact_success(self, mock_get, client):
        """Successfully get a specific contact."""
        from app.schemas.contact import ContactResponse

        mock_response = ContactResponse(
            id=1,
            name="John Smith",
            email="john@bank.com",
            phone=None,
            company=None,
            address=None,
            notes=None,
            user_id=1,
            workspace_id=client.workspace_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_get.return_value = mock_response

        response = client.get("/contacts/1")

        assert response.status_code == 200
        assert response.json()["name"] == "John Smith"

    @patch("app.services.contact.ContactService.get_contact")
    def test_get_contact_not_found(self, mock_get, client):
        """Return 404 for non-existent contact."""
        from app.exceptions import ContactNotFoundError
        mock_get.side_effect = ContactNotFoundError(99999)

        response = client.get("/contacts/99999")

        assert response.status_code == 404


class TestUpdateContactEndpoint:
    """Tests for PUT /contacts/{contact_id}"""

    @patch("app.services.contact.ContactService.update_contact", new_callable=AsyncMock)
    def test_update_contact_success(self, mock_update, client):
        """Successfully update a contact."""
        from app.schemas.contact import ContactResponse

        mock_response = ContactResponse(
            id=1,
            name="Updated Name",
            email="john@bank.com",
            phone=None,
            company=None,
            address=None,
            notes=None,
            user_id=1,
            workspace_id=client.workspace_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_update.return_value = mock_response

        response = client.put(
            "/contacts/1",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @patch("app.services.contact.ContactService.update_contact", new_callable=AsyncMock)
    def test_update_contact_not_found(self, mock_update, client):
        """Return 404 for non-existent contact."""
        from app.exceptions import ContactNotFoundError
        mock_update.side_effect = ContactNotFoundError(99999)

        response = client.put("/contacts/99999", json={"name": "Ghost"})

        assert response.status_code == 404

    def test_update_contact_empty_name(self, client):
        """Reject empty name on update."""
        response = client.put("/contacts/1", json={"name": ""})

        assert response.status_code == 422


class TestDeleteContactEndpoint:
    """Tests for DELETE /contacts/{contact_id}"""

    @patch("app.services.contact.ContactService.delete_contact")
    def test_delete_contact_success(self, mock_delete, client):
        """Successfully delete a contact."""
        mock_delete.return_value = True

        response = client.delete("/contacts/1")

        assert response.status_code == 204

    @patch("app.services.contact.ContactService.delete_contact")
    def test_delete_contact_not_found(self, mock_delete, client):
        """Return 404 for non-existent contact."""
        from app.exceptions import ContactNotFoundError
        mock_delete.side_effect = ContactNotFoundError(99999)

        response = client.delete("/contacts/99999")

        assert response.status_code == 404

    @patch("app.services.contact.ContactService.delete_contact")
    def test_delete_contact_with_debts(self, mock_delete, client):
        """Return 400 when contact has associated debts."""
        from app.exceptions import ContactHasAssociatedDebtsError
        mock_delete.side_effect = ContactHasAssociatedDebtsError(1, 3)

        response = client.delete("/contacts/1")

        assert response.status_code == 400
        data = response.json()
        assert "associated debts" in data["error"]


class TestContactSummariesEndpoint:
    """Tests for GET /contacts/summaries/"""

    @patch("app.services.contact.ContactService.get_contact_summaries")
    def test_get_summaries_success(self, mock_summaries, client):
        """Successfully get contact summaries."""
        from app.schemas.contact import ContactSummary

        mock_summaries.return_value = [
            ContactSummary(
                id=1,
                name="John Smith",
                company="Big Bank",
                debts_count=3,
                total_debt_amount=15000.0,
            ),
        ]

        response = client.get("/contacts/summaries/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "John Smith"
        assert data[0]["debts_count"] == 3

    @patch("app.services.contact.ContactService.get_contact_summaries")
    def test_get_summaries_empty(self, mock_summaries, client):
        """Return empty list when no contacts."""
        mock_summaries.return_value = []

        response = client.get("/contacts/summaries/")

        assert response.status_code == 200
        assert response.json() == []
