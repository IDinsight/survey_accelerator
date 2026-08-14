"""MCP server package.

`mount_mcp(app)` attaches the MCP endpoint to the FastAPI application and
returns the lifespan context the session manager needs.
"""

import contextlib
import json
from typing import Any, AsyncIterator, Callable, Optional

from app.config import MCP_ANON_RATE_LIMIT, MCP_API_KEY
from app.utils import setup_logger

from .server import mcp

logger = setup_logger()

MCP_PATH = "/mcp"


class McpPathFix:
    """
    Let `/mcp` work as well as `/mcp/`.

    Starlette's Mount only matches the trailing-slash form and 307-redirects the
    bare path. Some MCP clients drop the POST body on redirect, so rewrite the
    path before routing rather than relying on the redirect.
    """

    def __init__(self, app: Any) -> None:
        """Wrap the downstream ASGI app."""
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        """Rewrite a bare /mcp path to /mcp/ before passing the request on."""
        if scope["type"] == "http":
            path = scope.get("path", "")
            # Behind a root_path (production runs with BACKEND_ROOT_PATH=/api)
            # the incoming path may or may not carry that prefix, so match both.
            root = scope.get("root_path", "") or ""
            if path == MCP_PATH or (root and path == f"{root}{MCP_PATH}"):
                fixed = path + "/"
                scope = dict(scope, path=fixed, raw_path=fixed.encode())
        await self.app(scope, receive, send)


async def _reject(send: Callable, status: int, message: str) -> None:
    """Send a JSON error response from raw ASGI."""
    body = json.dumps({"error": message}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b'Bearer realm="survey-accelerator"'),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


def _bearer(scope: Any) -> Optional[str]:
    """Pull the bearer credential off the request, if there is one."""
    for name, value in scope.get("headers", []):
        if name == b"authorization":
            return value.decode("latin-1").removeprefix("Bearer ").strip() or None
    return None


def _authorized(token: Optional[str]) -> bool:
    """
    Decide whether the request may proceed at all.

    With no shared token configured the endpoint is open to everyone; identity
    and rate limiting are handled per tool call instead. A configured shared
    token turns it back into a closed endpoint.
    """
    if not MCP_API_KEY:
        return True
    return token == MCP_API_KEY


@contextlib.asynccontextmanager
async def mcp_lifespan(_app: Any) -> AsyncIterator[None]:
    """
    Run the streamable HTTP session manager for the lifetime of the app.

    FastAPI takes its lifespan at construction time, before there is an app to
    mount onto, so this is separate from `mount_mcp`. The session manager is
    resolved when the lifespan actually runs, by which point `mount_mcp` has
    created it.
    """
    async with mcp.session_manager.run():
        yield


def mount_mcp(app: Any) -> None:
    """Mount the MCP endpoint on a FastAPI app."""
    # The session manager is created lazily on the first call to
    # streamable_http_app(); call it once here so `mcp.session_manager` exists,
    # then drive the ASGI handler directly (mounting the Starlette app instead
    # would nest the route at /mcp/mcp).
    mcp.streamable_http_app()

    async def mcp_asgi(scope: Any, receive: Any, send: Any) -> None:
        """Identify the caller, then hand off to the MCP transport."""
        if not _authorized(_bearer(scope)):
            await _reject(send, 401, "Invalid or missing bearer token.")
            return
        # Per-caller identity is resolved inside the tools from the request the
        # transport attaches to each message; see identity.py.
        await mcp.session_manager.handle_request(scope, receive, send)

    app.mount(MCP_PATH, mcp_asgi)
    app.add_middleware(McpPathFix)

    if MCP_API_KEY:
        logger.info("MCP server mounted at /mcp (shared bearer token required)")
    else:
        logger.info(
            "MCP server mounted at /mcp (open; personal keys attribute searches, "
            f"anonymous callers limited to {MCP_ANON_RATE_LIMIT} searches per window)"
        )


__all__ = ["mount_mcp", "mcp_lifespan", "mcp", "MCP_PATH"]
