"""
Automation Repositories
Repositories for Automation, Webhook, and ApiKey models.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Q, F
from django.utils import timezone
from apps.core.repositories.base import OrganizationRepository
from apps.tasks.models import (
    Automation,
    AutomationLog,
    Webhook,
    WebhookDelivery,
    ApiKey,
)


class AutomationRepository(OrganizationRepository):
    """
    Repository for Automation model.
    """

    def __init__(self):
        super().__init__(Automation)

    def get_active_automations(self, organization_id=None, project_id=None):
        """Get active automations"""
        filters = {"is_active": True}
        if organization_id:
            filters["organization_id"] = organization_id
        if project_id:
            filters["project_id"] = project_id

        return self.filter(**filters).order_by("-priority", "name")

    def get_by_trigger(self, trigger_type, organization_id=None, project_id=None):
        """Get automations by trigger type"""
        filters = {"is_active": True, "trigger_type": trigger_type}
        if organization_id:
            filters["organization_id"] = organization_id
        if project_id:
            filters["project_id"] = project_id

        return self.filter(**filters).order_by("-priority")

    def get_project_automations(self, project_id):
        """Get automations for a project"""
        return self.filter(project_id=project_id).order_by("-priority", "name")

    def get_organization_automations(self, organization_id):
        """Get organization-wide automations"""
        return self.filter(
            organization_id=organization_id,
            project_id__isnull=True,
        ).order_by("-priority", "name")

    def get_automation_statistics(self, automation_id):
        """Get automation execution statistics"""
        automation = self.get_by_id(automation_id)
        if not automation:
            return None

        success_rate = 0
        if automation.execution_count > 0:
            success_rate = round(
                (automation.success_count / automation.execution_count) * 100, 1
            )

        return {
            "automation": automation,
            "executions": automation.execution_count,
            "successes": automation.success_count,
            "failures": automation.failure_count,
            "success_rate": success_rate,
            "last_executed": automation.last_executed_at,
        }


class AutomationLogRepository(OrganizationRepository):
    """
    Repository for AutomationLog model.
    """

    def __init__(self):
        super().__init__(AutomationLog)

    def get_automation_logs(self, automation_id, status=None, limit=100):
        """Get logs for an automation"""
        filters = {"automation_id": automation_id}
        if status:
            filters["status"] = status

        return self.filter(**filters).order_by("-created_at")[:limit]

    def get_failed_logs(self, automation_id):
        """Get failed execution logs"""
        return self.get_automation_logs(
            automation_id, status=AutomationLog.Status.FAILED
        )

    def create_log(
        self,
        automation_id,
        status,
        trigger_data,
        conditions_met=False,
        actions_performed=None,
        error_message="",
        execution_time_ms=0,
    ):
        """Create automation log entry"""
        return self.create(
            automation_id=automation_id,
            status=status,
            trigger_data=trigger_data,
            conditions_met=conditions_met,
            actions_performed=actions_performed or [],
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

    def cleanup_old_logs(self, days=90):
        """Delete old logs"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_logs = self.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        return count


class WebhookRepository(OrganizationRepository):
    """
    Repository for Webhook model.
    """

    def __init__(self):
        super().__init__(Webhook)

    def get_active_webhooks(self, organization_id=None, project_id=None):
        """Get active webhooks"""
        filters = {"is_active": True}
        if organization_id:
            filters["organization_id"] = organization_id
        if project_id:
            filters["project_id"] = project_id

        return self.filter(**filters).order_by("name")

    def get_webhooks_for_event(self, event_type, organization_id=None, project_id=None):
        """Get webhooks subscribed to an event"""
        filters = {"is_active": True}
        if organization_id:
            filters["organization_id"] = organization_id
        if project_id:
            filters["project_id"] = project_id

        # Filter webhooks that have this event in their events list or have "*" (all events)
        webhooks = self.filter(**filters)
        matching_webhooks = []

        for webhook in webhooks:
            if "*" in webhook.events or event_type in webhook.events:
                matching_webhooks.append(webhook)

        return matching_webhooks

    def get_project_webhooks(self, project_id):
        """Get webhooks for a project"""
        return self.filter(project_id=project_id).order_by("name")

    def get_organization_webhooks(self, organization_id):
        """Get organization-wide webhooks"""
        return self.filter(
            organization_id=organization_id,
            project_id__isnull=True,
        ).order_by("name")

    def get_webhook_statistics(self, webhook_id):
        """Get webhook delivery statistics"""
        webhook = self.get_by_id(webhook_id)
        if not webhook:
            return None

        success_rate = 0
        if webhook.delivery_count > 0:
            success_rate = round(
                (webhook.success_count / webhook.delivery_count) * 100, 1
            )

        return {
            "webhook": webhook,
            "deliveries": webhook.delivery_count,
            "successes": webhook.success_count,
            "failures": webhook.failure_count,
            "success_rate": success_rate,
            "last_triggered": webhook.last_triggered_at,
            "last_success": webhook.last_success_at,
        }


