"""
Team Models
Teams within organizations for project grouping and collaboration.
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models.base import BaseModel, SoftDeleteModel, OrganizationOwnedModel
from apps.core.utils.validators import validate_hex_color
from apps.core.managers.base import SoftDeleteManager, OrganizationManager

User = get_user_model()


class Team(OrganizationOwnedModel, SoftDeleteModel):
    """
    Team model for organizing members within an organization.
    Teams can be assigned to projects and have specific members.
    """

    # Team Visibility
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        SECRET = "secret", "Secret"

    # Basic Information
    name = models.CharField(max_length=255, help_text="Team name")
    description = models.TextField(blank=True, help_text="Team description")

    # Appearance
    color = models.CharField(
        max_length=7,
        default="#10B981",
        validators=[validate_hex_color],
        help_text="Team color (hex)",
    )
    icon = models.CharField(max_length=50, blank=True, help_text="Team icon identifier")

    # Settings
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        help_text="Team visibility level",
    )

    # Leadership
    lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
        help_text="Team lead/manager",
    )

    # Members
    members = models.ManyToManyField(
        User,
        through="TeamMember",
        through_fields=("team", "user"),
        related_name="teams",
        help_text="Team members",
    )

    # Statistics
    member_count = models.IntegerField(default=0, help_text="Current number of members")
    project_count = models.IntegerField(
        default=0, help_text="Number of assigned projects"
    )

    # Custom managers
    objects = OrganizationManager()
    all_objects = SoftDeleteManager()

    class Meta:
        db_table = "teams"
        ordering = ["name"]
        unique_together = [["organization", "name"]]
        indexes = [
            models.Index(fields=["organization", "visibility"]),
            models.Index(fields=["lead"]),
        ]
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def is_member(self, user):
        """Check if user is team member"""
        return self.members.filter(id=user.id).exists()

    def is_lead(self, user):
        """Check if user is team lead"""
        return self.lead == user

    def can_view(self, user):
        """Check if user can view team"""
        # Public teams visible to all org members
        if self.visibility == self.Visibility.PUBLIC:
            return self.organization.is_member(user)

        # Private teams visible to members
        if self.visibility == self.Visibility.PRIVATE:
            return self.is_member(user) or self.organization.has_permission(
                user, "manage_teams"
            )

        # Secret teams only visible to members
        if self.visibility == self.Visibility.SECRET:
            return self.is_member(user)

        return False

    def increment_member_count(self):
        """Increment member count"""
        self.member_count = models.F("member_count") + 1
        self.save(update_fields=["member_count"])
        self.refresh_from_db()

    def decrement_member_count(self):
        """Decrement member count"""
        self.member_count = models.F("member_count") - 1
        self.save(update_fields=["member_count"])
        self.refresh_from_db()

    def increment_project_count(self):
        """Increment project count"""
        self.project_count = models.F("project_count") + 1
        self.save(update_fields=["project_count"])
        self.refresh_from_db()

    def decrement_project_count(self):
        """Decrement project count"""
        self.project_count = models.F("project_count") - 1
        self.save(update_fields=["project_count"])
        self.refresh_from_db()


class TeamMember(BaseModel):
    """
    Team membership model linking users to teams.
    """

    # Member Roles
    class Role(models.TextChoices):
        LEAD = "lead", "Lead"
        MAINTAINER = "maintainer", "Maintainer"
        MEMBER = "member", "Member"

    # Relationships
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="team_memberships",
        help_text="Team",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_memberships",
        help_text="User",
    )

    # Role
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text="Member role in team",
    )

    # Added by
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_team_members",
        help_text="User who added this member",
    )

    # Activity
    joined_at = models.DateTimeField(
        auto_now_add=True, help_text="Date when user joined team"
    )
    last_active_at = models.DateTimeField(
        null=True, blank=True, help_text="Last activity in team context"
    )

    class Meta:
        db_table = "team_members"
        ordering = ["-joined_at"]
        unique_together = [["team", "user"]]
        indexes = [
            models.Index(fields=["team", "role"]),
            models.Index(fields=["user"]),
        ]
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.user.email} - {self.team.name} ({self.role})"

    def is_lead(self):
        """Check if member is team lead"""
        return self.role == self.Role.LEAD

    def is_maintainer(self):
        """Check if member is maintainer or lead"""
        return self.role in [self.Role.LEAD, self.Role.MAINTAINER]

    def can_manage_members(self):
        """Check if member can manage other team members"""
        return self.is_maintainer()

    def update_last_active(self):
        """Update last active timestamp"""
        from django.utils import timezone as django_timezone

        self.last_active_at = django_timezone.now()
        self.save(update_fields=["last_active_at"])


class Project(OrganizationOwnedModel, SoftDeleteModel):
    """
    Project model for organizing tasks and work items.
    Projects belong to organizations and can be assigned to teams.
    """

    # Project Status
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On Hold"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    # Project Priority
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    # Project Visibility
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        SECRET = "secret", "Secret"

    # Basic Information
    name = models.CharField(max_length=255, help_text="Project name")
    key = models.CharField(
        max_length=10,
        help_text="Project key/identifier (e.g., PROJ)",
    )
    description = models.TextField(blank=True, help_text="Project description")

    # Appearance
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        validators=[validate_hex_color],
        help_text="Project color (hex)",
    )
    icon = models.CharField(
        max_length=50, blank=True, help_text="Project icon identifier"
    )

    # Settings
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
        help_text="Project status",
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text="Project priority",
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        help_text="Project visibility level",
    )

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_projects",
        help_text="Project owner",
    )

    # Team Assignment
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text="Assigned team",
    )

    # Members
    members = models.ManyToManyField(
        User,
        through="ProjectMember",
        through_fields=("project", "user"),
        related_name="projects",
        help_text="Project members",
    )

    # Dates
    start_date = models.DateField(null=True, blank=True, help_text="Project start date")
    due_date = models.DateField(null=True, blank=True, help_text="Project due date")
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="When project was completed"
    )

    # Statistics
    member_count = models.IntegerField(default=0, help_text="Current number of members")
    task_count = models.IntegerField(default=0, help_text="Total number of tasks")
    open_task_count = models.IntegerField(default=0, help_text="Number of open tasks")
    completed_task_count = models.IntegerField(
        default=0, help_text="Number of completed tasks"
    )
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Completion percentage (0-100)",
    )

    # Settings
    is_template = models.BooleanField(
        default=False, help_text="Whether this is a project template"
    )
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Project-specific settings and preferences",
    )

    # Custom managers
    objects = OrganizationManager()
    all_objects = SoftDeleteManager()

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]
        unique_together = [["organization", "key"]]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "visibility"]),
            models.Index(fields=["team"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["due_date"]),
        ]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.key}: {self.name}"

    def is_member(self, user):
        """Check if user is project member"""
        return self.members.filter(id=user.id).exists()

    def is_owner(self, user):
        """Check if user is project owner"""
        return self.owner == user

    def can_view(self, user):
        """Check if user can view project"""
        # Public projects visible to all org members
        if self.visibility == self.Visibility.PUBLIC:
            return self.organization.is_member(user)

        # Private projects visible to members and team members
        if self.visibility == self.Visibility.PRIVATE:
            is_member = self.is_member(user)
            is_team_member = (
                self.team and self.team.is_member(user) if self.team else False
            )
            has_permission = self.organization.has_permission(user, "manage_projects")
            return is_member or is_team_member or has_permission

        # Secret projects only visible to members
        if self.visibility == self.Visibility.SECRET:
            return self.is_member(user)

        return False

    def increment_member_count(self):
        """Increment member count"""
        self.member_count = models.F("member_count") + 1
        self.save(update_fields=["member_count"])
        self.refresh_from_db()

    def decrement_member_count(self):
        """Decrement member count"""
        self.member_count = models.F("member_count") - 1
        self.save(update_fields=["member_count"])
        self.refresh_from_db()

    def update_progress(self):
        """Calculate and update project progress"""
        if self.task_count > 0:
            self.progress = (self.completed_task_count / self.task_count) * 100
        else:
            self.progress = 0
        self.save(update_fields=["progress"])

    def mark_completed(self):
        """Mark project as completed"""
        from django.utils import timezone as django_timezone

        self.status = self.Status.COMPLETED
        self.completed_at = django_timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def archive(self):
        """Archive the project"""
        self.status = self.Status.ARCHIVED
        self.save(update_fields=["status"])


class ProjectMember(BaseModel):
    """
    Project membership model linking users to projects.
    """

    # Member Roles
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        VIEWER = "viewer", "Viewer"

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        help_text="Project",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        help_text="User",
    )

    # Role
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text="Member role in project",
    )

    # Added by
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_project_members",
        help_text="User who added this member",
    )

    # Activity
    joined_at = models.DateTimeField(
        auto_now_add=True, help_text="Date when user joined project"
    )
    last_active_at = models.DateTimeField(
        null=True, blank=True, help_text="Last activity in project context"
    )

    # Permissions override
    custom_permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom permissions for this member",
    )

    class Meta:
        db_table = "project_members"
        ordering = ["-joined_at"]
        unique_together = [["project", "user"]]
        indexes = [
            models.Index(fields=["project", "role"]),
            models.Index(fields=["user"]),
        ]
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"

    def __str__(self):
        return f"{self.user.email} - {self.project.name} ({self.role})"

    def is_owner(self):
        """Check if member is project owner"""
        return self.role == self.Role.OWNER

    def is_admin(self):
        """Check if member is admin or owner"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]

    def can_edit(self):
        """Check if member can edit project"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN, self.Role.MEMBER]

    def can_manage_members(self):
        """Check if member can manage other project members"""
        return self.is_admin()

    def update_last_active(self):
        """Update last active timestamp"""
        from django.utils import timezone as django_timezone

        self.last_active_at = django_timezone.now()
        self.save(update_fields=["last_active_at"])


# ============================================================================
# Task Models
# ============================================================================


class Task(OrganizationOwnedModel, SoftDeleteModel):
    """
    Task model for work items within projects.
    Tasks can be assigned to users and tracked through various stages.
    """

    # Task Status
    class Status(models.TextChoices):
        BACKLOG = "backlog", "Backlog"
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        IN_REVIEW = "in_review", "In Review"
        BLOCKED = "blocked", "Blocked"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    # Task Priority
    class Priority(models.TextChoices):
        LOWEST = "lowest", "Lowest"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        HIGHEST = "highest", "Highest"

    # Task Type
    class TaskType(models.TextChoices):
        TASK = "task", "Task"
        BUG = "bug", "Bug"
        FEATURE = "feature", "Feature"
        EPIC = "epic", "Epic"
        STORY = "story", "Story"
        SUBTASK = "subtask", "Subtask"

    # Project relationship
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        help_text="Project this task belongs to",
    )

    # Basic Information
    title = models.CharField(max_length=500, help_text="Task title")
    description = models.TextField(blank=True, help_text="Task description")
    task_number = models.IntegerField(help_text="Sequential task number within project")

    # Classification
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.TASK,
        help_text="Task type",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        help_text="Task status",
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text="Task priority",
    )

    # Assignment
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        help_text="Currently assigned user",
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_tasks",
        help_text="User who created the task",
    )

    # Labels and tags
    labels = models.JSONField(
        default=list,
        blank=True,
        help_text="Task labels/tags",
    )

    # Relationships
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subtasks",
        help_text="Parent task for subtasks",
    )
    blocked_by = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="blocking_tasks",
        blank=True,
        help_text="Tasks blocking this task",
    )

    # Dates
    start_date = models.DateField(null=True, blank=True, help_text="Task start date")
    due_date = models.DateField(null=True, blank=True, help_text="Task due date")
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="When task was completed"
    )

    # Time tracking
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated hours to complete",
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        help_text="Actual hours spent",
    )

    # Metrics
    comment_count = models.IntegerField(default=0, help_text="Number of comments")
    attachment_count = models.IntegerField(default=0, help_text="Number of attachments")
    subtask_count = models.IntegerField(default=0, help_text="Number of subtasks")

    # Custom fields
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom field values",
    )

    # Custom managers
    objects = OrganizationManager()
    all_objects = SoftDeleteManager()

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        unique_together = [["project", "task_number"]]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "assignee"]),
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["parent_task"]),
        ]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return f"{self.project.key}-{self.task_number}: {self.title}"

    @property
    def task_key(self):
        """Get task identifier (e.g., PROJ-123)"""
        return f"{self.project.key}-{self.task_number}"

    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.status == self.Status.DONE:
            return False

        from django.utils import timezone as django_timezone

        return self.due_date < django_timezone.now().date()

    def is_blocked(self):
        """Check if task is blocked"""
        return self.blocked_by.filter(
            status__in=[
                self.Status.TODO,
                self.Status.IN_PROGRESS,
                self.Status.IN_REVIEW,
                self.Status.BLOCKED,
            ]
        ).exists()

    def mark_complete(self):
        """Mark task as complete"""
        from django.utils import timezone as django_timezone

        self.status = self.Status.DONE
        self.completed_at = django_timezone.now()
        self.save(update_fields=["status", "completed_at"])

        # Update project counters
        if self.project:
            self.project.completed_task_count = models.F("completed_task_count") + 1
            self.project.open_task_count = models.F("open_task_count") - 1
            self.project.save(update_fields=["completed_task_count", "open_task_count"])
            self.project.refresh_from_db()
            self.project.update_progress()

    def reopen(self):
        """Reopen completed task"""
        if self.status == self.Status.DONE:
            self.status = self.Status.TODO
            self.completed_at = None
            self.save(update_fields=["status", "completed_at"])

            # Update project counters
            if self.project:
                self.project.completed_task_count = models.F("completed_task_count") - 1
                self.project.open_task_count = models.F("open_task_count") + 1
                self.project.save(
                    update_fields=["completed_task_count", "open_task_count"]
                )
                self.project.refresh_from_db()
                self.project.update_progress()

    def save(self, *args, **kwargs):
        """Override save to auto-increment task_number"""
        if not self.task_number:
            # Get max task number for project
            max_number = Task.objects.filter(project=self.project).aggregate(
                max_num=models.Max("task_number")
            )["max_num"]
            self.task_number = (max_number or 0) + 1

        super().save(*args, **kwargs)


class TaskComment(BaseModel):
    """
    Comments on tasks for discussion and collaboration.
    """

    # Relationships
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="Task this comment belongs to",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="task_comments",
        help_text="Comment author",
    )

    # Content
    content = models.TextField(help_text="Comment content")

    # Reply threading
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text="Parent comment for replies",
    )

    # Edit tracking
    is_edited = models.BooleanField(
        default=False, help_text="Whether comment was edited"
    )
    edited_at = models.DateTimeField(
        null=True, blank=True, help_text="When comment was last edited"
    )

    class Meta:
        db_table = "task_comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
            models.Index(fields=["author"]),
        ]
        verbose_name = "Task Comment"
        verbose_name_plural = "Task Comments"

    def __str__(self):
        return f"Comment by {self.author.email} on {self.task.task_key}"

    def save(self, *args, **kwargs):
        """Override save to update task comment count"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.task.comment_count = models.F("comment_count") + 1
            self.task.save(update_fields=["comment_count"])


