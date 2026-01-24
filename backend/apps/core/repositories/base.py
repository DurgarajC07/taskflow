"""
Base repository pattern implementation.
Provides data access abstraction layer.
"""

from typing import Optional, List, Dict, Any
from django.db.models import Model, QuerySet, Q
from django.core.exceptions import ObjectDoesNotExist


class BaseRepository:
    """
    Base repository class providing common data access methods.
    All repositories should inherit from this class.
    """

    model: Model = None

    def __init__(self):
        if self.model is None:
            raise NotImplementedError("Repository must define a model class")

    def get_queryset(self) -> QuerySet:
        """
        Get the base queryset for this repository.
        Can be overridden to add default filters or select_related/prefetch_related.
        """
        return self.model.objects.all()

    def get_by_id(self, id: Any) -> Optional[Model]:
        """Get a single instance by ID."""
        try:
            return self.get_queryset().get(id=id)
        except ObjectDoesNotExist:
            return None

    def get_or_none(self, **filters) -> Optional[Model]:
        """Get a single instance by filters or return None."""
        try:
            return self.get_queryset().get(**filters)
        except ObjectDoesNotExist:
            return None

    def filter(self, **filters) -> QuerySet:
        """Filter instances by given criteria."""
        return self.get_queryset().filter(**filters)

    def filter_by_q(self, q: Q) -> QuerySet:
        """Filter instances using Q objects."""
        return self.get_queryset().filter(q)

    def all(self) -> QuerySet:
        """Get all instances."""
        return self.get_queryset()

    def exists(self, **filters) -> bool:
        """Check if instances exist matching filters."""
        return self.get_queryset().filter(**filters).exists()

    def count(self, **filters) -> int:
        """Count instances matching filters."""
        if filters:
            return self.get_queryset().filter(**filters).count()
        return self.get_queryset().count()

    def create(self, **data) -> Model:
        """Create a new instance."""
        return self.model.objects.create(**data)

    def bulk_create(self, instances: List[Model], batch_size: int = 100) -> List[Model]:
        """Bulk create instances."""
        return self.model.objects.bulk_create(instances, batch_size=batch_size)

    def update(self, instance: Model, **data) -> Model:
        """Update an existing instance."""
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def bulk_update(
        self, instances: List[Model], fields: List[str], batch_size: int = 100
    ):
        """Bulk update instances."""
        return self.model.objects.bulk_update(instances, fields, batch_size=batch_size)

    def delete(self, instance: Model) -> None:
        """Delete an instance."""
        instance.delete()

    def soft_delete(self, instance: Model, user=None) -> Model:
        """
        Soft delete an instance if the model supports it.
        """
        if hasattr(instance, "soft_delete"):
            instance.soft_delete(user=user)
            return instance
        raise NotImplementedError("Model does not support soft delete")

    def restore(self, instance: Model) -> Model:
        """
        Restore a soft-deleted instance.
        """
        if hasattr(instance, "restore"):
            instance.restore()
            return instance
        raise NotImplementedError("Model does not support restore")

    def get_active(self) -> QuerySet:
        """
        Get only active (non-deleted) instances.
        Only works with models that have soft delete.
        """
        if hasattr(self.model, "is_deleted"):
            return self.get_queryset().filter(is_deleted=False)
        return self.get_queryset()

    def search(self, query: str, fields: List[str]) -> QuerySet:
        """
        Search instances across multiple fields.

        Args:
            query: Search query string
            fields: List of field names to search in
        """
        if not query:
            return self.get_queryset()

        q_objects = Q()
        for field in fields:
            q_objects |= Q(**{f"{field}__icontains": query})

        return self.get_queryset().filter(q_objects)

    def paginate(
        self, queryset: QuerySet, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Paginate a queryset.

        Returns:
            Dict with 'results', 'count', 'page', 'page_size', 'total_pages'
        """
        count = queryset.count()
        total_pages = (count + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "results": list(queryset[start:end]),
            "count": count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }


class OrganizationRepository(BaseRepository):
    """
    Base repository for organization-owned models.
    Automatically filters by organization context.
    """

    def __init__(self, organization_id: Optional[Any] = None):
        super().__init__()
        self.organization_id = organization_id

    def get_queryset(self) -> QuerySet:
        """Get queryset filtered by organization if provided."""
        queryset = super().get_queryset()
        if self.organization_id:
            queryset = queryset.filter(organization_id=self.organization_id)
        return queryset

    def set_organization(self, organization_id: Any):
        """Set the organization context for this repository."""
        self.organization_id = organization_id
