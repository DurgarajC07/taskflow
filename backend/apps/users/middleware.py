"""
Middleware for tracking user activity.
"""

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware to track user's last activity.
    Updates last_activity timestamp on each authenticated request.
    """

    def process_request(self, request):
        """Process incoming request."""
        if request.user.is_authenticated:
            # Update last activity asynchronously to avoid blocking
            # In production, this could be done via background task
            try:
                if (
                    not request.user.last_activity
                    or (timezone.now() - request.user.last_activity).seconds > 300
                ):  # 5 minutes
                    request.user.update_last_activity()
            except Exception:
                # Silently fail to not break the request
                pass

        return None
