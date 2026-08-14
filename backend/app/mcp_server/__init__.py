"""MCP server package.

`mount_mcp(app)` attaches the MCP endpoint to the FastAPI application and
returns the lifespan context the session manager needs.
"""

import contextlib
import json
from typing import Any, AsyncIterator, Callable

from app.config import MCP_API_KEY
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
        if scope["type"] == "http" and scope["path"] == MCP_PATH:
            scope = dict(scope, path=MCP_PATH + "/", raw_path=(MCP_PATH + "/").encode())
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


def _authorized(scope: Any) -> bool:
    """Check the shared bearer token when one is configured."""
    if not MCP_API_KEY:
        return True
    for name, value in scope.get("headers", []):
        if name == b"authorization":
            token = value.decode("latin-1").removeprefix("Bearer ").strip()
            return token == MCP_API_KEY
    return False


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
        """Gate on the bearer token, then hand off to the MCP transport."""
        if not _authorized(scope):
            await _reject(send, 401, "Invalid or missing bearer token.")
            return
        await mcp.session_manager.handle_request(scope, receive, send)

    app.mount(MCP_PATH, mcp_asgi)
    app.add_middleware(McpPathFix)

    if MCP_API_KEY:
        logger.info("MCP server mounted at /mcp (bearer token required)")
    else:
        logger.warning(
            "MCP server mounted at /mcp with NO authentication. "
            "Set MCP_API_KEY to require a bearer token."
        )


__all__ = ["mount_mcp", "mcp_lifespan", "mcp", "MCP_PATH"]
