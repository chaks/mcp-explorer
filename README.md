# MCP Explorer

A lightweight CLI tool for discovering and inspecting tools exposed by a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) SSE server.

## Features

- Discovers tools from any MCP SSE server via the full MCP handshake protocol
- Supports querying multiple servers in a single invocation
- Outputs structured JSON (pipeable into `jq`) or human-readable formatted text
- Zero configuration — works out of the box with the default local endpoint

## Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/chaks/mcp-explorer.git
cd mcp-explorer
uv sync
```

## Usage

### Quick start

```bash
uv run list_mcp_tools.py
```

Lists tool names as a JSON array:

```json
["search_documents", "create_ticket", "run_query"]
```

### View tool details

```bash
uv run list_mcp_tools.py --detailed
```

Outputs the full tool schema as pretty-printed JSON, including descriptions and input schemas. Compatible with `jq`:

```bash
uv run list_mcp_tools.py --detailed | jq '.[].name'
uv run list_mcp_tools.py --detailed | jq '.[] | select(.name | startswith("search_"))'
```

### Human-readable output

```bash
uv run list_mcp_tools.py --render
```

Renders tool names, descriptions, and parameters in a formatted terminal layout with proper newline handling.

### Custom endpoint

```bash
uv run list_mcp_tools.py --url http://my-server:3000/mcp/sse
```

### Multiple servers

```bash
uv run list_mcp_tools.py \
  --url http://server-a:8080/mcp/sse \
  http://server-b:9090/mcp/sse
```

Tools from all servers are combined into a single output. With `--render`, each server's tools are grouped under a header.

## Options

```
--url URL [URL ...]  One or more SSE endpoint URLs (default: http://localhost:8080/mcp/sse)
-d, --detailed       Output full tool descriptions and input schemas as pretty-printed JSON
-r, --render         Output human-readable formatted text with rendered newlines
```

## Protocol

MCP Explorer follows the MCP specification:

1. Opens a streaming SSE connection to the server
2. Captures the dynamically assigned session endpoint
3. Sends an `initialize` handshake request
4. Sends the `notifications/initialized` confirmation
5. Requests `tools/list` and prints the response from the SSE stream
6. Closes the connection

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
