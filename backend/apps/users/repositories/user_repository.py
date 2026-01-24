"""
User repository for data access operations.
"""

from typing import Optional, List
from django.db.models import Q, QuerySet
from apps.core.repositories import BaseRepository
from apps.users.models import User


class UserRepository(BaseRepository):
    """Repository for User model operations."""

    model = User

    def get_queryset(self) -> QuerySet:
        """Get base queryset with optimizations."""
        return super().get_queryset().select_related()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.get_or_none(email=email)

    def get_active_users(self) -> QuerySet:
        """Get all active users."""
        return self.filter(
            is_active=True, is_deleted=False, account_status=User.AccountStatus.ACTIVE
        )

    def get_verified_users(self) -> QuerySet:
        """Get all verified users."""
        return self.filter(is_verified=True, is_deleted=False)

    def search_users(self, query: str) -> QuerySet:
        """
        Search users by email, first name, or last name.

        Args:
            query: Search query string

        Returns:
            QuerySet of matching users
        """
        if not query:
            return self.get_queryset()

        return (
            self.get_queryset()
            .filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
            .filter(is_deleted=False)
        )

    def get_by_account_status(self, status: str) -> QuerySet:
        """Get users by account status."""
        return self.filter(account_status=status, is_deleted=False)

    def get_inactive_users(self, days: int = 30) -> QuerySet:
        """
        Get users who haven't been active for specified days.

        Args:
            days: Number of days of inactivity

        Returns:
            QuerySet of inactive users
        """
        from datetime import timedelta
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(last_activity__lt=cutoff_date, is_deleted=False)

    def get_recently_joined(self, days: int = 7) -> QuerySet:
        """
        Get users who joined recently.

        Args:
            days: Number of days to look back

        Returns:
            QuerySet of recent users
        """
        from datetime import timedelta
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(date_joined__gte=cutoff_date, is_deleted=False)

    def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check
            exclude_id: User ID to exclude from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        queryset = self.get_queryset().filter(email=email)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    def update_last_activity(self, user_id: str) -> bool:
        """
        Update user's last activity timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated successfully
        """
        user = self.get_by_id(user_id)
        if user:
            user.update_last_activity()
            return True
        return False

    def bulk_update_account_status(self, user_ids: List[str], status: str):
        """
        Bulk update account status for multiple users.

        Args:
            user_ids: List of user IDs
            status: New account status
        """
        self.get_queryset().filter(id__in=user_ids).update(account_status=status)

    def get_user_statistics(self) -> dict:
        """
        Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        queryset = self.get_queryset().filter(is_deleted=False)

        return {
            "total_users": queryset.count(),
            "active_users": queryset.filter(
                is_active=True, account_status=User.AccountStatus.ACTIVE
            ).count(),
            "verified_users": queryset.filter(is_verified=True).count(),
            "suspended_users": queryset.filter(
                account_status=User.AccountStatus.SUSPENDED
            ).count(),
            "pending_users": queryset.filter(
                account_status=User.AccountStatus.PENDING
            ).count(),
        }
