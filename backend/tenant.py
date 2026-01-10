"""
Multi-tenant support via simple tenant codes.

Tenants are identified by a code passed in:
- Header: X-Tenant-ID
- Query param: tenant

No authentication - just simple separation for demo purposes.
"""

from typing import Annotated, Optional

from fastapi import Header, Query


def get_tenant_id(
    x_tenant_id: Annotated[Optional[str], Header()] = None,
    tenant: Annotated[Optional[str], Query()] = None,
) -> str:
    """
    Extract tenant ID from request.

    Priority:
    1. X-Tenant-ID header
    2. tenant query parameter
    3. Default to "default"

    Returns lowercase, alphanumeric tenant ID.
    """
    tenant_id = x_tenant_id or tenant or "default"

    # Sanitize: lowercase, alphanumeric + underscore only
    sanitized = "".join(c for c in tenant_id.lower() if c.isalnum() or c == "_")

    # Ensure not empty
    return sanitized if sanitized else "default"


# Type alias for dependency injection
TenantID = Annotated[str, get_tenant_id]
