"""
Tests for CategorySerializer.

These tests verify that the CategorySerializer properly validates data
and provides consistent serialization across different operations.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.serializers import CategorySerializer
from app.schemas.category import CategoryCreate, CategoryType
from app.models.category import Category
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryNameConflictError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryOwnershipError
)


class TestCategorySerializer:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.serializer = CategorySerializer()
        self.db = Mock(spec=Session)
        self.user_id = 1
        self.category_id = 1
        self.parent_id = 2
    
    def test_get_entity_class(self):
        """Test that get_entity_class returns Category."""
        assert self.serializer.get_entity_class() == Category
    
    def test_get_user_id_field(self):
        """Test that get_user_id_field returns correct field name."""
        assert self.serializer.get_user_id_field() == "user_id"
    
    def test_get_parent_id_field(self):
        """Test that get_parent_id_field returns correct field name."""
        assert self.serializer.get_parent_id_field() == "parent_id"
    
    def test_get_unique_fields(self):
        """Test that get_unique_fields returns correct field names."""
        assert self.serializer.get_unique_fields() == ["name"]
    
    def test_validate_category_type_valid(self):
        """Test category type validation with valid types."""
        # Should not raise any exception
        self.serializer.validate_category_type(CategoryType.EXPENSE)
        self.serializer.validate_category_type(CategoryType.INCOME)
    
    def test_validate_category_type_invalid(self):
        """Test category type validation with invalid type."""
        with pytest.raises(CategoryValidationError):
            self.serializer.validate_category_type("INVALID_TYPE")
    
    def test_validate_ownership_success(self):
        """Test successful ownership validation."""
        mock_category = Mock()
        mock_category.id = self.category_id
        mock_category.user_id = self.user_id
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_category
        
        result = self.serializer.validate_ownership(
            self.db, self.category_id, self.user_id, "Category"
        )
        
        assert result == mock_category
    
    def test_validate_ownership_not_found(self):
        """Test ownership validation when entity is not found."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(CategoryNotFoundError):
            self.serializer.validate_ownership(
                self.db, self.category_id, self.user_id, "Category"
            )
    
    def test_validate_ownership_wrong_user(self):
        """Test ownership validation when entity belongs to different user."""
        mock_category = Mock()
        mock_category.id = self.category_id
        mock_category.user_id = 999  # Different user
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_category
        
        with patch('app.serializers.validation_mixins.log_security_event') as mock_log:
            with pytest.raises(CategoryOwnershipError):
                self.serializer.validate_ownership(
                    self.db, self.category_id, self.user_id, "Category"
                )
            mock_log.assert_called_once()
    
    def test_validate_uniqueness_success(self):
        """Test successful uniqueness validation."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        data = {"name": "Test Category"}
        
        # Should not raise any exception
        self.serializer.validate_uniqueness(self.db, self.user_id, data)
    
    def test_validate_uniqueness_conflict(self):
        """Test uniqueness validation when conflict exists."""
        mock_category = Mock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_category
        
        data = {"name": "Existing Category"}
        
        with pytest.raises(CategoryNameConflictError):
            self.serializer.validate_uniqueness(self.db, self.user_id, data)
    
    def test_validate_uniqueness_with_exclude(self):
        """Test uniqueness validation with exclude_id."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        data = {"name": "Test Category"}
        exclude_id = 1
        
        # Should not raise any exception
        self.serializer.validate_uniqueness(self.db, self.user_id, data, exclude_id)
    
    def test_validate_circular_relationship_same_id(self):
        """Test circular relationship validation with same IDs."""
        with pytest.raises(CircularRelationshipError):
            self.serializer.validate_circular_relationship(
                self.db, self.category_id, self.category_id, self.user_id
            )
    
    def test_validate_circular_relationship_detection(self):
        """Test circular relationship detection."""
        # Mock parent that points back to original category
        mock_parent = Mock()
        mock_parent.id = self.parent_id
        mock_parent.parent_id = self.category_id  # Points back to original
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_parent
        
        with pytest.raises(CircularRelationshipError):
            self.serializer.validate_circular_relationship(
                self.db, self.category_id, self.parent_id, self.user_id
            )
    
    def test_validate_circular_relationship_success(self):
        """Test successful circular relationship validation."""
        # Mock parent that doesn't create circular relationship
        mock_parent = Mock()
        mock_parent.id = self.parent_id
        mock_parent.parent_id = None  # Root category
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_parent
        
        # Should not raise any exception
        self.serializer.validate_circular_relationship(
            self.db, self.category_id, self.parent_id, self.user_id
        )
    
    def test_get_entity_depth(self):
        """Test getting entity depth in hierarchy."""
        # Mock category with parent
        mock_category = Mock()
        mock_category.id = self.category_id
        mock_category.parent_id = self.parent_id
        
        # Mock parent (root category)
        mock_parent = Mock()
        mock_parent.id = self.parent_id
        mock_parent.parent_id = None
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_category,  # First call for category
            mock_parent     # Second call for parent
        ]
        
        depth = self.serializer.get_entity_depth(self.db, self.category_id, self.user_id)
        assert depth == 1
    
    def test_serialize_category_for_create(self):
        """Test serialization for category creation."""
        data = CategoryCreate(
            name="Test Category",
            parent_id=self.parent_id,
            type=CategoryType.EXPENSE
        )
        
        result = self.serializer.serialize_category_for_create(data, self.user_id)
        
        expected = {
            "name": "Test Category",
            "user_id": self.user_id,
            "parent_id": self.parent_id,
            "type": CategoryType.EXPENSE
        }
        
        assert result == expected
    
    def test_serialize_category_for_update(self):
        """Test serialization for category update."""
        data = CategoryCreate(
            name="Updated Category",
            parent_id=self.parent_id,
            type=CategoryType.INCOME
        )
        
        result = self.serializer.serialize_category_for_update(data)
        
        expected = {
            "name": "Updated Category",
            "parent_id": self.parent_id,
            "type": CategoryType.INCOME
        }
        
        assert result == expected
    
    def test_serialize_category_for_update_partial(self):
        """Test partial serialization for category update."""
        data = CategoryCreate(
            name="Updated Category",
            parent_id=None,
            type=None
        )
        
        result = self.serializer.serialize_category_for_update(data)
        
        expected = {
            "name": "Updated Category",
            "parent_id": None,
            "type": None
        }
        
        assert result == expected
    
    def test_validate_category_data_comprehensive(self):
        """Test comprehensive category data validation."""
        data = CategoryCreate(
            name="Test Category",
            parent_id=self.parent_id,
            type=CategoryType.EXPENSE
        )
        
        # Mock all validation methods
        with patch.object(self.serializer, 'validate_category_type') as mock_type, \
             patch.object(self.serializer, 'validate_uniqueness') as mock_unique, \
             patch.object(self.serializer, 'validate_parent_category') as mock_parent:
            
            self.serializer.validate_category_data(self.db, data, self.user_id)
            
            mock_type.assert_called_once_with(CategoryType.EXPENSE)
            mock_unique.assert_called_once()
            mock_parent.assert_called_once_with(self.db, self.parent_id, self.user_id)
    
    def test_validate_category_data_with_exclude(self):
        """Test category data validation with exclude_id for updates."""
        data = CategoryCreate(
            name="Test Category",
            parent_id=self.parent_id,
            type=CategoryType.EXPENSE
        )
        exclude_id = 1
        
        with patch.object(self.serializer, 'validate_category_type') as mock_type, \
             patch.object(self.serializer, 'validate_uniqueness') as mock_unique, \
             patch.object(self.serializer, 'validate_parent_category') as mock_parent, \
             patch.object(self.serializer, 'validate_circular_relationship') as mock_circular:
            
            self.serializer.validate_category_data(self.db, data, self.user_id, exclude_id)
            
            mock_type.assert_called_once_with(CategoryType.EXPENSE)
            mock_unique.assert_called_once_with(self.db, self.user_id, {"name": "Test Category"}, exclude_id)
            mock_parent.assert_called_once_with(self.db, self.parent_id, self.user_id)
            mock_circular.assert_called_once_with(self.db, exclude_id, self.parent_id, self.user_id)