class TaskAttachment(BaseModel):
    """
    File attachments for tasks.
    """

    # Relationships
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments",
        help_text="Task this attachment belongs to",
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="task_attachments",
        help_text="User who uploaded the file",
    )

    # File information
    file = models.FileField(
        upload_to="tasks/attachments/%Y/%m/%d/",
        help_text="Uploaded file",
    )
    filename = models.CharField(max_length=255, help_text="Original filename")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True, help_text="MIME type")

    # Metadata
    description = models.TextField(blank=True, help_text="File description")

    class Meta:
        db_table = "task_attachments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task"]),
            models.Index(fields=["uploaded_by"]),
        ]
        verbose_name = "Task Attachment"
        verbose_name_plural = "Task Attachments"

    def __str__(self):
        return f"{self.filename} on {self.task.task_key}"

    def save(self, *args, **kwargs):
        """Override save to update task attachment count"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.task.attachment_count = models.F("attachment_count") + 1
            self.task.save(update_fields=["attachment_count"])

    def delete(self, *args, **kwargs):
        """Override delete to update task attachment count"""
        task = self.task
        super().delete(*args, **kwargs)

        task.attachment_count = models.F("attachment_count") - 1
        task.save(update_fields=["attachment_count"])


class TaskActivity(BaseModel):
    """
    Activity log for tasks to track all changes.
    """

    # Activity Types
    class ActivityType(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        STATUS_CHANGED = "status_changed", "Status Changed"
        ASSIGNED = "assigned", "Assigned"
        UNASSIGNED = "unassigned", "Unassigned"
        COMMENT_ADDED = "comment_added", "Comment Added"
        ATTACHMENT_ADDED = "attachment_added", "Attachment Added"
        PRIORITY_CHANGED = "priority_changed", "Priority Changed"
        DUE_DATE_CHANGED = "due_date_changed", "Due Date Changed"
        COMPLETED = "completed", "Completed"
        REOPENED = "reopened", "Reopened"

    # Relationships
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="activities",
        help_text="Task this activity belongs to",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_activities",
        help_text="User who performed the action",
    )

    # Activity details
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
        help_text="Type of activity",
    )
    description = models.TextField(help_text="Activity description")

    # Change tracking
    old_value = models.JSONField(null=True, blank=True, help_text="Previous value")
    new_value = models.JSONField(null=True, blank=True, help_text="New value")

    class Meta:
        db_table = "task_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "-created_at"]),
            models.Index(fields=["user"]),
            models.Index(fields=["activity_type"]),
        ]
        verbose_name = "Task Activity"
        verbose_name_plural = "Task Activities"

    def __str__(self):
        return f"{self.activity_type} on {self.task.task_key} by {self.user.email if self.user else 'System'}"


# ============================================================================
# WORKFLOW MODELS
# ============================================================================


class Workflow(OrganizationOwnedModel, SoftDeleteModel):
    """
    Workflow defines custom task status flows for projects.
    Organizations can create multiple workflows for different project types.
    """

    # Basic Information
    name = models.CharField(max_length=255, help_text="Workflow name")
    description = models.TextField(blank=True, help_text="Workflow description")

    # Scope
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="workflows",
        help_text="Project-specific workflow (null for organization-level)",
    )

    # Settings
    is_default = models.BooleanField(
        default=False,
        help_text="Default workflow for new projects",
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System workflow (cannot be deleted)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether workflow is active",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
        help_text="User who created the workflow",
    )

    # Custom managers
    objects = OrganizationManager()
    all_objects = SoftDeleteManager()

    class Meta:
        db_table = "workflows"
        ordering = ["name"]
        unique_together = [["organization", "name"]]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["project"]),
            models.Index(fields=["is_default"]),
        ]
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"

    def __str__(self):
        return self.name


class WorkflowState(BaseModel):
    """
    Workflow state represents a status in a workflow.
    States define the possible statuses tasks can have within a workflow.
    """

    # State Category
    class Category(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    # Workflow relationship
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="states",
        help_text="Workflow this state belongs to",
    )

    # Basic Information
    name = models.CharField(max_length=100, help_text="State name")
    description = models.TextField(blank=True, help_text="State description")

    # Classification
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        help_text="State category",
    )

    # Appearance
    color = models.CharField(
        max_length=7,
        default="#6B7280",
        validators=[validate_hex_color],
        help_text="State color (hex)",
    )

    # Settings
    is_initial = models.BooleanField(
        default=False,
        help_text="Initial state for new tasks",
    )
    is_final = models.BooleanField(
        default=False,
        help_text="Final/completed state",
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Display order in UI",
    )

    class Meta:
        db_table = "workflow_states"
        ordering = ["workflow", "display_order", "name"]
        unique_together = [["workflow", "name"]]
        indexes = [
            models.Index(fields=["workflow", "display_order"]),
            models.Index(fields=["workflow", "is_initial"]),
            models.Index(fields=["workflow", "is_final"]),
        ]
        verbose_name = "Workflow State"
        verbose_name_plural = "Workflow States"

    def __str__(self):
        return f"{self.workflow.name}: {self.name}"


class WorkflowTransition(BaseModel):
    """
    Workflow transition defines allowed state changes.
    Transitions control which states tasks can move between.
    """

    # Workflow relationship
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="transitions",
        help_text="Workflow this transition belongs to",
    )

    # State relationships
    from_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name="outgoing_transitions",
        help_text="Source state",
    )
    to_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
        help_text="Target state",
    )

    # Basic Information
    name = models.CharField(
        max_length=100,
        help_text="Transition name (e.g., 'Start Progress', 'Complete')",
    )
    description = models.TextField(blank=True, help_text="Transition description")

    # Conditions
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conditions that must be met for transition",
    )

    # Actions
    actions = models.JSONField(
        default=list,
        blank=True,
        help_text="Actions to perform on transition",
    )

    # Settings
    requires_comment = models.BooleanField(
        default=False,
        help_text="Whether transition requires a comment",
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Display order in UI",
    )

    class Meta:
        db_table = "workflow_transitions"
        ordering = ["workflow", "display_order"]
        unique_together = [["workflow", "from_state", "to_state"]]
        indexes = [
            models.Index(fields=["workflow"]),
            models.Index(fields=["from_state"]),
            models.Index(fields=["to_state"]),
        ]
        verbose_name = "Workflow Transition"
        verbose_name_plural = "Workflow Transitions"

    def __str__(self):
        return f"{self.from_state.name} → {self.to_state.name}"


class WorkflowRule(BaseModel):
    """
    Workflow rule defines automation actions.
    Rules trigger actions based on events and conditions.
    """

    # Trigger Types
    class TriggerType(models.TextChoices):
        STATUS_CHANGED = "status_changed", "Status Changed"
        TASK_CREATED = "task_created", "Task Created"
        TASK_UPDATED = "task_updated", "Task Updated"
        TASK_ASSIGNED = "task_assigned", "Task Assigned"
        COMMENT_ADDED = "comment_added", "Comment Added"
        ATTACHMENT_ADDED = "attachment_added", "Attachment Added"
        DUE_DATE_APPROACHING = "due_date_approaching", "Due Date Approaching"
        DUE_DATE_PASSED = "due_date_passed", "Due Date Passed"

    # Workflow relationship
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="Workflow this rule belongs to",
    )

    # Basic Information
    name = models.CharField(max_length=255, help_text="Rule name")
    description = models.TextField(blank=True, help_text="Rule description")

    # Trigger
    trigger_type = models.CharField(
        max_length=30,
        choices=TriggerType.choices,
        help_text="What triggers this rule",
    )
    trigger_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Trigger-specific configuration",
    )

    # Conditions
    conditions = models.JSONField(
        default=list,
        blank=True,
        help_text="Conditions that must be met",
    )

    # Actions
    actions = models.JSONField(
        default=list,
        blank=True,
        help_text="Actions to perform when triggered",
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether rule is active",
    )
    priority = models.IntegerField(
        default=0,
        help_text="Execution priority (higher = earlier)",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflow_rules",
        help_text="User who created the rule",
    )

    # Statistics
    execution_count = models.IntegerField(
        default=0,
        help_text="Number of times rule has been executed",
    )
    last_executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last execution timestamp",
    )

    class Meta:
        db_table = "workflow_rules"
        ordering = ["-priority", "name"]
        indexes = [
            models.Index(fields=["workflow", "is_active"]),
            models.Index(fields=["trigger_type"]),
            models.Index(fields=["-priority"]),
        ]
        verbose_name = "Workflow Rule"
        verbose_name_plural = "Workflow Rules"

    def __str__(self):
        return f"{self.workflow.name}: {self.name}"


# ============================================================================
# COLLABORATION MODELS
# ============================================================================


class TaskReaction(BaseModel):
    """
    Emoji reactions to tasks and comments.
    Allows users to react with emojis to express sentiment quickly.
    """

    class ReactionType(models.TextChoices):
        THUMBS_UP = "👍", "Thumbs Up"
        THUMBS_DOWN = "👎", "Thumbs Down"
        HEART = "❤️", "Heart"
        FIRE = "🔥", "Fire"
        PARTY = "🎉", "Party"
        ROCKET = "🚀", "Rocket"
        EYES = "👀", "Eyes"
        THINKING = "🤔", "Thinking"
        CHECK = "✅", "Check"
        QUESTION = "❓", "Question"

    # Relations
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reactions",
        help_text="Related task",
    )
    comment = models.ForeignKey(
        "tasks.TaskComment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reactions",
        help_text="Related comment",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="task_reactions",
        help_text="User who reacted",
    )

    # Reaction
    reaction_type = models.CharField(
        max_length=10,
        choices=ReactionType.choices,
        help_text="Reaction emoji type",
    )

    class Meta:
        db_table = "task_reactions"
        ordering = ["-created_at"]
        unique_together = [["task", "comment", "user", "reaction_type"]]
        indexes = [
            models.Index(fields=["task", "reaction_type"]),
            models.Index(fields=["comment", "reaction_type"]),
            models.Index(fields=["user"]),
        ]
        verbose_name = "Task Reaction"
        verbose_name_plural = "Task Reactions"

    def __str__(self):
        target = self.task or self.comment
        return f"{self.user.email} reacted {self.reaction_type} on {target}"


class Mention(BaseModel):
    """
    @mention tracking for tasks and comments.
    Tracks when users are mentioned in content.
    """

    class ContentType(models.TextChoices):
        TASK = "task", "Task"
        COMMENT = "comment", "Comment"

    # Relations
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="mentions",
        help_text="Related task",
    )
    comment = models.ForeignKey(
        "tasks.TaskComment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="mentions",
        help_text="Related comment (if mentioned in comment)",
    )

    # Users
    mentioned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentions_created",
        help_text="User who created the mention",
    )
    mentioned_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentions_received",
        help_text="User who was mentioned",
    )

    # Content
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        help_text="Type of content containing mention",
    )

    # Status
    is_read = models.BooleanField(
        default=False,
        help_text="Whether mention has been seen",
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When mention was marked as read",
    )

    class Meta:
        db_table = "mentions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mentioned_user", "is_read"]),
            models.Index(fields=["task"]),
            models.Index(fields=["content_type"]),
        ]
        verbose_name = "Mention"
        verbose_name_plural = "Mentions"

    def __str__(self):
        return f"@{self.mentioned_user.email} mentioned by {self.mentioned_by.email}"

    def mark_as_read(self):
        """Mark mention as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.functions.Now()
            self.save(update_fields=["is_read", "read_at"])


