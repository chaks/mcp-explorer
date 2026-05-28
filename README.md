# MCP Explorer

A CLI tool for discovering and inspecting tools exposed by a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) SSE server.

## Overview

`list_mcp_tools.py` connects to a running MCP server via its SSE endpoint, performs the full MCP handshake protocol, and returns the list of available tools as JSON. Output is written to stdout (for piping into `jq`), while diagnostic messages go to stderr.

## Requirements

- Python 3.6+
- `requests` library

```bash
pip install requests
```

## Usage

Point the script at your MCP server's SSE endpoint by editing the `sse_url` variable at the top of the file (default: `http://localhost:8080/mcp/sse`).

### List tool names (default)

```bash
python list_mcp_tools.py
```

Output (stdout):

```json
["tool_one", "tool_two", "tool_three"]
```

### List full tool details

```bash
python list_mcp_tools.py --detailed
```

Output (stdout):

```json
[
  {
    "name": "tool_one",
    "description": "Does something useful",
    "inputSchema": { ... }
  }
]
```

### Pipe to jq

```bash
python list_mcp_tools.py | jq '.[]'
python list_mcp_tools.py -d | jq '.[].name'
```

## How It Works

1. Opens a streaming SSE connection to the MCP server
2. Captures the dynamically assigned session endpoint from the SSE stream
3. Sends an MCP `initialize` handshake request
4. Sends an `notifications/initialized` confirmation
5. Requests `tools/list` and prints the response received on the SSE stream
6. Closes the connection

## Configuration

| Variable | Default | Description |
|---|---|---|
| `sse_url` | `http://localhost:8080/mcp/sse` | MCP server SSE endpoint |

## CLI Flags

| Flag | Description |
|---|---|
| `-d`, `--detailed` | Include full tool descriptions, input schemas, and argument specifications |
