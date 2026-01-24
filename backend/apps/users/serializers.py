from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with all fields."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "is_verified",
            "account_status",
            "timezone",
            "language",
            "profile_completion",
            "last_activity",
            "date_joined",
            "preferences",
            "notification_settings",
            "working_hours",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "date_joined",
            "profile_completion",
            "last_activity",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "timezone",
            "language",
            "profile_completion",
        ]
        read_only_fields = ["id", "profile_completion"]


class UserPreferencesSerializer(serializers.Serializer):
    """Serializer for user preferences."""

    theme = serializers.ChoiceField(choices=["light", "dark", "auto"], required=False)
    layout = serializers.CharField(required=False)
    sidebar_collapsed = serializers.BooleanField(required=False)
    default_view = serializers.ChoiceField(
        choices=["list", "board", "calendar", "timeline"], required=False
    )
    items_per_page = serializers.IntegerField(
        min_value=10, max_value=100, required=False
    )
    date_format = serializers.CharField(required=False)
    time_format = serializers.ChoiceField(choices=["12h", "24h"], required=False)


class NotificationSettingsSerializer(serializers.Serializer):
    """Serializer for notification settings."""

    email = serializers.DictField(required=False)
    in_app = serializers.DictField(required=False)


class WorkingHoursSerializer(serializers.Serializer):
    """Serializer for working hours."""

    monday = serializers.DictField(required=False)
    tuesday = serializers.DictField(required=False)
    wednesday = serializers.DictField(required=False)
    thursday = serializers.DictField(required=False)
    friday = serializers.DictField(required=False)
    saturday = serializers.DictField(required=False)
    sunday = serializers.DictField(required=False)


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user lists."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "is_verified",
            "account_status",
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "timezone",
            "language",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class UserStatisticsSerializer(serializers.Serializer):
    """Serializer for user statistics."""

    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    suspended_users = serializers.IntegerField()
    pending_users = serializers.IntegerField()
