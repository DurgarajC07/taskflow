"""
Workflow Repository
Data access layer for Workflow models.
"""

from django.db import models
from django.db.models import Q, Count, Prefetch
from apps.tasks.models import Workflow, WorkflowState, WorkflowTransition, WorkflowRule


class WorkflowRepository:
    """Repository for Workflow data access"""

    @staticmethod
    def get_by_id(workflow_id):
        """Get workflow by ID"""
        try:
            return (
                Workflow.objects.select_related("organization", "project", "created_by")
                .prefetch_related("states", "transitions", "rules")
                .get(id=workflow_id)
            )
        except Workflow.DoesNotExist:
            return None

    @staticmethod
    def get_organization_workflows(organization, include_deleted=False):
        """Get all workflows for an organization"""
        queryset = Workflow.all_objects if include_deleted else Workflow.objects
        return (
            queryset.filter(organization=organization, project__isnull=True)
            .select_related("created_by")
            .prefetch_related("states")
        )

    @staticmethod
    def get_project_workflows(project, include_deleted=False):
        """Get all workflows for a project (including inherited org workflows)"""
        queryset = Workflow.all_objects if include_deleted else Workflow.objects
        return (
            queryset.filter(
                Q(project=project)
                | Q(organization=project.organization, project__isnull=True)
            )
            .select_related("created_by")
            .prefetch_related("states")
        )

    @staticmethod
    def get_default_workflow(organization):
        """Get default workflow for organization"""
        try:
            return (
                Workflow.objects.filter(
                    organization=organization,
                    is_default=True,
                    is_active=True,
                )
                .select_related("created_by")
                .prefetch_related("states")
                .first()
            )
        except Workflow.DoesNotExist:
            return None

    @staticmethod
    def get_active_workflows(organization):
        """Get all active workflows for organization"""
        return (
            Workflow.objects.filter(
                organization=organization,
                is_active=True,
            )
            .select_related("created_by")
            .prefetch_related("states")
        )

    @staticmethod
    def search_workflows(organization, query):
        """Search workflows by name or description"""
        return Workflow.objects.filter(organization=organization).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    @staticmethod
    def create(data):
        """Create new workflow"""
        return Workflow.objects.create(**data)

    @staticmethod
    def update(workflow, data):
        """Update workflow"""
        for key, value in data.items():
            setattr(workflow, key, value)
        workflow.save()
        return workflow

    @staticmethod
    def delete(workflow, soft=True):
        """Delete workflow"""
        if soft:
            workflow.deleted_at = models.functions.Now()
            workflow.save()
        else:
            workflow.delete()

    @staticmethod
    def restore(workflow):
        """Restore soft-deleted workflow"""
        workflow.deleted_at = None
        workflow.save()

    @staticmethod
    def count_workflows(organization, active_only=True):
        """Count workflows for organization"""
        queryset = Workflow.objects.filter(organization=organization)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.count()


class WorkflowStateRepository:
    """Repository for WorkflowState data access"""

    @staticmethod
    def get_by_id(state_id):
        """Get workflow state by ID"""
        try:
            return WorkflowState.objects.select_related("workflow").get(id=state_id)
        except WorkflowState.DoesNotExist:
            return None

    @staticmethod
    def get_workflow_states(workflow):
        """Get all states for a workflow"""
        return WorkflowState.objects.filter(workflow=workflow).order_by(
            "display_order", "name"
        )

    @staticmethod
    def get_initial_state(workflow):
        """Get initial state for workflow"""
        try:
            return WorkflowState.objects.filter(
                workflow=workflow,
                is_initial=True,
            ).first()
        except WorkflowState.DoesNotExist:
            return None

    @staticmethod
    def get_final_states(workflow):
        """Get all final states for workflow"""
        return WorkflowState.objects.filter(
            workflow=workflow,
            is_final=True,
        )

    @staticmethod
    def get_states_by_category(workflow, category):
        """Get states by category"""
        return WorkflowState.objects.filter(
            workflow=workflow,
            category=category,
        ).order_by("display_order")

    @staticmethod
    def create(data):
        """Create new workflow state"""
        return WorkflowState.objects.create(**data)

    @staticmethod
    def update(state, data):
        """Update workflow state"""
        for key, value in data.items():
            setattr(state, key, value)
        state.save()
        return state

    @staticmethod
    def delete(state):
        """Delete workflow state"""
        state.delete()

    @staticmethod
    def reorder_states(workflow, state_order):
        """
        Reorder states in workflow
        state_order: list of (state_id, display_order) tuples
        """
        for state_id, order in state_order:
            WorkflowState.objects.filter(id=state_id, workflow=workflow).update(
                display_order=order
            )


