"""
Team, Project, and Task Serializers
API serialization for Team, TeamMember, Project, ProjectMember, Task, TaskComment, and TaskAttachment models.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.tasks.models import (
    Team,
    TeamMember,
    Project,
    ProjectMember,
    Task,
    TaskComment,
    TaskAttachment,
    TaskActivity,
)

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    """Full team serializer"""

    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    lead_email = serializers.EmailField(
        source="lead.email", read_only=True, allow_null=True
    )
    lead_name = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "description",
            "color",
            "icon",
            "visibility",
            "lead",
            "lead_email",
            "lead_name",
            "member_count",
            "project_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "member_count",
            "project_count",
            "created_at",
            "updated_at",
        ]

    def get_lead_name(self, obj):
        """Get lead full name"""
        if not obj.lead:
            return None
        if obj.lead.first_name or obj.lead.last_name:
            return f"{obj.lead.first_name} {obj.lead.last_name}".strip()
        return obj.lead.email


class TeamListSerializer(serializers.ModelSerializer):
    """Lightweight team list serializer"""

    lead_name = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "color",
            "icon",
            "visibility",
            "lead_name",
            "member_count",
            "project_count",
        ]

    def get_lead_name(self, obj):
        """Get lead name"""
        if not obj.lead:
            return None
        if obj.lead.first_name or obj.lead.last_name:
            return f"{obj.lead.first_name} {obj.lead.last_name}".strip()
        return obj.lead.email


class TeamCreateSerializer(serializers.ModelSerializer):
    """Team creation serializer"""

    class Meta:
        model = Team
        fields = [
            "name",
            "description",
            "color",
            "icon",
            "visibility",
            "lead",
        ]


class TeamUpdateSerializer(serializers.ModelSerializer):
    """Team update serializer"""

    class Meta:
        model = Team
        fields = [
            "name",
            "description",
            "color",
            "icon",
            "visibility",
            "lead",
        ]


class TeamStatisticsSerializer(serializers.Serializer):
    """Team statistics serializer"""

    id = serializers.UUIDField()
    name = serializers.CharField()
    organization = serializers.CharField()
    member_count = serializers.IntegerField()
    project_count = serializers.IntegerField()
    visibility = serializers.CharField()
    lead = serializers.DictField()
    created_at = serializers.DateTimeField()


class OrganizationTeamStatisticsSerializer(serializers.Serializer):
    """Organization team statistics serializer"""

    total_teams = serializers.IntegerField()
    public_teams = serializers.IntegerField()
    private_teams = serializers.IntegerField()
    secret_teams = serializers.IntegerField()
    total_members = serializers.IntegerField()
    teams_with_lead = serializers.IntegerField()


# ============================================================================
# Team Member Serializers
# ============================================================================


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for member serializer"""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "avatar"]

    def get_full_name(self, obj):
        """Get full name"""
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.email


class TeamMemberSerializer(serializers.ModelSerializer):
    """Full team member serializer"""

    user = UserMinimalSerializer(read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True)
    added_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "team",
            "team_name",
            "user",
            "role",
            "added_by",
            "added_by_name",
            "joined_at",
            "last_active_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "team",
            "user",
            "added_by",
            "joined_at",
            "created_at",
            "updated_at",
        ]

    def get_added_by_name(self, obj):
        """Get adder name"""
        if not obj.added_by:
            return None
        if obj.added_by.first_name or obj.added_by.last_name:
            return f"{obj.added_by.first_name} {obj.added_by.last_name}".strip()
        return obj.added_by.email


class TeamMemberListSerializer(serializers.ModelSerializer):
    """Lightweight member list serializer"""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "user",
            "role",
            "joined_at",
            "last_active_at",
        ]


class TeamMemberAddSerializer(serializers.Serializer):
    """Add member serializer"""

    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=TeamMember.Role.choices, default=TeamMember.Role.MEMBER
    )

    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class TeamMemberUpdateSerializer(serializers.ModelSerializer):
    """Member update serializer"""

    class Meta:
        model = TeamMember
        fields = ["role"]


class TeamMemberStatisticsSerializer(serializers.Serializer):
    """Member statistics serializer"""

    total = serializers.IntegerField()
    by_role = serializers.DictField()


