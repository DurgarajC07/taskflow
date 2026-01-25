"""
Label and Tag Repositories
Repositories for Label, Tag, SavedFilter, and CustomView models.
"""

from typing import List, Optional
from django.db.models import Count, Q
from apps.core.repositories.base import OrganizationRepository
from apps.tasks.models import Label, Tag, SavedFilter, CustomView


class LabelRepository(OrganizationRepository):
    """
    Repository for Label model.
    """

    def __init__(self):
        super().__init__(Label)

    def get_project_labels(self, project_id):
        """Get all labels for a project"""
        return self.filter(project_id=project_id).order_by("name")

    def get_by_name(self, project_id, name):
        """Get label by name"""
        return self.filter(project_id=project_id, name=name).first()

    def get_or_create_label(
        self, project_id, organization_id, name, color=None, created_by_id=None
    ):
        """Get or create a label"""
        label = self.get_by_name(project_id, name)
        if label:
            return label, False

        return (
            self.create(
                project_id=project_id,
                organization_id=organization_id,
                name=name,
                color=color or "#6B7280",
                created_by_id=created_by_id,
            ),
            True,
        )

    def get_popular_labels(self, project_id, limit=10):
        """Get most used labels"""
        return self.filter(project_id=project_id).order_by("-usage_count", "name")[
            :limit
        ]

    def search_labels(self, project_id, query):
        """Search labels by name"""
        return self.filter(
            project_id=project_id,
            name__icontains=query,
        ).order_by("name")


class TagRepository(OrganizationRepository):
    """
    Repository for Tag model.
    """

    def __init__(self):
        super().__init__(Tag)

    def get_organization_tags(self, organization_id):
        """Get all tags for an organization"""
        return self.filter(organization_id=organization_id).order_by("name")

    def get_by_name(self, organization_id, name):
        """Get tag by name"""
        return self.filter(organization_id=organization_id, name=name).first()

    def get_or_create_tag(self, organization_id, name, color=None, created_by_id=None):
        """Get or create a tag"""
        tag = self.get_by_name(organization_id, name)
        if tag:
            return tag, False

        return (
            self.create(
                organization_id=organization_id,
                name=name,
                color=color or "#8B5CF6",
                created_by_id=created_by_id,
            ),
            True,
        )

    def get_popular_tags(self, organization_id, limit=10):
        """Get most used tags"""
        return self.filter(organization_id=organization_id).order_by(
            "-usage_count", "name"
        )[:limit]

    def search_tags(self, organization_id, query):
        """Search tags by name"""
        return self.filter(
            organization_id=organization_id,
            name__icontains=query,
        ).order_by("name")


class SavedFilterRepository(OrganizationRepository):
    """
    Repository for SavedFilter model.
    """

    def __init__(self):
        super().__init__(SavedFilter)

    def get_user_filters(self, user_id, project_id=None):
        """Get saved filters for a user"""
        filters = {"owner_id": user_id}
        if project_id:
            filters["project_id"] = project_id

        return self.filter(**filters).order_by("-is_favorite", "name")

    def get_shared_filters(self, organization_id, project_id=None, visibility=None):
        """Get shared filters (team or organization level)"""
        filters = {"organization_id": organization_id}
        if project_id:
            filters["project_id"] = project_id
        if visibility:
            filters["visibility"] = visibility
        else:
            filters["visibility__in"] = [
                SavedFilter.Visibility.TEAM,
                SavedFilter.Visibility.ORGANIZATION,
            ]

        return self.filter(**filters).order_by("name")

    def get_favorite_filters(self, user_id):
        """Get user's favorite filters"""
        return self.filter(owner_id=user_id, is_favorite=True).order_by("name")

    def get_popular_filters(self, organization_id, limit=10):
        """Get most used filters"""
        return (
            self.filter(organization_id=organization_id)
            .filter(Q(visibility=SavedFilter.Visibility.ORGANIZATION))
            .order_by("-usage_count", "name")[:limit]
        )


class CustomViewRepository(OrganizationRepository):
    """
    Repository for CustomView model.
    """

    def __init__(self):
        super().__init__(CustomView)

    def get_project_views(self, project_id, owner_id=None, visibility=None):
        """Get custom views for a project"""
        filters = {"project_id": project_id}
        if owner_id:
            filters["owner_id"] = owner_id
        if visibility:
            filters["visibility"] = visibility

        return self.filter(**filters).order_by("display_order", "name")

    def get_user_views(self, user_id, project_id=None):
        """Get custom views owned by user"""
        filters = {"owner_id": user_id}
        if project_id:
            filters["project_id"] = project_id

        return self.filter(**filters).order_by("display_order", "name")

    def get_default_view(self, project_id):
        """Get default view for a project"""
        return self.filter(project_id=project_id, is_default=True).first()

    def set_as_default(self, view_id, project_id):
        """Set a view as default"""
        # Remove default from other views
        self.filter(project_id=project_id, is_default=True).update(is_default=False)
        # Set this view as default
        view = self.get_by_id(view_id)
        if view:
            view.is_default = True
            view.save(update_fields=["is_default"])
            return view
        return None

    def get_by_view_type(self, project_id, view_type):
        """Get views by type"""
        return self.filter(project_id=project_id, view_type=view_type).order_by(
            "display_order"
        )

    def reorder_views(self, view_orders):
        """Reorder views"""
        for view_id, order in view_orders.items():
            self.filter(id=view_id).update(display_order=order)