class WorkflowTransitionRepository:
    """Repository for WorkflowTransition data access"""

    @staticmethod
    def get_by_id(transition_id):
        """Get workflow transition by ID"""
        try:
            return WorkflowTransition.objects.select_related(
                "workflow", "from_state", "to_state"
            ).get(id=transition_id)
        except WorkflowTransition.DoesNotExist:
            return None

    @staticmethod
    def get_workflow_transitions(workflow):
        """Get all transitions for a workflow"""
        return (
            WorkflowTransition.objects.filter(workflow=workflow)
            .select_related("from_state", "to_state")
            .order_by("display_order")
        )

    @staticmethod
    def get_available_transitions(from_state):
        """Get all available transitions from a state"""
        return (
            WorkflowTransition.objects.filter(from_state=from_state)
            .select_related("to_state")
            .order_by("display_order")
        )

    @staticmethod
    def get_transition(from_state, to_state):
        """Get specific transition between two states"""
        try:
            return WorkflowTransition.objects.get(
                from_state=from_state,
                to_state=to_state,
            )
        except WorkflowTransition.DoesNotExist:
            return None

    @staticmethod
    def can_transition(from_state, to_state):
        """Check if transition is allowed"""
        return WorkflowTransition.objects.filter(
            from_state=from_state,
            to_state=to_state,
        ).exists()

    @staticmethod
    def create(data):
        """Create new workflow transition"""
        return WorkflowTransition.objects.create(**data)

    @staticmethod
    def update(transition, data):
        """Update workflow transition"""
        for key, value in data.items():
            setattr(transition, key, value)
        transition.save()
        return transition

    @staticmethod
    def delete(transition):
        """Delete workflow transition"""
        transition.delete()


class WorkflowRuleRepository:
    """Repository for WorkflowRule data access"""

    @staticmethod
    def get_by_id(rule_id):
        """Get workflow rule by ID"""
        try:
            return WorkflowRule.objects.select_related("workflow", "created_by").get(
                id=rule_id
            )
        except WorkflowRule.DoesNotExist:
            return None

    @staticmethod
    def get_workflow_rules(workflow, active_only=True):
        """Get all rules for a workflow"""
        queryset = WorkflowRule.objects.filter(workflow=workflow)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.select_related("created_by").order_by("-priority", "name")

    @staticmethod
    def get_rules_by_trigger(workflow, trigger_type, active_only=True):
        """Get rules by trigger type"""
        queryset = WorkflowRule.objects.filter(
            workflow=workflow,
            trigger_type=trigger_type,
        )
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("-priority")

    @staticmethod
    def create(data):
        """Create new workflow rule"""
        return WorkflowRule.objects.create(**data)

    @staticmethod
    def update(rule, data):
        """Update workflow rule"""
        for key, value in data.items():
            setattr(rule, key, value)
        rule.save()
        return rule

    @staticmethod
    def delete(rule):
        """Delete workflow rule"""
        rule.delete()

    @staticmethod
    def increment_execution_count(rule):
        """Increment execution count for rule"""
        WorkflowRule.objects.filter(id=rule.id).update(
            execution_count=F("execution_count") + 1,
            last_executed_at=models.functions.Now(),
        )
