"""
Notification Models
User notifications and notification preferences.
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models.base import BaseModel

User = get_user_model()


class Notification(BaseModel):
    """
    User notifications for various events.
    """

    # Notification Types
    class NotificationType(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task Assigned"
        TASK_UPDATED = "task_updated", "Task Updated"
        TASK_COMPLETED = "task_completed", "Task Completed"
        TASK_COMMENTED = "task_commented", "Task Commented"
        MENTION = "mention", "Mentioned"
        PROJECT_INVITE = "project_invite", "Project Invitation"
        TEAM_INVITE = "team_invite", "Team Invitation"
        ORG_INVITE = "org_invite", "Organization Invitation"
        DUE_DATE_REMINDER = "due_date_reminder", "Due Date Reminder"
        OVERDUE = "overdue", "Task Overdue"
        APPROVAL_NEEDED = "approval_needed", "Approval Needed"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        STATUS_CHANGED = "status_changed", "Status Changed"
        PRIORITY_CHANGED = "priority_changed", "Priority Changed"
        ATTACHMENT_ADDED = "attachment_added", "Attachment Added"
        DEADLINE_APPROACHING = "deadline_approaching", "Deadline Approaching"
        SPRINT_STARTED = "sprint_started", "Sprint Started"
        SPRINT_COMPLETED = "sprint_completed", "Sprint Completed"

    # Priority Levels
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User receiving the notification",
    )

    # Content
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        help_text="Type of notification",
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title",
    )
    message = models.TextField(
        help_text="Notification message",
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text="Notification priority",
    )

    # Links and References
    link_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL to navigate to when clicked",
    )
    entity_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of related entity (task, project, etc.)",
    )
    entity_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of related entity",
    )

    # Actor (who triggered the notification)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
        help_text="User who triggered this notification",
    )

    # Status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether notification has been read",
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was read",
    )

    # Delivery
    is_sent = models.BooleanField(
        default=False,
        help_text="Whether notification has been sent (for email/push)",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent",
    )

    # Additional Data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional notification data",
    )

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.email}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone

        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(BaseModel):
    """
    User notification preferences.
    """

    # Delivery Channels
    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-App"
        EMAIL = "email", "Email"
        PUSH = "push", "Push Notification"
        SMS = "sms", "SMS"

    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        help_text="User these preferences belong to",
    )

    # Settings
    notification_type = models.CharField(
        max_length=30,
        choices=Notification.NotificationType.choices,
        help_text="Type of notification this preference applies to",
    )
    channel = models.CharField(
        max_length=10,
        choices=Channel.choices,
        help_text="Delivery channel",
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this notification type is enabled for this channel",
    )

    # Frequency (for digest emails)
    send_immediately = models.BooleanField(
        default=True,
        help_text="Send immediately or batch",
    )

    class Meta:
        db_table = "notification_preferences"
        ordering = ["notification_type", "channel"]
        unique_together = [["user", "notification_type", "channel"]]
        indexes = [
            models.Index(fields=["user", "is_enabled"]),
        ]
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"{self.user.email}: {self.notification_type} via {self.channel}"


class NotificationQueue(BaseModel):
    """
    Queue for batch processing of notifications.
    Used for email digests and scheduled notifications.
    """

    # Status
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    # Relations
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="queue_entries",
        help_text="Notification to be sent",
    )

    # Delivery
    channel = models.CharField(
        max_length=10,
        choices=NotificationPreference.Channel.choices,
        help_text="Delivery channel",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Queue status",
    )

    # Scheduling
    scheduled_for = models.DateTimeField(
        help_text="When to send this notification",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was actually sent",
    )

    # Error Handling
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if failed",
    )

    class Meta:
        db_table = "notification_queue"
        ordering = ["scheduled_for"]
        indexes = [
            models.Index(fields=["status", "scheduled_for"]),
            models.Index(fields=["channel", "status"]),
        ]
        verbose_name = "Notification Queue Entry"
        verbose_name_plural = "Notification Queue Entries"

    def __str__(self):
        return f"{self.notification.title} via {self.channel} ({self.status})"
