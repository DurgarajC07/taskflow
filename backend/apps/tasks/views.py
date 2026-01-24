"""
Team, Project, and Task Views
API endpoints for team, project, and task management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

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
from apps.organizations.models import Organization
from apps.tasks.serializers import (
    TeamSerializer,
    TeamListSerializer,
    TeamCreateSerializer,
    TeamUpdateSerializer,
    TeamStatisticsSerializer,
    OrganizationTeamStatisticsSerializer,
    TeamMemberSerializer,
    TeamMemberListSerializer,
    TeamMemberAddSerializer,
    TeamMemberUpdateSerializer,
    TeamMemberStatisticsSerializer,
    TransferLeadSerializer,
    ChangeVisibilitySerializer,
    TaskSerializer,
    TaskListSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskCommentSerializer,
    TaskCommentCreateSerializer,
    TaskAttachmentSerializer,
    TaskAttachmentCreateSerializer,
    TaskActivitySerializer,
    ChangeStatusSerializer,
    AssignTaskSerializer,
    AddLabelSerializer,
    RemoveLabelSerializer,
    AddBlockedBySerializer,
    RemoveBlockedBySerializer,
    BulkUpdateSerializer,
)
from apps.tasks.permissions import (
    CanViewTeam,
    IsTeamMember,
    IsTeamMaintainer,
    CanManageTeams,
    TeamPermission,
)
from apps.tasks.services import (
    TeamService,
    TeamMemberService,
    TaskService,
    TaskCommentService,
)
from apps.core.pagination import StandardResultsSetPagination


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Team operations.

    list: Get teams in organization
    retrieve: Get team details
    create: Create new team
    update: Update team
    partial_update: Partially update team
    destroy: Soft delete team
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = TeamService()

    def get_organization(self):
        """Get organization from URL"""
        org_slug = self.kwargs.get("organization_slug")
        return get_object_or_404(Organization, slug=org_slug)

    def get_queryset(self):
        """Get teams visible to user"""
        organization = self.get_organization()
        return self.service.get_visible_teams(organization, self.request.user)

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "list":
            return TeamListSerializer
        elif self.action == "create":
            return TeamCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return TeamUpdateSerializer
        elif self.action == "statistics":
            return TeamStatisticsSerializer
        elif self.action == "org_statistics":
            return OrganizationTeamStatisticsSerializer
        elif self.action == "change_visibility":
            return ChangeVisibilitySerializer
        return TeamSerializer

    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ["retrieve", "statistics"]:
            return [IsAuthenticated(), CanViewTeam()]
        elif self.action in ["update", "partial_update", "change_visibility"]:
            return [IsAuthenticated(), IsTeamMaintainer()]
        elif self.action in ["destroy"]:
            return [IsAuthenticated(), CanManageTeams()]
        return [IsAuthenticated()]

    def list(self, request, organization_slug=None):
        """List organization teams"""
        organization = self.get_organization()
        queryset = self.get_queryset()

        # Search filter
        search = request.query_params.get("search")
        if search:
            queryset = self.service.search_teams(organization, search, request.user)

        # Visibility filter
        visibility = request.query_params.get("visibility")
        if visibility:
            queryset = queryset.filter(visibility=visibility)

        # User teams only
        if request.query_params.get("my_teams") == "true":
            queryset = self.service.get_user_teams(organization, request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, organization_slug=None):
        """Create new team"""
        organization = self.get_organization()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            team = self.service.create_team(
                organization=organization,
                data=serializer.validated_data,
                created_by=request.user,
            )

            result_serializer = TeamSerializer(team)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, organization_slug=None, pk=None):
        """Get team details"""
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = self.get_serializer(team)
        return Response(serializer.data)

    def update(self, request, organization_slug=None, pk=None):
        """Update team (full)"""
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_team = self.service.update_team(
                team=team, data=serializer.validated_data, user=request.user
            )

            result_serializer = TeamSerializer(updated_team)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, organization_slug=None, pk=None):
        """Update team (partial)"""
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            updated_team = self.service.update_team(
                team=team, data=serializer.validated_data, user=request.user
            )

            result_serializer = TeamSerializer(updated_team)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, organization_slug=None, pk=None):
        """Soft delete team"""
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        try:
            self.service.delete_team(team, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def statistics(self, request, organization_slug=None, pk=None):
        """Get team statistics"""
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        stats = self.service.get_team_statistics(team.id)
        serializer = TeamStatisticsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def org_statistics(self, request, organization_slug=None):
        """Get organization team statistics"""
        organization = self.get_organization()

        stats = self.service.get_organization_statistics(organization)
        serializer = OrganizationTeamStatisticsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_visibility(self, request, organization_slug=None, pk=None):
        """Change team visibility"""
        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)

        serializer = ChangeVisibilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_team = self.service.change_visibility(
                team=team,
                visibility=serializer.validated_data["visibility"],
                user=request.user,
            )

            result_serializer = TeamSerializer(updated_team)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TeamMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Team Member operations.

    list: List team members
    create: Add member to team
    destroy: Remove member from team
    """

    permission_classes = [IsAuthenticated, IsTeamMember]
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = TeamMemberService()

    def get_team(self):
        """Get team from URL"""
        team_id = self.kwargs.get("team_pk")
        return get_object_or_404(Team, pk=team_id)

    def get_queryset(self):
        """Get members of team"""
        team = self.get_team()
        return self.service.repository.get_by_team(team)

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "list":
            return TeamMemberListSerializer
        elif self.action == "add":
            return TeamMemberAddSerializer
        elif self.action in ["update", "partial_update"]:
            return TeamMemberUpdateSerializer
        elif self.action == "statistics":
            return TeamMemberStatisticsSerializer
        elif self.action == "transfer_lead":
            return TransferLeadSerializer
        return TeamMemberSerializer

    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ["list", "retrieve", "statistics"]:
            return [IsAuthenticated(), IsTeamMember()]
        return [IsAuthenticated(), IsTeamMaintainer()]

    def list(self, request, organization_slug=None, team_pk=None):
        """List team members"""
        team = self.get_team()
        self.check_object_permissions(request, team)

        queryset = self.get_queryset()

        # Search filter
        search = request.query_params.get("search")
        if search:
            queryset = self.service.search_members(team, search)

        # Role filter
        role = request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add(self, request, organization_slug=None, team_pk=None):
        """Add member to team"""
        team = self.get_team()
        self.check_object_permissions(request, team)

        serializer = TeamMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=serializer.validated_data["user_id"])

            member = self.service.add_member(
                team=team,
                user=user,
                role=serializer.validated_data["role"],
                added_by=request.user,
            )

            result_serializer = TeamMemberSerializer(member)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"])
    def remove(self, request, organization_slug=None, team_pk=None, pk=None):
        """Remove member from team"""
        team = self.get_team()
        self.check_object_permissions(request, team)

        member = get_object_or_404(TeamMember, pk=pk, team=team)

        try:
            self.service.remove_member(team, member.user, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def leave(self, request, organization_slug=None, team_pk=None):
        """Leave team"""
        team = self.get_team()

        try:
            self.service.leave_team(team, request.user)
            return Response({"message": "Successfully left team"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def update_role(self, request, organization_slug=None, team_pk=None, pk=None):
        """Update member role"""
        team = self.get_team()
        self.check_object_permissions(request, team)

        member = get_object_or_404(TeamMember, pk=pk, team=team)
        new_role = request.data.get("role")

        if not new_role:
            return Response(
                {"error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_member = self.service.update_member_role(
                team, member.user, new_role, request.user
            )
            serializer = TeamMemberSerializer(updated_member)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def transfer_lead(self, request, organization_slug=None, team_pk=None):
        """Transfer team lead role"""
        team = self.get_team()
        self.check_object_permissions(request, team)

        serializer = TransferLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            new_lead = User.objects.get(id=serializer.validated_data["new_lead_id"])

            self.service.transfer_lead(team, new_lead, request.user)

            # Refresh team
            team.refresh_from_db()
            result_serializer = TeamSerializer(team)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"])
    def statistics(self, request, organization_slug=None, team_pk=None):
        """Get member statistics"""
        team = self.get_team()
        self.check_object_permissions(request, team)

        stats = self.service.get_member_statistics(team)
        serializer = TeamMemberStatisticsSerializer(stats)
        return Response(serializer.data)


# ============================================================================
# Project Views
# ============================================================================


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project operations.

    list: Get projects in organization
    retrieve: Get project details
    create: Create new project
    update: Update project
    partial_update: Partially update project
    destroy: Soft delete project
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.tasks.services import ProjectService
        from apps.tasks.repositories import ProjectRepository

        self.service = ProjectService()
        self.repository = ProjectRepository()

    def get_organization(self):
        """Get organization from URL"""
        slug = self.kwargs.get("organization_slug")
        return get_object_or_404(Organization, slug=slug)

    def get_queryset(self):
        """Get filtered queryset"""
        organization = self.get_organization()
        user = self.request.user

        # Check org membership
        if not organization.is_member(user):
            return Project.objects.none()

        # Get visible projects
        queryset = self.repository.get_visible_projects(user, organization)

        # Filter by status
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = self.repository.filter_by_status(queryset, status_param)

        # Filter by priority
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = self.repository.filter_by_priority(queryset, priority)

        # Filter by team
        team_id = self.request.query_params.get("team")
        if team_id:
            from apps.tasks.models import Team

            try:
                team = Team.objects.get(id=team_id, organization=organization)
                queryset = self.repository.filter_by_team(queryset, team)
            except Team.DoesNotExist:
                pass

        # Filter by owner
        owner_id = self.request.query_params.get("owner")
        if owner_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                owner = User.objects.get(id=owner_id)
                queryset = self.repository.filter_by_owner(queryset, owner)
            except User.DoesNotExist:
                pass

        # Search
        search = self.request.query_params.get("search")
        if search:
            queryset = self.repository.search_projects(organization, search)

        # My projects filter
        if self.request.query_params.get("my_projects") == "true":
            queryset = self.repository.get_user_projects(user, organization)

        return queryset.select_related("organization", "owner", "team")

    def get_serializer_class(self):
        """Get appropriate serializer"""
        from apps.tasks.serializers import (
            ProjectSerializer,
            ProjectListSerializer,
            ProjectCreateSerializer,
            ProjectUpdateSerializer,
        )

        if self.action == "list":
            return ProjectListSerializer
        elif self.action == "create":
            return ProjectCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ProjectUpdateSerializer
        return ProjectSerializer

    def create(self, request, organization_slug=None):
        """Create new project"""
        organization = self.get_organization()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = self.service.create_project(
                organization=organization,
                owner=request.user,
                data=serializer.validated_data,
            )
            result_serializer = ProjectSerializer(project)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, organization_slug=None, pk=None):
        """Update project"""
        project = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_project = self.service.update_project(
                project, request.user, serializer.validated_data
            )
            result_serializer = ProjectSerializer(updated_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, organization_slug=None, pk=None):
        """Soft delete project"""
        project = self.get_object()

        try:
            self.service.delete_project(project, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def statistics(self, request, organization_slug=None, pk=None):
        """Get project statistics"""
        project = self.get_object()

        from apps.tasks.serializers import ProjectStatisticsSerializer

        stats = self.service.get_statistics(project)
        serializer = ProjectStatisticsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def org_statistics(self, request, organization_slug=None):
        """Get organization project statistics"""
        organization = self.get_organization()

        stats = self.repository.get_statistics(organization)
        return Response(stats)

    @action(detail=True, methods=["post"])
    def change_status(self, request, organization_slug=None, pk=None):
        """Change project status"""
        project = self.get_object()

        from apps.tasks.serializers import ChangeProjectStatusSerializer

        serializer = ChangeProjectStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_project = self.service.change_status(
                project, request.user, serializer.validated_data["status"]
            )
            result_serializer = ProjectSerializer(updated_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def change_visibility(self, request, organization_slug=None, pk=None):
        """Change project visibility"""
        project = self.get_object()

        from apps.tasks.serializers import ChangeProjectVisibilitySerializer

        serializer = ChangeProjectVisibilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_project = self.service.change_visibility(
                project, request.user, serializer.validated_data["visibility"]
            )
            result_serializer = ProjectSerializer(updated_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def assign_team(self, request, organization_slug=None, pk=None):
        """Assign team to project"""
        project = self.get_object()

        from apps.tasks.serializers import AssignTeamSerializer

        serializer = AssignTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team = None
        team_id = serializer.validated_data.get("team_id")
        if team_id:
            try:
                from apps.tasks.models import Team

                team = Team.objects.get(id=team_id)
            except Team.DoesNotExist:
                return Response(
                    {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
                )

        try:
            updated_project = self.service.assign_team(project, request.user, team)
            result_serializer = ProjectSerializer(updated_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def archive(self, request, organization_slug=None, pk=None):
        """Archive project"""
        project = self.get_object()

        try:
            archived_project = self.service.archive_project(project, request.user)
            result_serializer = ProjectSerializer(archived_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete(self, request, organization_slug=None, pk=None):
        """Mark project as completed"""
        project = self.get_object()

        try:
            completed_project = self.service.complete_project(project, request.user)
            result_serializer = ProjectSerializer(completed_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, organization_slug=None, pk=None):
        """Duplicate project"""
        project = self.get_object()

        from apps.tasks.serializers import ProjectDuplicateSerializer

        serializer = ProjectDuplicateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            duplicated_project = self.service.duplicate_project(
                project,
                request.user,
                serializer.validated_data["name"],
                serializer.validated_data["key"],
            )
            result_serializer = ProjectSerializer(duplicated_project)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def transfer_ownership(self, request, organization_slug=None, pk=None):
        """Transfer project ownership"""
        project = self.get_object()

        from apps.tasks.serializers import TransferOwnershipSerializer

        serializer = TransferOwnershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            new_owner = User.objects.get(id=serializer.validated_data["new_owner_id"])

            updated_project = self.service.transfer_ownership(
                project, request.user, new_owner
            )
            result_serializer = ProjectSerializer(updated_project)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ProjectMemberViewSet(viewsets.GenericViewSet):
    """
    ViewSet for ProjectMember operations.

    list: Get project members
    add: Add member to project
    remove: Remove member from project
    leave: Leave project
    update_role: Update member role
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.tasks.services import ProjectMemberService
        from apps.tasks.repositories import ProjectMemberRepository

        self.service = ProjectMemberService()
        self.repository = ProjectMemberRepository()

    def get_project(self):
        """Get project from URL"""
        project_pk = self.kwargs.get("project_pk")
        organization_slug = self.kwargs.get("organization_slug")

        organization = get_object_or_404(Organization, slug=organization_slug)
        return get_object_or_404(Project, id=project_pk, organization=organization)

    def get_queryset(self):
        """Get filtered queryset"""
        project = self.get_project()

        queryset = self.repository.get_project_members(project)

        # Filter by role
        role = self.request.query_params.get("role")
        if role:
            queryset = self.repository.filter_by_role(queryset, role)

        # Search
        search = self.request.query_params.get("search")
        if search:
            queryset = self.repository.search_members(project, search)

        return queryset

    def get_serializer_class(self):
        """Get appropriate serializer"""
        from apps.tasks.serializers import (
            ProjectMemberSerializer,
            ProjectMemberListSerializer,
        )

        if self.action == "list":
            return ProjectMemberListSerializer
        return ProjectMemberSerializer

    def list(self, request, organization_slug=None, project_pk=None):
        """List project members"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add(self, request, organization_slug=None, project_pk=None):
        """Add member to project"""
        project = self.get_project()

        from apps.tasks.serializers import ProjectMemberAddSerializer

        serializer = ProjectMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=serializer.validated_data["user_id"])

            member = self.service.add_member(
                project=project,
                user=user,
                role=serializer.validated_data["role"],
                added_by=request.user,
            )

            from apps.tasks.serializers import ProjectMemberSerializer

            result_serializer = ProjectMemberSerializer(member)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def remove(self, request, organization_slug=None, project_pk=None):
        """Remove member from project"""
        project = self.get_project()

        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=user_id)

            self.service.remove_member(project, user, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def leave(self, request, organization_slug=None, project_pk=None):
        """Leave project"""
        project = self.get_project()

        try:
            self.service.leave_project(project, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def update_role(self, request, organization_slug=None, project_pk=None):
        """Update member role"""
        project = self.get_project()

        user_id = request.data.get("user_id")
        new_role = request.data.get("role")

        if not user_id or not new_role:
            return Response(
                {"error": "user_id and role are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=user_id)

            updated_member = self.service.update_role(
                project, user, new_role, request.user
            )

            from apps.tasks.serializers import ProjectMemberSerializer

            serializer = ProjectMemberSerializer(updated_member)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def bulk_add(self, request, organization_slug=None, project_pk=None):
        """Bulk add members to project"""
        project = self.get_project()

        from apps.tasks.serializers import ProjectMemberBulkAddSerializer

        serializer = ProjectMemberBulkAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            users_data = []

            for user_id in serializer.validated_data["user_ids"]:
                try:
                    user = User.objects.get(id=user_id)
                    users_data.append(
                        {"user": user, "role": serializer.validated_data["role"]}
                    )
                except User.DoesNotExist:
                    continue

            members = self.service.bulk_add_members(project, users_data, request.user)

            from apps.tasks.serializers import ProjectMemberSerializer

            result_serializer = ProjectMemberSerializer(members, many=True)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def statistics(self, request, organization_slug=None, project_pk=None):
        """Get member statistics"""
        project = self.get_project()

        from apps.tasks.serializers import ProjectMemberStatisticsSerializer

        stats = self.service.get_member_statistics(project)
        serializer = ProjectMemberStatisticsSerializer(stats)
        return Response(serializer.data)


# ============================================================================
# TASK VIEWS
# ============================================================================


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task operations.

    list: Get tasks in project
    retrieve: Get task details
    create: Create new task
    update: Update task
    partial_update: Partially update task
    destroy: Soft delete task
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = "pk"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = TaskService()

    def get_queryset(self):
        """Get tasks queryset"""
        organization_slug = self.kwargs.get("organization_slug")
        project_pk = self.kwargs.get("project_pk")

        if not organization_slug or not project_pk:
            return Task.objects.none()

        # Get project
        project = get_object_or_404(
            Project,
            id=project_pk,
            organization__slug=organization_slug,
            deleted_at__isnull=True,
        )

        queryset = Task.objects.filter(
            project=project, deleted_at__isnull=True
        ).select_related(
            "project",
            "assignee",
            "reporter",
            "parent_task",
        )

        # Apply filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        priority_filter = self.request.query_params.get("priority")
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        task_type = self.request.query_params.get("task_type")
        if task_type:
            queryset = queryset.filter(task_type=task_type)

        assignee_id = self.request.query_params.get("assignee")
        if assignee_id:
            if assignee_id == "unassigned":
                queryset = queryset.filter(assignee__isnull=True)
            else:
                queryset = queryset.filter(assignee_id=assignee_id)

        reporter_id = self.request.query_params.get("reporter")
        if reporter_id:
            queryset = queryset.filter(reporter_id=reporter_id)

        labels = self.request.query_params.get("labels")
        if labels:
            label_list = labels.split(",")
            for label in label_list:
                queryset = queryset.filter(labels__contains=[label.strip()])

        overdue = self.request.query_params.get("overdue")
        if overdue == "true":
            from django.utils import timezone

            queryset = queryset.filter(
                due_date__lt=timezone.now(),
                status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS],
            )

        blocked = self.request.query_params.get("blocked")
        if blocked == "true":
            queryset = queryset.filter(blocked_by__isnull=False).distinct()

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(task_key__icontains=search)
            )

        # Ordering
        ordering = self.request.query_params.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        return queryset

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "list":
            return TaskListSerializer
        elif self.action == "create":
            return TaskCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_project(self):
        """Get project from URL parameters"""
        organization_slug = self.kwargs.get("organization_slug")
        project_pk = self.kwargs.get("project_pk")
        return get_object_or_404(
            Project,
            id=project_pk,
            organization__slug=organization_slug,
            deleted_at__isnull=True,
        )

    def create(self, request, *args, **kwargs):
        """Create new task"""
        project = self.get_project()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            task = self.service.create_task(
                project=project,
                reporter=request.user,
                **serializer.validated_data,
            )
            result_serializer = TaskSerializer(task)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Update task"""
        task = self.get_object()
        serializer = self.get_serializer(
            task, data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)

        try:
            updated_task = self.service.update_task(
                task=task,
                user=request.user,
                **serializer.validated_data,
            )
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Soft delete task"""
        task = self.get_object()
        try:
            self.service.delete_task(task, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def assign(self, request, organization_slug=None, project_pk=None, pk=None):
        """Assign task to user"""
        task = self.get_object()
        serializer = AssignTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assignee_id = serializer.validated_data.get("assignee_id")
            assignee = None
            if assignee_id:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                assignee = get_object_or_404(User, id=assignee_id)

            updated_task = self.service.assign_task(task, assignee, request.user)
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def change_status(self, request, organization_slug=None, project_pk=None, pk=None):
        """Change task status"""
        task = self.get_object()
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_status = serializer.validated_data["status"]
            updated_task = self.service.change_status(task, new_status, request.user)
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete(self, request, organization_slug=None, project_pk=None, pk=None):
        """Mark task as complete"""
        task = self.get_object()
        try:
            task.mark_complete()
            self.service._log_activity(
                task, request.user, TaskActivity.ActivityType.STATUS_CHANGED
            )
            result_serializer = TaskSerializer(task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def reopen(self, request, organization_slug=None, project_pk=None, pk=None):
        """Reopen completed task"""
        task = self.get_object()
        try:
            task.reopen()
            self.service._log_activity(
                task, request.user, TaskActivity.ActivityType.STATUS_CHANGED
            )
            result_serializer = TaskSerializer(task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_label(self, request, organization_slug=None, project_pk=None, pk=None):
        """Add label to task"""
        task = self.get_object()
        serializer = AddLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            label = serializer.validated_data["label"]
            updated_task = self.service.add_label(task, label, request.user)
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def remove_label(self, request, organization_slug=None, project_pk=None, pk=None):
        """Remove label from task"""
        task = self.get_object()
        serializer = RemoveLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            label = serializer.validated_data["label"]
            updated_task = self.service.remove_label(task, label, request.user)
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_blocked_by(self, request, organization_slug=None, project_pk=None, pk=None):
        """Add blocking relationship"""
        task = self.get_object()
        serializer = AddBlockedBySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            blocked_by_id = serializer.validated_data["blocked_by_id"]
            blocking_task = get_object_or_404(Task, id=blocked_by_id)
            updated_task = self.service.add_blocked_by(
                task, blocking_task, request.user
            )
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def remove_blocked_by(
        self, request, organization_slug=None, project_pk=None, pk=None
    ):
        """Remove blocking relationship"""
        task = self.get_object()
        serializer = RemoveBlockedBySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            blocked_by_id = serializer.validated_data["blocked_by_id"]
            blocking_task = get_object_or_404(Task, id=blocked_by_id)
            updated_task = self.service.remove_blocked_by(
                task, blocking_task, request.user
            )
            result_serializer = TaskSerializer(updated_task)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def comments(self, request, organization_slug=None, project_pk=None, pk=None):
        """Get task comments"""
        task = self.get_object()
        include_replies = request.query_params.get("include_replies", "true") == "true"

        from apps.tasks.repositories import TaskCommentRepository

        repo = TaskCommentRepository()
        comments = repo.get_task_comments(task, include_replies=include_replies)
        serializer = TaskCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def attachments(self, request, organization_slug=None, project_pk=None, pk=None):
        """Get task attachments"""
        task = self.get_object()

        from apps.tasks.repositories import TaskAttachmentRepository

        repo = TaskAttachmentRepository()
        attachments = repo.get_task_attachments(task)
        serializer = TaskAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def activities(self, request, organization_slug=None, project_pk=None, pk=None):
        """Get task activities"""
        task = self.get_object()
        activities = TaskActivity.objects.filter(task=task).order_by("-created_at")
        serializer = TaskActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def subtasks(self, request, organization_slug=None, project_pk=None, pk=None):
        """Get task subtasks"""
        task = self.get_object()

        from apps.tasks.repositories import TaskRepository

        repo = TaskRepository()
        subtasks = repo.get_subtasks(task)
        serializer = TaskListSerializer(subtasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_update(self, request, organization_slug=None, project_pk=None):
        """Bulk update tasks"""
        serializer = BulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.tasks.repositories import TaskRepository

        repo = TaskRepository()
        task_ids = serializer.validated_data["task_ids"]
        tasks = repo.filter(id__in=task_ids)

        # Verify all tasks belong to project
        project = self.get_project()
        if tasks.exclude(project=project).exists():
            return Response(
                {"error": "All tasks must belong to this project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Apply updates
            if "status" in serializer.validated_data:
                repo.bulk_update_status(task_ids, serializer.validated_data["status"])

            if "priority" in serializer.validated_data:
                repo.bulk_update_priority(
                    task_ids, serializer.validated_data["priority"]
                )

            if "assignee_id" in serializer.validated_data:
                assignee_id = serializer.validated_data.get("assignee_id")
                from django.contrib.auth import get_user_model

                User = get_user_model()
                assignee = None
                if assignee_id:
                    assignee = get_object_or_404(User, id=assignee_id)
                repo.bulk_assign(task_ids, assignee)

            # Return updated tasks
            updated_tasks = repo.filter(id__in=task_ids)
            result_serializer = TaskListSerializer(updated_tasks, many=True)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def statistics(self, request, organization_slug=None, project_pk=None):
        """Get task statistics"""
        project = self.get_project()

        from apps.tasks.repositories import TaskRepository

        repo = TaskRepository()

        stats = {
            "by_status": repo.get_status_statistics(project),
            "by_priority": repo.get_priority_statistics(project),
            "by_type": repo.get_type_statistics(project),
            "overdue_count": repo.get_overdue_count(project),
            "unassigned_count": repo.get_unassigned_count(project),
            "blocked_count": repo.filter(project=project, blocked_by__isnull=False)
            .distinct()
            .count(),
            "avg_completion_time": repo.get_average_completion_time(project),
        }

        return Response(stats)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskComment operations.

    list: Get comments for task
    retrieve: Get comment details
    create: Create new comment
    update: Update comment
    destroy: Delete comment
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TaskCommentSerializer
    lookup_field = "pk"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = TaskCommentService()

    def get_queryset(self):
        """Get comments queryset"""
        organization_slug = self.kwargs.get("organization_slug")
        project_pk = self.kwargs.get("project_pk")
        task_pk = self.kwargs.get("task_pk")

        if not all([organization_slug, project_pk, task_pk]):
            return TaskComment.objects.none()

        # Get task
        task = get_object_or_404(
            Task,
            id=task_pk,
            project_id=project_pk,
            project__organization__slug=organization_slug,
            deleted_at__isnull=True,
        )

        return TaskComment.objects.filter(task=task).select_related(
            "author", "parent_comment"
        )

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "create":
            return TaskCommentCreateSerializer
        return TaskCommentSerializer

    def create(self, request, *args, **kwargs):
        """Create new comment"""
        task = self.get_task()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = self.service.create_comment(
                task=task,
                author=request.user,
                **serializer.validated_data,
            )
            result_serializer = TaskCommentSerializer(comment)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Update comment"""
        comment = self.get_object()
        content = request.data.get("content")

        if not content:
            return Response(
                {"error": "Content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            updated_comment = self.service.update_comment(
                comment, content, request.user
            )
            serializer = TaskCommentSerializer(updated_comment)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Delete comment"""
        comment = self.get_object()
        try:
            self.service.delete_comment(comment, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_task(self):
        """Get task from URL parameters"""
        organization_slug = self.kwargs.get("organization_slug")
        project_pk = self.kwargs.get("project_pk")
        task_pk = self.kwargs.get("task_pk")

        return get_object_or_404(
            Task,
            id=task_pk,
            project_id=project_pk,
            project__organization__slug=organization_slug,
            deleted_at__isnull=True,
        )

    @action(detail=True, methods=["get"])
    def replies(
        self, request, organization_slug=None, project_pk=None, task_pk=None, pk=None
    ):
        """Get comment replies"""
        comment = self.get_object()

        from apps.tasks.repositories import TaskCommentRepository

        repo = TaskCommentRepository()
        replies = repo.get_comment_replies(comment)
        serializer = TaskCommentSerializer(replies, many=True)
        return Response(serializer.data)


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskAttachment operations.

    list: Get attachments for task
    retrieve: Get attachment details
    create: Upload attachment
    destroy: Delete attachment
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TaskAttachmentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        """Get attachments queryset"""
        organization_slug = self.kwargs.get("organization_slug")
        project_pk = self.kwargs.get("project_pk")
        task_pk = self.kwargs.get("task_pk")

        if not all([organization_slug, project_pk, task_pk]):
            return TaskAttachment.objects.none()

        # Get task
        task = get_object_or_404(
            Task,
            id=task_pk,
            project_id=project_pk,
            project__organization__slug=organization_slug,
            deleted_at__isnull=True,
        )

        return TaskAttachment.objects.filter(task=task).select_related("uploaded_by")

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "create":
            return TaskAttachmentCreateSerializer
        return TaskAttachmentSerializer

    def create(self, request, *args, **kwargs):
        """Upload attachment"""
        task = self.get_task()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create attachment
        attachment = TaskAttachment.objects.create(
            task=task,
            file=serializer.validated_data["file"],
            uploaded_by=request.user,
        )

        result_serializer = TaskAttachmentSerializer(
            attachment, context={"request": request}
        )
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Delete attachment"""
        attachment = self.get_object()

        from apps.tasks.repositories import TaskAttachmentRepository

        repo = TaskAttachmentRepository()
        repo.delete_attachment(attachment)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_task(self):
        """Get task from URL parameters"""
        organization_slug = self.kwargs.get("organization_slug")
        project_pk = self.kwargs.get("project_pk")
        task_pk = self.kwargs.get("task_pk")

        return get_object_or_404(
            Task,
            id=task_pk,
            project_id=project_pk,
            project__organization__slug=organization_slug,
            deleted_at__isnull=True,
        )
