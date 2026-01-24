"""
Task Service
Business logic for task operations.
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.tasks.repositories import TaskRepository, ProjectMemberRepository
from apps.tasks.models import Task, TaskActivity


class TaskService:
    """Service for task business logic"""

    @staticmethod
    def create_task(project, user, data):
        """Create new task"""
        # Validate project membership
        member = ProjectMemberRepository.get_project_member(project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to create tasks in this project")

        # Validate assignee is project member
        assignee = data.get("assignee")
        if assignee and not ProjectMemberRepository.is_member(project, assignee):
            raise ValidationError({"assignee": "Assignee must be project member"})

        # Validate parent task belongs to same project
        parent_task = data.get("parent_task")
        if parent_task and parent_task.project != project:
            raise ValidationError(
                {"parent_task": "Parent task must belong to same project"}
            )

        with transaction.atomic():
            # Create task
            task_data = {
                **data,
                "project": project,
                "organization": project.organization,
                "reporter": user,
                "created_by": user,
            }
            task = TaskRepository.create_task(task_data)

            # Update project task count
            project.task_count = project.task_count + 1
            if task.status != Task.Status.DONE:
                project.open_task_count = project.open_task_count + 1
            project.save(update_fields=["task_count", "open_task_count"])

            # Log activity
            TaskService._log_activity(
                task,
                user,
                TaskActivity.ActivityType.CREATED,
                f"Created task {task.task_key}",
            )

        return task

    @staticmethod
    def update_task(task, user, data):
        """Update task"""
        # Check permissions
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to edit this task")

        # Track changes for activity log
        changes = {}

        # Validate assignee
        new_assignee = data.get("assignee")
        if new_assignee and new_assignee != task.assignee:
            if not ProjectMemberRepository.is_member(task.project, new_assignee):
                raise ValidationError({"assignee": "Assignee must be project member"})
            changes["assignee"] = {
                "old": task.assignee.email if task.assignee else None,
                "new": new_assignee.email,
            }

        # Track status changes
        new_status = data.get("status")
        if new_status and new_status != task.status:
            changes["status"] = {"old": task.status, "new": new_status}

        # Track priority changes
        new_priority = data.get("priority")
        if new_priority and new_priority != task.priority:
            changes["priority"] = {"old": task.priority, "new": new_priority}

        # Track due date changes
        new_due_date = data.get("due_date")
        if new_due_date and new_due_date != task.due_date:
            changes["due_date"] = {
                "old": str(task.due_date) if task.due_date else None,
                "new": str(new_due_date),
            }

        with transaction.atomic():
            # Update task
            data["updated_by"] = user
            task = TaskRepository.update_task(task, data)

            # Log changes
            for field, change in changes.items():
                activity_type = {
                    "status": TaskActivity.ActivityType.STATUS_CHANGED,
                    "assignee": TaskActivity.ActivityType.ASSIGNED,
                    "priority": TaskActivity.ActivityType.PRIORITY_CHANGED,
                    "due_date": TaskActivity.ActivityType.DUE_DATE_CHANGED,
                }.get(field, TaskActivity.ActivityType.UPDATED)

                TaskService._log_activity(
                    task,
                    user,
                    activity_type,
                    f"Changed {field} from {change['old']} to {change['new']}",
                    old_value=change["old"],
                    new_value=change["new"],
                )

        return task

    @staticmethod
    def delete_task(task, user):
        """Soft delete task"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.is_admin():
            raise PermissionDenied("Only project admins can delete tasks")

        with transaction.atomic():
            # Update project counts
            project = task.project
            project.task_count = project.task_count - 1
            if task.status != Task.Status.DONE:
                project.open_task_count = project.open_task_count - 1
            else:
                project.completed_task_count = project.completed_task_count - 1
            project.save(
                update_fields=["task_count", "open_task_count", "completed_task_count"]
            )
            project.update_progress()

            TaskRepository.delete_task(task, user)

        return task

    @staticmethod
    def assign_task(task, user, assignee):
        """Assign task to user"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member:
            raise PermissionDenied("No permission to assign this task")

        if assignee and not ProjectMemberRepository.is_member(task.project, assignee):
            raise ValidationError({"assignee": "Assignee must be project member"})

        old_assignee = task.assignee
        task.assignee = assignee
        task.save(update_fields=["assignee"])

        # Log activity
        if assignee:
            TaskService._log_activity(
                task,
                user,
                TaskActivity.ActivityType.ASSIGNED,
                f"Assigned to {assignee.email}",
                old_value=old_assignee.email if old_assignee else None,
                new_value=assignee.email,
            )
        else:
            TaskService._log_activity(
                task,
                user,
                TaskActivity.ActivityType.UNASSIGNED,
                f"Unassigned from {old_assignee.email}",
                old_value=old_assignee.email if old_assignee else None,
            )

        return task

    @staticmethod
    def change_status(task, user, new_status):
        """Change task status"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to change task status")

        # Validate status
        if new_status not in dict(Task.Status.choices):
            raise ValidationError({"status": "Invalid status"})

        old_status = task.status

        with transaction.atomic():
            # Handle completion
            if new_status == Task.Status.DONE and old_status != Task.Status.DONE:
                task.mark_complete()
                TaskService._log_activity(
                    task,
                    user,
                    TaskActivity.ActivityType.COMPLETED,
                    f"Completed task",
                    old_value=old_status,
                    new_value=new_status,
                )
            # Handle reopening
            elif old_status == Task.Status.DONE and new_status != Task.Status.DONE:
                task.reopen()
                TaskService._log_activity(
                    task,
                    user,
                    TaskActivity.ActivityType.REOPENED,
                    f"Reopened task",
                    old_value=old_status,
                    new_value=new_status,
                )
            else:
                task.status = new_status
                task.save(update_fields=["status"])
                TaskService._log_activity(
                    task,
                    user,
                    TaskActivity.ActivityType.STATUS_CHANGED,
                    f"Changed status from {old_status} to {new_status}",
                    old_value=old_status,
                    new_value=new_status,
                )

        return task

    @staticmethod
    def add_label(task, user, label):
        """Add label to task"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to edit this task")

        if label not in task.labels:
            task.labels.append(label)
            task.save(update_fields=["labels"])

        return task

    @staticmethod
    def remove_label(task, user, label):
        """Remove label from task"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to edit this task")

        if label in task.labels:
            task.labels.remove(label)
            task.save(update_fields=["labels"])

        return task

    @staticmethod
    def add_blocked_by(task, user, blocking_task):
        """Add blocking task relationship"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to edit this task")

        # Validate blocking task belongs to same project
        if blocking_task.project != task.project:
            raise ValidationError(
                {"blocking_task": "Blocking task must belong to same project"}
            )

        # Avoid circular dependencies
        if task in blocking_task.blocked_by.all():
            raise ValidationError(
                {"blocking_task": "Cannot create circular dependency"}
            )

        task.blocked_by.add(blocking_task)

        # Update status if needed
        if task.is_blocked() and task.status != Task.Status.BLOCKED:
            task.status = Task.Status.BLOCKED
            task.save(update_fields=["status"])

        return task

    @staticmethod
    def remove_blocked_by(task, user, blocking_task):
        """Remove blocking task relationship"""
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member or not member.can_edit():
            raise PermissionDenied("No permission to edit this task")

        task.blocked_by.remove(blocking_task)
        return task

    @staticmethod
    def get_statistics(project):
        """Get task statistics for project"""
        return TaskRepository.get_statistics(project)

    @staticmethod
    def _log_activity(
        task, user, activity_type, description, old_value=None, new_value=None
    ):
        """Log task activity"""
        TaskActivity.objects.create(
            task=task,
            user=user,
            activity_type=activity_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
            created_by=user,
        )
