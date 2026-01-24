"""
Organization Member Repository
Data access layer for OrganizationMember model.
"""

from django.db.models import Q, Count
from django.utils import timezone as django_timezone
from apps.core.repositories.base import BaseRepository
from apps.organizations.models import OrganizationMember


class OrganizationMemberRepository(BaseRepository):
    """Repository for OrganizationMember model"""

    model = OrganizationMember

    def get_by_organization(self, organization, status=None):
        """Get members of organization"""
        queryset = self.model.objects.filter(organization=organization)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_by_user(self, user, status=None):
        """Get user's organization memberships"""
        queryset = self.model.objects.filter(user=user)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_membership(self, organization, user):
        """Get specific membership"""
        try:
            return self.model.objects.get(organization=organization, user=user)
        except self.model.DoesNotExist:
            return None

    def get_active_members(self, organization):
        """Get active members of organization"""
        return self.model.objects.filter(
            organization=organization, status=OrganizationMember.MembershipStatus.ACTIVE
        )

    def get_invited_members(self, organization):
        """Get invited (pending) members of organization"""
        return self.model.objects.filter(
            organization=organization,
            status=OrganizationMember.MembershipStatus.INVITED,
        )

    def get_by_role(self, organization, role):
        """Get members by role"""
        return self.model.objects.filter(
            organization=organization,
            role=role,
            status=OrganizationMember.MembershipStatus.ACTIVE,
        )

    def get_owners(self, organization):
        """Get organization owners"""
        return self.get_by_role(organization, OrganizationMember.Role.OWNER)

    def get_admins(self, organization):
        """Get organization admins (owners + admins)"""
        return self.model.objects.filter(
            organization=organization,
            role__in=[OrganizationMember.Role.OWNER, OrganizationMember.Role.ADMIN],
            status=OrganizationMember.MembershipStatus.ACTIVE,
        )

    def user_is_member(self, organization, user):
        """Check if user is member of organization"""
        return self.model.objects.filter(
            organization=organization,
            user=user,
            status=OrganizationMember.MembershipStatus.ACTIVE,
        ).exists()

    def user_is_owner(self, organization, user):
        """Check if user is owner"""
        return self.model.objects.filter(
            organization=organization,
            user=user,
            role=OrganizationMember.Role.OWNER,
            status=OrganizationMember.MembershipStatus.ACTIVE,
        ).exists()

    def user_is_admin(self, organization, user):
        """Check if user is admin or owner"""
        return self.model.objects.filter(
            organization=organization,
            user=user,
            role__in=[OrganizationMember.Role.OWNER, OrganizationMember.Role.ADMIN],
            status=OrganizationMember.MembershipStatus.ACTIVE,
        ).exists()

    def user_has_permission(self, organization, user, permission):
        """Check if user has specific permission"""
        try:
            membership = self.get_membership(organization, user)
            if (
                not membership
                or membership.status != OrganizationMember.MembershipStatus.ACTIVE
            ):
                return False
            return membership.has_permission(permission)
        except Exception:
            return False

    def get_by_invitation_token(self, token):
        """Get membership by invitation token"""
        try:
            return self.model.objects.get(
                invitation_token=token,
                status=OrganizationMember.MembershipStatus.INVITED,
            )
        except self.model.DoesNotExist:
            return None

    def get_expired_invitations(self):
        """Get expired invitations"""
        now = django_timezone.now()
        return self.model.objects.filter(
            status=OrganizationMember.MembershipStatus.INVITED,
            invitation_expires_at__lt=now,
        )

    def search_members(self, organization, query):
        """Search organization members"""
        queryset = self.model.objects.filter(organization=organization)

        if query:
            queryset = queryset.filter(
                Q(user__email__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
            )

        return queryset

    def get_member_statistics(self, organization):
        """Get organization member statistics"""
        members = self.model.objects.filter(organization=organization)

        return {
            "total": members.count(),
            "active": members.filter(
                status=OrganizationMember.MembershipStatus.ACTIVE
            ).count(),
            "invited": members.filter(
                status=OrganizationMember.MembershipStatus.INVITED
            ).count(),
            "suspended": members.filter(
                status=OrganizationMember.MembershipStatus.SUSPENDED
            ).count(),
            "by_role": {
                "owners": members.filter(role=OrganizationMember.Role.OWNER).count(),
                "admins": members.filter(role=OrganizationMember.Role.ADMIN).count(),
                "members": members.filter(role=OrganizationMember.Role.MEMBER).count(),
                "guests": members.filter(role=OrganizationMember.Role.GUEST).count(),
            },
        }

    def get_recently_joined(self, organization, days=30):
        """Get recently joined members"""
        from datetime import timedelta

        since = django_timezone.now() - timedelta(days=days)

        return self.model.objects.filter(
            organization=organization,
            status=OrganizationMember.MembershipStatus.ACTIVE,
            joined_at__gte=since,
        )

    def get_inactive_members(self, organization, days=90):
        """Get members who haven't accessed organization recently"""
        from datetime import timedelta

        threshold = django_timezone.now() - timedelta(days=days)

        return self.model.objects.filter(
            organization=organization,
            status=OrganizationMember.MembershipStatus.ACTIVE,
            last_accessed_at__lt=threshold,
        )

    def update_last_access(self, organization, user):
        """Update member's last access time"""
        try:
            membership = self.get_membership(organization, user)
            if membership:
                membership.update_last_access()
                return True
            return False
        except Exception:
            return False
