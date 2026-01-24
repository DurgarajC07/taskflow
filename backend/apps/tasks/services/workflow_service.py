"""
Workflow Service
Business logic for workflow operations.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.tasks.repositories import (
    WorkflowRepository,
    WorkflowStateRepository,
    WorkflowTransitionRepository,
    WorkflowRuleRepository,
)
from apps.tasks.models import Workflow, WorkflowState, WorkflowTransition, WorkflowRule


class WorkflowService:
    """Service for workflow business logic"""

    @staticmethod
    def create_workflow(organization, user, data):
        """Create new workflow"""
        # Validate default workflow uniqueness
        if data.get("is_default"):
            existing_default = WorkflowRepository.get_default_workflow(organization)
            if existing_default:
                raise ValidationError(
                    {"is_default": "Organization already has a default workflow"}
                )

        # Validate project belongs to organization
        project = data.get("project")
        if project and project.organization != organization:
            raise ValidationError(
                {"project": "Project must belong to same organization"}
            )

        with transaction.atomic():
            # Create workflow
            workflow_data = {
                **data,
                "organization": organization,
                "created_by": user,
            }
            workflow = WorkflowRepository.create(workflow_data)

        return workflow

    @staticmethod
    def update_workflow(workflow, user, data):
        """Update workflow"""
        # Prevent system workflow modification
        if workflow.is_system:
            raise PermissionDenied("Cannot modify system workflow")

        # Validate default workflow uniqueness
        if data.get("is_default") and not workflow.is_default:
            existing_default = WorkflowRepository.get_default_workflow(
                workflow.organization
            )
            if existing_default and existing_default.id != workflow.id:
                raise ValidationError(
                    {"is_default": "Organization already has a default workflow"}
                )

        with transaction.atomic():
            workflow = WorkflowRepository.update(workflow, data)

        return workflow

    @staticmethod
    def delete_workflow(workflow, soft=True):
        """Delete workflow"""
        # Prevent system workflow deletion
        if workflow.is_system:
            raise PermissionDenied("Cannot delete system workflow")

        # Check if workflow is in use by projects
        if workflow.project:
            raise ValidationError("Cannot delete workflow assigned to a project")

        with transaction.atomic():
            WorkflowRepository.delete(workflow, soft=soft)

    @staticmethod
    def duplicate_workflow(workflow, name, user):
        """Duplicate workflow with all states and transitions"""
        with transaction.atomic():
            # Create new workflow
            new_workflow = WorkflowRepository.create(
                {
                    "organization": workflow.organization,
                    "name": name,
                    "description": f"Copy of {workflow.name}",
                    "created_by": user,
                    "is_active": True,
                }
            )

            # Copy states
            state_mapping = {}  # old_id -> new_state
            for old_state in WorkflowStateRepository.get_workflow_states(workflow):
                new_state = WorkflowStateRepository.create(
                    {
                        "workflow": new_workflow,
                        "name": old_state.name,
                        "description": old_state.description,
                        "category": old_state.category,
                        "color": old_state.color,
                        "is_initial": old_state.is_initial,
                        "is_final": old_state.is_final,
                        "display_order": old_state.display_order,
                    }
                )
                state_mapping[old_state.id] = new_state

            # Copy transitions
            for old_transition in WorkflowTransitionRepository.get_workflow_transitions(
                workflow
            ):
                WorkflowTransitionRepository.create(
                    {
                        "workflow": new_workflow,
                        "from_state": state_mapping[old_transition.from_state.id],
                        "to_state": state_mapping[old_transition.to_state.id],
                        "name": old_transition.name,
                        "description": old_transition.description,
                        "conditions": old_transition.conditions,
                        "actions": old_transition.actions,
                        "requires_comment": old_transition.requires_comment,
                        "display_order": old_transition.display_order,
                    }
                )

            # Copy rules
            for old_rule in WorkflowRuleRepository.get_workflow_rules(
                workflow, active_only=False
            ):
                WorkflowRuleRepository.create(
                    {
                        "workflow": new_workflow,
                        "name": old_rule.name,
                        "description": old_rule.description,
                        "trigger_type": old_rule.trigger_type,
                        "trigger_config": old_rule.trigger_config,
                        "conditions": old_rule.conditions,
                        "actions": old_rule.actions,
                        "is_active": old_rule.is_active,
                        "priority": old_rule.priority,
                        "created_by": user,
                    }
                )

        return new_workflow

    @staticmethod
    def validate_workflow(workflow):
        """Validate workflow configuration"""
        errors = []

        # Get states
        states = WorkflowStateRepository.get_workflow_states(workflow)
        if not states:
            errors.append("Workflow must have at least one state")
            return errors

        # Check for initial state
        initial_states = [s for s in states if s.is_initial]
        if not initial_states:
            errors.append("Workflow must have an initial state")
        elif len(initial_states) > 1:
            errors.append("Workflow can only have one initial state")

        # Check for final state
        final_states = [s for s in states if s.is_final]
        if not final_states:
            errors.append("Workflow must have at least one final state")

        # Check state categories
        for state in states:
            if state.is_initial and state.is_final:
                errors.append(f"State '{state.name}' cannot be both initial and final")

        # Check transitions
        transitions = WorkflowTransitionRepository.get_workflow_transitions(workflow)
        if not transitions:
            errors.append("Workflow must have at least one transition")

        return errors


class WorkflowStateService:
    """Service for workflow state business logic"""

    @staticmethod
    def create_state(workflow, data):
        """Create new workflow state"""
        # Validate initial state uniqueness
        if data.get("is_initial"):
            existing_initial = WorkflowStateRepository.get_initial_state(workflow)
            if existing_initial:
                raise ValidationError(
                    {"is_initial": "Workflow already has an initial state"}
                )

        # Validate category
        if data.get("is_initial") and data.get("category") not in [
            WorkflowState.Category.TODO
        ]:
            raise ValidationError(
                {"category": "Initial state must be in TODO category"}
            )

        if data.get("is_final") and data.get("category") not in [
            WorkflowState.Category.DONE,
            WorkflowState.Category.CANCELLED,
        ]:
            raise ValidationError(
                {"category": "Final state must be in DONE or CANCELLED category"}
            )

        with transaction.atomic():
            state_data = {**data, "workflow": workflow}
            state = WorkflowStateRepository.create(state_data)

        return state

    @staticmethod
    def update_state(state, data):
        """Update workflow state"""
        # Validate initial state uniqueness
        if data.get("is_initial") and not state.is_initial:
            existing_initial = WorkflowStateRepository.get_initial_state(state.workflow)
            if existing_initial and existing_initial.id != state.id:
                raise ValidationError(
                    {"is_initial": "Workflow already has an initial state"}
                )

        # Validate category
        if data.get("is_initial") and data.get("category", state.category) not in [
            WorkflowState.Category.TODO
        ]:
            raise ValidationError(
                {"category": "Initial state must be in TODO category"}
            )

        if data.get("is_final") and data.get("category", state.category) not in [
            WorkflowState.Category.DONE,
            WorkflowState.Category.CANCELLED,
        ]:
            raise ValidationError(
                {"category": "Final state must be in DONE or CANCELLED category"}
            )

        with transaction.atomic():
            state = WorkflowStateRepository.update(state, data)

        return state

    @staticmethod
    def delete_state(state):
        """Delete workflow state"""
        # Check if state is in use by transitions
        outgoing = WorkflowTransitionRepository.get_available_transitions(state)
        incoming = state.incoming_transitions.all()

        if outgoing.exists() or incoming.exists():
            raise ValidationError(
                "Cannot delete state with transitions. Remove transitions first."
            )

        with transaction.atomic():
            WorkflowStateRepository.delete(state)

    @staticmethod
    def reorder_states(workflow, state_order):
        """
        Reorder states in workflow
        state_order: list of state IDs in desired order
        """
        with transaction.atomic():
            order_mapping = [
                (state_id, index) for index, state_id in enumerate(state_order)
            ]
            WorkflowStateRepository.reorder_states(workflow, order_mapping)


class WorkflowTransitionService:
    """Service for workflow transition business logic"""

    @staticmethod
    def create_transition(workflow, data):
        """Create new workflow transition"""
        from_state = data.get("from_state")
        to_state = data.get("to_state")

        # Validate states belong to same workflow
        if from_state.workflow != workflow or to_state.workflow != workflow:
            raise ValidationError("Both states must belong to the same workflow")

        # Validate no duplicate transition
        existing = WorkflowTransitionRepository.get_transition(from_state, to_state)
        if existing:
            raise ValidationError("Transition already exists between these states")

        # Validate not self-transition
        if from_state == to_state:
            raise ValidationError("Cannot create transition from state to itself")

        with transaction.atomic():
            transition_data = {**data, "workflow": workflow}
            transition = WorkflowTransitionRepository.create(transition_data)

        return transition

    @staticmethod
    def update_transition(transition, data):
        """Update workflow transition"""
        # Validate if changing states
        from_state = data.get("from_state", transition.from_state)
        to_state = data.get("to_state", transition.to_state)

        if from_state != transition.from_state or to_state != transition.to_state:
            # Check for duplicates
            existing = WorkflowTransitionRepository.get_transition(from_state, to_state)
            if existing and existing.id != transition.id:
                raise ValidationError("Transition already exists between these states")

            # Validate not self-transition
            if from_state == to_state:
                raise ValidationError("Cannot create transition from state to itself")

        with transaction.atomic():
            transition = WorkflowTransitionRepository.update(transition, data)

        return transition

    @staticmethod
    def delete_transition(transition):
        """Delete workflow transition"""
        with transaction.atomic():
            WorkflowTransitionRepository.delete(transition)

    @staticmethod
    def validate_transition(task, from_state, to_state, user, comment=None):
        """Validate if a transition can be performed"""
        # Check if transition exists
        transition = WorkflowTransitionRepository.get_transition(from_state, to_state)
        if not transition:
            return False, "Transition not allowed"

        # Check if comment required
        if transition.requires_comment and not comment:
            return False, "Comment required for this transition"

        # Check conditions
        if transition.conditions:
            # Evaluate conditions based on task state
            # This is a simplified example - implement your condition logic
            for condition in transition.conditions:
                if not WorkflowTransitionService._evaluate_condition(
                    task, condition, user
                ):
                    return False, f"Condition not met: {condition}"

        return True, "Transition allowed"

    @staticmethod
    def _evaluate_condition(task, condition, user):
        """Evaluate a single condition"""
        # Implement your condition evaluation logic here
        # Example conditions:
        # - assignee_required: task must have assignee
        # - due_date_required: task must have due date
        # - resolution_required: task must have resolution
        # - user_is_assignee: current user must be assignee
        # etc.

        condition_type = condition.get("type")
        condition_value = condition.get("value")

        if condition_type == "assignee_required":
            return task.assignee is not None

        if condition_type == "due_date_required":
            return task.due_date is not None

        if condition_type == "user_is_assignee":
            return task.assignee == user

        # Add more conditions as needed
        return True


class WorkflowRuleService:
    """Service for workflow rule business logic"""

    @staticmethod
    def create_rule(workflow, user, data):
        """Create new workflow rule"""
        with transaction.atomic():
            rule_data = {**data, "workflow": workflow, "created_by": user}
            rule = WorkflowRuleRepository.create(rule_data)

        return rule

    @staticmethod
    def update_rule(rule, data):
        """Update workflow rule"""
        with transaction.atomic():
            rule = WorkflowRuleRepository.update(rule, data)

        return rule

    @staticmethod
    def delete_rule(rule):
        """Delete workflow rule"""
        with transaction.atomic():
            WorkflowRuleRepository.delete(rule)

    @staticmethod
    def execute_rules(workflow, trigger_type, trigger_data):
        """Execute all rules for a given trigger"""
        rules = WorkflowRuleRepository.get_rules_by_trigger(
            workflow, trigger_type, active_only=True
        )

        executed_rules = []
        for rule in rules:
            # Check conditions
            if WorkflowRuleService._check_conditions(rule, trigger_data):
                # Execute actions
                WorkflowRuleService._execute_actions(rule, trigger_data)
                WorkflowRuleRepository.increment_execution_count(rule)
                executed_rules.append(rule)

        return executed_rules

    @staticmethod
    def _check_conditions(rule, trigger_data):
        """Check if all conditions are met"""
        if not rule.conditions:
            return True

        for condition in rule.conditions:
            if not WorkflowRuleService._evaluate_condition(condition, trigger_data):
                return False

        return True

    @staticmethod
    def _evaluate_condition(condition, trigger_data):
        """Evaluate a single condition"""
        # Implement your condition evaluation logic
        # Example: {"field": "priority", "operator": "equals", "value": "high"}
        field = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")

        actual_value = trigger_data.get(field)

        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "in":
            return actual_value in expected_value
        elif operator == "not_in":
            return actual_value not in expected_value
        elif operator == "greater_than":
            return actual_value > expected_value
        elif operator == "less_than":
            return actual_value < expected_value

        return True

    @staticmethod
    def _execute_actions(rule, trigger_data):
        """Execute rule actions"""
        task = trigger_data.get("task")

        for action in rule.actions:
            action_type = action.get("type")

            if action_type == "set_field":
                # Set task field
                field = action.get("field")
                value = action.get("value")
                setattr(task, field, value)
                task.save()

            elif action_type == "add_comment":
                # Add comment to task
                comment_text = action.get("text")
                # Implement comment creation logic

            elif action_type == "send_notification":
                # Send notification
                # Implement notification logic
                pass

            elif action_type == "assign_to":
                # Assign task to user
                user_id = action.get("user_id")
                # Implement assignment logic
                pass

            # Add more action types as needed
