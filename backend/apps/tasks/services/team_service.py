"""
Team Service
Business logic layer for Team operations.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from apps.core.services.base import BaseService
from apps.tasks.repositories import TeamRepository, TeamMemberRepository
from apps.tasks.models import Team, TeamMember


class TeamService(BaseService):
    """Service for Team business logic"""

    repository_class = TeamRepository

    def __init__(self):
        self.repository = TeamRepository()
        self.member_repository = TeamMemberRepository()

    def validate_create_data(self, data):
        """Validate team creation data"""
        errors = {}

        # Validate name
        if not data.get("name"):
            errors["name"] = "Team name is required"
        elif len(data["name"]) < 2:
            errors["name"] = "Team name must be at least 2 characters"

        # Validate organization
        if not data.get("organization"):
            errors["organization"] = "Organization is required"

        # Check name uniqueness within organization
        if data.get("organization") and data.get("name"):
            if self.repository.name_exists(data["organization"], data["name"]):
                errors["name"] = "Team name already exists in this organization"

        if errors:
            raise ValidationError(errors)

        return data

    def validate_update_data(self, team, data):
        """Validate team update data"""
        errors = {}

        # Validate name if being updated
        if "name" in data:
            if not data["name"]:
                errors["name"] = "Team name is required"
            elif len(data["name"]) < 2:
                errors["name"] = "Team name must be at least 2 characters"
            elif self.repository.name_exists(
                team.organization, data["name"], exclude_id=team.id
            ):
                errors["name"] = "Team name already exists in this organization"

        if errors:
            raise ValidationError(errors)

        return data

    @transaction.atomic
    def create_team(self, organization, data, created_by):
        """Create new team"""
        # Check permission
        if not organization.has_permission(created_by, "manage_teams"):
            raise ValidationError("You do not have permission to create teams")

        # Set organization
        data["organization"] = organization

        # Validate data
        self.validate_create_data(data)

        # Create team
        team = self.repository.create(data)

        # If lead is specified, add them as team member with lead role
        if "lead" in data and data["lead"]:
            self.member_repository.create(
                {
                    "team": team,
                    "user": data["lead"],
                    "role": TeamMember.Role.LEAD,
                    "added_by": created_by,
                }
            )
            team.increment_member_count()

        return team

    def update_team(self, team, data, user):
        """Update team"""
        # Check permission
        membership = self.member_repository.get_membership(team, user)
        if not membership or not membership.can_manage_members():
            if not team.organization.has_permission(user, "manage_teams"):
                raise ValidationError("You do not have permission to update this team")

        # Validate data
        self.validate_update_data(team, data)

        # If lead is being changed, update memberships
        if "lead" in data:
            old_lead = team.lead
            new_lead = data["lead"]

            # Remove old lead role if exists
            if old_lead:
                old_membership = self.member_repository.get_membership(team, old_lead)
                if old_membership and old_membership.is_lead():
                    self.member_repository.update(
                        old_membership.id, {"role": TeamMember.Role.MAINTAINER}
                    )

            # Add or update new lead
            if new_lead:
                new_membership = self.member_repository.get_membership(team, new_lead)
                if new_membership:
                    self.member_repository.update(
                        new_membership.id, {"role": TeamMember.Role.LEAD}
                    )
                else:
                    # Add new lead as member
                    self.member_repository.create(
                        {
                            "team": team,
                            "user": new_lead,
                            "role": TeamMember.Role.LEAD,
                            "added_by": user,
                        }
                    )
                    team.increment_member_count()

        # Update team
        return self.repository.update(team.id, data)

    @transaction.atomic
    def delete_team(self, team, user):
        """Soft delete team"""
        # Check permission
        if not team.organization.has_permission(user, "manage_teams"):
            raise ValidationError("You do not have permission to delete teams")

        # Soft delete team
        return self.repository.delete(team.id)

    def get_user_teams(self, organization, user):
        """Get teams user is member of"""
        return self.repository.get_user_teams(organization, user)

    def get_visible_teams(self, organization, user):
        """Get teams visible to user"""
        return self.repository.get_visible_teams(organization, user)

    def search_teams(self, organization, query, user):
        """Search teams"""
        return self.repository.search_teams(organization, query, user)

    def get_team_statistics(self, team_id):
        """Get team statistics"""
        return self.repository.get_team_statistics(team_id)

    def get_organization_statistics(self, organization):
        """Get team statistics for organization"""
        return self.repository.get_organization_statistics(organization)

    def change_visibility(self, team, visibility, user):
        """Change team visibility"""
        # Check permission
        membership = self.member_repository.get_membership(team, user)
        if not membership or not membership.can_manage_members():
            if not team.organization.has_permission(user, "manage_teams"):
                raise ValidationError(
                    "You do not have permission to change team visibility"
                )

        return self.repository.update(team.id, {"visibility": visibility})
