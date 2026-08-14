# Survey Accelerator MCP server

Survey Accelerator exposes its library to Claude as an MCP server, so you can
ask for surveys in plain language and have Claude read the actual instruments:

> "Find me high-quality surveys measuring household food security, then pull the
> exact question wording and draft a module I could adapt."

The server is mounted inside the existing backend at `/mcp`. There is no
separate service to deploy.

## Connecting

The endpoint is open: it works with no credentials at all. Adding your personal
key attributes your searches to you and removes the anonymous rate limit, so it
is worth the one extra flag.

### Get a personal key

Log in to Survey Accelerator, then:

```bash
curl -X POST https://survey.idinsight.io/api/users/mcp-key \
  -H "Authorization: Bearer <your login token>"
```

The key is shown once and only its hash is stored. Calling this again replaces
the old key, which is how you rotate a leaked one. `DELETE` on the same path
revokes it.

### Claude Code

```bash
claude mcp add --transport http survey-accelerator https://survey.idinsight.io/mcp \
  --header "Authorization: Bearer sa_your_key_here"
```

Without a key it still works, just anonymously:

```bash
claude mcp add --transport http survey-accelerator https://survey.idinsight.io/mcp
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "survey-accelerator": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "https://survey.idinsight.io/mcp",
        "--header", "Authorization: Bearer sa_your_key_here"
      ]
    }
  }
}
```

Drop the two `--header` arguments to connect anonymously.

### Running locally

```bash
cd backend
python main.py           # http://localhost:8000/mcp
```

## Tools

| Tool | What it does |
| --- | --- |
| `search_surveys` | Hybrid semantic + keyword search across every indexed page, LLM-reranked. Returns matching documents with the pages that matched and why. |
| `get_document_pages` | The verbatim text of specific pages. This is the follow-up to a search, and what lets Claude quote real question wording. |
| `get_document_text` | Reads a document straight through in page order, paginating via `next_start_page`. |
| `get_document_info` | Metadata and page count for one document. |
| `list_documents` | Browses the library by organization, survey type, country, region or year. |
| `list_filter_values` | The valid values for each filter. Worth calling before filtering, since the stored strings are exact. |

The intended flow is search first, then read. `search_surveys` returns
explanations of why each page matched, but those are summaries; the actual
survey text only comes from `get_document_pages` or `get_document_text`. Every
search result carries a `document_id` and `page_number` to feed straight into
the follow-up call.

## Deploying

Production is `survey.idinsight.io`, an EC2 instance in `ap-south-1`
(`ec2-65-2-55-67.ap-south-1.compute.amazonaws.com`) running the Docker Compose
stack in `deployment/docker-compose` behind Caddy.

The MCP server ships inside the backend image, so deploying it means
redeploying the backend. On that host:

```bash
cd <repo>
git pull

cd deployment/docker-compose
# -p sa is required. The live stack runs under the project name "sa"; without
# it compose builds a second stack and collides on the postgres port.
docker compose -p sa up -d --no-deps --build backend
docker compose -p sa restart caddy      # picks up the /mcp route
```

`startup.sh` runs `alembic upgrade head`, so migrations apply on container
start. Revision `b1c4e7a92f10` adds the personal key column and widens the
search log; both are additive and safe on a running database.

### Verifying

Caddy serves the React app as a catch-all, so **an unmatched path returns 200
with HTML rather than a 404**. A status code alone therefore proves nothing.

`/mcp` is a mounted ASGI app rather than a FastAPI route, so it never appears
in `openapi.json`. Do not look for it there. The only real check is calling it:

```bash
curl -s -X POST https://survey.idinsight.io/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | head -c 200
```

A JSON-RPC body listing six tools means it is live. Anything else tells you
where it broke:

| Response | Cause |
| --- | --- |
| `<!doctype html>` | Request fell through to the frontend catch-all; Caddy has no `/mcp` route. |
| `{"detail":"Not Found"}` | Reached the backend, but the MCP server did not mount. Check the startup log for `MCP server mounted at /mcp`. |
| `Invalid Host header` (421) | The hostname is missing from `MCP_ALLOWED_HOSTS`. |
| `401` | Only when `MCP_API_KEY` is set. An unrecognised personal key is not an error; the caller is treated as anonymous. |
| `307` | Redirect to the trailing-slash form; Caddy's `rewrite /mcp /mcp/` is missing. |

The server-side confirmation is the startup log:

