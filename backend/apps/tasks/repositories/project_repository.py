"""
Project Repository
Data access layer for Project model.
"""

from django.db import models
from django.db.models import Q, Count, Avg, F
from apps.tasks.models import Project


class ProjectRepository:
    """Repository for Project data access"""

    @staticmethod
    def get_by_id(project_id):
        """Get project by ID"""
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return None

    @staticmethod
    def get_by_key(organization, key):
        """Get project by key within organization"""
        try:
            return Project.objects.get(organization=organization, key=key)
        except Project.DoesNotExist:
            return None

    @staticmethod
    def get_organization_projects(organization, include_deleted=False):
        """Get all projects for an organization"""
        if include_deleted:
            return Project.all_objects.filter(organization=organization)
        return Project.objects.filter(organization=organization)

    @staticmethod
    def get_user_projects(user, organization=None):
        """Get all projects user is member of"""
        queryset = Project.objects.filter(members=user)
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset.distinct()

    @staticmethod
    def get_team_projects(team):
        """Get all projects assigned to a team"""
        return Project.objects.filter(team=team)

    @staticmethod
    def get_owned_projects(user, organization=None):
        """Get projects owned by user"""
        queryset = Project.objects.filter(owner=user)
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset

    @staticmethod
    def get_visible_projects(user, organization):
        """Get all projects visible to user"""
        # Public projects
        public_q = Q(visibility=Project.Visibility.PUBLIC)

        # Private projects where user is member or team member
        private_q = Q(visibility=Project.Visibility.PRIVATE) & (
            Q(members=user) | Q(team__members=user)
        )

        # Secret projects where user is member
        secret_q = Q(visibility=Project.Visibility.SECRET) & Q(members=user)

        return (
            Project.objects.filter(organization=organization)
            .filter(public_q | private_q | secret_q)
            .distinct()
        )

    @staticmethod
    def search_projects(organization, query):
        """Search projects by name, key, or description"""
        return Project.objects.filter(organization=organization).filter(
            Q(name__icontains=query)
            | Q(key__icontains=query)
            | Q(description__icontains=query)
        )

    @staticmethod
    def filter_by_status(queryset, status):
        """Filter projects by status"""
        return queryset.filter(status=status)

    @staticmethod
    def filter_by_priority(queryset, priority):
        """Filter projects by priority"""
        return queryset.filter(priority=priority)

    @staticmethod
    def filter_by_visibility(queryset, visibility):
        """Filter projects by visibility"""
        return queryset.filter(visibility=visibility)

    @staticmethod
    def filter_by_team(queryset, team):
        """Filter projects by team"""
        return queryset.filter(team=team)

    @staticmethod
    def filter_by_owner(queryset, owner):
        """Filter projects by owner"""
        return queryset.filter(owner=owner)

    @staticmethod
    def get_active_projects(organization):
        """Get active projects"""
        return Project.objects.filter(
            organization=organization, status=Project.Status.ACTIVE
        )

    @staticmethod
    def get_overdue_projects(organization):
        """Get projects past their due date"""
        from django.utils import timezone as django_timezone

        return Project.objects.filter(
            organization=organization,
            status__in=[Project.Status.PLANNING, Project.Status.ACTIVE],
            due_date__lt=django_timezone.now().date(),
        )

    @staticmethod
    def get_completed_projects(organization):
        """Get completed projects"""
        return Project.objects.filter(
            organization=organization, status=Project.Status.COMPLETED
        )

    @staticmethod
    def get_templates(organization):
        """Get project templates"""
        return Project.objects.filter(organization=organization, is_template=True)

    @staticmethod
    def create_project(data):
        """Create new project"""
        return Project.objects.create(**data)

    @staticmethod
    def update_project(project, data):
        """Update project"""
        for key, value in data.items():
            setattr(project, key, value)
        project.save()
        return project

    @staticmethod
    def delete_project(project, user=None):
        """Soft delete project"""
        project.soft_delete(user)
        return project

    @staticmethod
    def restore_project(project):
        """Restore soft-deleted project"""
        project.restore()
        return project

    @staticmethod
    def permanent_delete(project):
        """Permanently delete project"""
        project.delete()

    @staticmethod
    def get_statistics(organization):
        """Get project statistics for organization"""
        projects = Project.objects.filter(organization=organization)

        return {
            "total": projects.count(),
            "active": projects.filter(status=Project.Status.ACTIVE).count(),
            "planning": projects.filter(status=Project.Status.PLANNING).count(),
            "on_hold": projects.filter(status=Project.Status.ON_HOLD).count(),
            "completed": projects.filter(status=Project.Status.COMPLETED).count(),
            "archived": projects.filter(status=Project.Status.ARCHIVED).count(),
            "high_priority": projects.filter(priority=Project.Priority.HIGH).count(),
            "critical_priority": projects.filter(
                priority=Project.Priority.CRITICAL
            ).count(),
            "avg_progress": projects.aggregate(avg=Avg("progress"))["avg"] or 0,
            "total_tasks": projects.aggregate(sum=models.Sum("task_count"))["sum"] or 0,
            "completed_tasks": projects.aggregate(
                sum=models.Sum("completed_task_count")
            )["sum"]
            or 0,
        }

    @staticmethod
    def get_project_statistics(project):
        """Get detailed statistics for a single project"""
        return {
            "member_count": project.member_count,
            "task_count": project.task_count,
            "open_task_count": project.open_task_count,
            "completed_task_count": project.completed_task_count,
            "progress": float(project.progress),
        }

    @staticmethod
    def update_member_count(project):
        """Update member count from actual members"""
        count = project.members.count()
        project.member_count = count
        project.save(update_fields=["member_count"])
        return count

    @staticmethod
    def key_exists(organization, key, exclude_project=None):
        """Check if project key exists in organization"""
        queryset = Project.objects.filter(organization=organization, key=key)
        if exclude_project:
            queryset = queryset.exclude(id=exclude_project.id)
        return queryset.exists()