# ============================================================================
# TIME TRACKING MODELS
# ============================================================================


class TimeEntry(OrganizationOwnedModel):
    """
    Time tracking entries for tasks.
    Records hours worked on tasks with billability tracking.
    """

    # Relations
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="time_entries",
        help_text="Related task",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="time_entries",
        help_text="User who logged time",
    )

    # Time Information
    description = models.TextField(
        blank=True,
        help_text="Description of work performed",
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Hours worked",
    )
    date = models.DateField(
        help_text="Date of work",
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time of work",
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="End time of work",
    )

    # Settings
    is_billable = models.BooleanField(
        default=True,
        help_text="Whether time is billable",
    )

    class Meta:
        db_table = "time_entries"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "task"]),
            models.Index(fields=["user", "date"]),
            models.Index(fields=["is_billable"]),
            models.Index(fields=["-date"]),
        ]
        verbose_name = "Time Entry"
        verbose_name_plural = "Time Entries"

    def __str__(self):
        return f"{self.user.email} - {self.hours}h on {self.task.task_key}"

    def calculate_duration(self):
        """Calculate duration from start/end times"""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta

            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            duration = end - start
            return duration.total_seconds() / 3600  # Convert to hours
        return None


class WorkLog(BaseModel):
    """
    Automatic activity logging for tasks.
    Records all task-related actions for audit trail.
    """

    class LogType(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        ASSIGNED = "assigned", "Assigned"
        STATUS_CHANGED = "status_changed", "Status Changed"
        COMMENTED = "commented", "Commented"
        ATTACHED = "attached", "Attachment Added"
        TIME_LOGGED = "time_logged", "Time Logged"
        LINKED = "linked", "Linked"

    # Relations
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="work_logs",
        help_text="Related task",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="work_logs",
        help_text="User who performed the action",
    )

    # Log Details
    log_type = models.CharField(
        max_length=20,
        choices=LogType.choices,
        help_text="Type of activity",
    )
    description = models.TextField(
        help_text="Description of the activity",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional activity metadata",
    )

    class Meta:
        db_table = "work_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "-created_at"]),
            models.Index(fields=["user"]),
            models.Index(fields=["log_type"]),
        ]
        verbose_name = "Work Log"
        verbose_name_plural = "Work Logs"

    def __str__(self):
        return f"{self.log_type} - {self.task.task_key} by {self.user}"


