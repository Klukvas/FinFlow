"""
Unit tests for ContactService business logic.

Tests cover:
- Contact CRUD operations
- Contact summaries with debt info
- Authorization checks
- Error handling
- Edge cases
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.services.contact import ContactService
from app.models.debt import Contact, Debt
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.exceptions import (
    ContactNotFoundError,
    ContactCreationFailedError,
    ContactUpdateFailedError,
    ContactDeletionFailedError,
    ContactHasAssociatedDebtsError,
)


class TestCreateContact:
    """Tests for ContactService.create_contact()"""

    @pytest.mark.asyncio
    async def test_create_contact_success(self, contact_service, workspace_id, user_id):
        """Successfully create a contact with all fields."""
        contact_data = ContactCreate(
            name="Jane Doe",
            email="jane@example.com",
            phone="+1-555-9876",
            company="ABC Finance",
            address="456 Oak Ave",
            notes="Secondary contact",
        )

        result = await contact_service.create_contact(contact_data, user_id, workspace_id)

        assert result.name == "Jane Doe"
        assert result.email == "jane@example.com"
        assert result.phone == "+1-555-9876"
        assert result.company == "ABC Finance"
        assert result.address == "456 Oak Ave"
        assert result.notes == "Secondary contact"
        assert result.user_id == user_id
        assert result.workspace_id == workspace_id

    @pytest.mark.asyncio
    async def test_create_contact_minimal(self, contact_service, workspace_id, user_id):
        """Create a contact with only required name field."""
        contact_data = ContactCreate(name="Minimal Contact")

        result = await contact_service.create_contact(contact_data, user_id, workspace_id)

        assert result.name == "Minimal Contact"
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.address is None
        assert result.notes is None

    @pytest.mark.asyncio
    async def test_create_contact_workspace_authorization(self, contact_service, workspace_id, user_id):
        """Verify workspace authorization is called."""
        contact_data = ContactCreate(name="Auth Check")

        await contact_service.create_contact(contact_data, user_id, workspace_id)

        contact_service.workspace_client.authorize.assert_called_with(
            workspace_id, user_id, "member"
        )

    @pytest.mark.asyncio
    async def test_create_contact_db_error_raises(self, contact_service, workspace_id, user_id):
        """Database error raises ContactCreationFailedError."""
        contact_data = ContactCreate(name="DB Error Contact")

        original_add = contact_service.db.add
        contact_service.db.add = lambda x: (_ for _ in ()).throw(RuntimeError("DB error"))

        with pytest.raises(ContactCreationFailedError):
            await contact_service.create_contact(contact_data, user_id, workspace_id)

        contact_service.db.add = original_add


class TestGetContacts:
    """Tests for ContactService.get_contacts()"""

    def test_get_contacts_returns_all(self, contact_service, workspace_id, user_id, multiple_contacts):
        """Get all contacts in workspace."""
        contacts = contact_service.get_contacts(user_id, workspace_id)

        assert len(contacts) == 5

    def test_get_contacts_empty_workspace(self, contact_service, user_id):
        """Return empty list for workspace with no contacts."""
        empty_ws = uuid4()
        contacts = contact_service.get_contacts(user_id, empty_ws)

        assert contacts == []

    def test_get_contacts_pagination_skip(self, contact_service, workspace_id, user_id, multiple_contacts):
        """Skip pagination works."""
        contacts = contact_service.get_contacts(user_id, workspace_id, skip=3)

        assert len(contacts) == 2

    def test_get_contacts_pagination_limit(self, contact_service, workspace_id, user_id, multiple_contacts):
        """Limit pagination works."""
        contacts = contact_service.get_contacts(user_id, workspace_id, limit=2)

        assert len(contacts) == 2

    def test_get_contacts_isolates_workspaces(self, contact_service, db_session, user_id):
        """Contacts from different workspaces are isolated."""
        ws1 = uuid4()
        ws2 = uuid4()

        c1 = Contact(user_id=user_id, workspace_id=ws1, name="Contact in WS1")
        c2 = Contact(user_id=user_id, workspace_id=ws2, name="Contact in WS2")
        db_session.add_all([c1, c2])
        db_session.commit()

        contacts_ws1 = contact_service.get_contacts(user_id, ws1)
        contacts_ws2 = contact_service.get_contacts(user_id, ws2)

        assert len(contacts_ws1) == 1
        assert contacts_ws1[0].name == "Contact in WS1"
        assert len(contacts_ws2) == 1
        assert contacts_ws2[0].name == "Contact in WS2"


class TestGetContact:
    """Tests for ContactService.get_contact()"""

    def test_get_contact_success(self, contact_service, workspace_id, user_id, sample_contact):
        """Get a specific contact by ID."""
        result = contact_service.get_contact(sample_contact.id, user_id, workspace_id)

        assert result.id == sample_contact.id
        assert result.name == "John Smith"
        assert result.email == "john@bank.com"

    def test_get_contact_not_found(self, contact_service, workspace_id, user_id):
        """Raise error when contact does not exist."""
        with pytest.raises(ContactNotFoundError):
            contact_service.get_contact(99999, user_id, workspace_id)

    def test_get_contact_wrong_workspace(self, contact_service, user_id, sample_contact):
        """Raise error when contact belongs to different workspace."""
        other_ws = uuid4()
        with pytest.raises(ContactNotFoundError):
            contact_service.get_contact(sample_contact.id, user_id, other_ws)


class TestUpdateContact:
    """Tests for ContactService.update_contact()"""

    @pytest.mark.asyncio
    async def test_update_contact_name(self, contact_service, workspace_id, user_id, sample_contact):
        """Update contact name."""
        update = ContactUpdate(name="Updated Name")

        result = await contact_service.update_contact(sample_contact.id, update, user_id, workspace_id)

        assert result.name == "Updated Name"
        # Other fields unchanged
        assert result.email == "john@bank.com"

    @pytest.mark.asyncio
    async def test_update_contact_multiple_fields(self, contact_service, workspace_id, user_id, sample_contact):
        """Update multiple contact fields."""
        update = ContactUpdate(
            name="New Name",
            email="new@email.com",
            phone="+1-555-0000",
            company="New Bank",
        )

        result = await contact_service.update_contact(sample_contact.id, update, user_id, workspace_id)

        assert result.name == "New Name"
        assert result.email == "new@email.com"
        assert result.phone == "+1-555-0000"
        assert result.company == "New Bank"

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, contact_service, workspace_id, user_id):
        """Raise error when updating non-existent contact."""
        update = ContactUpdate(name="Ghost")

        with pytest.raises(ContactNotFoundError):
            await contact_service.update_contact(99999, update, user_id, workspace_id)

    @pytest.mark.asyncio
    async def test_update_contact_partial(self, contact_service, workspace_id, user_id, sample_contact):
        """Partial update only changes specified fields."""
        update = ContactUpdate(notes="Updated notes only")

        result = await contact_service.update_contact(sample_contact.id, update, user_id, workspace_id)

        assert result.notes == "Updated notes only"
        assert result.name == "John Smith"  # Unchanged
        assert result.email == "john@bank.com"  # Unchanged


class TestDeleteContact:
    """Tests for ContactService.delete_contact()"""

    def test_delete_contact_success(self, contact_service, workspace_id, user_id, db_session):
        """Successfully delete a contact with no debts."""
        contact = Contact(
            user_id=user_id,
            workspace_id=workspace_id,
            name="To Delete",
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)
        contact_id = contact.id

        result = contact_service.delete_contact(contact_id, user_id, workspace_id)

        assert result is True

        # Verify deletion
        with pytest.raises(ContactNotFoundError):
            contact_service.get_contact(contact_id, user_id, workspace_id)

    def test_delete_contact_with_debts_raises(self, contact_service, workspace_id, user_id, sample_contact, sample_debt):
        """Cannot delete contact that has associated debts."""
        with pytest.raises(ContactHasAssociatedDebtsError) as exc_info:
            contact_service.delete_contact(sample_contact.id, user_id, workspace_id)

        assert "associated debts" in str(exc_info.value.message)

    def test_delete_contact_not_found(self, contact_service, workspace_id, user_id):
        """Raise error when deleting non-existent contact."""
        with pytest.raises(ContactNotFoundError):
            contact_service.delete_contact(99999, user_id, workspace_id)

    def test_delete_contact_wrong_workspace(self, contact_service, user_id, sample_contact):
        """Raise error when contact belongs to different workspace."""
        other_ws = uuid4()
        with pytest.raises(ContactNotFoundError):
            contact_service.delete_contact(sample_contact.id, user_id, other_ws)


class TestGetContactSummaries:
    """Tests for ContactService.get_contact_summaries()"""

    def test_summaries_with_debts(self, contact_service, workspace_id, user_id, sample_contact, sample_debt):
        """Summaries include debt information."""
        summaries = contact_service.get_contact_summaries(user_id, workspace_id)

        assert len(summaries) == 1
        assert summaries[0].name == "John Smith"
        assert summaries[0].debts_count == 1
        assert summaries[0].total_debt_amount > 0

    def test_summaries_no_debts(self, contact_service, workspace_id, user_id, sample_contact):
        """Summaries for contacts with no debts show zero."""
        summaries = contact_service.get_contact_summaries(user_id, workspace_id)

        assert len(summaries) == 1
        assert summaries[0].debts_count == 0
        assert summaries[0].total_debt_amount == 0

    def test_summaries_empty(self, contact_service, user_id):
        """Return empty list when no contacts exist."""
        empty_ws = uuid4()
        summaries = contact_service.get_contact_summaries(user_id, empty_ws)

        assert summaries == []

    def test_summaries_multiple_contacts_with_debts(
        self, contact_service, workspace_id, user_id, db_session
    ):
        """Multiple contacts each with their own debts."""
        c1 = Contact(user_id=user_id, workspace_id=workspace_id, name="Contact A")
        c2 = Contact(user_id=user_id, workspace_id=workspace_id, name="Contact B")
        db_session.add_all([c1, c2])
        db_session.flush()

        d1 = Debt(
            user_id=user_id, workspace_id=workspace_id, contact_id=c1.id,
            name="Debt A", debt_type="LOAN", currency="USD",
            initial_amount=Decimal("1000"), current_balance=Decimal("800"),
            start_date=date(2024, 1, 1), is_active=True,
        )
        d2 = Debt(
            user_id=user_id, workspace_id=workspace_id, contact_id=c2.id,
            name="Debt B1", debt_type="LOAN", currency="USD",
            initial_amount=Decimal("2000"), current_balance=Decimal("1500"),
            start_date=date(2024, 1, 1), is_active=True,
        )
        d3 = Debt(
            user_id=user_id, workspace_id=workspace_id, contact_id=c2.id,
            name="Debt B2", debt_type="LOAN", currency="USD",
            initial_amount=Decimal("3000"), current_balance=Decimal("2500"),
            start_date=date(2024, 1, 1), is_active=True,
        )
        db_session.add_all([d1, d2, d3])
        db_session.commit()

        summaries = contact_service.get_contact_summaries(user_id, workspace_id)

        assert len(summaries) == 2
        summary_map = {s.name: s for s in summaries}

        assert summary_map["Contact A"].debts_count == 1
        assert float(summary_map["Contact A"].total_debt_amount) == 800.0

        assert summary_map["Contact B"].debts_count == 2
        assert float(summary_map["Contact B"].total_debt_amount) == 4000.0


class TestGetContactById:
    """Tests for ContactService.get_contact_by_id() (internal)"""

    def test_get_contact_by_id_success(self, contact_service, workspace_id, user_id, sample_contact):
        """Successfully get contact model by ID."""
        result = contact_service.get_contact_by_id(sample_contact.id, user_id)

        assert result.id == sample_contact.id
        assert isinstance(result, Contact)

    def test_get_contact_by_id_not_found(self, contact_service, user_id):
        """Raise error when contact ID does not exist."""
        with pytest.raises(ContactNotFoundError):
            contact_service.get_contact_by_id(99999, user_id)

    def test_get_contact_by_id_wrong_user(self, contact_service, sample_contact):
        """Raise error when user does not own the contact."""
        with pytest.raises(ContactNotFoundError):
            contact_service.get_contact_by_id(sample_contact.id, 99999)
