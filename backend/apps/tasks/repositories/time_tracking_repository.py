"""
Time Tracking Repositories
Repositories for TimeEntry and WorkLog models.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from apps.core.repositories.base import BaseRepository, OrganizationRepository
from apps.tasks.models import TimeEntry, WorkLog


class TimeEntryRepository(OrganizationRepository):
    """
    Repository for TimeEntry model.
    """

    def __init__(self):
        super().__init__(TimeEntry)

    def get_task_time_entries(self, task_id):
        """Get all time entries for a task"""
        return self.filter(task_id=task_id).order_by("-date", "-created_at")

    def get_user_time_entries(self, user_id, start_date=None, end_date=None):
        """Get time entries for a user within date range"""
        filters = {"user_id": user_id}
        queryset = self.filter(**filters)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset.order_by("-date")

    def get_project_time_entries(self, project_id, start_date=None, end_date=None):
        """Get time entries for a project"""
        queryset = self.filter(task__project_id=project_id)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset.order_by("-date")

    def get_total_hours(
        self,
        task_id=None,
        user_id=None,
        project_id=None,
        start_date=None,
        end_date=None,
    ):
        """Calculate total hours with optional filters"""
        filters = {}
        if task_id:
            filters["task_id"] = task_id
        if user_id:
            filters["user_id"] = user_id
        if project_id:
            filters["task__project_id"] = project_id

        queryset = self.filter(**filters)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        result = queryset.aggregate(total=Sum("hours"))
        return result["total"] or 0

    def get_billable_hours(self, **filters):
        """Get total billable hours"""
        queryset = self.filter(is_billable=True, **filters)
        result = queryset.aggregate(total=Sum("hours"))
        return result["total"] or 0

    def get_time_by_user(self, project_id=None, start_date=None, end_date=None):
        """Get time grouped by user"""
        filters = {}
        if project_id:
            filters["task__project_id"] = project_id

        queryset = self.filter(**filters)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return (
            queryset.values(
                "user__id", "user__email", "user__first_name", "user__last_name"
            )
            .annotate(
                total_hours=Sum("hours"),
                entry_count=Count("id"),
                billable_hours=Sum("hours", filter=Q(is_billable=True)),
            )
            .order_by("-total_hours")
        )

    def get_daily_summary(self, user_id, date):
        """Get summary of time entries for a specific day"""
        entries = self.filter(user_id=user_id, date=date)
        return {
            "date": date,
            "entries": entries,
            "total_hours": entries.aggregate(total=Sum("hours"))["total"] or 0,
            "billable_hours": entries.filter(is_billable=True).aggregate(
                total=Sum("hours")
            )["total"]
            or 0,
            "entry_count": entries.count(),
        }


class WorkLogRepository(BaseRepository):
    """
    Repository for WorkLog model.
    """

    def __init__(self):
        super().__init__(WorkLog)

    def get_task_logs(self, task_id, log_type=None):
        """Get work logs for a task"""
        filters = {"task_id": task_id}
        if log_type:
            filters["log_type"] = log_type
        return self.filter(**filters).order_by("-created_at")

    def get_user_logs(self, user_id, start_date=None, end_date=None):
        """Get work logs by user"""
        queryset = self.filter(user_id=user_id)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset.order_by("-created_at")

    def create_log(self, task_id, user_id, log_type, description, metadata=None):
        """Create a work log entry"""
        return self.create(
            task_id=task_id,
            user_id=user_id,
            log_type=log_type,
            description=description,
            metadata=metadata or {},
        )

    def get_activity_summary(self, task_id):
        """Get activity summary by type"""
        return (
            self.filter(task_id=task_id)
            .values("log_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

    def get_recent_activity(self, project_id=None, user_id=None, limit=50):
        """Get recent activity logs"""
        filters = {}
        if project_id:
            filters["task__project_id"] = project_id
        if user_id:
            filters["user_id"] = user_id

        return self.filter(**filters).order_by("-created_at")[:limit]
