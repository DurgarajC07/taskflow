"""
Task Comment Repository
Data access layer for TaskComment model.
"""

from django.db.models import Q
from apps.tasks.models import TaskComment


class TaskCommentRepository:
    """Repository for TaskComment data access"""

    @staticmethod
    def get_by_id(comment_id):
        """Get comment by ID"""
        try:
            return TaskComment.objects.get(id=comment_id)
        except TaskComment.DoesNotExist:
            return None

    @staticmethod
    def get_task_comments(task, include_replies=True):
        """Get all comments for a task"""
        if include_replies:
            return TaskComment.objects.filter(task=task).select_related(
                "author", "parent_comment"
            )
        return TaskComment.objects.filter(
            task=task, parent_comment__isnull=True
        ).select_related("author")

    @staticmethod
    def get_comment_replies(comment):
        """Get replies to a comment"""
        return TaskComment.objects.filter(parent_comment=comment).select_related(
            "author"
        )

    @staticmethod
    def get_user_comments(user, organization=None):
        """Get all comments by user"""
        queryset = TaskComment.objects.filter(author=user).select_related("task")
        if organization:
            queryset = queryset.filter(task__organization=organization)
        return queryset

    @staticmethod
    def create_comment(data):
        """Create new comment"""
        return TaskComment.objects.create(**data)

    @staticmethod
    def update_comment(comment, content):
        """Update comment content"""
        from django.utils import timezone as django_timezone

        comment.content = content
        comment.is_edited = True
        comment.edited_at = django_timezone.now()
        comment.save(update_fields=["content", "is_edited", "edited_at"])
        return comment

    @staticmethod
    def delete_comment(comment):
        """Delete comment"""
        comment.delete()

    @staticmethod
    def search_comments(task, query):
        """Search comments by content"""
        return TaskComment.objects.filter(task=task).filter(content__icontains=query)

    @staticmethod
    def get_statistics(task):
        """Get comment statistics for task"""
        comments = TaskComment.objects.filter(task=task)

        return {
            "total": comments.count(),
            "top_level": comments.filter(parent_comment__isnull=True).count(),
            "replies": comments.filter(parent_comment__isnull=False).count(),
        }
