"""
Task Comment Service
Business logic for task comment operations.
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.tasks.repositories import TaskCommentRepository, ProjectMemberRepository
from apps.tasks.models import TaskActivity


class TaskCommentService:
    """Service for task comment business logic"""

    @staticmethod
    def create_comment(task, user, content, parent_comment=None):
        """Create new comment on task"""
        # Validate project membership
        member = ProjectMemberRepository.get_project_member(task.project, user)
        if not member:
            raise PermissionDenied("Must be project member to comment")

        # Validate parent comment belongs to same task
        if parent_comment and parent_comment.task != task:
            raise ValidationError(
                {"parent_comment": "Parent comment must belong to same task"}
            )

        with transaction.atomic():
            # Create comment
            comment_data = {
                "task": task,
                "author": user,
                "content": content,
                "parent_comment": parent_comment,
                "created_by": user,
            }
            comment = TaskCommentRepository.create_comment(comment_data)

            # Log activity
            from apps.tasks.services import TaskService

            TaskService._log_activity(
                task,
                user,
                TaskActivity.ActivityType.COMMENT_ADDED,
                f"Added comment",
            )

        return comment

    @staticmethod
    def update_comment(comment, user, content):
        """Update comment"""
        # Validate author
        if comment.author != user:
            raise PermissionDenied("Can only edit your own comments")

        comment = TaskCommentRepository.update_comment(comment, content)
        return comment

    @staticmethod
    def delete_comment(comment, user):
        """Delete comment"""
        # Validate author or project admin
        is_author = comment.author == user
        member = ProjectMemberRepository.get_project_member(comment.task.project, user)
        is_admin = member and member.is_admin()

        if not (is_author or is_admin):
            raise PermissionDenied(
                "Can only delete your own comments or must be project admin"
            )

        with transaction.atomic():
            # Update task comment count
            task = comment.task
            TaskCommentRepository.delete_comment(comment)

            # Decrement count
            task.comment_count = max(0, task.comment_count - 1)
            task.save(update_fields=["comment_count"])

        return comment

    @staticmethod
    def get_task_comments(task, user):
        """Get all comments for task"""
        # Validate can view task
        if not task.can_view(user):
            raise PermissionDenied("No permission to view this task")

        return TaskCommentRepository.get_task_comments(task)

    @staticmethod
    def get_comment_statistics(task):
        """Get comment statistics"""
        return TaskCommentRepository.get_statistics(task)
