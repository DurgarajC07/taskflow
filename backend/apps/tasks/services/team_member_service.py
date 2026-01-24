"""
Team Member Service
Business logic layer for team membership operations.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from apps.core.services.base import BaseService
from apps.tasks.repositories import TeamMemberRepository, TeamRepository
from apps.tasks.models import TeamMember


class TeamMemberService(BaseService):
    """Service for TeamMember business logic"""

    repository_class = TeamMemberRepository

    def __init__(self):
        self.repository = TeamMemberRepository()
        self.team_repository = TeamRepository()

    def validate_add_member_data(self, team, data):
        """Validate member addition data"""
        errors = {}

        # Validate user
        if not data.get("user"):
            errors["user"] = "User is required"

        # Check if user is organization member
        if data.get("user") and not team.organization.is_member(data["user"]):
            errors["user"] = "User must be a member of the organization"

        # Check if user is already a team member
        if data.get("user") and self.repository.get_membership(team, data["user"]):
            errors["user"] = "User is already a member of this team"

        # Validate role
        if "role" in data and data["role"] not in dict(TeamMember.Role.choices):
            errors["role"] = "Invalid role"

        if errors:
            raise ValidationError(errors)

        return data

    @transaction.atomic
    def add_member(self, team, user, role, added_by):
        """Add member to team"""
        # Check permission
        adder_membership = self.repository.get_membership(team, added_by)
        if not adder_membership or not adder_membership.can_manage_members():
            if not team.organization.has_permission(added_by, "manage_teams"):
                raise ValidationError("You do not have permission to add team members")

        # Validate data
        data = {"user": user, "role": role}
        self.validate_add_member_data(team, data)

        # Create membership
        member = self.repository.create(
            {
                "team": team,
                "user": user,
                "role": role,
                "added_by": added_by,
            }
        )

        # Increment team member count
        team.increment_member_count()

        # If adding as lead, update team lead field
        if role == TeamMember.Role.LEAD:
            self.team_repository.update(team.id, {"lead": user})

        return member

    @transaction.atomic
    def remove_member(self, team, user, removed_by):
        """Remove member from team"""
        # Check permission
        remover_membership = self.repository.get_membership(team, removed_by)
        if not remover_membership or not remover_membership.can_manage_members():
            if not team.organization.has_permission(removed_by, "manage_teams"):
                raise ValidationError(
                    "You do not have permission to remove team members"
                )

        # Get membership
        membership = self.repository.get_membership(team, user)
        if not membership:
            raise ValidationError("User is not a member of this team")

        # Cannot remove yourself if you're the only lead
        if user == removed_by and membership.is_lead():
            lead_count = self.repository.get_leads(team).count()
            if lead_count <= 1:
                raise ValidationError("Cannot remove yourself as the only team lead")

        # If removing lead, clear team lead field
        if membership.is_lead() and team.lead == user:
            self.team_repository.update(team.id, {"lead": None})

        # Delete membership
        self.repository.delete(membership.id)

        # Decrement team member count
        team.decrement_member_count()

        return True

    @transaction.atomic
    def leave_team(self, team, user):
        """User leaves team"""
        # Get membership
        membership = self.repository.get_membership(team, user)
        if not membership:
            raise ValidationError("You are not a member of this team")

        # Cannot leave if you're the only lead
        if membership.is_lead():
            lead_count = self.repository.get_leads(team).count()
            if lead_count <= 1:
                raise ValidationError(
                    "Cannot leave team as the only lead. Assign another lead first."
                )

        # If leaving as lead, clear team lead field
        if membership.is_lead() and team.lead == user:
            self.team_repository.update(team.id, {"lead": None})

        # Delete membership
        self.repository.delete(membership.id)

        # Decrement team member count
        team.decrement_member_count()

        return True

    def update_member_role(self, team, user, new_role, updated_by):
        """Update member role"""
        # Check permission
        updater_membership = self.repository.get_membership(team, updated_by)
        if not updater_membership or not updater_membership.can_manage_members():
            if not team.organization.has_permission(updated_by, "manage_teams"):
                raise ValidationError(
                    "You do not have permission to update member roles"
                )

        # Get membership
        membership = self.repository.get_membership(team, user)
        if not membership:
            raise ValidationError("User is not a member of this team")

        old_role = membership.role

        # Update role
        updated_membership = self.repository.update(membership.id, {"role": new_role})

        # Update team lead field if needed
        if new_role == TeamMember.Role.LEAD:
            self.team_repository.update(team.id, {"lead": user})
        elif old_role == TeamMember.Role.LEAD and team.lead == user:
            self.team_repository.update(team.id, {"lead": None})

        return updated_membership

    @transaction.atomic
    def transfer_lead(self, team, new_lead, current_lead):
        """Transfer team lead role"""
        # Verify current lead
        current_membership = self.repository.get_membership(team, current_lead)
        if not current_membership or not current_membership.is_lead():
            raise ValidationError("Only team lead can transfer leadership")

        # Get new lead membership
        new_membership = self.repository.get_membership(team, new_lead)
        if not new_membership:
            raise ValidationError("New lead must be a team member")

        # Update roles
        self.repository.update(
            current_membership.id, {"role": TeamMember.Role.MAINTAINER}
        )
        self.repository.update(new_membership.id, {"role": TeamMember.Role.LEAD})

        # Update team lead
        self.team_repository.update(team.id, {"lead": new_lead})

        return True

    def get_member_statistics(self, team):
        """Get team member statistics"""
        return self.repository.get_member_statistics(team)

    def search_members(self, team, query):
        """Search team members"""
        return self.repository.search_members(team, query)
