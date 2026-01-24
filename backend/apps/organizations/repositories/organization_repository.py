"""
Organization Repository
Data access layer for Organization model.
"""

from django.db import models
from django.db.models import Q, Count, Sum
from django.utils import timezone as django_timezone
from apps.core.repositories.base import BaseRepository
from apps.organizations.models import Organization


class OrganizationRepository(BaseRepository):
    """Repository for Organization model"""

    model = Organization

    def get_by_slug(self, slug, include_deleted=False):
        """Get organization by slug"""
        queryset = self.model.all_objects if include_deleted else self.model.objects
        try:
            return queryset.get(slug=slug)
        except self.model.DoesNotExist:
            return None

    def get_by_owner(self, owner, include_deleted=False):
        """Get organizations owned by user"""
        queryset = self.model.all_objects if include_deleted else self.model.objects
        return queryset.filter(owner=owner)

    def get_by_member(self, user, include_deleted=False):
        """Get organizations where user is member"""
        queryset = self.model.all_objects if include_deleted else self.model.objects
        return queryset.filter(members=user, memberships__status="active").distinct()

    def get_user_organizations(self, user, include_deleted=False):
        """Get all organizations accessible by user (owned + member)"""
        queryset = self.model.all_objects if include_deleted else self.model.objects
        return queryset.filter(
            Q(owner=user) | Q(members=user, memberships__status="active")
        ).distinct()

    def get_active_organizations(self):
        """Get active organizations"""
        return self.model.objects.filter(status=Organization.OrganizationStatus.ACTIVE)

    def get_trial_organizations(self):
        """Get organizations on trial"""
        return self.model.objects.filter(status=Organization.OrganizationStatus.TRIAL)

    def get_expired_trials(self):
        """Get organizations with expired trials"""
        now = django_timezone.now()
        return self.model.objects.filter(
            status=Organization.OrganizationStatus.TRIAL, trial_ends_at__lt=now
        )

    def get_by_plan(self, plan):
        """Get organizations by plan type"""
        return self.model.objects.filter(plan=plan)

    def search_organizations(self, query, user=None):
        """Search organizations by name or slug"""
        queryset = self.model.objects.all()

        # Filter by user access if provided
        if user:
            queryset = queryset.filter(
                Q(owner=user) | Q(members=user, memberships__status="active")
            ).distinct()

        # Search by query
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(slug__icontains=query)
                | Q(description__icontains=query)
            )

        return queryset

    def slug_exists(self, slug, exclude_id=None):
        """Check if slug exists"""
        queryset = self.model.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    def get_organization_statistics(self, organization_id):
        """Get organization statistics"""
        try:
            org = self.get_by_id(organization_id)
            if not org:
                return None

            return {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "status": org.status,
                "plan": org.plan,
                "members": {
                    "current": org.current_members,
                    "max": org.max_members,
                    "usage_percent": (
                        (org.current_members / org.max_members * 100)
                        if org.max_members > 0
                        else 0
                    ),
                },
                "projects": {
                    "current": org.current_projects,
                    "max": org.max_projects,
                    "usage_percent": (
                        (org.current_projects / org.max_projects * 100)
                        if org.max_projects > 0
                        else 0
                    ),
                },
                "storage": {
                    "current_gb": float(org.current_storage_gb),
                    "max_gb": org.max_storage_gb,
                    "usage_percent": (
                        (float(org.current_storage_gb) / org.max_storage_gb * 100)
                        if org.max_storage_gb > 0
                        else 0
                    ),
                },
                "created_at": org.created_at,
                "trial_ends_at": org.trial_ends_at,
                "subscription_ends_at": org.subscription_ends_at,
            }
        except Exception:
            return None

    def get_organizations_near_limit(self, limit_type="members", threshold=0.8):
        """Get organizations near their limits (members, projects, or storage)"""
        if limit_type == "members":
            return self.model.objects.filter(
                current_members__gte=models.F("max_members") * threshold
            )
        elif limit_type == "projects":
            return self.model.objects.filter(
                current_projects__gte=models.F("max_projects") * threshold
            )
        elif limit_type == "storage":
            return self.model.objects.filter(
                current_storage_gb__gte=models.F("max_storage_gb") * threshold
            )
        return self.model.objects.none()

    def update_usage_statistics(self, organization_id):
        """Recalculate and update organization usage statistics"""
        from apps.organizations.models import OrganizationMember

        try:
            org = self.get_by_id(organization_id)
            if not org:
                return False

            # Recalculate member count
            active_members = OrganizationMember.objects.filter(
                organization=org, status="active"
            ).count()

            # Update organization
            org.current_members = active_members
            org.save(update_fields=["current_members"])

            return True
        except Exception:
            return False

    def get_verified_organizations(self):
        """Get verified organizations"""
        return self.model.objects.filter(verified=True)

    def get_by_domain(self, domain):
        """Get organization by verified domain"""
        try:
            return self.model.objects.get(domain=domain, verified=True)
        except self.model.DoesNotExist:
            return None
