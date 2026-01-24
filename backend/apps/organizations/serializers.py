"""
Organization Serializers
API serialization for Organization and OrganizationMember models.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, OrganizationMember

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Full organization serializer"""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner_name = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(source="current_members", read_only=True)
    usage_stats = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "primary_color",
            "status",
            "plan",
            "owner",
            "owner_email",
            "owner_name",
            "settings",
            "max_members",
            "max_projects",
            "max_storage_gb",
            "current_members",
            "current_projects",
            "current_storage_gb",
            "member_count",
            "usage_stats",
            "trial_ends_at",
            "subscription_ends_at",
            "verified",
            "domain",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "current_members",
            "current_projects",
            "current_storage_gb",
            "created_at",
            "updated_at",
        ]

    def get_owner_name(self, obj):
        """Get owner full name"""
        if obj.owner.first_name or obj.owner.last_name:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return obj.owner.email

    def get_usage_stats(self, obj):
        """Get usage statistics"""
        return {
            "members": {
                "current": obj.current_members,
                "max": obj.max_members,
                "percentage": round(
                    (
                        (obj.current_members / obj.max_members * 100)
                        if obj.max_members > 0
                        else 0
                    ),
                    2,
                ),
            },
            "projects": {
                "current": obj.current_projects,
                "max": obj.max_projects,
                "percentage": round(
                    (
                        (obj.current_projects / obj.max_projects * 100)
                        if obj.max_projects > 0
                        else 0
                    ),
                    2,
                ),
            },
            "storage": {
                "current_gb": float(obj.current_storage_gb),
                "max_gb": obj.max_storage_gb,
                "percentage": round(
                    (
                        (float(obj.current_storage_gb) / obj.max_storage_gb * 100)
                        if obj.max_storage_gb > 0
                        else 0
                    ),
                    2,
                ),
            },
        }


class OrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight organization list serializer"""

    owner_name = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(source="current_members", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "primary_color",
            "status",
            "plan",
            "owner_name",
            "member_count",
            "created_at",
        ]

    def get_owner_name(self, obj):
        """Get owner name"""
        if obj.owner.first_name or obj.owner.last_name:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return obj.owner.email


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Organization creation serializer"""

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "description",
            "primary_color",
            "plan",
        ]

    def validate_slug(self, value):
        """Validate slug uniqueness"""
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug is already taken")
        return value


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """Organization update serializer"""

    class Meta:
        model = Organization
        fields = [
            "name",
            "description",
            "logo",
            "primary_color",
            "settings",
        ]


class OrganizationSettingsSerializer(serializers.Serializer):
    """Organization settings serializer"""

    # General settings
    timezone = serializers.CharField(required=False)
    date_format = serializers.CharField(required=False)
    time_format = serializers.CharField(required=False)

    # Feature toggles
    enable_time_tracking = serializers.BooleanField(required=False, default=True)
    enable_file_attachments = serializers.BooleanField(required=False, default=True)
    enable_comments = serializers.BooleanField(required=False, default=True)
    enable_notifications = serializers.BooleanField(required=False, default=True)

    # Security settings
    require_2fa = serializers.BooleanField(required=False, default=False)
    session_timeout_minutes = serializers.IntegerField(required=False, default=480)
    allowed_domains = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )


class OrganizationStatisticsSerializer(serializers.Serializer):
    """Organization statistics serializer"""

    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    status = serializers.CharField()
    plan = serializers.CharField()
    members = serializers.DictField()
    projects = serializers.DictField()
    storage = serializers.DictField()
    created_at = serializers.DateTimeField()
    trial_ends_at = serializers.DateTimeField(allow_null=True)
    subscription_ends_at = serializers.DateTimeField(allow_null=True)


# ============================================================================
# Organization Member Serializers
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


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Full organization member serializer"""

    user = UserMinimalSerializer(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    invited_by_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "organization",
            "organization_name",
            "user",
            "role",
            "status",
            "custom_permissions",
            "permissions",
            "invited_by",
            "invited_by_name",
            "invitation_token",
            "invitation_expires_at",
            "joined_at",
            "last_accessed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "user",
            "invited_by",
            "invitation_token",
            "joined_at",
            "created_at",
            "updated_at",
        ]

    def get_invited_by_name(self, obj):
        """Get inviter name"""
        if not obj.invited_by:
            return None
        if obj.invited_by.first_name or obj.invited_by.last_name:
            return f"{obj.invited_by.first_name} {obj.invited_by.last_name}".strip()
        return obj.invited_by.email

    def get_permissions(self, obj):
        """Get member permissions"""
        return obj.get_permissions()


class OrganizationMemberListSerializer(serializers.ModelSerializer):
    """Lightweight member list serializer"""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "user",
            "role",
            "status",
            "joined_at",
            "last_accessed_at",
        ]


class OrganizationMemberInviteSerializer(serializers.Serializer):
    """Member invitation serializer"""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=OrganizationMember.Role.choices, default=OrganizationMember.Role.MEMBER
    )

    def validate_role(self, value):
        """Validate role - cannot invite as owner"""
        if value == OrganizationMember.Role.OWNER:
            raise serializers.ValidationError("Cannot invite as owner")
        return value


class OrganizationMemberUpdateSerializer(serializers.ModelSerializer):
    """Member update serializer"""

    class Meta:
        model = OrganizationMember
        fields = ["role", "custom_permissions"]

    def validate_role(self, value):
        """Validate role - cannot change to owner"""
        if value == OrganizationMember.Role.OWNER:
            raise serializers.ValidationError("Cannot promote to owner via update")
        return value


class OrganizationMemberStatisticsSerializer(serializers.Serializer):
    """Member statistics serializer"""

    total = serializers.IntegerField()
    active = serializers.IntegerField()
    invited = serializers.IntegerField()
    suspended = serializers.IntegerField()
    by_role = serializers.DictField()


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
