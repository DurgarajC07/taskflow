"""
Organization URLs
URL routing for organization API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.organizations.views import OrganizationViewSet, OrganizationMemberViewSet

app_name = "organizations"

router = DefaultRouter()
router.register(r"", OrganizationViewSet, basename="organization")

# Nested router for organization members
member_router = DefaultRouter()
member_router.register(r"members", OrganizationMemberViewSet, basename="member")

urlpatterns = [
    # Organization endpoints
    path("", include(router.urls)),
    # Organization member endpoints (nested)
    path("<slug:organization_slug>/", include(member_router.urls)),
]