# ============================================================================
# AGILE MODELS
# ============================================================================


class Sprint(BaseModel):
    """
    Sprint/Iteration management for agile projects.
    Represents time-boxed development cycles.
    """

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    # Relations
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        related_name="sprints",
        help_text="Related project",
    )

    # Sprint Information
    name = models.CharField(
        max_length=255,
        help_text="Sprint name",
    )
    sprint_number = models.IntegerField(
        help_text="Sprint sequence number",
    )
    goal = models.TextField(
        blank=True,
        help_text="Sprint goal/objective",
    )
    description = models.TextField(
        blank=True,
        help_text="Sprint description",
    )

    # Timeline
    start_date = models.DateField(
        help_text="Sprint start date",
    )
    end_date = models.DateField(
        help_text="Sprint end date",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
        help_text="Sprint status",
    )

    # Capacity
    capacity = models.IntegerField(
        null=True,
        blank=True,
        help_text="Team capacity (story points)",
    )
    story_points_completed = models.IntegerField(
        default=0,
        help_text="Completed story points",
    )

    # Statistics
    completed_tasks_count = models.IntegerField(
        default=0,
        help_text="Number of completed tasks",
    )
    total_tasks_count = models.IntegerField(
        default=0,
        help_text="Total number of tasks",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_sprints",
        help_text="User who created the sprint",
    )

    class Meta:
        db_table = "sprints"
        ordering = ["-sprint_number"]
        unique_together = [["project", "sprint_number"]]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["-sprint_number"]),
        ]
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def start(self):
        """Start the sprint"""
        self.status = self.Status.ACTIVE
        self.save(update_fields=["status"])

    def complete(self):
        """Complete the sprint"""
        self.status = self.Status.COMPLETED
        self.save(update_fields=["status"])

    @property
    def velocity(self):
        """Calculate sprint velocity"""
        return self.story_points_completed


