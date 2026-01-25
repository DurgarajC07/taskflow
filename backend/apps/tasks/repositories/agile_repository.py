"""
Agile Repositories
Repositories for Sprint, Backlog, and related models.
"""

from typing import List, Optional
from datetime import datetime
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from apps.core.repositories.base import OrganizationRepository
from apps.tasks.models import Sprint, SprintTask, Backlog, BacklogItem


class SprintRepository(OrganizationRepository):
    """
    Repository for Sprint model.
    """

    def __init__(self):
        super().__init__(Sprint)

    def get_project_sprints(self, project_id, status=None):
        """Get sprints for a project"""
        filters = {"project_id": project_id}
        if status:
            filters["status"] = status
        return self.filter(**filters).order_by("-sprint_number")

    def get_active_sprint(self, project_id):
        """Get active sprint for a project"""
        return self.filter(project_id=project_id, status=Sprint.Status.ACTIVE).first()

    def get_current_sprint(self, project_id):
        """Get current or next sprint"""
        active = self.get_active_sprint(project_id)
        if active:
            return active

        # Return next planned sprint
        return (
            self.filter(
                project_id=project_id,
                status=Sprint.Status.PLANNED,
            )
            .order_by("start_date")
            .first()
        )

    def get_next_sprint_number(self, project_id):
        """Get next available sprint number"""
        last_sprint = (
            self.filter(project_id=project_id).order_by("-sprint_number").first()
        )
        return (last_sprint.sprint_number + 1) if last_sprint else 1

    def get_sprint_velocity(self, project_id, num_sprints=5):
        """Calculate average velocity from recent sprints"""
        completed_sprints = self.filter(
            project_id=project_id,
            status=Sprint.Status.COMPLETED,
        ).order_by("-sprint_number")[:num_sprints]

        if not completed_sprints:
            return 0

        total_points = sum(
            sprint.completed_story_points for sprint in completed_sprints
        )
        return round(total_points / len(completed_sprints), 1)

    def get_sprint_statistics(self, sprint_id):
        """Get detailed sprint statistics"""
        sprint = self.get_by_id(sprint_id)
        if not sprint:
            return None

        return {
            "sprint": sprint,
            "task_count": sprint.task_count,
            "completed_count": sprint.completed_task_count,
            "completion_rate": sprint.completion_percentage,
            "story_points_total": sprint.story_points,
            "story_points_completed": sprint.completed_story_points,
            "velocity": sprint.velocity,
            "days_elapsed": (
                (timezone.now().date() - sprint.start_date).days
                if sprint.is_active
                else None
            ),
            "days_remaining": (
                (sprint.end_date - timezone.now().date()).days
                if sprint.is_active
                else None
            ),
        }


class SprintTaskRepository(OrganizationRepository):
    """
    Repository for SprintTask model.
    """

    def __init__(self):
        super().__init__(SprintTask)

    def get_sprint_tasks(self, sprint_id):
        """Get all tasks in a sprint"""
        return self.filter(sprint_id=sprint_id).order_by("sprint_order")

    def add_task_to_sprint(self, sprint_id, task_id, story_points=0, added_by_id=None):
        """Add a task to sprint"""
        max_order = self.filter(sprint_id=sprint_id).aggregate(max_order=Count("id"))
        order = (max_order["max_order"] or 0) + 1

        return self.create(
            sprint_id=sprint_id,
            task_id=task_id,
            story_points=story_points,
            sprint_order=order,
            added_by_id=added_by_id,
        )

    def remove_task_from_sprint(self, sprint_id, task_id):
        """Remove a task from sprint"""
        sprint_task = self.filter(sprint_id=sprint_id, task_id=task_id).first()
        if sprint_task:
            sprint_task.delete()
            return True
        return False

    def reorder_tasks(self, sprint_id, task_orders):
        """Reorder tasks in sprint"""
        for task_id, new_order in task_orders.items():
            self.filter(sprint_id=sprint_id, task_id=task_id).update(
                sprint_order=new_order
            )

    def get_committed_tasks(self, sprint_id):
        """Get committed tasks in sprint"""
        return self.filter(sprint_id=sprint_id, committed=True)


class BacklogRepository(OrganizationRepository):
    """
    Repository for Backlog model.
    """

    def __init__(self):
        super().__init__(Backlog)

    def get_project_backlog(self, project_id, backlog_type=None):
        """Get backlog for a project"""
        filters = {"project_id": project_id}
        if backlog_type:
            filters["backlog_type"] = backlog_type
        return self.filter(**filters).first()

    def get_or_create_product_backlog(self, project_id, organization_id):
        """Get or create product backlog for project"""
        backlog = self.filter(
            project_id=project_id,
            backlog_type=Backlog.BacklogType.PRODUCT,
        ).first()

        if not backlog:
            backlog = self.create(
                project_id=project_id,
                organization_id=organization_id,
                name="Product Backlog",
                backlog_type=Backlog.BacklogType.PRODUCT,
            )

        return backlog

    def get_sprint_backlog(self, sprint_id):
        """Get sprint backlog"""
        return self.filter(sprint_id=sprint_id).first()


class BacklogItemRepository(OrganizationRepository):
    """
    Repository for BacklogItem model.
    """

    def __init__(self):
        super().__init__(BacklogItem)

    def get_backlog_items(self, backlog_id):
        """Get all items in a backlog"""
        return self.filter(backlog_id=backlog_id).order_by("priority_order")

    def add_to_backlog(
        self, backlog_id, task_id, story_points=0, business_value=0, added_by_id=None
    ):
        """Add task to backlog"""
        # Get next priority order
        max_priority = self.filter(backlog_id=backlog_id).aggregate(
            max_priority=Count("id")
        )
        priority = (max_priority["max_priority"] or 0) + 1

        return self.create(
            backlog_id=backlog_id,
            task_id=task_id,
            priority_order=priority,
            story_points=story_points,
            business_value=business_value,
            added_by_id=added_by_id,
        )

    def remove_from_backlog(self, backlog_id, task_id):
        """Remove task from backlog"""
        item = self.filter(backlog_id=backlog_id, task_id=task_id).first()
        if item:
            item.delete()
            # Reorder remaining items
            self._reorder_after_deletion(backlog_id, item.priority_order)
            return True
        return False

    def reorder_items(self, backlog_id, item_orders):
        """Reorder backlog items"""
        for task_id, new_order in item_orders.items():
            self.filter(backlog_id=backlog_id, task_id=task_id).update(
                priority_order=new_order
            )

    def move_to_top(self, backlog_id, task_id):
        """Move item to top of backlog"""
        items = self.get_backlog_items(backlog_id)
        # Shift all items down
        items.update(priority_order=F("priority_order") + 1)
        # Set this item to 1
        self.filter(backlog_id=backlog_id, task_id=task_id).update(priority_order=1)

    def _reorder_after_deletion(self, backlog_id, deleted_order):
        """Reorder items after deletion to fill gaps"""
        items_below = self.filter(
            backlog_id=backlog_id, priority_order__gt=deleted_order
        )
        items_below.update(priority_order=F("priority_order") - 1)

    def get_high_priority_items(self, backlog_id, limit=10):
        """Get top priority items"""
        return self.get_backlog_items(backlog_id)[:limit]