class TransferLeadSerializer(serializers.Serializer):
    """Transfer lead serializer"""

    new_lead_id = serializers.UUIDField()

    def validate_new_lead_id(self, value):
        """Validate new lead exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class ChangeVisibilitySerializer(serializers.Serializer):
    """Change visibility serializer"""

    visibility = serializers.ChoiceField(choices=Team.Visibility.choices)


# ============================================================================
# Project Serializers
# ============================================================================


class ProjectListSerializer(serializers.ModelSerializer):
    """List view serializer for projects"""

    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    owner_name = serializers.SerializerMethodField()
    team_name = serializers.CharField(
        source="team.name", read_only=True, allow_null=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "key",
            "description",
            "color",
            "icon",
            "status",
            "status_display",
            "priority",
            "visibility",
            "owner",
            "owner_name",
            "team",
            "team_name",
            "member_count",
            "task_count",
            "progress",
            "start_date",
            "due_date",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "member_count",
            "task_count",
            "progress",
            "created_at",
        ]

    def get_owner_name(self, obj):
        """Get owner's full name"""
        if obj.owner:
            return (
                f"{obj.owner.first_name} {obj.owner.last_name}".strip()
                or obj.owner.email
            )
        return None


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer"""

    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    owner_email = serializers.EmailField(
        source="owner.email", read_only=True, allow_null=True
    )
    owner_name = serializers.SerializerMethodField()
    team_name = serializers.CharField(
        source="team.name", read_only=True, allow_null=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "key",
            "description",
            "color",
            "icon",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "visibility",
            "owner",
            "owner_email",
            "owner_name",
            "team",
            "team_name",
            "member_count",
            "task_count",
            "open_task_count",
            "completed_task_count",
            "progress",
            "start_date",
            "due_date",
            "completed_at",
            "is_template",
            "settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "member_count",
            "task_count",
            "open_task_count",
            "completed_task_count",
            "progress",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def get_owner_name(self, obj):
        """Get owner's full name"""
        if obj.owner:
            return (
                f"{obj.owner.first_name} {obj.owner.last_name}".strip()
                or obj.owner.email
            )
        return None


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Project creation serializer"""

    class Meta:
        model = Project
        fields = [
            "name",
            "key",
            "description",
            "color",
            "icon",
            "status",
            "priority",
            "visibility",
            "team",
            "start_date",
            "due_date",
            "settings",
        ]

    def validate_key(self, value):
        """Validate project key format"""
        if not value.isupper() or not value.isalnum():
            raise serializers.ValidationError(
                "Project key must be uppercase alphanumeric"
            )
        if len(value) > 10:
            raise serializers.ValidationError(
                "Project key must be 10 characters or less"
            )
        return value


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Project update serializer"""

    class Meta:
        model = Project
        fields = [
            "name",
            "key",
            "description",
            "color",
            "icon",
            "status",
            "priority",
            "visibility",
            "team",
            "start_date",
            "due_date",
            "settings",
        ]

    def validate_key(self, value):
        """Validate project key format"""
        if not value.isupper() or not value.isalnum():
            raise serializers.ValidationError(
                "Project key must be uppercase alphanumeric"
            )
        if len(value) > 10:
            raise serializers.ValidationError(
                "Project key must be 10 characters or less"
            )
        return value


class ProjectStatisticsSerializer(serializers.Serializer):
    """Project statistics serializer"""

    member_count = serializers.IntegerField()
    task_count = serializers.IntegerField()
    open_task_count = serializers.IntegerField()
    completed_task_count = serializers.IntegerField()
    progress = serializers.FloatField()


class ProjectDuplicateSerializer(serializers.Serializer):
    """Project duplication serializer"""

    name = serializers.CharField(max_length=255)
    key = serializers.CharField(max_length=10)

    def validate_key(self, value):
        """Validate project key format"""
        if not value.isupper() or not value.isalnum():
            raise serializers.ValidationError(
                "Project key must be uppercase alphanumeric"
            )
        return value


# ============================================================================
# Project Member Serializers
# ============================================================================


