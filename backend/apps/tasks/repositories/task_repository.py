"""
Task Repository
Data access layer for Task model.
"""

from django.db import models
from django.db.models import Q, Count, Avg, Sum, F
from apps.tasks.models import Task


class TaskRepository:
    """Repository for Task data access"""

    @staticmethod
    def get_by_id(task_id):
        """Get task by ID"""
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None

    @staticmethod
    def get_by_task_key(project, task_number):
        """Get task by project and task number"""
        try:
            return Task.objects.get(project=project, task_number=task_number)
        except Task.DoesNotExist:
            return None

    @staticmethod
    def get_project_tasks(project, include_deleted=False):
        """Get all tasks for a project"""
        if include_deleted:
            return Task.all_objects.filter(project=project)
        return Task.objects.filter(project=project)

    @staticmethod
    def get_assigned_tasks(user, organization=None):
        """Get all tasks assigned to user"""
        queryset = Task.objects.filter(assignee=user)
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset

    @staticmethod
    def get_reported_tasks(user, organization=None):
        """Get all tasks reported by user"""
        queryset = Task.objects.filter(reporter=user)
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset

    @staticmethod
    def search_tasks(project, query):
        """Search tasks by title or description"""
        return Task.objects.filter(project=project).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    @staticmethod
    def filter_by_status(queryset, status):
        """Filter tasks by status"""
        return queryset.filter(status=status)

    @staticmethod
    def filter_by_priority(queryset, priority):
        """Filter tasks by priority"""
        return queryset.filter(priority=priority)

    @staticmethod
    def filter_by_type(queryset, task_type):
        """Filter tasks by type"""
        return queryset.filter(task_type=task_type)

    @staticmethod
    def filter_by_assignee(queryset, assignee):
        """Filter tasks by assignee"""
        return queryset.filter(assignee=assignee)

    @staticmethod
    def filter_by_reporter(queryset, reporter):
        """Filter tasks by reporter"""
        return queryset.filter(reporter=reporter)

    @staticmethod
    def filter_by_labels(queryset, labels):
        """Filter tasks by labels"""
        for label in labels:
            queryset = queryset.filter(labels__contains=[label])
        return queryset

    @staticmethod
    def get_overdue_tasks(project):
        """Get tasks past their due date"""
        from django.utils import timezone as django_timezone

        return Task.objects.filter(
            project=project,
            status__in=[
                Task.Status.TODO,
                Task.Status.IN_PROGRESS,
                Task.Status.IN_REVIEW,
                Task.Status.BLOCKED,
            ],
            due_date__lt=django_timezone.now().date(),
        )

    @staticmethod
    def get_blocked_tasks(project):
        """Get blocked tasks"""
        return Task.objects.filter(project=project, status=Task.Status.BLOCKED)

    @staticmethod
    def get_completed_tasks(project):
        """Get completed tasks"""
        return Task.objects.filter(project=project, status=Task.Status.DONE)

    @staticmethod
    def get_subtasks(parent_task):
        """Get subtasks of a task"""
        return Task.objects.filter(parent_task=parent_task)

    @staticmethod
    def create_task(data):
        """Create new task"""
        return Task.objects.create(**data)

    @staticmethod
    def update_task(task, data):
        """Update task"""
        for key, value in data.items():
            setattr(task, key, value)
        task.save()
        return task

    @staticmethod
    def delete_task(task, user=None):
        """Soft delete task"""
        task.soft_delete(user)
        return task

    @staticmethod
    def restore_task(task):
        """Restore soft-deleted task"""
        task.restore()
        return task

    @staticmethod
    def permanent_delete(task):
        """Permanently delete task"""
        task.delete()

    @staticmethod
    def get_statistics(project):
        """Get task statistics for project"""
        tasks = Task.objects.filter(project=project)

        return {
            "total": tasks.count(),
            "by_status": {
                "backlog": tasks.filter(status=Task.Status.BACKLOG).count(),
                "todo": tasks.filter(status=Task.Status.TODO).count(),
                "in_progress": tasks.filter(status=Task.Status.IN_PROGRESS).count(),
                "in_review": tasks.filter(status=Task.Status.IN_REVIEW).count(),
                "blocked": tasks.filter(status=Task.Status.BLOCKED).count(),
                "done": tasks.filter(status=Task.Status.DONE).count(),
                "cancelled": tasks.filter(status=Task.Status.CANCELLED).count(),
            },
            "by_priority": {
                "lowest": tasks.filter(priority=Task.Priority.LOWEST).count(),
                "low": tasks.filter(priority=Task.Priority.LOW).count(),
                "medium": tasks.filter(priority=Task.Priority.MEDIUM).count(),
                "high": tasks.filter(priority=Task.Priority.HIGH).count(),
                "highest": tasks.filter(priority=Task.Priority.HIGHEST).count(),
            },
            "by_type": {
                "task": tasks.filter(task_type=Task.TaskType.TASK).count(),
                "bug": tasks.filter(task_type=Task.TaskType.BUG).count(),
                "feature": tasks.filter(task_type=Task.TaskType.FEATURE).count(),
                "epic": tasks.filter(task_type=Task.TaskType.EPIC).count(),
                "story": tasks.filter(task_type=Task.TaskType.STORY).count(),
                "subtask": tasks.filter(task_type=Task.TaskType.SUBTASK).count(),
            },
            "overdue": TaskRepository.get_overdue_tasks(project).count(),
            "unassigned": tasks.filter(assignee__isnull=True).count(),
            "avg_completion_time": tasks.filter(completed_at__isnull=False).aggregate(
                avg=Avg(F("completed_at") - F("created_at"))
            )["avg"],
        }

    @staticmethod
    def get_user_statistics(user, organization):
        """Get task statistics for user"""
        assigned = Task.objects.filter(assignee=user, organization=organization)
        reported = Task.objects.filter(reporter=user, organization=organization)

        return {
            "assigned_total": assigned.count(),
            "assigned_open": assigned.exclude(
                status__in=[Task.Status.DONE, Task.Status.CANCELLED]
            ).count(),
            "assigned_completed": assigned.filter(status=Task.Status.DONE).count(),
            "reported_total": reported.count(),
            "reported_open": reported.exclude(
                status__in=[Task.Status.DONE, Task.Status.CANCELLED]
            ).count(),
        }

    @staticmethod
    def bulk_update_status(tasks, new_status):
        """Bulk update task status"""
        tasks.update(status=new_status)

    @staticmethod
    def bulk_update_priority(tasks, new_priority):
        """Bulk update task priority"""
        tasks.update(priority=new_priority)

    @staticmethod
    def bulk_assign(tasks, assignee):
        """Bulk assign tasks"""
        tasks.update(assignee=assignee)
