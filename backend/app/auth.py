import os
from dataclasses import dataclass
from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import ActorRole


security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    role: ActorRole
    actor_id: str


def _tokens() -> dict:
    importer_token = os.getenv("SHIP_HOPPA_IMPORTER_TOKEN")
    admin_token = os.getenv("SHIP_HOPPA_ADMIN_TOKEN")
    production_mode = os.getenv("SHIP_HOPPA_ENV") == "production"
    if production_mode and (not importer_token or not admin_token):
        raise RuntimeError("SHIP_HOPPA_IMPORTER_TOKEN and SHIP_HOPPA_ADMIN_TOKEN must be set in production.")

    return {
        (importer_token or "shiphoppa-importer-dev"): Principal(
            role=ActorRole.importer,
            actor_id="dev-importer",
        ),
        (admin_token or "shiphoppa-admin-dev"): Principal(
            role=ActorRole.admin,
            actor_id="dev-admin",
        ),
    }


def require_roles(roles: Iterable[ActorRole]):
    allowed_roles = set(roles)

    def dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Principal:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )
        principal = _tokens().get(credentials.credentials)
        if not principal:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            )
        if principal.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation",
            )
        return principal

    return dependency


require_importer = require_roles([ActorRole.importer, ActorRole.admin])
require_admin = require_roles([ActorRole.admin])


def require_cron(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Principal:
    """Authorize a request from a scheduled cron caller (e.g. Railway cron)."""
    expected = os.getenv("SHIP_HOPPA_CRON_TOKEN") or "shiphoppa-cron-dev"
    if not credentials or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron token",
        )
    return Principal(role=ActorRole.system, actor_id="cron")


def require_inbound_webhook(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Principal:
    """Authorize an inbound email or partner webhook with a shared secret."""
    expected = os.getenv("SHIP_HOPPA_INBOUND_EMAIL_TOKEN") or "shiphoppa-inbound-dev"
    if not credentials or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid inbound webhook token",
        )
    return Principal(role=ActorRole.system, actor_id="inbound-webhook")