class ProjectMemberListSerializer(serializers.ModelSerializer):
    """List view serializer for project members"""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "project",
            "user",
            "user_email",
            "user_name",
            "role",
            "role_display",
            "joined_at",
            "last_active_at",
        ]
        read_only_fields = [
            "id",
            "project",
            "joined_at",
            "last_active_at",
        ]

    def get_user_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Full project member serializer"""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    added_by_email = serializers.EmailField(
        source="added_by.email", read_only=True, allow_null=True
    )
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "project",
            "user",
            "user_email",
            "user_name",
            "role",
            "role_display",
            "added_by",
            "added_by_email",
            "joined_at",
            "last_active_at",
            "custom_permissions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "project",
            "joined_at",
            "last_active_at",
            "created_at",
            "updated_at",
        ]

    def get_user_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class ProjectMemberAddSerializer(serializers.Serializer):
    """Add member serializer"""

    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=ProjectMember.Role.choices, default=ProjectMember.Role.MEMBER
    )

    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class ProjectMemberBulkAddSerializer(serializers.Serializer):
    """Bulk add members serializer"""

    user_ids = serializers.ListField(child=serializers.UUIDField())
    role = serializers.ChoiceField(
        choices=ProjectMember.Role.choices, default=ProjectMember.Role.MEMBER
    )


class ProjectMemberUpdateSerializer(serializers.ModelSerializer):
    """Member update serializer"""

    class Meta:
        model = ProjectMember
        fields = ["role", "custom_permissions"]


class ProjectMemberStatisticsSerializer(serializers.Serializer):
    """Member statistics serializer"""

    total = serializers.IntegerField()
    owners = serializers.IntegerField()
    admins = serializers.IntegerField()
    members = serializers.IntegerField()
    viewers = serializers.IntegerField()


class TransferOwnershipSerializer(serializers.Serializer):
    """Transfer ownership serializer"""

    new_owner_id = serializers.UUIDField()

    def validate_new_owner_id(self, value):
        """Validate new owner exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class ChangeProjectVisibilitySerializer(serializers.Serializer):
    """Change project visibility serializer"""

    visibility = serializers.ChoiceField(choices=Project.Visibility.choices)


class ChangeProjectStatusSerializer(serializers.Serializer):
    """Change project status serializer"""

    status = serializers.ChoiceField(choices=Project.Status.choices)


class AssignTeamSerializer(serializers.Serializer):
    """Assign team serializer"""

    team_id = serializers.UUIDField(allow_null=True, required=False)

    def validate_team_id(self, value):
        """Validate team exists"""
        if value:
            from apps.tasks.models import Team

            try:
                Team.objects.get(id=value)
            except Team.DoesNotExist:
                raise serializers.ValidationError("Team not found")
        return value


# ============================================================================
# TASK SERIALIZERS
# ============================================================================


