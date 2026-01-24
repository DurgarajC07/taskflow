"""
Project Member Service
Business logic for project member operations.
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.tasks.repositories import ProjectRepository, ProjectMemberRepository
from apps.tasks.models import ProjectMember


class ProjectMemberService:
    """Service for project member business logic"""

    @staticmethod
    def add_member(project, user, role, added_by):
        """Add member to project"""
        # Check if already member
        if ProjectMemberRepository.is_member(project, user):
            raise ValidationError({"user": "User is already a project member"})

        # Validate user is org member
        if not project.organization.is_member(user):
            raise ValidationError({"user": "User must be organization member"})

        # Validate role
        if role not in dict(ProjectMember.Role.choices):
            raise ValidationError({"role": "Invalid role"})

        with transaction.atomic():
            # Create membership
            member_data = {
                "project": project,
                "user": user,
                "role": role,
                "added_by": added_by,
                "created_by": added_by,
            }
            member = ProjectMemberRepository.create_member(member_data)

            # Update project member count
            project.increment_member_count()

        return member

    @staticmethod
    def remove_member(project, user, removed_by):
        """Remove member from project"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member:
            raise ValidationError({"user": "User is not a project member"})

        # Cannot remove owner
        if member.is_owner():
            raise ValidationError({"user": "Cannot remove project owner"})

        # Check permissions
        remover_member = ProjectMemberRepository.get_project_member(project, removed_by)
        if not remover_member or not remover_member.can_manage_members():
            raise PermissionDenied("No permission to remove members")

        with transaction.atomic():
            ProjectMemberRepository.delete_member(member)
            project.decrement_member_count()

        return member

    @staticmethod
    def leave_project(project, user):
        """User leaves project"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member:
            raise ValidationError({"user": "User is not a project member"})

        # Owner cannot leave
        if member.is_owner():
            raise ValidationError(
                {"user": "Project owner cannot leave. Transfer ownership first."}
            )

        with transaction.atomic():
            ProjectMemberRepository.delete_member(member)
            project.decrement_member_count()

        return member

    @staticmethod
    def update_role(project, user, new_role, updated_by):
        """Update member role"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member:
            raise ValidationError({"user": "User is not a project member"})

        # Cannot change owner role directly
        if member.is_owner() or new_role == ProjectMember.Role.OWNER:
            raise ValidationError({"role": "Use transfer ownership to change owner"})

        # Check permissions
        updater_member = ProjectMemberRepository.get_project_member(project, updated_by)
        if not updater_member or not updater_member.can_manage_members():
            raise PermissionDenied("No permission to update member roles")

        # Validate role
        if new_role not in dict(ProjectMember.Role.choices):
            raise ValidationError({"role": "Invalid role"})

        member.role = new_role
        member.save(update_fields=["role"])
        return member

    @staticmethod
    def update_permissions(project, user, permissions, updated_by):
        """Update member custom permissions"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member:
            raise ValidationError({"user": "User is not a project member"})

        # Check permissions
        updater_member = ProjectMemberRepository.get_project_member(project, updated_by)
        if not updater_member or not updater_member.is_owner():
            raise PermissionDenied("Only project owner can update permissions")

        member.custom_permissions = permissions
        member.save(update_fields=["custom_permissions"])
        return member

    @staticmethod
    def bulk_add_members(project, users_data, added_by):
        """Add multiple members at once"""
        # Check permissions
        adder_member = ProjectMemberRepository.get_project_member(project, added_by)
        if not adder_member or not adder_member.can_manage_members():
            raise PermissionDenied("No permission to add members")

        members = []
        for user_data in users_data:
            user = user_data["user"]
            role = user_data.get("role", ProjectMember.Role.MEMBER)

            # Skip if already member
            if ProjectMemberRepository.is_member(project, user):
                continue

            # Validate org membership
            if not project.organization.is_member(user):
                continue

            members.append(
                {
                    "project": project,
                    "user": user,
                    "role": role,
                    "added_by": added_by,
                    "created_by": added_by,
                }
            )

        if members:
            with transaction.atomic():
                created_members = ProjectMemberRepository.bulk_create_members(members)
                # Update member count
                ProjectRepository.update_member_count(project)

            return created_members

        return []

    @staticmethod
    def add_team_members(project, team, added_by):
        """Add all team members to project"""
        # Check permissions
        adder_member = ProjectMemberRepository.get_project_member(project, added_by)
        if not adder_member or not adder_member.is_admin():
            raise PermissionDenied("Only project admins can add team members")

        # Validate team belongs to same org
        if team.organization != project.organization:
            raise ValidationError({"team": "Team must belong to same organization"})

        # Get team members not already in project
        team_members = team.members.all()
        members_to_add = []

        for user in team_members:
            if not ProjectMemberRepository.is_member(project, user):
                members_to_add.append(
                    {
                        "user": user,
                        "role": ProjectMember.Role.MEMBER,
                    }
                )

        return ProjectMemberService.bulk_add_members(project, members_to_add, added_by)

    @staticmethod
    def get_member_statistics(project):
        """Get member statistics"""
        return ProjectMemberRepository.get_statistics(project)

    @staticmethod
    def update_last_active(project, user):
        """Update member's last active timestamp"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if member:
            ProjectMemberRepository.update_last_active(member)
        return member

    @staticmethod
    def has_permission(project, user, permission):
        """Check if user has permission in project"""
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member:
            return False

        return ProjectMemberRepository.has_permission(member, permission)
