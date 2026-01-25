"""
Collaboration Repositories
Repositories for TaskReaction and Mention models.
"""

from typing import List, Optional
from django.db.models import Count, Q
from apps.core.repositories.base import BaseRepository
from apps.tasks.models import TaskReaction, Mention


class TaskReactionRepository(BaseRepository):
    """
    Repository for TaskReaction model.
    """

    def __init__(self):
        super().__init__(TaskReaction)

    def get_task_reactions(self, task_id):
        """Get all reactions for a task"""
        return self.filter(task_id=task_id)

    def get_comment_reactions(self, comment_id):
        """Get all reactions for a comment"""
        return self.filter(comment_id=comment_id)

    def get_user_reaction(self, task_id, user_id, comment_id=None):
        """Get user's reaction to task or comment"""
        filters = {"task_id": task_id, "user_id": user_id}
        if comment_id:
            filters["comment_id"] = comment_id
        return self.filter(**filters).first()

    def toggle_reaction(self, task_id, user_id, reaction_type, comment_id=None):
        """Toggle a reaction on/off"""
        filters = {
            "task_id": task_id,
            "user_id": user_id,
            "reaction_type": reaction_type,
        }
        if comment_id:
            filters["comment_id"] = comment_id

        existing = self.filter(**filters).first()
        if existing:
            existing.delete()
            return None
        else:
            return self.create(**filters)

    def get_reaction_summary(self, task_id, comment_id=None):
        """Get reaction summary with counts"""
        filters = {"task_id": task_id}
        if comment_id:
            filters["comment_id"] = comment_id

        return (
            self.filter(**filters)
            .values("reaction_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

    def get_user_reactions(self, user_id, task_id=None):
        """Get all reactions by a user"""
        filters = {"user_id": user_id}
        if task_id:
            filters["task_id"] = task_id
        return self.filter(**filters)


class MentionRepository(BaseRepository):
    """
    Repository for Mention model.
    """

    def __init__(self):
        super().__init__(Mention)

    def get_user_mentions(self, user_id, is_read=None):
        """Get mentions for a user"""
        filters = {"mentioned_user_id": user_id}
        if is_read is not None:
            filters["is_read"] = is_read
        return self.filter(**filters).order_by("-created_at")

    def get_unread_mentions(self, user_id):
        """Get unread mentions for a user"""
        return self.get_user_mentions(user_id, is_read=False)

    def get_task_mentions(self, task_id):
        """Get all mentions in a task"""
        return self.filter(task_id=task_id)

    def create_mention(
        self, task_id, mentioned_by_id, mentioned_user_id, content_type, comment_id=None
    ):
        """Create a new mention"""
        return self.create(
            task_id=task_id,
            mentioned_by_id=mentioned_by_id,
            mentioned_user_id=mentioned_user_id,
            content_type=content_type,
            comment_id=comment_id,
        )

    def mark_all_as_read(self, user_id):
        """Mark all mentions as read for a user"""
        from django.utils import timezone

        mentions = self.get_unread_mentions(user_id)
        mentions.update(is_read=True, read_at=timezone.now())
        return mentions.count()

    def get_mention_statistics(self, user_id):
        """Get mention statistics for a user"""
        mentions = self.filter(mentioned_user_id=user_id)
        return {
            "total": mentions.count(),
            "unread": mentions.filter(is_read=False).count(),
            "read": mentions.filter(is_read=True).count(),
        }
