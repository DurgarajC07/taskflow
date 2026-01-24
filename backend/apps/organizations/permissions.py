"""
Organization Permissions
Role-based permission system for organizations.
"""

from rest_framework import permissions
from apps.organizations.models import OrganizationMember


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission check: User is a member of the organization.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is organization member"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get organization from object
        organization = getattr(obj, "organization", obj)

        return organization.is_member(request.user)


class IsOrganizationOwner(permissions.BasePermission):
    """
    Permission check: User is the organization owner.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is organization owner"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get organization from object
        organization = getattr(obj, "organization", obj)

        return organization.is_owner(request.user)


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Permission check: User is organization owner or admin.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is organization admin"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get organization from object
        organization = getattr(obj, "organization", obj)

        # Check if user is member
        try:
            membership = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status=OrganizationMember.MembershipStatus.ACTIVE,
            )
            return membership.is_admin()
        except OrganizationMember.DoesNotExist:
            return False


class HasOrganizationPermission(permissions.BasePermission):
    """
    Permission check: User has specific organization permission.
    Set `required_permission` on the view.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user has required permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get required permission from view
        required_permission = getattr(view, "required_permission", None)
        if not required_permission:
            return False

        # Get organization from object
        organization = getattr(obj, "organization", obj)

        # Check permission
        return organization.has_permission(request.user, required_permission)


class CanManageOrganization(permissions.BasePermission):
    """
    Permission check: User can manage organization settings.
    """

    def has_object_permission(self, request, view, obj):
        """Check manage_organization permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", obj)
        return organization.has_permission(request.user, "manage_organization")


class CanManageMembers(permissions.BasePermission):
    """
    Permission check: User can manage organization members.
    """

    def has_object_permission(self, request, view, obj):
        """Check manage_members permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", obj)
        return organization.has_permission(request.user, "manage_members")


class CanManageProjects(permissions.BasePermission):
    """
    Permission check: User can manage projects.
    """

    def has_object_permission(self, request, view, obj):
        """Check manage_projects permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", obj)
        return organization.has_permission(request.user, "manage_projects")


class OrganizationPermission(permissions.BasePermission):
    """
    Combined permission for organization operations.
    Handles different permission requirements per HTTP method.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check permissions based on HTTP method"""
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", obj)

        # Safe methods (GET, HEAD, OPTIONS) - member access
        if request.method in permissions.SAFE_METHODS:
            return organization.is_member(request.user)

        # Update methods (PUT, PATCH) - owner only
        if request.method in ["PUT", "PATCH"]:
            return organization.is_owner(request.user)

        # Delete method - owner only
        if request.method == "DELETE":
            return organization.is_owner(request.user)

        # POST and other methods - admin access
        return organization.has_permission(request.user, "manage_organization")


class OrganizationMemberPermission(permissions.BasePermission):
    """
    Combined permission for organization member operations.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check permissions based on HTTP method"""
        if not request.user or not request.user.is_authenticated:
            return False

        # For OrganizationMember objects
        if isinstance(obj, OrganizationMember):
            organization = obj.organization
        else:
            organization = obj

        # Safe methods - member access
        if request.method in permissions.SAFE_METHODS:
            return organization.is_member(request.user)

        # Modifying methods - need manage_members permission
        return organization.has_permission(request.user, "manage_members")
