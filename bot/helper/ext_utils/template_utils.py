from datetime import datetime


def apply_upload_template(template: str, user_id: int, username: str,
                          category: str = "", task_type: str = "mirror") -> str:
    """
    Apply template variables to create upload path.

    Supported variables:
    - {username}: Username of the user
    - {user_id}: Numeric user ID
    - {date}: Current date (YYYY-MM-DD)
    - {year}: Current year
    - {month}: Current month
    - {day}: Current day
    - {category}: Selected category
    - {task_type}: Task type (mirror/leech/clone)

    Args:
        template: The template string with variables
        user_id: User's Telegram ID
        username: User's username
        category: Category for organization
        task_type: Type of task

    Returns:
        Formatted path string
    """
    if not template:
        return ""

    now = datetime.now()

    # Sanitize username for filesystem safety
    safe_username = (username or str(user_id)).replace("/", "_").replace("\\", "_")
    safe_category = (category or "Uncategorized").replace("/", "_").replace("\\", "_")

    replacements = {
        "{username}": safe_username,
        "{user_id}": str(user_id),
        "{date}": now.strftime("%Y-%m-%d"),
        "{year}": now.strftime("%Y"),
        "{month}": now.strftime("%m"),
        "{day}": now.strftime("%d"),
        "{category}": safe_category,
        "{task_type}": task_type,
    }

    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)

    # Clean up path
    result = result.rstrip("/").replace("//", "/")

    return result