```bash
docker logs sa-backend-1 2>&1 | grep "MCP server"
# MCP server mounted at /mcp (open; personal keys attribute searches, ...)
```

### If something goes wrong

Set `MCP_ENABLED=0` in `.backend.env` and restart the backend. The endpoint
disappears and the rest of the API is untouched; no rollback of the image is
needed.

Watch the first container start. This release moves uvicorn from 0.23.2 to
0.33.0, and production runs gunicorn with the `main.Worker` class built on
`uvicorn.workers`. That module still exists in 0.33 but is deprecated, and it
was removed in 0.34, so do not bump uvicorn further without moving to the
`uvicorn-worker` package first.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `MCP_ENABLED` | `1` | Set to `0` to drop the `/mcp` endpoint. |
| `MCP_API_KEY` | unset | Shared bearer token. Setting it closes the endpoint entirely and disables the per-user model below. Normally left unset. |
| `MCP_ANON_RATE_LIMIT` | `20` | Searches an unidentified caller gets per window, per IP. `0` removes the limit. |
| `MCP_ANON_RATE_WINDOW_MINUTES` | `60` | Length of that window. |
| `MCP_DEFAULT_MAX_RESULTS` | `10` | Results per search when the caller does not specify. |
| `MCP_MAX_RESULTS_LIMIT` | `25` | Hard cap on results per search. |
| `MCP_MAX_TEXT_CHARS` | `40000` | Character budget before `get_document_text` paginates. |
| `MCP_ALLOWED_HOSTS` | unset | Comma-separated hostnames this server answers on. **Required for any non-localhost deployment**: the transport's DNS rebinding protection allows only localhost by default and rejects everything else with 421. Production is `survey.idinsight.io`. |

### Access model

The endpoint is deliberately open. Anyone who can reach it can search, with or
without credentials. Three things follow from that:

- **Every search is logged**, identified or not, to `search_logs` with
  `source = 'mcp'` and the caller's IP. Usage is visible even when it cannot be
  attributed to a person.
- **A personal key attributes the search** to that Survey Accelerator account,
  so it also shows up in the user's own search history in the web app. A login
  JWT works as a credential too, but expires after a day, so the personal key is
  what to hand out.
- **Anonymous callers are rate limited** per IP (`MCP_ANON_RATE_LIMIT` per
  `MCP_ANON_RATE_WINDOW_MINUTES`). Identified callers are not limited. The count
  comes from the search log rather than process memory, so it holds across
  gunicorn workers instead of being multiplied by their number.

Setting `MCP_API_KEY` overrides all of this and turns the endpoint back into a
closed one gated by a single shared secret.

Every `search_surveys` call spends Cohere and OpenAI credits: one embedding, one
reranking call, and two calls per returned result. `MCP_MAX_RESULTS_LIMIT` bounds
a single call; the anonymous rate limit bounds an unidentified caller.

A one-click "Connect" button in the claude.ai web app would need an OAuth 2.1
layer, which this does not implement.

### Who has been using it

```sql
-- searches by person, MCP only
SELECT u.email, COUNT(*) AS searches, MAX(s.timestamp) AS last_used
FROM search_logs s LEFT JOIN users u ON u.user_id = s.user_id
WHERE s.source = 'mcp'
GROUP BY u.email ORDER BY searches DESC;
```

A null email is anonymous traffic; group those by `client_ip` to see whether it
is one heavy caller or many light ones.

## Design notes

- **Mounted, not standalone.** The MCP server shares the backend's database
  engine and calls `hybrid_search` directly, so search behaviour cannot drift
  from the web app.
- **Stateless sessions.** `stateless_http=True`, because the backend runs under
  gunicorn with several workers and requests are not pinned to one of them.
- **Highlighted PDFs are opt-in.** `search_surveys` accepts
  `include_highlighted_pdfs`, off by default since generating them roughly
  doubles the time a search takes.
- **Page text is extracted from the indexed chunk.** Chunks are stored as
  `METADATA / CONTEXT / RAW TEXT`; the tools return the `RAW TEXT` section, with
  the rest available via `include_context`.

## Smoke checks

```bash
curl -s https://survey.idinsight.io/api/openapi.json | grep -c mcp   # route registered?

curl -s -X POST https://survey.idinsight.io/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

With a token set, the same request without an `Authorization` header should
return 401. If any of these return HTML, the request reached the frontend
catch-all rather than the backend.