class SprintTask(BaseModel):
    """
    Association between sprints and tasks.
    Tracks tasks committed to a sprint.
    """

    # Relations
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.CASCADE,
        related_name="sprint_tasks",
        help_text="Related sprint",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="sprint_assignments",
        help_text="Related task",
    )

    # Task Details
    story_points = models.IntegerField(
        null=True,
        blank=True,
        help_text="Story points for this task",
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order within sprint",
    )

    # Metadata
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sprint_task_additions",
        help_text="User who added task to sprint",
    )

    class Meta:
        db_table = "sprint_tasks"
        ordering = ["order", "-created_at"]
        unique_together = [["sprint", "task"]]
        indexes = [
            models.Index(fields=["sprint", "order"]),
            models.Index(fields=["task"]),
        ]
        verbose_name = "Sprint Task"
        verbose_name_plural = "Sprint Tasks"

    def __str__(self):
        return f"{self.sprint.name} - {self.task.task_key}"


class Backlog(BaseModel):
    """
    Product or Sprint backlog management.
    Container for backlog items.
    """

    class BacklogType(models.TextChoices):
        PRODUCT = "product", "Product Backlog"
        SPRINT = "sprint", "Sprint Backlog"

    # Relations
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        related_name="backlogs",
        help_text="Related project",
    )

    # Backlog Information
    name = models.CharField(
        max_length=255,
        help_text="Backlog name",
    )
    backlog_type = models.CharField(
        max_length=20,
        choices=BacklogType.choices,
        default=BacklogType.PRODUCT,
        help_text="Type of backlog",
    )
    description = models.TextField(
        blank=True,
        help_text="Backlog description",
    )

    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_backlogs",
        help_text="Backlog owner",
    )

    class Meta:
        db_table = "backlogs"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["project", "backlog_type"]),
        ]
        verbose_name = "Backlog"
        verbose_name_plural = "Backlogs"

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class BacklogItem(BaseModel):
    """
    Individual items in backlogs.
    Represents prioritized work items.
    """

    class Priority(models.IntegerChoices):
        HIGHEST = 1, "Highest"
        HIGH = 2, "High"
        MEDIUM = 3, "Medium"
        LOW = 4, "Low"
        LOWEST = 5, "Lowest"

    # Relations
    backlog = models.ForeignKey(
        Backlog,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Related backlog",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="backlog_items",
        help_text="Related task",
    )

    # Prioritization
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text="Item priority",
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order in backlog",
    )
    story_points = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated story points",
    )
    business_value = models.IntegerField(
        null=True,
        blank=True,
        help_text="Business value score",
    )

    # Metadata
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="backlog_item_additions",
        help_text="User who added item",
    )

    class Meta:
        db_table = "backlog_items"
        ordering = ["priority", "order"]
        unique_together = [["backlog", "task"]]
        indexes = [
            models.Index(fields=["backlog", "priority", "order"]),
            models.Index(fields=["task"]),
        ]
        verbose_name = "Backlog Item"
        verbose_name_plural = "Backlog Items"

    def __str__(self):
        return f"{self.backlog.name} - {self.task.task_key}"


