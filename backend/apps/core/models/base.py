"""
Base model classes for the application.
Provides common functionality and patterns used across all models.
"""

from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields and functionality.
    All models should inherit from this class.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Override save to add custom logic if needed."""
        super().save(*args, **kwargs)


class SoftDeleteModel(BaseModel):
    """
    Abstract model that provides soft delete functionality.
    Instead of deleting records, marks them as deleted.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted",
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Soft delete the instance."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def restore(self):
        """Restore a soft-deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])


class TrackableModel(BaseModel):
    """
    Abstract model that tracks who created and last updated the record.
    """

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


class OrganizationOwnedModel(SoftDeleteModel, TrackableModel):
    """
    Abstract model for entities that belong to an organization.
    Provides organization isolation and common tracking fields.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
        ]
