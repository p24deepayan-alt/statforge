"""UUID generation for StatForge artifacts and sessions."""

import uuid


def new_id() -> str:
    """Generate a new UUIDv4 string."""
    return str(uuid.uuid4())
