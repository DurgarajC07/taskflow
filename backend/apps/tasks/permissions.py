"""
Team and Project Permissions
Permission classes for team and project access control.
"""

from rest_framework import permissions
from apps.tasks.models import TeamMember, ProjectMember


class CanViewTeam(permissions.BasePermission):
    """Permission check: User can view team"""

    def has_object_permission(self, request, view, obj):
        """Check if user can view team"""
        if not request.user or not request.user.is_authenticated:
            return False

        team = getattr(obj, "team", obj)
        return team.can_view(request.user)


class IsTeamMember(permissions.BasePermission):
    """Permission check: User is team member"""

    def has_object_permission(self, request, view, obj):
        """Check if user is team member"""
        if not request.user or not request.user.is_authenticated:
            return False

        team = getattr(obj, "team", obj)
        return team.is_member(request.user)


class IsTeamMaintainer(permissions.BasePermission):
    """Permission check: User is team maintainer or lead"""

    def has_object_permission(self, request, view, obj):
        """Check if user is team maintainer"""
        if not request.user or not request.user.is_authenticated:
            return False

        team = getattr(obj, "team", obj)

        try:
            membership = TeamMember.objects.get(team=team, user=request.user)
            return membership.is_maintainer()
        except TeamMember.DoesNotExist:
            return False


class CanManageTeams(permissions.BasePermission):
    """Permission check: User can manage teams in organization"""

    def has_object_permission(self, request, view, obj):
        """Check manage_teams permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        team = getattr(obj, "team", obj)
        organization = team.organization

        return organization.has_permission(request.user, "manage_teams")


class TeamPermission(permissions.BasePermission):
    """Combined permission for team operations"""

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check permissions based on HTTP method"""
        if not request.user or not request.user.is_authenticated:
            return False

        team = getattr(obj, "team", obj)

        # Safe methods - can view
        if request.method in permissions.SAFE_METHODS:
            return team.can_view(request.user)

        # Modifying methods - need maintainer access or manage_teams permission
        try:
            membership = TeamMember.objects.get(team=team, user=request.user)
            if membership.is_maintainer():
                return True
        except TeamMember.DoesNotExist:
            pass

        return team.organization.has_permission(request.user, "manage_teams")


# ============================================================================
# Project Permissions
# ============================================================================


class CanViewProject(permissions.BasePermission):
    """Permission check: User can view project"""

    def has_object_permission(self, request, view, obj):
        """Check if user can view project"""
        if not request.user or not request.user.is_authenticated:
            return False

        project = getattr(obj, "project", obj)
        return project.can_view(request.user)


class IsProjectMember(permissions.BasePermission):
    """Permission check: User is project member"""

    def has_object_permission(self, request, view, obj):
        """Check if user is project member"""
        if not request.user or not request.user.is_authenticated:
            return False

        project = getattr(obj, "project", obj)
        return project.is_member(request.user)


class IsProjectAdmin(permissions.BasePermission):
    """Permission check: User is project admin or owner"""

    def has_object_permission(self, request, view, obj):
        """Check if user is project admin"""
        if not request.user or not request.user.is_authenticated:
            return False

        project = getattr(obj, "project", obj)

        try:
            membership = ProjectMember.objects.get(project=project, user=request.user)
            return membership.is_admin()
        except ProjectMember.DoesNotExist:
            return False


class IsProjectOwner(permissions.BasePermission):
    """Permission check: User is project owner"""

    def has_object_permission(self, request, view, obj):
        """Check if user is project owner"""
        if not request.user or not request.user.is_authenticated:
            return False

        project = getattr(obj, "project", obj)
        return project.is_owner(request.user)


class CanManageProjects(permissions.BasePermission):
    """Permission check: User can manage projects in organization"""

    def has_object_permission(self, request, view, obj):
        """Check manage_projects permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        project = getattr(obj, "project", obj)
        organization = project.organization

        return organization.has_permission(request.user, "manage_projects")


class ProjectPermission(permissions.BasePermission):
    """Combined permission for project operations"""

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check permissions based on HTTP method"""
        if not request.user or not request.user.is_authenticated:
            return False

        project = getattr(obj, "project", obj)

        # Safe methods - can view
        if request.method in permissions.SAFE_METHODS:
            return project.can_view(request.user)

        # DELETE method - need owner access
        if request.method == "DELETE":
            return project.is_owner(request.user)

        # Modifying methods - need member access who can edit
        try:
            membership = ProjectMember.objects.get(project=project, user=request.user)
            return membership.can_edit()
        except ProjectMember.DoesNotExist:
            pass

        return project.organization.has_permission(request.user, "manage_projects")
