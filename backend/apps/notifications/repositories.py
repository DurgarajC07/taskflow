"""
Notification Repositories
Repositories for Notification and NotificationPreference models.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.utils import timezone
from apps.core.repositories.base import BaseRepository
from apps.notifications.models import (
    Notification,
    NotificationPreference,
    NotificationQueue,
)


class NotificationRepository(BaseRepository):
    """
    Repository for Notification model.
    """

    def __init__(self):
        super().__init__(Notification)

    def get_user_notifications(
        self, user_id, is_read=None, notification_type=None, limit=50
    ):
        """Get notifications for a user"""
        filters = {"user_id": user_id}
        if is_read is not None:
            filters["is_read"] = is_read
        if notification_type:
            filters["notification_type"] = notification_type

        return self.filter(**filters).order_by("-created_at")[:limit]

    def get_unread_notifications(self, user_id):
        """Get unread notifications"""
        return self.get_user_notifications(user_id, is_read=False)

    def get_unread_count(self, user_id):
        """Get count of unread notifications"""
        return self.filter(user_id=user_id, is_read=False).count()

    def create_notification(
        self,
        user_id,
        notification_type,
        title,
        message,
        priority=Notification.Priority.MEDIUM,
        link_url="",
        entity_type="",
        entity_id=None,
        actor_id=None,
        metadata=None,
    ):
        """Create a new notification"""
        return self.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            link_url=link_url,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            metadata=metadata or {},
        )

    def mark_all_as_read(self, user_id):
        """Mark all notifications as read for a user"""
        unread = self.filter(user_id=user_id, is_read=False)
        count = unread.count()
        unread.update(is_read=True, read_at=timezone.now())
        return count

    def mark_as_read_by_entity(self, user_id, entity_type, entity_id):
        """Mark all notifications for a specific entity as read"""
        notifications = self.filter(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            is_read=False,
        )
        count = notifications.count()
        notifications.update(is_read=True, read_at=timezone.now())
        return count

    def delete_old_notifications(self, days=90):
        """Delete notifications older than specified days"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_notifications = self.filter(created_at__lt=cutoff_date, is_read=True)
        count = old_notifications.count()
        old_notifications.delete()
        return count

    def get_notification_statistics(self, user_id):
        """Get notification statistics for a user"""
        all_notifications = self.filter(user_id=user_id)

        return {
            "total": all_notifications.count(),
            "unread": all_notifications.filter(is_read=False).count(),
            "by_type": all_notifications.values("notification_type")
            .annotate(count=Count("id"))
            .order_by("-count"),
            "by_priority": all_notifications.values("priority")
            .annotate(count=Count("id"))
            .order_by("-count"),
        }

    def get_recent_by_actor(self, actor_id, limit=20):
        """Get recent notifications triggered by an actor"""
        return self.filter(actor_id=actor_id).order_by("-created_at")[:limit]


class NotificationPreferenceRepository(BaseRepository):
    """
    Repository for NotificationPreference model.
    """

    def __init__(self):
        super().__init__(NotificationPreference)

    def get_user_preferences(self, user_id):
        """Get all notification preferences for a user"""
        return self.filter(user_id=user_id).order_by("notification_type", "channel")

    def get_preference(self, user_id, notification_type, channel):
        """Get specific preference"""
        return self.filter(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
        ).first()

    def is_enabled(self, user_id, notification_type, channel):
        """Check if notification type is enabled for channel"""
        pref = self.get_preference(user_id, notification_type, channel)
        if pref:
            return pref.is_enabled
        # Default to enabled if no preference set
        return True

    def set_preference(self, user_id, notification_type, channel, is_enabled):
        """Set notification preference"""
        pref = self.get_preference(user_id, notification_type, channel)
        if pref:
            pref.is_enabled = is_enabled
            pref.save(update_fields=["is_enabled"])
            return pref
        else:
            return self.create(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                is_enabled=is_enabled,
            )

    def get_enabled_channels(self, user_id, notification_type):
        """Get enabled channels for a notification type"""
        prefs = self.filter(
            user_id=user_id,
            notification_type=notification_type,
            is_enabled=True,
        )
        return [pref.channel for pref in prefs]


class NotificationQueueRepository(BaseRepository):
    """
    Repository for NotificationQueue model.
    """

    def __init__(self):
        super().__init__(NotificationQueue)

    def enqueue(self, notification_id, channel, scheduled_for=None):
        """Add notification to queue"""
        if scheduled_for is None:
            scheduled_for = timezone.now()

        return self.create(
            notification_id=notification_id,
            channel=channel,
            scheduled_for=scheduled_for,
        )

    def get_pending(self, channel=None, limit=100):
        """Get pending notifications"""
        filters = {
            "status": NotificationQueue.Status.PENDING,
            "scheduled_for__lte": timezone.now(),
        }
        if channel:
            filters["channel"] = channel

        return self.filter(**filters).order_by("scheduled_for")[:limit]

    def mark_as_sent(self, queue_id):
        """Mark notification as sent"""
        entry = self.get_by_id(queue_id)
        if entry:
            entry.status = NotificationQueue.Status.SENT
            entry.sent_at = timezone.now()
            entry.save(update_fields=["status", "sent_at"])
            return entry
        return None

    def mark_as_failed(self, queue_id, error_message):
        """Mark notification as failed"""
        entry = self.get_by_id(queue_id)
        if entry:
            entry.status = NotificationQueue.Status.FAILED
            entry.error_message = error_message
            entry.retry_count += 1
            entry.save(update_fields=["status", "error_message", "retry_count"])
            return entry
        return None

    def retry(self, queue_id, retry_after_minutes=5):
        """Schedule for retry"""
        entry = self.get_by_id(queue_id)
        if entry:
            entry.scheduled_for = timezone.now() + timedelta(
                minutes=retry_after_minutes
            )
            entry.status = NotificationQueue.Status.PENDING
            entry.save(update_fields=["scheduled_for", "status"])
            return entry
        return None

    def cleanup_old_entries(self, days=30):
        """Delete old sent/failed entries"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_entries = self.filter(
            created_at__lt=cutoff_date,
            status__in=[NotificationQueue.Status.SENT, NotificationQueue.Status.FAILED],
        )
        count = old_entries.count()
        old_entries.delete()
        return count