# ============================================================================
# LABELS & TAGS MODELS
# ============================================================================


class Label(BaseModel):
    """
    Project-specific labels for task categorization.
    Allows project-level organization.
    """

    # Relations
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        related_name="labels",
        help_text="Related project",
    )

    # Label Information
    name = models.CharField(
        max_length=100,
        help_text="Label name",
    )
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        validators=[validate_hex_color],
        help_text="Label color (hex)",
    )
    description = models.TextField(
        blank=True,
        help_text="Label description",
    )

    # Statistics
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times label is used",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_labels",
        help_text="User who created the label",
    )

    class Meta:
        db_table = "labels"
        ordering = ["name"]
        unique_together = [["project", "name"]]
        indexes = [
            models.Index(fields=["project"]),
        ]
        verbose_name = "Label"
        verbose_name_plural = "Labels"

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count = models.F("usage_count") + 1
        self.save(update_fields=["usage_count"])


class Tag(OrganizationOwnedModel):
    """
    Organization-wide tags for cross-project categorization.
    Allows organization-level task categorization.
    """

    # Tag Information
    name = models.CharField(
        max_length=100,
        help_text="Tag name",
    )
    color = models.CharField(
        max_length=7,
        default="#8B5CF6",
        validators=[validate_hex_color],
        help_text="Tag color (hex)",
    )
    description = models.TextField(
        blank=True,
        help_text="Tag description",
    )

    # Statistics
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times tag is used",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tags",
        help_text="User who created the tag",
    )

    class Meta:
        db_table = "tags"
        ordering = ["name"]
        unique_together = [["organization", "name"]]
        indexes = [
            models.Index(fields=["organization"]),
        ]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count = models.F("usage_count") + 1
        self.save(update_fields=["usage_count"])


