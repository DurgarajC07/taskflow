"""
Organization Views
API endpoints for organization management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.serializers import (
    OrganizationSerializer,
    OrganizationListSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    OrganizationSettingsSerializer,
    OrganizationStatisticsSerializer,
    OrganizationMemberSerializer,
    OrganizationMemberListSerializer,
    OrganizationMemberInviteSerializer,
    OrganizationMemberUpdateSerializer,
    OrganizationMemberStatisticsSerializer,
    TransferOwnershipSerializer,
)
from apps.organizations.permissions import (
    IsOrganizationMember,
    IsOrganizationOwner,
    IsOrganizationAdmin,
    CanManageMembers,
    OrganizationPermission,
)
from apps.organizations.services import OrganizationService, OrganizationMemberService
from apps.core.pagination import StandardResultsSetPagination


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Organization operations.

    list: Get organizations user has access to
    retrieve: Get organization details
    create: Create new organization
    update: Update organization (owner only)
    partial_update: Partially update organization (owner only)
    destroy: Soft delete organization (owner only)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = "slug"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = OrganizationService()

    def get_queryset(self):
        """Get organizations accessible by user"""
        return self.service.repository.get_user_organizations(self.request.user)

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "list":
            return OrganizationListSerializer
        elif self.action == "create":
            return OrganizationCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return OrganizationUpdateSerializer
        elif self.action == "statistics":
            return OrganizationStatisticsSerializer
        elif self.action == "update_settings":
            return OrganizationSettingsSerializer
        return OrganizationSerializer

    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in [
            "update",
            "partial_update",
            "destroy",
            "change_plan",
            "verify",
            "transfer_ownership",
        ]:
            return [IsAuthenticated(), IsOrganizationOwner()]
        elif self.action in ["retrieve", "statistics", "members"]:
            return [IsAuthenticated(), IsOrganizationMember()]
        elif self.action in ["update_settings"]:
            return [IsAuthenticated(), IsOrganizationAdmin()]
        return [IsAuthenticated()]

    def list(self, request):
        """List user's organizations"""
        queryset = self.get_queryset()

        # Search filter
        search = request.query_params.get("search")
        if search:
            queryset = self.service.search_organizations(search, request.user)

        # Status filter
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Plan filter
        plan_filter = request.query_params.get("plan")
        if plan_filter:
            queryset = queryset.filter(plan=plan_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create new organization"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            organization = self.service.create_organization(
                owner=request.user, data=serializer.validated_data
            )

            result_serializer = OrganizationSerializer(organization)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, slug=None):
        """Get organization details"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        serializer = self.get_serializer(organization)
        return Response(serializer.data)

    def update(self, request, slug=None):
        """Update organization (full)"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_org = self.service.update_organization(
                organization=organization,
                data=serializer.validated_data,
                user=request.user,
            )

            result_serializer = OrganizationSerializer(updated_org)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, slug=None):
        """Update organization (partial)"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            updated_org = self.service.update_organization(
                organization=organization,
                data=serializer.validated_data,
                user=request.user,
            )

            result_serializer = OrganizationSerializer(updated_org)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, slug=None):
        """Soft delete organization"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        try:
            self.service.delete_organization(organization, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def statistics(self, request, slug=None):
        """Get organization statistics"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        stats = self.service.get_organization_statistics(organization.id)
        serializer = OrganizationStatisticsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_plan(self, request, slug=None):
        """Change organization plan"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        plan = request.data.get("plan")
        if not plan:
            return Response(
                {"error": "Plan is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_org = self.service.change_plan(organization, plan, request.user)
            serializer = OrganizationSerializer(updated_org)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "patch"])
    def update_settings(self, request, slug=None):
        """Update organization settings"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        serializer = OrganizationSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_org = self.service.update_settings(
                organization=organization,
                settings=serializer.validated_data,
                user=request.user,
            )

            result_serializer = OrganizationSerializer(updated_org)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def verify(self, request, slug=None):
        """Verify organization domain"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        domain = request.data.get("domain")
        if not domain:
            return Response(
                {"error": "Domain is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_org = self.service.verify_organization(organization, domain)
            serializer = OrganizationSerializer(updated_org)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def transfer_ownership(self, request, slug=None):
        """Transfer organization ownership"""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        serializer = TransferOwnershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            new_owner = User.objects.get(id=serializer.validated_data["new_owner_id"])

            member_service = OrganizationMemberService()
            member_service.transfer_ownership(organization, new_owner, request.user)

            # Refresh organization
            organization.refresh_from_db()
            result_serializer = OrganizationSerializer(organization)
            return Response(result_serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class OrganizationMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Organization Member operations.

    list: List organization members
    retrieve: Get member details
    update: Update member role/permissions
    destroy: Remove member from organization
    """

    permission_classes = [IsAuthenticated, CanManageMembers]
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = OrganizationMemberService()
        self.org_service = OrganizationService()

    def get_organization(self):
        """Get organization from URL"""
        org_slug = self.kwargs.get("organization_slug")
        return get_object_or_404(Organization, slug=org_slug)

    def get_queryset(self):
        """Get members of organization"""
        organization = self.get_organization()
        return self.service.repository.get_by_organization(organization)

    def get_serializer_class(self):
        """Get appropriate serializer class"""
        if self.action == "list":
            return OrganizationMemberListSerializer
        elif self.action == "invite":
            return OrganizationMemberInviteSerializer
        elif self.action in ["update", "partial_update"]:
            return OrganizationMemberUpdateSerializer
        elif self.action == "statistics":
            return OrganizationMemberStatisticsSerializer
        return OrganizationMemberSerializer

    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ["list", "retrieve", "statistics"]:
            return [IsAuthenticated(), IsOrganizationMember()]
        return [IsAuthenticated(), CanManageMembers()]

    def list(self, request, organization_slug=None):
        """List organization members"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        queryset = self.get_queryset()

        # Search filter
        search = request.query_params.get("search")
        if search:
            queryset = self.service.search_members(organization, search)

        # Role filter
        role = request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)

        # Status filter
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def invite(self, request, organization_slug=None):
        """Invite user to organization"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        serializer = OrganizationMemberInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invitation = self.service.invite_member(
                organization=organization,
                email=serializer.validated_data["email"],
                role=serializer.validated_data["role"],
                invited_by=request.user,
            )

            result_serializer = OrganizationMemberSerializer(invitation)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def accept_invitation(self, request):
        """Accept organization invitation"""
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Invitation token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = self.service.accept_invitation(token, request.user)
            serializer = OrganizationMemberSerializer(membership)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"])
    def remove(self, request, organization_slug=None, pk=None):
        """Remove member from organization"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)

        try:
            self.service.remove_member(organization, member.user, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def leave(self, request, organization_slug=None):
        """Leave organization"""
        organization = self.get_organization()

        try:
            self.service.leave_organization(organization, request.user)
            return Response({"message": "Successfully left organization"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def update_role(self, request, organization_slug=None, pk=None):
        """Update member role"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)
        new_role = request.data.get("role")

        if not new_role:
            return Response(
                {"error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_member = self.service.update_member_role(
                organization, member.user, new_role, request.user
            )
            serializer = OrganizationMemberSerializer(updated_member)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def suspend(self, request, organization_slug=None, pk=None):
        """Suspend member"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)
        reason = request.data.get("reason")

        try:
            updated_member = self.service.suspend_member(
                organization, member.user, request.user, reason
            )
            serializer = OrganizationMemberSerializer(updated_member)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def activate(self, request, organization_slug=None, pk=None):
        """Activate suspended member"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        member = get_object_or_404(OrganizationMember, pk=pk, organization=organization)

        try:
            updated_member = self.service.activate_member(
                organization, member.user, request.user
            )
            serializer = OrganizationMemberSerializer(updated_member)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def statistics(self, request, organization_slug=None):
        """Get member statistics"""
        organization = self.get_organization()
        self.check_object_permissions(request, organization)

        stats = self.service.get_member_statistics(organization)
        serializer = OrganizationMemberStatisticsSerializer(stats)
        return Response(serializer.data)
