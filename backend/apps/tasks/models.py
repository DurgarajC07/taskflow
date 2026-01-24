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
