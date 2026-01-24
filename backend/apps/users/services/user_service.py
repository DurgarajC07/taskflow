"""
User service for business logic operations.
"""

from typing import Optional, Dict, List
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.core.services import BaseService
from apps.users.repositories import UserRepository
from apps.users.models import User


class UserService(BaseService):
    """Service for User business logic."""

    def __init__(self):
        repository = UserRepository()
        super().__init__(repository=repository)

    def validate_create_data(self, data: Dict) -> Dict:
        """Validate user creation data."""
        # Check if email already exists
        if self.repository.email_exists(data.get("email")):
            raise ValidationError({"email": "User with this email already exists."})

        return data

    def validate_update_data(self, instance: User, data: Dict) -> Dict:
        """Validate user update data."""
        # Check if email is being changed and if new email exists
        if "email" in data and data["email"] != instance.email:
            if self.repository.email_exists(data["email"], exclude_id=instance.id):
                raise ValidationError({"email": "User with this email already exists."})

        return data

    @transaction.atomic
    def create_user(self, email: str, password: str, **extra_data) -> User:
        """
        Create a new user with password.

        Args:
            email: User email
            password: User password
            **extra_data: Additional user data

        Returns:
            Created User instance
        """
        data = {"email": email, **extra_data}
        validated_data = self.validate_create_data(data)

        user = User.objects.create_user(
            email=validated_data.pop("email"), password=password, **validated_data
        )

        # Calculate initial profile completion
        user.calculate_profile_completion()

        return user

    def update_profile(self, user_id: str, data: Dict) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User ID
            data: Profile data to update

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        validated_data = self.validate_update_data(user, data)
        user = self.repository.update(user, **validated_data)

        # Recalculate profile completion
        user.calculate_profile_completion()

        return user

    def update_preferences(self, user_id: str, preferences: Dict) -> Optional[User]:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: Preferences dictionary

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        # Merge with existing preferences
        current_prefs = user.preferences or {}
        updated_prefs = {**current_prefs, **preferences}

        return self.repository.update(user, preferences=updated_prefs)

    def update_notification_settings(
        self, user_id: str, settings: Dict
    ) -> Optional[User]:
        """
        Update user notification settings.

        Args:
            user_id: User ID
            settings: Notification settings dictionary

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        # Merge with existing settings
        current_settings = user.notification_settings or {}
        updated_settings = {**current_settings, **settings}

        return self.repository.update(user, notification_settings=updated_settings)

    def update_working_hours(self, user_id: str, working_hours: Dict) -> Optional[User]:
        """
        Update user working hours.

        Args:
            user_id: User ID
            working_hours: Working hours configuration

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        # Merge with existing working hours
        current_hours = user.working_hours or {}
        updated_hours = {**current_hours, **working_hours}

        return self.repository.update(user, working_hours=updated_hours)

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return False

        # Verify old password
        if not user.check_password(old_password):
            raise ValidationError({"old_password": "Current password is incorrect."})

        # Set new password
        user.set_password(new_password)
        user.save()

        return True

    def verify_user(self, user_id: str) -> Optional[User]:
        """
        Mark user as verified.

        Args:
            user_id: User ID

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        return self.repository.update(user, is_verified=True)

    def suspend_user(self, user_id: str) -> Optional[User]:
        """
        Suspend user account.

        Args:
            user_id: User ID

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        return self.repository.update(
            user, account_status=User.AccountStatus.SUSPENDED, is_active=False
        )

    def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate suspended user account.

        Args:
            user_id: User ID

        Returns:
            Updated User instance or None
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None

        return self.repository.update(
            user, account_status=User.AccountStatus.ACTIVE, is_active=True
        )

    def search_users(self, query: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        Search users with pagination.

        Args:
            query: Search query
            page: Page number
            page_size: Items per page

        Returns:
            Paginated search results
        """
        queryset = self.repository.search_users(query)
        return self.repository.paginate(queryset, page, page_size)

    def get_user_statistics(self) -> Dict:
        """
        Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        return self.repository.get_user_statistics()

    def get_inactive_users(self, days: int = 30) -> List[User]:
        """
        Get users who haven't been active.

        Args:
            days: Number of days of inactivity

        Returns:
            List of inactive users
        """
        return list(self.repository.get_inactive_users(days))

    def get_recently_joined(self, days: int = 7) -> List[User]:
        """
        Get recently joined users.

        Args:
            days: Number of days to look back

        Returns:
            List of recent users
        """
        return list(self.repository.get_recently_joined(days))

    def update_last_activity(self, user_id: str) -> bool:
        """
        Update user's last activity.

        Args:
            user_id: User ID

        Returns:
            True if updated successfully
        """
        return self.repository.update_last_activity(user_id)
