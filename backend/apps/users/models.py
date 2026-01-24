from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone as django_timezone
from apps.core.utils.validators import validate_timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Enhanced User model with enterprise features."""

    # Account Status Choices
    class AccountStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ARCHIVED = "archived", "Archived"
        PENDING = "pending", "Pending Verification"

    # Language Choices
    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        SPANISH = "es", "Spanish"
        FRENCH = "fr", "French"
        GERMAN = "de", "German"
        CHINESE = "zh", "Chinese"
        JAPANESE = "ja", "Japanese"

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    # Account Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
        db_index=True,
    )

    # Preferences & Settings
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        validators=[validate_timezone],
        help_text="User timezone for date/time display",
    )
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.ENGLISH,
        help_text="Preferred language for UI",
    )
    preferences = models.JSONField(
        default=dict, blank=True, help_text="User preferences (theme, layout, etc.)"
    )
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Notification preferences (email, in-app, etc.)",
    )
    working_hours = models.JSONField(
        default=dict, blank=True, help_text="User working hours configuration"
    )

    # Profile & Activity
    profile_completion = models.IntegerField(
        default=0, help_text="Profile completion percentage (0-100)"
    )
    last_activity = models.DateTimeField(
        null=True, blank=True, db_index=True, help_text="Last user activity timestamp"
    )

    # Timestamps
    date_joined = models.DateTimeField(default=django_timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft Delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email", "is_active"]),
            models.Index(fields=["account_status", "is_deleted"]),
            models.Index(fields=["-last_activity"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return full name of user."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        """Return short name of user."""
        return self.first_name or self.email.split("@")[0]

    def soft_delete(self):
        """Soft delete the user account."""
        self.is_deleted = True
        self.deleted_at = django_timezone.now()
        self.is_active = False
        self.account_status = self.AccountStatus.ARCHIVED
        self.save(
            update_fields=["is_deleted", "deleted_at", "is_active", "account_status"]
        )

    def restore(self):
        """Restore a soft-deleted user account."""
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.account_status = self.AccountStatus.ACTIVE
        self.save(
            update_fields=["is_deleted", "deleted_at", "is_active", "account_status"]
        )

    def update_last_activity(self):
        """Update last activity timestamp."""
        self.last_activity = django_timezone.now()
        self.save(update_fields=["last_activity"])

    def calculate_profile_completion(self):
        """Calculate and update profile completion percentage."""
        fields_to_check = [
            "first_name",
            "last_name",
            "avatar",
            "timezone",
            "language",
        ]

        completed = sum(1 for field in fields_to_check if getattr(self, field))
        percentage = int((completed / len(fields_to_check)) * 100)

        if self.profile_completion != percentage:
            self.profile_completion = percentage
            self.save(update_fields=["profile_completion"])

        return percentage

    def get_default_notification_settings(self):
        """Get default notification settings."""
        return {
            "email": {
                "task_assigned": True,
                "task_commented": True,
                "task_mentioned": True,
                "task_due_soon": True,
                "daily_digest": False,
                "weekly_summary": False,
            },
            "in_app": {
                "task_assigned": True,
                "task_commented": True,
                "task_mentioned": True,
                "task_due_soon": True,
                "task_completed": True,
            },
        }

    def get_default_preferences(self):
        """Get default user preferences."""
        return {
            "theme": "light",
            "layout": "default",
            "sidebar_collapsed": False,
            "default_view": "list",
            "items_per_page": 20,
            "date_format": "MM/DD/YYYY",
            "time_format": "12h",
        }

    def get_default_working_hours(self):
        """Get default working hours."""
        return {
            "monday": {"start": "09:00", "end": "17:00", "enabled": True},
            "tuesday": {"start": "09:00", "end": "17:00", "enabled": True},
            "wednesday": {"start": "09:00", "end": "17:00", "enabled": True},
            "thursday": {"start": "09:00", "end": "17:00", "enabled": True},
            "friday": {"start": "09:00", "end": "17:00", "enabled": True},
            "saturday": {"start": "09:00", "end": "17:00", "enabled": False},
            "sunday": {"start": "09:00", "end": "17:00", "enabled": False},
        }

    def save(self, *args, **kwargs):
        """Override save to set defaults for JSON fields."""
        if not self.preferences:
            self.preferences = self.get_default_preferences()
        if not self.notification_settings:
            self.notification_settings = self.get_default_notification_settings()
        if not self.working_hours:
            self.working_hours = self.get_default_working_hours()
        super().save(*args, **kwargs)
