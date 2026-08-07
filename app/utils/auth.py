from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.exceptions.exceptions import ForbiddenException
import logging
from typing import Dict, List, Callable

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()

# ---------------------------------------------------------------------------
# Core identity
# ---------------------------------------------------------------------------

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Dict:
    """Decode the bearer token into the JWT claims dict."""
    return decode_access_token(credentials.credentials)


def require_login(current_user: dict = Depends(get_current_user)) -> dict:
    """Any authenticated user, no further checks. Single chokepoint everything else depends on."""
    return current_user


# ---------------------------------------------------------------------------
# Permission-based checks — PRIMARY authorization mechanism.
# Use these directly in routes: Depends(require_permission(Permissions.MANAGE_USERS))
# ---------------------------------------------------------------------------

def require_permission(permission: str) -> Callable:
    def _check(current_user: dict = Depends(require_login)) -> dict:
        perms = current_user.get("permissions", [])
        if "*" in perms or permission in perms:
            return current_user
        logger.warning(f'Permission "{permission}" denied for user {current_user.get("sub")}')
        raise ForbiddenException(f"Permission required: {permission}")
    return _check






def require_any_permission(permissions: List[str]) -> Callable:
    """Allow access if user has ANY of the listed permissions."""
    def _check(current_user: dict = Depends(require_login)) -> dict:
        perms = current_user.get("permissions", [])
        if "*" in perms or any(p in perms for p in permissions):
            return current_user
        logger.warning(f'None of {permissions} found for user {current_user.get("sub")}')
        raise ForbiddenException(f"One of these permissions required: {permissions}")
    return _check


def require_all_permissions(permissions: List[str]) -> Callable:
    """User must have ALL listed permissions."""
    def _check(current_user: dict = Depends(require_login)) -> dict:
        perms = current_user.get("permissions", [])
        if "*" in perms or all(p in perms for p in permissions):
            return current_user
        logger.warning(f'Not all of {permissions} found for user {current_user.get("sub")}')
        raise ForbiddenException(f"All of these permissions required: {permissions}")
    return _check


# ---------------------------------------------------------------------------
# Non-permission identity checks — kept because they check something a
# permission code can't express (a linked staff record, a platform-level flag).
# ---------------------------------------------------------------------------

def require_staff(current_user: dict = Depends(require_login)) -> dict:
    """User must have a linked staff record (not just a login)."""
    if not current_user.get("staff_id"):
        raise ForbiddenException("Staff access required.")
    return current_user


def require_superuser(current_user: dict = Depends(require_login)) -> Dict:
    """
    """
    if current_user.get("role") != "superuser":
        raise ForbiddenException("Superuser access required.")
    return current_user


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def require_admin(current_user: Dict = Depends(require_login)) -> Dict:
    role = current_user.get("role")
    if role not in ["admin", "superuser", "manager"]:
        logger.warning(f'Admin access denied for user {current_user.get("sub")}')
        raise ForbiddenException("Admin access required.")
    return current_user


def require_manager(current_user: dict = Depends(require_login)) -> dict:
    role = current_user.get("role")
    if role not in ["manager", "admin", "superuser"]:
        logger.warning(f'Manager access denied for user {current_user.get("sub")}')
        raise ForbiddenException("Manager access required.")
    return current_user


def require_employee(current_user: Dict = Depends(require_login)) -> Dict:
    """Alias for require_login — no additional check. Prefer require_login directly."""
    return current_user