"""
Team, Project, and Task URLs
URL routing for team, project, and task API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tasks.views import (
    TeamViewSet,
    TeamMemberViewSet,
    ProjectViewSet,
    ProjectMemberViewSet,
    TaskViewSet,
    TaskCommentViewSet,
    TaskAttachmentViewSet,
)

app_name = "tasks"

# Main router for teams
teams_router = DefaultRouter()
teams_router.register(r"teams", TeamViewSet, basename="team")
teams_router.register(
    r"teams/(?P<team_pk>[^/.]+)/members", TeamMemberViewSet, basename="team-member"
)

# Router for projects
projects_router = DefaultRouter()
projects_router.register(r"projects", ProjectViewSet, basename="project")
projects_router.register(
    r"projects/(?P<project_pk>[^/.]+)/members",
    ProjectMemberViewSet,
    basename="project-member",
)

# Router for tasks
tasks_router = DefaultRouter()
tasks_router.register(r"tasks", TaskViewSet, basename="task")
tasks_router.register(
    r"tasks/(?P<task_pk>[^/.]+)/comments",
    TaskCommentViewSet,
    basename="task-comment",
)
tasks_router.register(
    r"tasks/(?P<task_pk>[^/.]+)/attachments",
    TaskAttachmentViewSet,
    basename="task-attachment",
)

urlpatterns = teams_router.urls + projects_router.urls + tasks_router.urls
