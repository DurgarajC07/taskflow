"""
Team Member Repository
Data access layer for TeamMember model.
"""

from django.db.models import Q, Count
from django.utils import timezone as django_timezone
from apps.core.repositories.base import BaseRepository
from apps.tasks.models import TeamMember


class TeamMemberRepository(BaseRepository):
    """Repository for TeamMember model"""

    model = TeamMember

    def get_by_team(self, team, role=None):
        """Get members of team"""
        queryset = self.model.objects.filter(team=team)
        if role:
            queryset = queryset.filter(role=role)
        return queryset

    def get_by_user(self, user):
        """Get user's team memberships"""
        return self.model.objects.filter(user=user)

    def get_membership(self, team, user):
        """Get specific team membership"""
        try:
            return self.model.objects.get(team=team, user=user)
        except self.model.DoesNotExist:
            return None

    def get_leads(self, team):
        """Get team leads"""
        return self.model.objects.filter(team=team, role=TeamMember.Role.LEAD)

    def get_maintainers(self, team):
        """Get team maintainers (leads + maintainers)"""
        return self.model.objects.filter(
            team=team, role__in=[TeamMember.Role.LEAD, TeamMember.Role.MAINTAINER]
        )

    def user_is_member(self, team, user):
        """Check if user is team member"""
        return self.model.objects.filter(team=team, user=user).exists()

    def user_is_lead(self, team, user):
        """Check if user is team lead"""
        return self.model.objects.filter(
            team=team, user=user, role=TeamMember.Role.LEAD
        ).exists()

    def user_is_maintainer(self, team, user):
        """Check if user is maintainer or lead"""
        return self.model.objects.filter(
            team=team,
            user=user,
            role__in=[TeamMember.Role.LEAD, TeamMember.Role.MAINTAINER],
        ).exists()

    def search_members(self, team, query):
        """Search team members"""
        queryset = self.model.objects.filter(team=team)

        if query:
            queryset = queryset.filter(
                Q(user__email__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
            )

        return queryset

    def get_member_statistics(self, team):
        """Get team member statistics"""
        members = self.model.objects.filter(team=team)

        return {
            "total": members.count(),
            "by_role": {
                "leads": members.filter(role=TeamMember.Role.LEAD).count(),
                "maintainers": members.filter(role=TeamMember.Role.MAINTAINER).count(),
                "members": members.filter(role=TeamMember.Role.MEMBER).count(),
            },
        }

    def get_recently_joined(self, team, days=30):
        """Get recently joined members"""
        from datetime import timedelta

        since = django_timezone.now() - timedelta(days=days)

        return self.model.objects.filter(team=team, joined_at__gte=since)

    def get_inactive_members(self, team, days=90):
        """Get members who haven't been active recently"""
        from datetime import timedelta

        threshold = django_timezone.now() - timedelta(days=days)

        return self.model.objects.filter(team=team, last_active_at__lt=threshold)

    def update_last_active(self, team, user):
        """Update member's last active time"""
        try:
            membership = self.get_membership(team, user)
            if membership:
                membership.update_last_active()
                return True
            return False
        except Exception:
            return False

    def get_user_role_in_team(self, team, user):
        """Get user's role in team"""
        try:
            membership = self.get_membership(team, user)
            return membership.role if membership else None
        except Exception:
            return None
