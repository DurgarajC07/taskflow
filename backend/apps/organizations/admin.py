"""
Organization Admin Configuration
Django admin interface for Organization models.
"""

from django.contrib import admin
from apps.organizations.models import Organization, OrganizationMember


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model"""

    list_display = [
        "name",
        "slug",
        "status",
        "plan",
        "owner",
        "current_members",
        "max_members",
        "current_projects",
        "max_projects",
        "verified",
        "created_at",
    ]
    list_filter = ["status", "plan", "verified", "created_at"]
    search_fields = ["name", "slug", "owner__email", "domain"]
    readonly_fields = [
        "id",
        "slug",
        "current_members",
        "current_projects",
        "current_storage_gb",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "name", "slug", "description", "owner")},
        ),
        ("Branding", {"fields": ("logo", "primary_color")}),
        ("Status & Plan", {"fields": ("status", "plan", "verified", "domain")}),
        (
            "Limits",
            {
                "fields": (
                    ("max_members", "current_members"),
                    ("max_projects", "current_projects"),
                    ("max_storage_gb", "current_storage_gb"),
                )
            },
        ),
        ("Billing", {"fields": ("trial_ends_at", "subscription_ends_at")}),
        ("Settings", {"fields": ("settings",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted organizations"""
        return Organization.all_objects.all()


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Admin interface for OrganizationMember model"""

    list_display = [
        "user",
        "organization",
        "role",
        "status",
        "joined_at",
        "last_accessed_at",
    ]
    list_filter = ["role", "status", "joined_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "organization__name",
    ]
    readonly_fields = [
        "id",
        "invitation_token",
        "joined_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("id", "organization", "user")}),
        ("Role & Status", {"fields": ("role", "status")}),
        ("Permissions", {"fields": ("custom_permissions",), "classes": ("collapse",)}),
        (
            "Invitation",
            {
                "fields": (
                    "invited_by",
                    "invitation_token",
                    "invitation_expires_at",
                    "joined_at",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Activity", {"fields": ("last_accessed_at",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return (
            super()
            .get_queryset(request)
            .select_related("user", "organization", "invited_by")
        )