class SavedFilter(OrganizationOwnedModel):
    """
    User-defined saved filters for task queries.
    Allows users to save and reuse complex filter configurations.
    """

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        SHARED = "shared", "Shared with Team"
        PUBLIC = "public", "Public"

    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_filters",
        help_text="Filter owner",
    )
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="saved_filters",
        help_text="Optional project filter scope",
    )

    # Filter Information
    name = models.CharField(
        max_length=255,
        help_text="Filter name",
    )
    description = models.TextField(
        blank=True,
        help_text="Filter description",
    )
    filter_config = models.JSONField(
        default=dict,
        help_text="Filter configuration (criteria, sorting, grouping)",
    )

    # Settings
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        help_text="Filter visibility",
    )
    is_favorite = models.BooleanField(
        default=False,
        help_text="Whether filter is favorited",
    )

    # Statistics
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times filter has been used",
    )

    class Meta:
        db_table = "saved_filters"
        ordering = ["-is_favorite", "name"]
        indexes = [
            models.Index(fields=["organization", "user"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["-is_favorite"]),
        ]
        verbose_name = "Saved Filter"
        verbose_name_plural = "Saved Filters"

    def __str__(self):
        return f"{self.user.email} - {self.name}"


class CustomView(OrganizationOwnedModel):
    """
    Custom task views with different visualization types.
    Allows users to create personalized task views.
    """

    class ViewType(models.TextChoices):
        LIST = "list", "List View"
        BOARD = "board", "Board View"
        TIMELINE = "timeline", "Timeline View"
        CALENDAR = "calendar", "Calendar View"
        GANTT = "gantt", "Gantt View"
        TABLE = "table", "Table View"

    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="custom_views",
        help_text="View owner",
    )
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_views",
        help_text="Optional project view scope",
    )

    # View Information
    name = models.CharField(
        max_length=255,
        help_text="View name",
    )
    description = models.TextField(
        blank=True,
        help_text="View description",
    )
    view_type = models.CharField(
        max_length=20,
        choices=ViewType.choices,
        default=ViewType.LIST,
        help_text="Type of view",
    )
    view_config = models.JSONField(
        default=dict,
        help_text="View configuration (columns, filters, grouping, etc.)",
    )

    # Settings
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default view",
    )
    is_shared = models.BooleanField(
        default=False,
        help_text="Whether view is shared with team",
    )

    class Meta:
        db_table = "custom_views"
        ordering = ["-is_default", "name"]
        indexes = [
            models.Index(fields=["organization", "user"]),
            models.Index(fields=["view_type"]),
            models.Index(fields=["-is_default"]),
        ]
        verbose_name = "Custom View"
        verbose_name_plural = "Custom Views"

    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.view_type})"


# ============================================================================
# AUTOMATION MODELS
# ============================================================================


class Automation(BaseModel):
    """
    Workflow automation rules for automatic task actions.
    Executes actions based on triggers and conditions.
    """

    class TriggerType(models.TextChoices):
        TASK_CREATED = "task_created", "Task Created"
        TASK_UPDATED = "task_updated", "Task Updated"
        STATUS_CHANGED = "status_changed", "Status Changed"
        ASSIGNEE_CHANGED = "assignee_changed", "Assignee Changed"
        DUE_DATE_CHANGED = "due_date_changed", "Due Date Changed"
        PRIORITY_CHANGED = "priority_changed", "Priority Changed"
        COMMENT_ADDED = "comment_added", "Comment Added"
        ATTACHMENT_ADDED = "attachment_added", "Attachment Added"
        TIME_LOGGED = "time_logged", "Time Logged"
        SCHEDULED = "scheduled", "Scheduled Trigger"

    class ActionType(models.TextChoices):
        ASSIGN_TASK = "assign_task", "Assign Task"
        CHANGE_STATUS = "change_status", "Change Status"
        CHANGE_PRIORITY = "change_priority", "Change Priority"
        ADD_LABEL = "add_label", "Add Label"
        SEND_NOTIFICATION = "send_notification", "Send Notification"
        SEND_EMAIL = "send_email", "Send Email"
        ADD_COMMENT = "add_comment", "Add Comment"
        CREATE_SUBTASK = "create_subtask", "Create Subtask"
        TRIGGER_WEBHOOK = "trigger_webhook", "Trigger Webhook"

    # Relations
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        related_name="automations",
        help_text="Related project",
    )

    # Automation Information
    name = models.CharField(
        max_length=255,
        help_text="Automation rule name",
    )
    description = models.TextField(
        blank=True,
        help_text="Automation description",
    )

    # Trigger
    trigger_type = models.CharField(
        max_length=30,
        choices=TriggerType.choices,
        help_text="What triggers this automation",
    )
    trigger_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Trigger-specific configuration",
    )

    # Conditions
    conditions = models.JSONField(
        default=list,
        blank=True,
        help_text="Conditions that must be met (if-then logic)",
    )

    # Actions
    actions = models.JSONField(
        default=list,
        blank=True,
        help_text="Actions to perform when triggered",
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether automation is active",
    )
    priority = models.IntegerField(
        default=0,
        help_text="Execution priority (higher = earlier)",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_automations",
        help_text="User who created the automation",
    )

    # Statistics
    execution_count = models.IntegerField(
        default=0,
        help_text="Number of times automation has executed",
    )
    last_executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last execution timestamp",
    )

    class Meta:
        db_table = "automations"
        ordering = ["-priority", "name"]
        indexes = [
            models.Index(fields=["project", "is_active"]),
            models.Index(fields=["trigger_type"]),
            models.Index(fields=["-priority"]),
        ]
        verbose_name = "Automation"
        verbose_name_plural = "Automations"

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class AutomationLog(BaseModel):
    """
    Execution logs for automation rules.
    Tracks automation execution history and results.
    """

    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partially Successful"

    # Relations
    automation = models.ForeignKey(
        Automation,
        on_delete=models.CASCADE,
        related_name="execution_logs",
        help_text="Related automation",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automation_logs",
        help_text="Related task (if applicable)",
    )

    # Execution Details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        help_text="Execution status",
    )
    execution_time = models.IntegerField(
        help_text="Execution time in milliseconds",
    )
    trigger_data = models.JSONField(
        default=dict,
        help_text="Data that triggered the automation",
    )
    actions_performed = models.JSONField(
        default=list,
        help_text="List of actions that were performed",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed",
    )

    class Meta:
        db_table = "automation_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["automation", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["task"]),
        ]
        verbose_name = "Automation Log"
        verbose_name_plural = "Automation Logs"

    def __str__(self):
        return f"{self.automation.name} - {self.status} - {self.created_at}"


