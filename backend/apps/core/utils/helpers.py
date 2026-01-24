"""
Utility functions and helpers.
"""

import re
from typing import Optional
from django.utils.text import slugify
import uuid


def generate_unique_slug(text: str, max_length: int = 50) -> str:
    """
    Generate a unique slug from text.

    Args:
        text: Text to slugify
        max_length: Maximum length of slug

    Returns:
        Unique slug string
    """
    base_slug = slugify(text)[:max_length]
    unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
    return unique_slug


def generate_project_key(name: str, existing_keys: Optional[list] = None) -> str:
    """
    Generate a unique project key from project name.
    Example: "My Project" -> "MP" or "MYP"

    Args:
        name: Project name
        existing_keys: List of existing keys to avoid duplicates

    Returns:
        Unique project key (2-5 uppercase letters)
    """
    # Remove special characters and split into words
    words = re.sub(r"[^a-zA-Z\s]", "", name).split()

    if not words:
        return "PROJ"

    # Try initials first
    key = "".join(word[0].upper() for word in words if word)

    # If too short, take first few letters of first word
    if len(key) < 2:
        key = name[:3].upper().replace(" ", "")

    # Limit to 5 characters
    key = key[:5]

    # Check for uniqueness
    if existing_keys and key in existing_keys:
        # Add number suffix
        counter = 1
        while f"{key}{counter}" in existing_keys:
            counter += 1
        key = f"{key}{counter}"

    return key


def calculate_percentage(part: int, total: int) -> int:
    """
    Calculate percentage safely.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage as integer (0-100)
    """
    if total == 0:
        return 0
    return int((part / total) * 100)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_file_size(bytes: int) -> str:
    """
    Format bytes to human-readable file size.

    Args:
        bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def parse_mentions(text: str) -> list:
    """
    Parse @mentions from text.

    Args:
        text: Text containing @mentions

    Returns:
        List of mentioned usernames
    """
    # Match @username pattern (alphanumeric and underscore)
    pattern = r"@(\w+)"
    mentions = re.findall(pattern, text)
    return list(set(mentions))  # Remove duplicates


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r"[^\w\s.-]", "", filename)
    filename = re.sub(r"\s+", "_", filename)
    return filename


def generate_file_path(instance, filename: str, subfolder: str = "") -> str:
    """
    Generate file storage path.

    Args:
        instance: Model instance
        filename: Original filename
        subfolder: Optional subfolder

    Returns:
        File path string
    """
    from datetime import datetime

    # Get file extension
    ext = filename.split(".")[-1] if "." in filename else ""

    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    # Build path
    year = datetime.now().year
    month = datetime.now().month

    if subfolder:
        return f"{subfolder}/{year}/{month:02d}/{unique_filename}"
    return f"{year}/{month:02d}/{unique_filename}"
