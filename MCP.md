# Survey Accelerator MCP server

Survey Accelerator exposes its library to Claude as an MCP server, so you can
ask for surveys in plain language and have Claude read the actual instruments:

> "Find me high-quality surveys measuring household food security, then pull the
> exact question wording and draft a module I could adapt."

The server is mounted inside the existing backend at `/mcp`. There is no
separate service to deploy.

## Connecting

### Claude Code

```bash
claude mcp add --transport http survey-accelerator https://survey.idinsight.io/mcp
```

With a bearer token configured:

```bash
claude mcp add --transport http survey-accelerator https://survey.idinsight.io/mcp \
  --header "Authorization: Bearer <MCP_API_KEY>"
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
        "--header", "Authorization: Bearer <MCP_API_KEY>"
      ]
    }
  }
}
```

Drop the two `--header` arguments if no token is set.

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

# Set the shared token before building. This file is gitignored and exists
# only on the server.
echo "MCP_API_KEY=$(openssl rand -hex 32)" >> deployment/docker-compose/.backend.env

cd deployment/docker-compose
docker compose up -d --build backend   # --build is required: requirements.txt changed
docker compose restart caddy           # picks up the new /mcp route
```

No database migration is needed. This release adds no columns, only optional
fields on an existing response schema.

### Verifying

Caddy serves the React app as a catch-all, so **an unmatched path returns 200
with HTML rather than a 404**. A status code alone therefore proves nothing.
Check the backend's own route table instead:

```bash
# 0 before the deploy, non-zero after
curl -s https://survey.idinsight.io/api/openapi.json | grep -c mcp
```

Then confirm the endpoint answers JSON rather than the SPA:

```bash
curl -s -X POST https://survey.idinsight.io/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | head -c 200
```

A JSON-RPC body listing six tools means it is live. HTML starting with
`<!doctype html>` means the request fell through to the frontend, so the
backend did not pick up the new route.

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
| `MCP_API_KEY` | unset | Shared bearer token. **Unset means the endpoint is open to anyone who can reach the backend.** |
| `MCP_DEFAULT_MAX_RESULTS` | `10` | Results per search when the caller does not specify. |
| `MCP_MAX_RESULTS_LIMIT` | `25` | Hard cap on results per search. |
| `MCP_MAX_TEXT_CHARS` | `40000` | Character budget before `get_document_text` paginates. |

### A note on cost and access

Every `search_surveys` call spends Cohere and OpenAI credits: one embedding, one
reranking call, and two calls per returned result. `MCP_MAX_RESULTS_LIMIT` is
what bounds a single call.

Set `MCP_API_KEY` in any internet-facing deployment. Without it the endpoint is
unauthenticated, and anyone who finds the URL can run searches against your API
budget. The backend logs a warning at startup when it starts up in that state.

The token is a single shared secret rather than per-user auth, which means MCP
searches are not attributed to a user and are not written to `search_logs` (that
table requires a user id). If you need per-user attribution or a one-click
"Connect" button in the claude.ai web app, that needs an OAuth 2.1 layer, which
this does not implement.

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
