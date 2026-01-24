"""
Organization Models
Handles workspaces/companies with multi-tenancy support.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models.base import BaseModel, SoftDeleteModel
from apps.core.utils.validators import validate_slug, validate_hex_color
from apps.core.managers.base import SoftDeleteManager

User = get_user_model()


class Organization(SoftDeleteModel):
    """
    Organization/Workspace model for multi-tenancy.
    Each organization is an isolated workspace.
    """

    # Organization Status
    class OrganizationStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        TRIAL = "trial", "Trial"
        EXPIRED = "expired", "Expired"

    # Plan Types
    class PlanType(models.TextChoices):
        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PROFESSIONAL = "professional", "Professional"
        ENTERPRISE = "enterprise", "Enterprise"

    # Basic Information
    name = models.CharField(max_length=255, help_text="Organization name")
    slug = models.SlugField(
        max_length=255,
        unique=True,
        validators=[validate_slug],
        help_text="URL-friendly organization identifier",
    )
    description = models.TextField(blank=True, help_text="Organization description")

    # Branding
    logo = models.ImageField(
        upload_to="organizations/logos/",
        null=True,
        blank=True,
        help_text="Organization logo",
    )
    primary_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        validators=[validate_hex_color],
        help_text="Primary brand color (hex)",
    )

    # Status & Plan
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.TRIAL,
        db_index=True,
    )
    plan = models.CharField(
        max_length=20, choices=PlanType.choices, default=PlanType.FREE, db_index=True
    )

    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
        help_text="Organization owner",
    )

    # Members
    members = models.ManyToManyField(
        User,
        through="OrganizationMember",
        through_fields=("organization", "user"),
        related_name="organizations",
        help_text="Organization members",
    )

    # Settings (JSON)
    settings = models.JSONField(
        default=dict, blank=True, help_text="Organization settings"
    )

    # Limits
    max_members = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of members",
    )
    max_projects = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of projects",
    )
    max_storage_gb = models.IntegerField(
        default=5, validators=[MinValueValidator(1)], help_text="Maximum storage in GB"
    )

    # Usage Statistics
    current_members = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Current number of members",
    )
    current_projects = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current number of projects",
    )
    current_storage_gb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current storage usage in GB",
    )

    # Billing
    trial_ends_at = models.DateTimeField(
        null=True, blank=True, help_text="Trial end date"
    )
    subscription_ends_at = models.DateTimeField(
        null=True, blank=True, help_text="Subscription end date"
    )

    # Metadata
    verified = models.BooleanField(
        default=False, help_text="Organization verification status"
    )
    domain = models.CharField(
        max_length=255, blank=True, help_text="Verified domain for SSO"
    )

    # Custom manager
    objects = SoftDeleteManager()

    class Meta:
        db_table = "organizations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status", "is_deleted"]),
            models.Index(fields=["owner"]),
        ]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get organization URL"""
        return f"/org/{self.slug}/"

    def is_owner(self, user):
        """Check if user is organization owner"""
        return self.owner == user

    def is_member(self, user):
        """Check if user is organization member"""
        return self.members.filter(id=user.id, is_active=True).exists()

    def has_permission(self, user, permission):
        """Check if user has specific permission in organization"""
        try:
            membership = self.organizationmember_set.get(user=user)
            return membership.has_permission(permission)
        except OrganizationMember.DoesNotExist:
            return False

    def can_add_member(self):
        """Check if organization can add more members"""
        return self.current_members < self.max_members

    def can_add_project(self):
        """Check if organization can add more projects"""
        return self.current_projects < self.max_projects

    def has_storage_available(self, required_gb=0):
        """Check if organization has storage available"""
        return (self.current_storage_gb + required_gb) <= self.max_storage_gb

    def increment_member_count(self):
        """Increment member count"""
        self.current_members = models.F("current_members") + 1
        self.save(update_fields=["current_members"])
        self.refresh_from_db()

    def decrement_member_count(self):
        """Decrement member count"""
        self.current_members = models.F("current_members") - 1
        self.save(update_fields=["current_members"])
        self.refresh_from_db()

    def increment_project_count(self):
        """Increment project count"""
        self.current_projects = models.F("current_projects") + 1
        self.save(update_fields=["current_projects"])
        self.refresh_from_db()

    def decrement_project_count(self):
        """Decrement project count"""
        self.current_projects = models.F("current_projects") - 1
        self.save(update_fields=["current_projects"])
        self.refresh_from_db()


class OrganizationMember(BaseModel):
    """
    Organization membership with role-based permissions.
    Links users to organizations with specific roles.
    """

    # Member Roles
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        GUEST = "guest", "Guest"

    # Membership Status
    class MembershipStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INVITED = "invited", "Invited"
        SUSPENDED = "suspended", "Suspended"

    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
        help_text="Organization",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships", help_text="User"
    )

    # Role & Status
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
        help_text="Member role",
    )
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
        db_index=True,
        help_text="Membership status",
    )

    # Permissions (JSON)
    custom_permissions = models.JSONField(
        default=dict, blank=True, help_text="Custom role permissions override"
    )

    # Invitation
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        help_text="User who sent the invitation",
    )
    invitation_token = models.CharField(
        max_length=255, blank=True, help_text="Invitation token"
    )
    invitation_expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Invitation expiration date"
    )
    joined_at = models.DateTimeField(
        null=True, blank=True, help_text="Date when user accepted invitation"
    )

    # Activity
    last_accessed_at = models.DateTimeField(
        null=True, blank=True, help_text="Last time user accessed this organization"
    )

    class Meta:
        db_table = "organization_members"
        ordering = ["-created_at"]
        unique_together = [["organization", "user"]]
        indexes = [
            models.Index(fields=["organization", "role"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["invitation_token"]),
        ]
        verbose_name = "Organization Member"
        verbose_name_plural = "Organization Members"

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"

    def get_permissions(self):
        """Get member permissions based on role"""
        # Base permissions by role
        permissions = {
            "owner": [
                "manage_organization",
                "manage_members",
                "manage_billing",
                "manage_projects",
                "manage_teams",
                "manage_tasks",
                "view_analytics",
                "delete_organization",
            ],
            "admin": [
                "manage_members",
                "manage_projects",
                "manage_teams",
                "manage_tasks",
                "view_analytics",
            ],
            "member": [
                "view_projects",
                "create_projects",
                "manage_assigned_tasks",
                "comment_on_tasks",
                "upload_attachments",
            ],
            "guest": [
                "view_projects",
                "view_tasks",
                "comment_on_tasks",
            ],
        }

        # Get base permissions
        role_permissions = permissions.get(self.role, [])

        # Apply custom permissions override
        if self.custom_permissions:
            # Add custom granted permissions
            granted = self.custom_permissions.get("granted", [])
            # Remove custom revoked permissions
            revoked = self.custom_permissions.get("revoked", [])

            role_permissions = list(set(role_permissions + granted) - set(revoked))

        return role_permissions

    def has_permission(self, permission):
        """Check if member has specific permission"""
        return permission in self.get_permissions()

    def is_owner(self):
        """Check if member is owner"""
        return self.role == self.Role.OWNER

    def is_admin(self):
        """Check if member is admin or owner"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]

    def can_manage_members(self):
        """Check if member can manage other members"""
        return self.has_permission("manage_members")

    def can_manage_projects(self):
        """Check if member can manage projects"""
        return self.has_permission("manage_projects")

    def update_last_access(self):
        """Update last access timestamp"""
        from django.utils import timezone as django_timezone

        self.last_accessed_at = django_timezone.now()
        self.save(update_fields=["last_accessed_at"])
