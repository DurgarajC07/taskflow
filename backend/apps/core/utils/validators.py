"""
Validation utilities.
"""

from django.core.exceptions import ValidationError
import re


def validate_slug(value: str):
    """Validate slug format."""
    if not re.match(r"^[a-z0-9-]+$", value):
        raise ValidationError(
            "Slug must contain only lowercase letters, numbers, and hyphens."
        )


def validate_project_key(value: str):
    """Validate project key format."""
    if not re.match(r"^[A-Z0-9]{2,10}$", value):
        raise ValidationError("Project key must be 2-10 uppercase letters or numbers.")


def validate_hex_color(value: str):
    """Validate hex color code."""
    if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
        raise ValidationError("Color must be a valid hex code (e.g., #FF5733).")


def validate_timezone(value: str):
    """Validate timezone string."""
    import pytz

    if value not in pytz.all_timezones:
        raise ValidationError(f"Invalid timezone: {value}")


def validate_file_size(file, max_size_mb: int = 10):
    """
    Validate uploaded file size.

    Args:
        file: Uploaded file object
        max_size_mb: Maximum size in megabytes
    """
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"File size exceeds maximum allowed size of {max_size_mb}MB."
        )


def validate_file_extension(file, allowed_extensions: list):
    """
    Validate uploaded file extension.

    Args:
        file: Uploaded file object
        allowed_extensions: List of allowed extensions (e.g., ['pdf', 'docx'])
    """
    ext = file.name.split(".")[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File type .{ext} is not allowed. Allowed types: {", ".join(allowed_extensions)}'
        )
