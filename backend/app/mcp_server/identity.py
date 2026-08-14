"""Caller identity and anonymous rate limiting for the MCP server.

The endpoint is open: a caller with no credentials is served, just recorded as
anonymous and held to a rate limit. A caller presenting a personal key (or a
login token) is attributed to their Survey Accelerator account, so their
searches land in their own search history.

Identity is resolved once per request in the ASGI wrapper and carried to the
tools in a context variable, because MCP tools are plain functions with no
access to the underlying request.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from mcp.server.lowlevel.server import request_ctx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import JWT_ALGORITHM, JWT_SECRET_KEY
from app.config import (
    MCP_ANON_RATE_LIMIT,
    MCP_ANON_RATE_WINDOW_MINUTES,
    MCP_KEY_PREFIX,
)
from app.search.models import SearchLogDB
from app.users.models import UsersDB
from app.utils import get_key_hash, setup_logger

logger = setup_logger()

# Personal keys carry a prefix so they are recognisable in a config file and
# distinguishable from a login JWT at a glance.
KEY_PREFIX = MCP_KEY_PREFIX


def _http_request() -> Any:
    """
    Get the HTTP request behind the current tool call.

    The transport attaches it to the message metadata and the low-level server
    exposes it through `request_ctx`, which is set inside the task that runs the
    tool. A context variable of our own set in the ASGI wrapper would not work:
    the session manager's task group is created at startup, so per-request
    context does not reach the handler.

    Note this relies on `json_response=True`; the transport only attaches the
    request on that path (or with an event store configured).
    """
    try:
        ctx = request_ctx.get()
    except LookupError:
        return None
    return getattr(ctx, "request", None)


def caller_token() -> Optional[str]:
    """The bearer credential presented with the current tool call, if any."""
    request = _http_request()
    if request is None:
        return None
    header = request.headers.get("authorization")
    if not header:
        return None
    return header.removeprefix("Bearer ").strip() or None


def caller_ip() -> Optional[str]:
    """
    The current request's client IP, if known.

    Behind Caddy every connection appears to come from the proxy, so the
    forwarded header is what identifies the real caller.
    """
    request = _http_request()
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Left-most entry is the original client.
        return forwarded.split(",")[0].strip() or None
    client = getattr(request, "client", None)
    return client.host if client else None


async def resolve_caller(session: AsyncSession) -> Optional[UsersDB]:
    """
    Identify the caller, or return None for an anonymous one.

    Tries the personal key first since that is the credential we hand out, then
    falls back to a login token so an existing session works without minting a
    key. Neither failing is an error: the caller is simply anonymous.
    """
    token = caller_token()
    if not token:
        return None

    if token.startswith(KEY_PREFIX):
        result = await session.execute(
            select(UsersDB).where(UsersDB.mcp_key_hash == get_key_hash(token))
        )
        return result.scalars().first()

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None
    result = await session.execute(select(UsersDB).where(UsersDB.user_id == user_id))
    return result.scalars().first()


async def anonymous_quota_exceeded(session: AsyncSession) -> bool:
    """
    Check whether this anonymous IP has used up its allowance.

    Counted from the search log rather than in process memory, so the limit
    holds across all gunicorn workers instead of being multiplied by their
    number. Callers who identify themselves are never rate limited.
    """
    if MCP_ANON_RATE_LIMIT <= 0:
        return False

    ip = caller_ip()
    if not ip:
        # Without an IP there is nothing to count against, so let it through
        # rather than block every caller behind an unknown proxy.
        return False

    since = datetime.now(timezone.utc) - timedelta(minutes=MCP_ANON_RATE_WINDOW_MINUTES)
    result = await session.execute(
        select(func.count())
        .select_from(SearchLogDB)
        .where(
            SearchLogDB.source == "mcp",
            SearchLogDB.user_id.is_(None),
            SearchLogDB.client_ip == ip,
            SearchLogDB.timestamp >= since,
        )
    )
    used = int(result.scalar() or 0)
    if used >= MCP_ANON_RATE_LIMIT:
        logger.warning(f"MCP: anonymous rate limit hit for {ip} ({used} searches)")
        return True
    return False


def rate_limit_message() -> str:
    """Explain the anonymous limit and how to lift it."""
    return (
        f"Anonymous rate limit reached ({MCP_ANON_RATE_LIMIT} searches per "
        f"{MCP_ANON_RATE_WINDOW_MINUTES} minutes). Add your personal Survey "
        "Accelerator key to the connection to remove this limit -- see MCP.md, "
        "or ask the Survey Accelerator team for one."
    )
