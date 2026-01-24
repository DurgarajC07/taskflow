"""
Base service layer implementation.
Provides business logic abstraction.
"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError


class BaseService:
    """
    Base service class providing common business logic patterns.
    All services should inherit from this class.
    """

    repository = None

    def __init__(self, repository=None):
        if repository:
            self.repository = repository
        elif self.repository is None:
            raise NotImplementedError("Service must define a repository")

    def get_by_id(self, id: Any) -> Optional[Any]:
        """Get an instance by ID."""
        return self.repository.get_by_id(id)

    def get_all(self, filters: Optional[Dict] = None) -> List[Any]:
        """Get all instances with optional filters."""
        if filters:
            return list(self.repository.filter(**filters))
        return list(self.repository.all())

    def search(self, query: str, fields: List[str]) -> List[Any]:
        """Search instances."""
        return list(self.repository.search(query, fields))

    def validate_create_data(self, data: Dict) -> Dict:
        """
        Validate data before creation.
        Override in subclasses to add specific validation.
        """
        return data

    def validate_update_data(self, instance: Any, data: Dict) -> Dict:
        """
        Validate data before update.
        Override in subclasses to add specific validation.
        """
        return data

    @transaction.atomic
    def create(self, data: Dict, created_by=None) -> Any:
        """
        Create a new instance with validation.
        Wraps the operation in a transaction.
        """
        validated_data = self.validate_create_data(data)

        # Add created_by if model supports it
        if created_by and hasattr(self.repository.model, "created_by"):
            validated_data["created_by"] = created_by

        return self.repository.create(**validated_data)

    @transaction.atomic
    def update(self, id: Any, data: Dict, updated_by=None) -> Optional[Any]:
        """
        Update an existing instance with validation.
        Wraps the operation in a transaction.
        """
        instance = self.repository.get_by_id(id)
        if not instance:
            return None

        validated_data = self.validate_update_data(instance, data)

        # Add updated_by if model supports it
        if updated_by and hasattr(instance, "updated_by"):
            validated_data["updated_by"] = updated_by

        return self.repository.update(instance, **validated_data)

    @transaction.atomic
    def delete(self, id: Any, user=None, soft: bool = True) -> bool:
        """
        Delete an instance (soft delete by default if supported).

        Args:
            id: Instance ID
            user: User performing the deletion
            soft: Whether to soft delete (if supported) or hard delete
        """
        instance = self.repository.get_by_id(id)
        if not instance:
            return False

        if soft and hasattr(instance, "soft_delete"):
            self.repository.soft_delete(instance, user=user)
        else:
            self.repository.delete(instance)

        return True

    def restore(self, id: Any) -> bool:
        """Restore a soft-deleted instance."""
        instance = self.repository.get_by_id(id)
        if not instance:
            return False

        if hasattr(instance, "restore"):
            self.repository.restore(instance)
            return True

        return False

    def exists(self, **filters) -> bool:
        """Check if instances exist."""
        return self.repository.exists(**filters)

    def count(self, **filters) -> int:
        """Count instances."""
        return self.repository.count(**filters)

    def bulk_create(self, data_list: List[Dict], created_by=None) -> List[Any]:
        """
        Bulk create instances.

        Args:
            data_list: List of data dictionaries
            created_by: User creating the instances
        """
        instances = []
        for data in data_list:
            validated_data = self.validate_create_data(data)
            if created_by and hasattr(self.repository.model, "created_by"):
                validated_data["created_by"] = created_by
            instances.append(self.repository.model(**validated_data))

        return self.repository.bulk_create(instances)


class OrganizationService(BaseService):
    """
    Base service for organization-owned resources.
    Automatically handles organization context.
    """

    def __init__(self, repository=None, organization_id=None):
        super().__init__(repository)
        self.organization_id = organization_id
        if hasattr(self.repository, "set_organization") and organization_id:
            self.repository.set_organization(organization_id)

    def validate_create_data(self, data: Dict) -> Dict:
        """Add organization_id to create data if not present."""
        validated_data = super().validate_create_data(data)
        if self.organization_id and "organization_id" not in validated_data:
            validated_data["organization_id"] = self.organization_id
        return validated_data

    def set_organization(self, organization_id: Any):
        """Set the organization context."""
        self.organization_id = organization_id
        if hasattr(self.repository, "set_organization"):
            self.repository.set_organization(organization_id)
