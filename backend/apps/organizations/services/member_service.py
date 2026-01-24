"""
Organization Member Service
Business logic layer for organization membership operations.
"""

from django.db import transaction
from django.utils import timezone as django_timezone
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from apps.core.services.base import BaseService
from apps.organizations.repositories import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from apps.organizations.models import OrganizationMember


class OrganizationMemberService(BaseService):
    """Service for OrganizationMember business logic"""

    repository_class = OrganizationMemberRepository

    def __init__(self):
        self.repository = OrganizationMemberRepository()
        self.org_repository = OrganizationRepository()

    def validate_add_member_data(self, organization, data):
        """Validate member addition data"""
        errors = {}

        # Check if organization can add members
        if not organization.can_add_member():
            errors["limit"] = (
                f"Organization has reached maximum members limit ({organization.max_members})"
            )

        # Validate user
        if not data.get("user"):
            errors["user"] = "User is required"

        # Check if user is already a member
        if data.get("user") and self.repository.get_membership(
            organization, data["user"]
        ):
            errors["user"] = "User is already a member of this organization"

        # Validate role
        if "role" in data and data["role"] not in dict(OrganizationMember.Role.choices):
            errors["role"] = "Invalid role"

        if errors:
            raise ValidationError(errors)

        return data

    @transaction.atomic
    def add_member(self, organization, user, role, invited_by):
        """Add member to organization"""
        # Check permission
        membership = self.repository.get_membership(organization, invited_by)
        if not membership or not membership.can_manage_members():
            raise ValidationError("You do not have permission to add members")

        # Validate data
        data = {
            "user": user,
            "role": role,
        }
        self.validate_add_member_data(organization, data)

        # Create membership
        member = self.repository.create(
            {
                "organization": organization,
                "user": user,
                "role": role,
                "status": OrganizationMember.MembershipStatus.ACTIVE,
                "invited_by": invited_by,
                "joined_at": django_timezone.now(),
            }
        )

        # Increment organization member count
        organization.increment_member_count()

        return member

    @transaction.atomic
    def invite_member(self, organization, email, role, invited_by, expiration_days=7):
        """Invite user to organization via email"""
        from django.contrib.auth import get_user_model
        from datetime import timedelta

        User = get_user_model()

        # Check permission
        membership = self.repository.get_membership(organization, invited_by)
        if not membership or not membership.can_manage_members():
            raise ValidationError("You do not have permission to invite members")

        # Check if organization can add members
        if not organization.can_add_member():
            raise ValidationError(
                f"Organization has reached maximum members limit ({organization.max_members})"
            )

        # Get or create user by email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "is_active": False,  # Will be activated when they accept invitation
            },
        )

        # Check if already a member
        if self.repository.get_membership(organization, user):
            raise ValidationError("User is already a member of this organization")

        # Generate invitation token
        token = get_random_string(64)

        # Create invitation
        invitation = self.repository.create(
            {
                "organization": organization,
                "user": user,
                "role": role,
                "status": OrganizationMember.MembershipStatus.INVITED,
                "invited_by": invited_by,
                "invitation_token": token,
                "invitation_expires_at": django_timezone.now()
                + timedelta(days=expiration_days),
            }
        )

        # TODO: Send invitation email
        # send_invitation_email(user.email, organization, token)

        return invitation

    @transaction.atomic
    def accept_invitation(self, token, user=None):
        """Accept organization invitation"""
        # Get invitation
        invitation = self.repository.get_by_invitation_token(token)

        if not invitation:
            raise ValidationError("Invalid or expired invitation")

        # Check expiration
        if invitation.invitation_expires_at < django_timezone.now():
            raise ValidationError("This invitation has expired")

        # Update invitation
        invitation.status = OrganizationMember.MembershipStatus.ACTIVE
        invitation.joined_at = django_timezone.now()
        invitation.invitation_token = ""  # Clear token
        invitation.save()

        # Activate user if not active
        if not invitation.user.is_active:
            invitation.user.is_active = True
            invitation.user.save()

        # Increment organization member count
        invitation.organization.increment_member_count()

        return invitation

    @transaction.atomic
    def remove_member(self, organization, user, removed_by):
        """Remove member from organization"""
        # Check permission
        remover_membership = self.repository.get_membership(organization, removed_by)
        if not remover_membership or not remover_membership.can_manage_members():
            raise ValidationError("You do not have permission to remove members")

        # Get membership
        membership = self.repository.get_membership(organization, user)
        if not membership:
            raise ValidationError("User is not a member of this organization")

        # Cannot remove owner
        if membership.is_owner():
            raise ValidationError("Cannot remove organization owner")

        # Cannot remove yourself
        if user == removed_by:
            raise ValidationError(
                "Cannot remove yourself. Use leave organization instead."
            )

        # Delete membership
        self.repository.delete(membership.id)

        # Decrement organization member count
        organization.decrement_member_count()

        return True

    @transaction.atomic
    def leave_organization(self, organization, user):
        """User leaves organization"""
        # Get membership
        membership = self.repository.get_membership(organization, user)
        if not membership:
            raise ValidationError("You are not a member of this organization")

        # Cannot leave if owner (must transfer ownership first)
        if membership.is_owner():
            raise ValidationError(
                "Organization owner cannot leave. Transfer ownership first."
            )

        # Delete membership
        self.repository.delete(membership.id)

        # Decrement organization member count
        organization.decrement_member_count()

        return True

    def update_member_role(self, organization, user, new_role, updated_by):
        """Update member role"""
        # Check permission
        updater_membership = self.repository.get_membership(organization, updated_by)
        if not updater_membership or not updater_membership.can_manage_members():
            raise ValidationError("You do not have permission to update member roles")

        # Get membership
        membership = self.repository.get_membership(organization, user)
        if not membership:
            raise ValidationError("User is not a member of this organization")

        # Cannot change owner role
        if membership.is_owner():
            raise ValidationError(
                "Cannot change organization owner role. Transfer ownership instead."
            )

        # Cannot promote to owner
        if new_role == OrganizationMember.Role.OWNER:
            raise ValidationError(
                "Cannot promote to owner. Use transfer ownership instead."
            )

        # Update role
        return self.repository.update(membership.id, {"role": new_role})

    @transaction.atomic
    def transfer_ownership(self, organization, new_owner, current_owner):
        """Transfer organization ownership"""
        # Verify current owner
        if not organization.is_owner(current_owner):
            raise ValidationError("Only organization owner can transfer ownership")

        # Get memberships
        current_membership = self.repository.get_membership(organization, current_owner)
        new_membership = self.repository.get_membership(organization, new_owner)

        if not new_membership:
            raise ValidationError("New owner must be a member of the organization")

        # Update roles
        self.repository.update(
            current_membership.id, {"role": OrganizationMember.Role.ADMIN}
        )
        self.repository.update(
            new_membership.id, {"role": OrganizationMember.Role.OWNER}
        )

        # Update organization owner
        self.org_repository.update(organization.id, {"owner": new_owner})

        return True

    def suspend_member(self, organization, user, suspended_by, reason=None):
        """Suspend organization member"""
        # Check permission
        suspender_membership = self.repository.get_membership(
            organization, suspended_by
        )
        if not suspender_membership or not suspender_membership.can_manage_members():
            raise ValidationError("You do not have permission to suspend members")

        # Get membership
        membership = self.repository.get_membership(organization, user)
        if not membership:
            raise ValidationError("User is not a member of this organization")

        # Cannot suspend owner
        if membership.is_owner():
            raise ValidationError("Cannot suspend organization owner")

        # Update custom permissions with suspension info
        custom_permissions = membership.custom_permissions or {}
        custom_permissions["suspension_reason"] = reason
        custom_permissions["suspended_at"] = django_timezone.now().isoformat()
        custom_permissions["suspended_by"] = str(suspended_by.id)

        return self.repository.update(
            membership.id,
            {
                "status": OrganizationMember.MembershipStatus.SUSPENDED,
                "custom_permissions": custom_permissions,
            },
        )

    def activate_member(self, organization, user, activated_by):
        """Activate suspended member"""
        # Check permission
        activator_membership = self.repository.get_membership(
            organization, activated_by
        )
        if not activator_membership or not activator_membership.can_manage_members():
            raise ValidationError("You do not have permission to activate members")

        # Get membership
        membership = self.repository.get_membership(organization, user)
        if not membership:
            raise ValidationError("User is not a member of this organization")

        return self.repository.update(
            membership.id,
            {
                "status": OrganizationMember.MembershipStatus.ACTIVE,
            },
        )

    def update_member_permissions(
        self, organization, user, granted=None, revoked=None, updated_by=None
    ):
        """Update member custom permissions"""
        # Check permission
        if updated_by:
            updater_membership = self.repository.get_membership(
                organization, updated_by
            )
            if not updater_membership or not updater_membership.can_manage_members():
                raise ValidationError(
                    "You do not have permission to update member permissions"
                )

        # Get membership
        membership = self.repository.get_membership(organization, user)
        if not membership:
            raise ValidationError("User is not a member of this organization")

        # Update custom permissions
        custom_permissions = membership.custom_permissions or {}
        if granted:
            custom_permissions["granted"] = list(
                set(custom_permissions.get("granted", []) + granted)
            )
        if revoked:
            custom_permissions["revoked"] = list(
                set(custom_permissions.get("revoked", []) + revoked)
            )

        return self.repository.update(
            membership.id, {"custom_permissions": custom_permissions}
        )

    def get_member_statistics(self, organization):
        """Get organization member statistics"""
        return self.repository.get_member_statistics(organization)

    def search_members(self, organization, query):
        """Search organization members"""
        return self.repository.search_members(organization, query)

    def clean_expired_invitations(self):
        """Clean up expired invitations"""
        expired = self.repository.get_expired_invitations()
        count = expired.count()

        for invitation in expired:
            self.repository.delete(invitation.id)

        return count
