"""
Team Repository
Data access layer for Team model.
"""

from django.db.models import Q, Count
from apps.core.repositories.base import OrganizationRepository
from apps.tasks.models import Team


class TeamRepository(OrganizationRepository):
    """Repository for Team model"""

    model = Team

    def get_by_name(self, organization, name):
        """Get team by name within organization"""
        try:
            return self.model.objects.get(organization=organization, name=name)
        except self.model.DoesNotExist:
            return None

    def get_public_teams(self, organization):
        """Get public teams in organization"""
        return self.get_by_organization(organization).filter(
            visibility=Team.Visibility.PUBLIC
        )

    def get_private_teams(self, organization):
        """Get private teams in organization"""
        return self.get_by_organization(organization).filter(
            visibility=Team.Visibility.PRIVATE
        )

    def get_user_teams(self, organization, user):
        """Get teams user is member of"""
        return self.get_by_organization(organization).filter(members=user).distinct()

    def get_visible_teams(self, organization, user):
        """Get teams visible to user"""
        # Public teams + teams user is member of
        return (
            self.get_by_organization(organization)
            .filter(Q(visibility=Team.Visibility.PUBLIC) | Q(members=user))
            .distinct()
        )

    def get_by_lead(self, organization, user):
        """Get teams led by user"""
        return self.get_by_organization(organization).filter(lead=user)

    def search_teams(self, organization, query, user=None):
        """Search teams by name or description"""
        queryset = self.get_by_organization(organization)

        # Filter by visibility if user provided
        if user:
            queryset = self.get_visible_teams(organization, user)

        # Search
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        return queryset

    def name_exists(self, organization, name, exclude_id=None):
        """Check if team name exists in organization"""
        queryset = self.get_by_organization(organization).filter(name=name)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    def get_team_statistics(self, team_id):
        """Get team statistics"""
        try:
            team = self.get_by_id(team_id)
            if not team:
                return None

            return {
                "id": str(team.id),
                "name": team.name,
                "organization": team.organization.name,
                "member_count": team.member_count,
                "project_count": team.project_count,
                "visibility": team.visibility,
                "lead": {
                    "id": str(team.lead.id) if team.lead else None,
                    "email": team.lead.email if team.lead else None,
                    "name": (
                        f"{team.lead.first_name} {team.lead.last_name}".strip()
                        if team.lead
                        else None
                    ),
                },
                "created_at": team.created_at,
            }
        except Exception:
            return None

    def get_organization_statistics(self, organization):
        """Get team statistics for entire organization"""
        teams = self.get_by_organization(organization)

        return {
            "total_teams": teams.count(),
            "public_teams": teams.filter(visibility=Team.Visibility.PUBLIC).count(),
            "private_teams": teams.filter(visibility=Team.Visibility.PRIVATE).count(),
            "secret_teams": teams.filter(visibility=Team.Visibility.SECRET).count(),
            "total_members": sum(team.member_count for team in teams),
            "teams_with_lead": teams.exclude(lead__isnull=True).count(),
        }

    def update_member_count(self, team_id):
        """Recalculate and update team member count"""
        from apps.tasks.models import TeamMember

        try:
            team = self.get_by_id(team_id)
            if not team:
                return False

            # Recalculate member count
            member_count = TeamMember.objects.filter(team=team).count()

            # Update team
            team.member_count = member_count
            team.save(update_fields=["member_count"])

            return True
        except Exception:
            return False
