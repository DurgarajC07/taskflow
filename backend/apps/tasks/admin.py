"""
Team, Project, Task, and Workflow Admin Configuration
Django admin interface for Team, Project, Task, and Workflow models.
"""

from django.contrib import admin
from apps.tasks.models import (
    Team,
    TeamMember,
    Project,
    ProjectMember,
    Task,
    TaskComment,
    TaskAttachment,
    TaskActivity,
    Workflow,
    WorkflowState,
    WorkflowTransition,
    WorkflowRule,
)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin interface for Team model"""

    list_display = [
        "name",
        "organization",
        "visibility",
        "lead",
        "member_count",
        "project_count",
        "created_at",
    ]
    list_filter = ["visibility", "created_at", "organization"]
    search_fields = ["name", "description", "organization__name"]
    readonly_fields = [
        "id",
        "member_count",
        "project_count",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "organization", "name", "description")},
        ),
        ("Appearance", {"fields": ("color", "icon")}),
        ("Settings", {"fields": ("visibility", "lead")}),
        ("Statistics", {"fields": ("member_count", "project_count")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted teams"""
        return Team.all_objects.all()


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin interface for TeamMember model"""

    list_display = [
        "user",
        "team",
        "role",
        "joined_at",
        "last_active_at",
    ]
    list_filter = ["role", "joined_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "team__name",
    ]
    readonly_fields = [
        "id",
        "joined_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("id", "team", "user")}),
        ("Role", {"fields": ("role", "added_by")}),
        ("Activity", {"fields": ("joined_at", "last_active_at")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request).select_related("user", "team", "added_by")


# ============================================================================
# Project Admin
# ============================================================================


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model"""

    list_display = [
        "key",
        "name",
        "organization",
        "status",
        "priority",
        "visibility",
        "owner",
        "team",
        "progress",
        "due_date",
        "created_at",
    ]
    list_filter = [
        "status",
        "priority",
        "visibility",
        "is_template",
        "created_at",
        "organization",
    ]
    search_fields = ["name", "key", "description", "organization__name"]
    readonly_fields = [
        "id",
        "member_count",
        "task_count",
        "open_task_count",
        "completed_task_count",
        "progress",
        "completed_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "organization", "name", "key", "description")},
        ),
        ("Appearance", {"fields": ("color", "icon")}),
        (
            "Settings",
            {"fields": ("status", "priority", "visibility", "is_template")},
        ),
        ("Ownership", {"fields": ("owner", "team")}),
        (
            "Dates",
            {"fields": ("start_date", "due_date", "completed_at")},
        ),
        (
            "Statistics",
            {
                "fields": (
                    "member_count",
                    "task_count",
                    "open_task_count",
                    "completed_task_count",
                    "progress",
                )
            },
        ),
        ("Settings Data", {"fields": ("settings",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted projects"""
        return Project.all_objects.all()


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    """Admin interface for ProjectMember model"""

    list_display = [
        "user",
        "project",
        "role",
        "joined_at",
        "last_active_at",
    ]
    list_filter = ["role", "joined_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "project__name",
        "project__key",
    ]
    readonly_fields = [
        "id",
        "joined_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("id", "project", "user")}),
        ("Role", {"fields": ("role", "added_by")}),
        ("Activity", {"fields": ("joined_at", "last_active_at")}),
        (
            "Permissions",
            {"fields": ("custom_permissions",), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return (
            super().get_queryset(request).select_related("user", "project", "added_by")
        )


# ============================================================================
# TASK ADMIN
# ============================================================================


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model"""

    list_display = [
        "task_key",
        "title",
        "project",
        "status",
        "priority",
        "task_type",
        "assignee",
        "reporter",
        "due_date",
        "created_at",
    ]
    list_filter = [
        "status",
        "priority",
        "task_type",
        "created_at",
        "due_date",
        "project__organization",
    ]
    search_fields = [
        "title",
        "description",
        "task_key",
        "task_number",
        "project__name",
    ]
    readonly_fields = [
        "id",
        "task_key",
        "task_number",
        "reporter",
        "comment_count",
        "attachment_count",
        "created_at",
        "updated_at",
    ]
    filter_horizontal = ["blocked_by"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "task_key",
                    "task_number",
                    "project",
                    "title",
                    "description",
                )
            },
        ),
        (
            "Classification",
            {"fields": ("status", "priority", "task_type", "labels")},
        ),
        (
            "Assignment",
            {"fields": ("assignee", "reporter", "parent_task")},
        ),
        (
            "Timeline",
            {"fields": ("due_date", "start_date", "estimated_hours", "actual_hours")},
        ),
        ("Progress", {"fields": ("progress",)}),
        ("Relationships", {"fields": ("blocked_by",)}),
        (
            "Custom Data",
            {"fields": ("custom_fields",), "classes": ("collapse",)},
        ),
        (
            "Statistics",
            {"fields": ("comment_count", "attachment_count")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted tasks"""
        return Task.all_objects.select_related(
            "project",
            "assignee",
            "reporter",
            "parent_task",
        ).prefetch_related("blocked_by")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin interface for TaskComment model"""

    list_display = [
        "task",
        "author",
        "content_preview",
        "parent_comment",
        "is_edited",
        "created_at",
    ]
    list_filter = ["is_edited", "created_at", "task__project__organization"]
    search_fields = ["content", "task__title", "author__email"]
    readonly_fields = [
        "id",
        "is_edited",
        "edited_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Comment Information", {"fields": ("id", "task", "author")}),
        ("Content", {"fields": ("content",)}),
        ("Threading", {"fields": ("parent_comment",)}),
        ("Edit History", {"fields": ("is_edited", "edited_at")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def content_preview(self, obj):
        """Show preview of content"""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"

    def get_queryset(self, request):
        """Optimize query"""
        return (
            super()
            .get_queryset(request)
            .select_related("task", "author", "parent_comment")
        )


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    """Admin interface for TaskAttachment model"""

    list_display = [
        "filename",
        "task",
        "uploaded_by",
        "file_size_display",
        "mime_type",
        "created_at",
    ]
    list_filter = ["mime_type", "created_at", "task__project__organization"]
    search_fields = ["filename", "task__title", "uploaded_by__email"]
    readonly_fields = [
        "id",
        "filename",
        "file_size",
        "mime_type",
        "uploaded_by",
        "created_at",
    ]

    fieldsets = (
        ("Attachment Information", {"fields": ("id", "task", "file")}),
        (
            "File Details",
            {"fields": ("filename", "file_size", "mime_type", "description")},
        ),
        ("Upload Info", {"fields": ("uploaded_by", "created_at")}),
    )

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    file_size_display.short_description = "File Size"

    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request).select_related("task", "uploaded_by")


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    """Admin interface for TaskActivity model"""

    list_display = [
        "task",
        "user",
        "activity_type",
        "created_at",
    ]
    list_filter = ["activity_type", "created_at", "task__project__organization"]
    search_fields = [
        "task__title",
        "user__email",
        "description",
    ]
    readonly_fields = [
        "id",
        "task",
        "user",
        "activity_type",
        "description",
        "old_value",
        "new_value",
        "created_at",
    ]

    fieldsets = (
        ("Activity Information", {"fields": ("id", "task", "user")}),
        (
            "Activity Details",
            {
                "fields": (
                    "activity_type",
                    "description",
                    "old_value",
                    "new_value",
                )
            },
        ),
        ("Timestamp", {"fields": ("created_at",)}),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request).select_related("task", "user")

    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False


# ============================================================================
# Workflow Admin
# ============================================================================


class WorkflowStateInline(admin.TabularInline):
    """Inline admin for workflow states"""

    model = WorkflowState
    extra = 0
    fields = ["name", "category", "color", "is_initial", "is_final", "display_order"]
    ordering = ["display_order", "name"]


class WorkflowTransitionInline(admin.TabularInline):
    """Inline admin for workflow transitions"""

    model = WorkflowTransition
    extra = 0
    fields = ["name", "from_state", "to_state", "requires_comment", "display_order"]
    fk_name = "workflow"
    ordering = ["display_order"]


class WorkflowRuleInline(admin.TabularInline):
    """Inline admin for workflow rules"""

    model = WorkflowRule
    extra = 0
    fields = ["name", "trigger_type", "is_active", "priority"]
    ordering = ["-priority", "name"]


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """Admin interface for Workflow model"""

    list_display = [
        "name",
        "organization",
        "project",
        "is_default",
        "is_system",
        "is_active",
        "created_by",
        "state_count",
        "transition_count",
        "rule_count",
        "created_at",
    ]
    list_filter = [
        "is_default",
        "is_system",
        "is_active",
        "created_at",
        "organization",
    ]
    search_fields = ["name", "description", "organization__name", "project__name"]
    readonly_fields = [
        "id",
        "state_count",
        "transition_count",
        "rule_count",
        "created_at",
        "updated_at",
    ]
    inlines = [WorkflowStateInline, WorkflowTransitionInline, WorkflowRuleInline]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "organization", "name", "description")},
        ),
        ("Scope", {"fields": ("project",)}),
        (
            "Settings",
            {
                "fields": (
                    "is_default",
                    "is_system",
                    "is_active",
                )
            },
        ),
        ("Metadata", {"fields": ("created_by",)}),
        (
            "Statistics",
            {"fields": ("state_count", "transition_count", "rule_count")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def state_count(self, obj):
        """Get number of states"""
        return obj.states.count()

    state_count.short_description = "States"

    def transition_count(self, obj):
        """Get number of transitions"""
        return obj.transitions.count()

    transition_count.short_description = "Transitions"

    def rule_count(self, obj):
        """Get number of rules"""
        return obj.rules.count()

    rule_count.short_description = "Rules"

    def get_queryset(self, request):
        """Include soft-deleted workflows"""
        return Workflow.all_objects.all().select_related(
            "organization", "project", "created_by"
        )


@admin.register(WorkflowState)
class WorkflowStateAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowState model"""

    list_display = [
        "name",
        "workflow",
        "category",
        "color",
        "is_initial",
        "is_final",
        "display_order",
        "created_at",
    ]
    list_filter = ["category", "is_initial", "is_final", "created_at"]
    search_fields = ["name", "description", "workflow__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "workflow", "name", "description")},
        ),
        ("Classification", {"fields": ("category",)}),
        ("Appearance", {"fields": ("color",)}),
        (
            "Settings",
            {
                "fields": (
                    "is_initial",
                    "is_final",
                    "display_order",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request).select_related("workflow")


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowTransition model"""

    list_display = [
        "name",
        "workflow",
        "from_state",
        "to_state",
        "requires_comment",
        "display_order",
        "created_at",
    ]
    list_filter = ["requires_comment", "created_at"]
    search_fields = [
        "name",
        "description",
        "workflow__name",
        "from_state__name",
        "to_state__name",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "workflow", "name", "description")},
        ),
        (
            "State Relationships",
            {
                "fields": (
                    "from_state",
                    "to_state",
                )
            },
        ),
        ("Conditions", {"fields": ("conditions",)}),
        ("Actions", {"fields": ("actions",)}),
        (
            "Settings",
            {
                "fields": (
                    "requires_comment",
                    "display_order",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return (
            super()
            .get_queryset(request)
            .select_related("workflow", "from_state", "to_state")
        )


@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowRule model"""

    list_display = [
        "name",
        "workflow",
        "trigger_type",
        "is_active",
        "priority",
        "execution_count",
        "last_executed_at",
        "created_by",
        "created_at",
    ]
    list_filter = ["trigger_type", "is_active", "created_at"]
    search_fields = ["name", "description", "workflow__name"]
    readonly_fields = [
        "id",
        "execution_count",
        "last_executed_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "workflow", "name", "description")},
        ),
        (
            "Trigger",
            {
                "fields": (
                    "trigger_type",
                    "trigger_config",
                )
            },
        ),
        ("Conditions", {"fields": ("conditions",)}),
        ("Actions", {"fields": ("actions",)}),
        (
            "Settings",
            {
                "fields": (
                    "is_active",
                    "priority",
                )
            },
        ),
        ("Metadata", {"fields": ("created_by",)}),
        (
            "Statistics",
            {
                "fields": (
                    "execution_count",
                    "last_executed_at",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request).select_related("workflow", "created_by")