class TaskCommentSerializer(serializers.ModelSerializer):
    """Task comment serializer"""

    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    author_email = serializers.EmailField(source="author.email", read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = [
            "id",
            "task",
            "author",
            "author_name",
            "author_email",
            "content",
            "parent_comment",
            "is_edited",
            "edited_at",
            "replies_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "is_edited",
            "edited_at",
            "created_at",
            "updated_at",
        ]

    def get_replies_count(self, obj):
        """Get number of replies"""
        return obj.replies.count()


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """Task attachment serializer"""

    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TaskAttachment
        fields = [
            "id",
            "task",
            "file",
            "file_url",
            "filename",
            "file_size",
            "mime_type",
            "description",
            "uploaded_by",
            "uploaded_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "filename",
            "file_size",
            "mime_type",
            "uploaded_by",
            "created_at",
        ]

    def get_file_url(self, obj):
        """Get file URL"""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class TaskActivitySerializer(serializers.ModelSerializer):
    """Task activity serializer"""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    activity_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )

    class Meta:
        model = TaskActivity
        fields = [
            "id",
            "task",
            "user",
            "user_name",
            "activity_type",
            "activity_display",
            "description",
            "old_value",
            "new_value",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TaskListSerializer(serializers.ModelSerializer):
    """Task list serializer (lightweight)"""

    project_key = serializers.CharField(source="project.key", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_name = serializers.CharField(
        source="assignee.get_full_name", read_only=True
    )
    reporter_name = serializers.CharField(
        source="reporter.get_full_name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "task_key",
            "task_number",
            "project",
            "project_key",
            "project_name",
            "title",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "task_type",
            "type_display",
            "assignee",
            "assignee_name",
            "reporter",
            "reporter_name",
            "due_date",
            "is_overdue",
            "is_blocked",
            "labels",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "task_key", "task_number", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    """Full task serializer"""

    project_key = serializers.CharField(source="project.key", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_name = serializers.CharField(
        source="assignee.get_full_name", read_only=True
    )
    reporter_name = serializers.CharField(
        source="reporter.get_full_name", read_only=True
    )
    parent_task_key = serializers.CharField(
        source="parent_task.task_key", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)

    # Nested serializers
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "task_key",
            "task_number",
            "project",
            "project_key",
            "project_name",
            "title",
            "description",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "task_type",
            "type_display",
            "assignee",
            "assignee_name",
            "reporter",
            "reporter_name",
            "parent_task",
            "parent_task_key",
            "due_date",
            "start_date",
            "is_overdue",
            "is_blocked",
            "estimated_hours",
            "actual_hours",
            "labels",
            "custom_fields",
            "comment_count",
            "attachment_count",
            "comments",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "task_key",
            "task_number",
            "reporter",
            "comment_count",
            "attachment_count",
            "created_at",
            "updated_at",
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    """Task creation serializer"""

    class Meta:
        model = Task
        fields = [
            "project",
            "title",
            "description",
            "status",
            "priority",
            "task_type",
            "assignee",
            "parent_task",
            "due_date",
            "start_date",
            "estimated_hours",
            "labels",
            "custom_fields",
        ]

    def validate_parent_task(self, value):
        """Validate parent task belongs to same project"""
        if value:
            project = self.initial_data.get("project")
            if project and str(value.project_id) != str(project):
                raise serializers.ValidationError(
                    "Parent task must belong to the same project"
                )
        return value

    def validate_assignee(self, value):
        """Validate assignee is member of project"""
        if value:
            project = self.initial_data.get("project")
            if project:
                if not ProjectMember.objects.filter(
                    project_id=project, user=value
                ).exists():
                    raise serializers.ValidationError(
                        "Assignee must be a member of the project"
                    )
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Task update serializer"""

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "status",
            "priority",
            "task_type",
            "assignee",
            "parent_task",
            "due_date",
            "start_date",
            "estimated_hours",
            "actual_hours",
            "labels",
            "custom_fields",
        ]

    def validate_parent_task(self, value):
        """Validate parent task belongs to same project"""
        if value:
            task = self.instance
            if task and value.project_id != task.project_id:
                raise serializers.ValidationError(
                    "Parent task must belong to the same project"
                )
            # Prevent circular dependency
            if task and value.id == task.id:
                raise serializers.ValidationError("Task cannot be its own parent")
        return value

    def validate_assignee(self, value):
        """Validate assignee is member of project"""
        if value:
            task = self.instance
            if (
                task
                and not ProjectMember.objects.filter(
                    project=task.project, user=value
                ).exists()
            ):
                raise serializers.ValidationError(
                    "Assignee must be a member of the project"
                )
        return value


class TaskCommentCreateSerializer(serializers.ModelSerializer):
    """Task comment creation serializer"""

    class Meta:
        model = TaskComment
        fields = ["task", "content", "parent_comment"]

    def validate_parent_comment(self, value):
        """Validate parent comment belongs to same task"""
        if value:
            task = self.initial_data.get("task")
            if task and str(value.task_id) != str(task):
                raise serializers.ValidationError(
                    "Parent comment must belong to the same task"
                )
        return value


class TaskAttachmentCreateSerializer(serializers.ModelSerializer):
    """Task attachment creation serializer"""

    class Meta:
        model = TaskAttachment
        fields = ["task", "file"]


# Action serializers
class ChangeStatusSerializer(serializers.Serializer):
    """Change task status serializer"""

    status = serializers.ChoiceField(choices=Task.Status.choices)


class AssignTaskSerializer(serializers.Serializer):
    """Assign task serializer"""

    assignee_id = serializers.UUIDField(allow_null=True, required=False)

    def validate_assignee_id(self, value):
        """Validate assignee exists and is project member"""
        if value:
            try:
                user = User.objects.get(id=value)
                # Project validation will be done in view
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError("User not found")
        return value


class AddLabelSerializer(serializers.Serializer):
    """Add label serializer"""

    label = serializers.CharField(max_length=50)


class RemoveLabelSerializer(serializers.Serializer):
    """Remove label serializer"""

    label = serializers.CharField(max_length=50)


class AddBlockedBySerializer(serializers.Serializer):
    """Add blocked by relationship serializer"""

    blocked_by_id = serializers.UUIDField()

    def validate_blocked_by_id(self, value):
        """Validate blocking task exists"""
        try:
            Task.objects.get(id=value)
            return value
        except Task.DoesNotExist:
            raise serializers.ValidationError("Blocking task not found")


class RemoveBlockedBySerializer(serializers.Serializer):
    """Remove blocked by relationship serializer"""

    blocked_by_id = serializers.UUIDField()


class BulkUpdateSerializer(serializers.Serializer):
    """Bulk update tasks serializer"""

    task_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    status = serializers.ChoiceField(choices=Task.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=Task.Priority.choices, required=False)
    assignee_id = serializers.UUIDField(allow_null=True, required=False)

    def validate(self, data):
        """Validate at least one field to update"""
        if not any([data.get("status"), data.get("priority"), "assignee_id" in data]):
            raise serializers.ValidationError(
                "At least one field (status, priority, or assignee_id) must be provided"
            )
        return data
