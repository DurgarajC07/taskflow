"""
Organization Service
Business logic layer for Organization operations.
"""

from django.db import transaction
from django.utils import timezone as django_timezone
from django.core.exceptions import ValidationError
from apps.core.services.base import BaseService
from apps.organizations.repositories import (
    OrganizationRepository,
    OrganizationMemberRepository,
)
from apps.organizations.models import Organization, OrganizationMember
from apps.core.utils.helpers import generate_unique_slug


class OrganizationService(BaseService):
    """Service for Organization business logic"""

    repository_class = OrganizationRepository

    def __init__(self):
        self.repository = OrganizationRepository()
        self.member_repository = OrganizationMemberRepository()

    def validate_create_data(self, data):
        """Validate organization creation data"""
        errors = {}

        # Validate name
        if not data.get("name"):
            errors["name"] = "Organization name is required"
        elif len(data["name"]) < 3:
            errors["name"] = "Organization name must be at least 3 characters"

        # Validate slug if provided
        if "slug" in data:
            if self.repository.slug_exists(data["slug"]):
                errors["slug"] = "This slug is already taken"

        # Validate plan limits
        if "max_members" in data and data["max_members"] < 1:
            errors["max_members"] = "Maximum members must be at least 1"

        if "max_projects" in data and data["max_projects"] < 1:
            errors["max_projects"] = "Maximum projects must be at least 1"

        if "max_storage_gb" in data and data["max_storage_gb"] < 1:
            errors["max_storage_gb"] = "Maximum storage must be at least 1 GB"

        if errors:
            raise ValidationError(errors)

        return data

    def validate_update_data(self, organization, data):
        """Validate organization update data"""
        errors = {}

        # Validate name if being updated
        if "name" in data:
            if not data["name"]:
                errors["name"] = "Organization name is required"
            elif len(data["name"]) < 3:
                errors["name"] = "Organization name must be at least 3 characters"

        # Validate slug if being updated
        if "slug" in data:
            if self.repository.slug_exists(data["slug"], exclude_id=organization.id):
                errors["slug"] = "This slug is already taken"

        # Validate limits don't go below current usage
        if "max_members" in data and data["max_members"] < organization.current_members:
            errors["max_members"] = (
                f"Cannot set limit below current usage ({organization.current_members} members)"
            )

        if (
            "max_projects" in data
            and data["max_projects"] < organization.current_projects
        ):
            errors["max_projects"] = (
                f"Cannot set limit below current usage ({organization.current_projects} projects)"
            )

        if "max_storage_gb" in data and data["max_storage_gb"] < float(
            organization.current_storage_gb
        ):
            errors["max_storage_gb"] = (
                f"Cannot set limit below current usage ({organization.current_storage_gb} GB)"
            )

        if errors:
            raise ValidationError(errors)

        return data

    @transaction.atomic
    def create_organization(self, owner, data):
        """Create new organization with owner membership"""
        # Validate data
        self.validate_create_data(data)

        # Generate slug if not provided
        if "slug" not in data or not data["slug"]:
            data["slug"] = generate_unique_slug(
                data["name"], self.repository.slug_exists
            )

        # Set owner
        data["owner"] = owner

        # Set initial member count to 1 (owner)
        data["current_members"] = 1

        # Set trial period (30 days)
        if data.get("status") == Organization.OrganizationStatus.TRIAL:
            from datetime import timedelta

            data["trial_ends_at"] = django_timezone.now() + timedelta(days=30)

        # Create organization
        organization = self.repository.create(data)

        # Create owner membership
        self.member_repository.create(
            {
                "organization": organization,
                "user": owner,
                "role": OrganizationMember.Role.OWNER,
                "status": OrganizationMember.MembershipStatus.ACTIVE,
                "joined_at": django_timezone.now(),
            }
        )

        return organization

    def update_organization(self, organization, data, user):
        """Update organization"""
        # Check permission
        if not organization.is_owner(user):
            raise ValidationError(
                "Only organization owner can update organization settings"
            )

        # Validate data
        self.validate_update_data(organization, data)

        # Update organization
        return self.repository.update(organization.id, data)

    @transaction.atomic
    def delete_organization(self, organization, user):
        """Soft delete organization"""
        # Check permission
        if not organization.is_owner(user):
            raise ValidationError("Only organization owner can delete organization")

        # Soft delete organization
        return self.repository.delete(organization.id)

    def get_user_organizations(self, user):
        """Get all organizations accessible by user"""
        return self.repository.get_user_organizations(user)

    def get_organization_by_slug(self, slug):
        """Get organization by slug"""
        return self.repository.get_by_slug(slug)

    def search_organizations(self, query, user=None):
        """Search organizations"""
        return self.repository.search_organizations(query, user)

    def get_organization_statistics(self, organization_id):
        """Get organization usage statistics"""
        return self.repository.get_organization_statistics(organization_id)

    def change_plan(self, organization, plan, user):
        """Change organization plan"""
        # Check permission
        if not organization.is_owner(user):
            raise ValidationError("Only organization owner can change plan")

        # Plan limits
        plan_limits = {
            Organization.PlanType.FREE: {
                "max_members": 5,
                "max_projects": 3,
                "max_storage_gb": 1,
            },
            Organization.PlanType.STARTER: {
                "max_members": 10,
                "max_projects": 10,
                "max_storage_gb": 5,
            },
            Organization.PlanType.PROFESSIONAL: {
                "max_members": 50,
                "max_projects": 50,
                "max_storage_gb": 50,
            },
            Organization.PlanType.ENTERPRISE: {
                "max_members": 999,
                "max_projects": 999,
                "max_storage_gb": 500,
            },
        }

        limits = plan_limits.get(plan, plan_limits[Organization.PlanType.FREE])

        # Check if downgrading
        if limits["max_members"] < organization.current_members:
            raise ValidationError(
                f'Cannot downgrade: Current members ({organization.current_members}) exceeds new limit ({limits["max_members"]})'
            )

        if limits["max_projects"] < organization.current_projects:
            raise ValidationError(
                f'Cannot downgrade: Current projects ({organization.current_projects}) exceeds new limit ({limits["max_projects"]})'
            )

        if limits["max_storage_gb"] < float(organization.current_storage_gb):
            raise ValidationError(
                f'Cannot downgrade: Current storage ({organization.current_storage_gb} GB) exceeds new limit ({limits["max_storage_gb"]} GB)'
            )

        # Update plan and limits
        return self.repository.update(
            organization.id,
            {
                "plan": plan,
                "status": Organization.OrganizationStatus.ACTIVE,
                **limits,
            },
        )

    def update_settings(self, organization, settings, user):
        """Update organization settings"""
        # Check permission
        if not self.member_repository.user_has_permission(
            organization, user, "manage_organization"
        ):
            raise ValidationError(
                "You do not have permission to update organization settings"
            )

        # Merge with existing settings
        current_settings = organization.settings or {}
        updated_settings = {**current_settings, **settings}

        return self.repository.update(organization.id, {"settings": updated_settings})

    def verify_organization(self, organization, domain):
        """Verify organization domain"""
        # Check if domain is already taken
        existing = self.repository.get_by_domain(domain)
        if existing and existing.id != organization.id:
            raise ValidationError(
                "This domain is already verified by another organization"
            )

        return self.repository.update(
            organization.id,
            {
                "domain": domain,
                "verified": True,
            },
        )

    def suspend_organization(self, organization, reason=None):
        """Suspend organization"""
        settings = organization.settings or {}
        settings["suspension_reason"] = reason
        settings["suspended_at"] = django_timezone.now().isoformat()

        return self.repository.update(
            organization.id,
            {
                "status": Organization.OrganizationStatus.SUSPENDED,
                "settings": settings,
            },
        )

    def activate_organization(self, organization):
        """Activate suspended organization"""
        return self.repository.update(
            organization.id,
            {
                "status": Organization.OrganizationStatus.ACTIVE,
            },
        )

    def check_and_expire_trials(self):
        """Check and expire trial organizations"""
        expired_trials = self.repository.get_expired_trials()

        for org in expired_trials:
            self.repository.update(
                org.id,
                {
                    "status": Organization.OrganizationStatus.EXPIRED,
                },
            )

        return expired_trials.count()
