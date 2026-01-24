"""
Custom model managers providing reusable query logic.
"""

from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Manager that automatically filters out soft-deleted objects.
    """

    def get_queryset(self):
        """Return only non-deleted objects."""
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Return all objects including deleted ones."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only deleted objects."""
        return super().get_queryset().filter(is_deleted=True)

    def restore(self, id):
        """Restore a soft-deleted object by ID."""
        obj = self.all_with_deleted().get(id=id)
        obj.restore()
        return obj


class OrganizationManager(models.Manager):
    """
    Manager for organization-scoped queries.
    """

    def for_organization(self, organization_id):
        """Filter objects by organization."""
        return self.get_queryset().filter(organization_id=organization_id)

    def active_for_organization(self, organization_id):
        """Get active objects for an organization."""
        queryset = self.get_queryset().filter(organization_id=organization_id)
        if hasattr(self.model, "is_deleted"):
            queryset = queryset.filter(is_deleted=False)
        return queryset
