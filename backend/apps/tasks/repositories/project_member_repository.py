"""
Project Member Repository
Data access layer for ProjectMember model.
"""

from django.db.models import Q, Count
from apps.tasks.models import ProjectMember


class ProjectMemberRepository:
    """Repository for ProjectMember data access"""

    @staticmethod
    def get_by_id(member_id):
        """Get project member by ID"""
        try:
            return ProjectMember.objects.get(id=member_id)
        except ProjectMember.DoesNotExist:
            return None

    @staticmethod
    def get_project_member(project, user):
        """Get specific project member"""
        try:
            return ProjectMember.objects.get(project=project, user=user)
        except ProjectMember.DoesNotExist:
            return None

    @staticmethod
    def get_project_members(project):
        """Get all members of a project"""
        return ProjectMember.objects.filter(project=project).select_related("user")

    @staticmethod
    def get_user_memberships(user, organization=None):
        """Get all project memberships for user"""
        queryset = ProjectMember.objects.filter(user=user).select_related("project")
        if organization:
            queryset = queryset.filter(project__organization=organization)
        return queryset

    @staticmethod
    def filter_by_role(queryset, role):
        """Filter members by role"""
        return queryset.filter(role=role)

    @staticmethod
    def get_owners(project):
        """Get project owners"""
        return ProjectMember.objects.filter(
            project=project, role=ProjectMember.Role.OWNER
        )

    @staticmethod
    def get_admins(project):
        """Get project admins (including owners)"""
        return ProjectMember.objects.filter(
            project=project,
            role__in=[ProjectMember.Role.OWNER, ProjectMember.Role.ADMIN],
        )

    @staticmethod
    def is_member(project, user):
        """Check if user is project member"""
        return ProjectMember.objects.filter(project=project, user=user).exists()

    @staticmethod
    def get_member_role(project, user):
        """Get user's role in project"""
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role
        except ProjectMember.DoesNotExist:
            return None

    @staticmethod
    def create_member(data):
        """Create new project member"""
        return ProjectMember.objects.create(**data)

    @staticmethod
    def update_member(member, data):
        """Update project member"""
        for key, value in data.items():
            setattr(member, key, value)
        member.save()
        return member

    @staticmethod
    def delete_member(member):
        """Delete project member"""
        member.delete()

    @staticmethod
    def bulk_create_members(members_data):
        """Bulk create project members"""
        members = [ProjectMember(**data) for data in members_data]
        return ProjectMember.objects.bulk_create(members)

    @staticmethod
    def search_members(project, query):
        """Search project members by name or email"""
        return ProjectMember.objects.filter(project=project).filter(
            Q(user__email__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
        )

    @staticmethod
    def get_statistics(project):
        """Get member statistics for project"""
        members = ProjectMember.objects.filter(project=project)

        return {
            "total": members.count(),
            "owners": members.filter(role=ProjectMember.Role.OWNER).count(),
            "admins": members.filter(role=ProjectMember.Role.ADMIN).count(),
            "members": members.filter(role=ProjectMember.Role.MEMBER).count(),
            "viewers": members.filter(role=ProjectMember.Role.VIEWER).count(),
        }

    @staticmethod
    def get_active_members(project, days=30):
        """Get recently active members"""
        from django.utils import timezone as django_timezone
        from datetime import timedelta

        cutoff = django_timezone.now() - timedelta(days=days)
        return ProjectMember.objects.filter(project=project, last_active_at__gte=cutoff)

    @staticmethod
    def update_last_active(member):
        """Update member's last active timestamp"""
        member.update_last_active()
        return member

    @staticmethod
    def has_permission(member, permission):
        """Check if member has specific permission"""
        # Check custom permissions first
        if permission in member.custom_permissions:
            return member.custom_permissions[permission]

        # Role-based permissions
        role_permissions = {
            ProjectMember.Role.OWNER: [
                "view",
                "edit",
                "delete",
                "manage_members",
                "manage_settings",
                "manage_tasks",
            ],
            ProjectMember.Role.ADMIN: [
                "view",
                "edit",
                "manage_members",
                "manage_tasks",
            ],
            ProjectMember.Role.MEMBER: ["view", "edit", "manage_tasks"],
            ProjectMember.Role.VIEWER: ["view"],
        }

        return permission in role_permissions.get(member.role, [])

    @staticmethod
    def count_projects_for_user(user, organization=None):
        """Count number of projects user is member of"""
        queryset = ProjectMember.objects.filter(user=user)
        if organization:
            queryset = queryset.filter(project__organization=organization)
        return queryset.count()
