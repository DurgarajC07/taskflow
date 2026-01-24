"""
Project Service
Business logic for project operations.
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.tasks.repositories import ProjectRepository, ProjectMemberRepository
from apps.organizations.repositories import OrganizationRepository


class ProjectService:
    """Service for project business logic"""

    @staticmethod
    def create_project(organization, owner, data):
        """Create new project with owner as first member"""
        # Validate organization membership
        if not OrganizationRepository.is_member(organization, owner):
            raise PermissionDenied("User must be organization member")

        # Validate key uniqueness
        key = data.get("key")
        if ProjectRepository.key_exists(organization, key):
            raise ValidationError({"key": "Project key already exists in organization"})

        # Validate team ownership
        team = data.get("team")
        if team and team.organization != organization:
            raise ValidationError({"team": "Team must belong to same organization"})

        with transaction.atomic():
            # Create project
            project_data = {
                **data,
                "organization": organization,
                "owner": owner,
                "created_by": owner,
            }
            project = ProjectRepository.create_project(project_data)

            # Add owner as project member
            from apps.tasks.services import ProjectMemberService

            ProjectMemberService.add_member(
                project=project,
                user=owner,
                role="owner",
                added_by=owner,
            )

            # Increment team's project count if assigned
            if team:
                team.increment_project_count()

        return project

    @staticmethod
    def update_project(project, user, data):
        """Update project"""
        # Check permissions
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to edit project")

        # Validate key if changed
        new_key = data.get("key")
        if new_key and new_key != project.key:
            if ProjectRepository.key_exists(
                project.organization, new_key, exclude_project=project
            ):
                raise ValidationError(
                    {"key": "Project key already exists in organization"}
                )

        # Handle team assignment changes
        old_team = project.team
        new_team = data.get("team")

        with transaction.atomic():
            # Update project
            data["updated_by"] = user
            project = ProjectRepository.update_project(project, data)

            # Update team project counts
            if old_team != new_team:
                if old_team:
                    old_team.decrement_project_count()
                if new_team:
                    if new_team.organization != project.organization:
                        raise ValidationError(
                            {"team": "Team must belong to same organization"}
                        )
                    new_team.increment_project_count()

        return project

    @staticmethod
    def delete_project(project, user):
        """Soft delete project"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.is_owner():
            raise PermissionDenied("Only project owner can delete project")

        with transaction.atomic():
            # Decrement team project count
            if project.team:
                project.team.decrement_project_count()

            ProjectRepository.delete_project(project, user)

        return project

    @staticmethod
    def restore_project(project, user):
        """Restore soft-deleted project"""
        # Check organization admin permission
        if not project.organization.has_permission(user, "manage_projects"):
            raise PermissionDenied("No permission to restore project")

        with transaction.atomic():
            project = ProjectRepository.restore_project(project)

            # Increment team project count
            if project.team:
                project.team.increment_project_count()

        return project

    @staticmethod
    def archive_project(project, user):
        """Archive project"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.is_admin():
            raise PermissionDenied("Only project admins can archive project")

        project.archive()
        return project

    @staticmethod
    def complete_project(project, user):
        """Mark project as completed"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.is_admin():
            raise PermissionDenied("Only project admins can complete project")

        project.mark_completed()
        return project

    @staticmethod
    def change_status(project, user, new_status):
        """Change project status"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to change project status")

        # Validate status
        from apps.tasks.models import Project

        if new_status not in dict(Project.Status.choices):
            raise ValidationError({"status": "Invalid status"})

        project.status = new_status
        if new_status == Project.Status.COMPLETED:
            from django.utils import timezone as django_timezone

            project.completed_at = django_timezone.now()

        project.save(update_fields=["status", "completed_at"])
        return project

    @staticmethod
    def change_visibility(project, user, new_visibility):
        """Change project visibility"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.is_admin():
            raise PermissionDenied("Only project admins can change visibility")

        # Validate visibility
        from apps.tasks.models import Project

        if new_visibility not in dict(Project.Visibility.choices):
            raise ValidationError({"visibility": "Invalid visibility level"})

        project.visibility = new_visibility
        project.save(update_fields=["visibility"])
        return project

    @staticmethod
    def assign_team(project, user, team):
        """Assign team to project"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.is_admin():
            raise PermissionDenied("Only project admins can assign teams")

        if team and team.organization != project.organization:
            raise ValidationError({"team": "Team must belong to same organization"})

        old_team = project.team

        with transaction.atomic():
            project.team = team
            project.save(update_fields=["team"])

            # Update team project counts
            if old_team:
                old_team.decrement_project_count()
            if team:
                team.increment_project_count()

        return project

    @staticmethod
    def transfer_ownership(project, current_owner, new_owner):
        """Transfer project ownership"""
        # Validate current owner
        if project.owner != current_owner:
            raise PermissionDenied("Only current owner can transfer ownership")

        # Validate new owner is member
        new_member = ProjectMemberRepository.get_project_member(project, new_owner)
        if not new_member:
            raise ValidationError({"user": "New owner must be a project member"})

        with transaction.atomic():
            # Update project owner
            project.owner = new_owner
            project.save(update_fields=["owner"])

            # Update member roles
            new_member.role = "owner"
            new_member.save(update_fields=["role"])

            old_member = ProjectMemberRepository.get_project_member(
                project, current_owner
            )
            if old_member:
                old_member.role = "admin"
                old_member.save(update_fields=["role"])

        return project

    @staticmethod
    def duplicate_project(project, user, new_name, new_key):
        """Duplicate project as template"""
        # Check permissions
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member:
            raise PermissionDenied("Must be project member to duplicate")

        # Validate new key
        if ProjectRepository.key_exists(project.organization, new_key):
            raise ValidationError({"key": "Project key already exists"})

        # Create duplicate
        duplicate_data = {
            "name": new_name,
            "key": new_key,
            "description": project.description,
            "color": project.color,
            "icon": project.icon,
            "visibility": project.visibility,
            "priority": project.priority,
            "team": project.team,
            "settings": project.settings.copy() if project.settings else {},
        }

        return ProjectService.create_project(
            organization=project.organization,
            owner=user,
            data=duplicate_data,
        )

    @staticmethod
    def get_statistics(project):
        """Get project statistics"""
        return ProjectRepository.get_project_statistics(project)

    @staticmethod
    def update_progress(project):
        """Update project progress based on tasks"""
        project.update_progress()
        return project