class WebhookDeliveryRepository(OrganizationRepository):
    """
    Repository for WebhookDelivery model.
    """

    def __init__(self):
        super().__init__(WebhookDelivery)

    def get_webhook_deliveries(self, webhook_id, status=None, limit=100):
        """Get deliveries for a webhook"""
        filters = {"webhook_id": webhook_id}
        if status:
            filters["status"] = status

        return self.filter(**filters).order_by("-created_at")[:limit]

    def get_failed_deliveries(self, webhook_id):
        """Get failed deliveries"""
        return self.get_webhook_deliveries(
            webhook_id, status=WebhookDelivery.Status.FAILED
        )

    def get_pending_retries(self, limit=100):
        """Get deliveries pending retry"""
        return self.filter(
            status=WebhookDelivery.Status.RETRYING,
            next_retry_at__lte=timezone.now(),
        ).order_by("next_retry_at")[:limit]

    def create_delivery(self, webhook_id, event_type, payload):
        """Create webhook delivery entry"""
        return self.create(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            status=WebhookDelivery.Status.PENDING,
        )

    def mark_as_success(
        self,
        delivery_id,
        status_code,
        response_body,
        response_headers,
        delivery_time_ms,
    ):
        """Mark delivery as successful"""
        delivery = self.get_by_id(delivery_id)
        if delivery:
            delivery.status = WebhookDelivery.Status.SUCCESS
            delivery.status_code = status_code
            delivery.response_body = response_body
            delivery.response_headers = response_headers
            delivery.delivery_time_ms = delivery_time_ms
            delivery.save(
                update_fields=[
                    "status",
                    "status_code",
                    "response_body",
                    "response_headers",
                    "delivery_time_ms",
                ]
            )
            return delivery
        return None

    def mark_as_failed(self, delivery_id, error_message, status_code=None):
        """Mark delivery as failed"""
        delivery = self.get_by_id(delivery_id)
        if delivery:
            delivery.status = WebhookDelivery.Status.FAILED
            delivery.error_message = error_message
            delivery.status_code = status_code
            delivery.retry_count += 1
            delivery.save(
                update_fields=["status", "error_message", "status_code", "retry_count"]
            )
            return delivery
        return None

    def schedule_retry(self, delivery_id, retry_after_minutes=5):
        """Schedule delivery for retry"""
        delivery = self.get_by_id(delivery_id)
        if delivery:
            delivery.status = WebhookDelivery.Status.RETRYING
            delivery.next_retry_at = timezone.now() + timedelta(
                minutes=retry_after_minutes
            )
            delivery.save(update_fields=["status", "next_retry_at"])
            return delivery
        return None

    def cleanup_old_deliveries(self, days=90):
        """Delete old delivery records"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_deliveries = self.filter(
            created_at__lt=cutoff_date,
            status__in=[WebhookDelivery.Status.SUCCESS, WebhookDelivery.Status.FAILED],
        )
        count = old_deliveries.count()
        old_deliveries.delete()
        return count


class ApiKeyRepository(OrganizationRepository):
    """
    Repository for ApiKey model.
    """

    def __init__(self):
        super().__init__(ApiKey)

    def get_user_api_keys(self, user_id, is_active=None):
        """Get API keys for a user"""
        filters = {"user_id": user_id}
        if is_active is not None:
            filters["is_active"] = is_active

        return self.filter(**filters).order_by("-created_at")

    def get_by_key_prefix(self, key_prefix):
        """Get API key by prefix"""
        return self.filter(key_prefix=key_prefix).first()

    def verify_key(self, key_hash):
        """Verify an API key"""
        api_key = self.filter(key_hash=key_hash, is_active=True).first()
        if api_key and not api_key.is_expired():
            return api_key
        return None

    def revoke_key(self, api_key_id):
        """Revoke an API key"""
        api_key = self.get_by_id(api_key_id)
        if api_key:
            api_key.is_active = False
            api_key.save(update_fields=["is_active"])
            return api_key
        return None

    def cleanup_expired_keys(self):
        """Delete expired inactive keys"""
        expired_keys = self.filter(
            is_active=False,
            expires_at__lt=timezone.now(),
        )
        count = expired_keys.count()
        expired_keys.delete()
        return count

    def get_api_key_statistics(self, api_key_id):
        """Get API key usage statistics"""
        api_key = self.get_by_id(api_key_id)
        if not api_key:
            return None

        return {
            "api_key": api_key,
            "usage_count": api_key.usage_count,
            "last_used": api_key.last_used_at,
            "is_expired": api_key.is_expired(),
            "is_active": api_key.is_active,
            "created_at": api_key.created_at,
        }
