"""
Task Attachment Repository
Data access layer for TaskAttachment model.
"""

from apps.tasks.models import TaskAttachment


class TaskAttachmentRepository:
    """Repository for TaskAttachment data access"""

    @staticmethod
    def get_by_id(attachment_id):
        """Get attachment by ID"""
        try:
            return TaskAttachment.objects.get(id=attachment_id)
        except TaskAttachment.DoesNotExist:
            return None

    @staticmethod
    def get_task_attachments(task):
        """Get all attachments for a task"""
        return TaskAttachment.objects.filter(task=task).select_related("uploaded_by")

    @staticmethod
    def get_user_attachments(user, organization=None):
        """Get all attachments uploaded by user"""
        queryset = TaskAttachment.objects.filter(uploaded_by=user).select_related(
            "task"
        )
        if organization:
            queryset = queryset.filter(task__organization=organization)
        return queryset

    @staticmethod
    def create_attachment(data):
        """Create new attachment"""
        return TaskAttachment.objects.create(**data)

    @staticmethod
    def delete_attachment(attachment):
        """Delete attachment"""
        # Delete the file from storage
        if attachment.file:
            attachment.file.delete(save=False)
        attachment.delete()

    @staticmethod
    def get_statistics(task):
        """Get attachment statistics for task"""
        from django.db.models import Sum

        attachments = TaskAttachment.objects.filter(task=task)

        return {
            "total": attachments.count(),
            "total_size": attachments.aggregate(total=Sum("file_size"))["total"] or 0,
        }

    @staticmethod
    def filter_by_mime_type(queryset, mime_type):
        """Filter attachments by MIME type"""
        return queryset.filter(mime_type__startswith=mime_type)

    @staticmethod
    def get_images(task):
        """Get image attachments"""
        return TaskAttachment.objects.filter(task=task, mime_type__startswith="image/")

    @staticmethod
    def get_documents(task):
        """Get document attachments"""
        return TaskAttachment.objects.filter(task=task).filter(
            mime_type__in=[
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ]
        )
