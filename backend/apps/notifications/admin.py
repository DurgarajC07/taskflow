"""
Notification Admin Configuration
Django admin interface for Notification models.
"""

from django.contrib import admin
from apps.notifications.models import (
    Notification,
    NotificationPreference,
    NotificationQueue,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""

    list_display = [
        "user",
        "title_preview",
        "notification_type",
        "priority",
        "is_read",
        "is_sent",
        "created_at",
    ]
    list_filter = [
        "notification_type",
        "priority",
        "is_read",
        "is_sent",
        "created_at",
    ]
    search_fields = [
        "user__email",
        "title",
        "message",
        "actor__email",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "read_at",
        "sent_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        ("User", {"fields": ("user", "actor")}),
        ("Content", {"fields": ("notification_type", "title", "message", "priority")}),
        ("Links", {"fields": ("link_url", "entity_type", "entity_id")}),
        ("Status", {"fields": ("is_read", "read_at", "is_sent", "sent_at")}),
        ("Metadata", {"fields": ("metadata",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def title_preview(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

    title_preview.short_description = "Title"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "actor")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for NotificationPreference model"""

    list_display = [
        "user",
        "notification_type",
        "channel",
        "is_enabled",
        "send_immediately",
    ]
    list_filter = [
        "notification_type",
        "channel",
        "is_enabled",
        "send_immediately",
    ]
    search_fields = ["user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("User", {"fields": ("user",)}),
        ("Settings", {"fields": ("notification_type", "channel", "is_enabled")}),
        ("Frequency", {"fields": ("send_immediately",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    """Admin interface for NotificationQueue model"""

    list_display = [
        "notification",
        "channel",
        "status",
        "scheduled_for",
        "sent_at",
        "retry_count",
    ]
    list_filter = [
        "status",
        "channel",
        "scheduled_for",
        "created_at",
    ]
    search_fields = [
        "notification__user__email",
        "notification__title",
        "error_message",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "sent_at",
    ]
    date_hierarchy = "scheduled_for"

    fieldsets = (
        ("Notification", {"fields": ("notification",)}),
        ("Delivery", {"fields": ("channel", "status", "scheduled_for", "sent_at")}),
        ("Error Handling", {"fields": ("retry_count", "error_message")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("notification", "notification__user")
        )