class Webhook(OrganizationOwnedModel):
    """
    Webhook configurations for external integrations.
    Sends HTTP requests to external endpoints on events.
    """

    class EventType(models.TextChoices):
        TASK_CREATED = "task.created", "Task Created"
        TASK_UPDATED = "task.updated", "Task Updated"
        TASK_DELETED = "task.deleted", "Task Deleted"
        COMMENT_ADDED = "comment.added", "Comment Added"
        PROJECT_CREATED = "project.created", "Project Created"
        PROJECT_UPDATED = "project.updated", "Project Updated"
        SPRINT_STARTED = "sprint.started", "Sprint Started"
        SPRINT_COMPLETED = "sprint.completed", "Sprint Completed"

    # Relations
    project = models.ForeignKey(
        "tasks.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="webhooks",
        help_text="Optional project scope (null = organization-wide)",
    )

    # Webhook Information
    name = models.CharField(
        max_length=255,
        help_text="Webhook name",
    )
    url = models.URLField(
        max_length=500,
        help_text="Webhook endpoint URL",
    )
    secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Secret token for request signing",
    )
    description = models.TextField(
        blank=True,
        help_text="Webhook description",
    )

    # Events
    events = models.JSONField(
        default=list,
        help_text="Subscribed event types",
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether webhook is active",
    )
    retry_on_failure = models.BooleanField(
        default=True,
        help_text="Whether to retry failed deliveries",
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts",
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_webhooks",
        help_text="User who created the webhook",
    )

    # Statistics
    delivery_count = models.IntegerField(
        default=0,
        help_text="Total number of deliveries attempted",
    )
    failure_count = models.IntegerField(
        default=0,
        help_text="Number of failed deliveries",
    )
    last_triggered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last trigger timestamp",
    )

    class Meta:
        db_table = "webhooks"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["project"]),
        ]
        verbose_name = "Webhook"
        verbose_name_plural = "Webhooks"

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def increment_delivery(self):
        """Increment delivery counter"""
        self.delivery_count = models.F("delivery_count") + 1
        self.save(update_fields=["delivery_count"])

    def increment_failure(self):
        """Increment failure counter"""
        self.failure_count = models.F("failure_count") + 1
        self.save(update_fields=["failure_count"])


class WebhookDelivery(BaseModel):
    """
    Webhook delivery tracking and retry management.
    Records webhook delivery attempts and responses.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"

    # Relations
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name="deliveries",
        help_text="Related webhook",
    )

    # Delivery Details
    event_type = models.CharField(
        max_length=50,
        help_text="Event that triggered the webhook",
    )
    payload = models.JSONField(
        help_text="Request payload",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Delivery status",
    )

    # Response
    response_status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP response status code",
    )
    response_body = models.TextField(
        blank=True,
        help_text="HTTP response body",
    )
    response_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="HTTP response headers",
    )

    # Timing
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When delivery was attempted",
    )
    response_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Response time in milliseconds",
    )

    # Retry
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts",
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next retry scheduled time",
    )

    # Error
    error_message = models.TextField(
        blank=True,
        help_text="Error message if delivery failed",
    )

    class Meta:
        db_table = "webhook_deliveries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["webhook", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["next_retry_at"]),
        ]
        verbose_name = "Webhook Delivery"
        verbose_name_plural = "Webhook Deliveries"

    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} - {self.status}"


class ApiKey(OrganizationOwnedModel):
    """
    API key management for external API access.
    Provides secure token-based API authentication.
    """

    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="API key owner",
    )

    # Key Information
    name = models.CharField(
        max_length=255,
        help_text="API key name/description",
    )
    key_hash = models.CharField(
        max_length=255,
        unique=True,
        help_text="Hashed API key",
    )
    key_prefix = models.CharField(
        max_length=10,
        help_text="Key prefix for identification",
    )

    # Permissions
    permissions = models.JSONField(
        default=list,
        help_text="API permission scopes",
    )
    is_readonly = models.BooleanField(
        default=False,
        help_text="Whether key has read-only access",
    )

    # Security
    allowed_ips = models.JSONField(
        default=list,
        blank=True,
        help_text="Allowed IP addresses (empty = all)",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Key expiration date",
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether key is active",
    )

    # Statistics
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last usage timestamp",
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times key has been used",
    )

    class Meta:
        db_table = "api_keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "user"]),
            models.Index(fields=["key_prefix"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["expires_at"]),
        ]
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        return f"{self.organization.name} - {self.name} ({self.key_prefix})"

    def is_expired(self):
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        from django.utils import timezone

        return timezone.now() > self.expires_at
