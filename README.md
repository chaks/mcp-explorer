## 🔍 Why This Matters

[](#-why-this-matters)

When building AI-powered applications, **discovering and understanding available tools** is the first critical step. Most developers waste time:

*   Manually inspecting API documentation
*   Guessing at available endpoints and parameters
*   Writing boilerplate code to test each server

**MCP Explorer** solves this by providing **instant, structured visibility** into any MCP server's capabilities — so you can start integrating immediately.

## ⚡ Quick Start

[](#-quick-start)

```bash
git clone https://github.com/chaks/mcp-explorer.git
cd mcp-explorer
uv sync
```

✅ **Done!** You're ready to discover tools on any MCP server:

```bash
uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse
```

## 🧠 How It Works

[](#-how-it-works)

### The Magic Formula: **CONNECT → DISCOVER → INSPECT**

[](#the-magic-formula-connect--discover--inspect)

```
CONNECT → DISCOVER → INSPECT → ✅ INTEGRATE
   ↓           ↓            ↖
SSE Handshake  Tools List   JSON/Text
```

This streamlined workflow ensures:

*   **No guesswork**: Full protocol-compliant handshake with any MCP server
*   **Flexible output**: JSON output pipeable into `jq` for automation
*   **Human-readable**: Clean terminal rendering for quick inspection

### 🔧 Core Components

[](#-core-components)

#### **Full MCP Protocol Support**

[](#full-mcp-protocol-support)

Implements the complete MCP handshake sequence:

1.  Opens a streaming SSE connection to the server
2.  Captures the dynamically assigned session endpoint
3.  Sends an `initialize` handshake request
4.  Confirms with `notifications/initialized`
5.  Requests `tools/list` and parses the response
6.  Gracefully closes the connection

#### **Flexible Output Modes**

[](#flexible-output-modes)

*   **Default**: Compact JSON array for piping and automation
*   **`--detailed`**: Full tool schemas with descriptions, compatible with `jq`
*   **`--render`**: Human-readable formatted terminal output

#### **Multi-Server Discovery**

[](#multi-server-discovery)

Query multiple MCP servers in a single invocation — tools from all servers are combined into a unified output, or rendered with clear server groupings.

## 📊 Output Examples

[](#-output-examples)

### Quick list (default)

[](#quick-list-default)

```bash
$ uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse
```

```json
["search_documents", "create_ticket", "run_query"]
```

### Detailed schemas (with jq)

[](#detailed-schemas-with-jq)

```bash
$ uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse --detailed | jq '.[].name'
$ uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse --detailed | jq '.[] | select(.name | startswith("search_"))'
```

### Human-readable rendering

[](#human-readable-rendering)

```bash
$ uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse --render
```

Clean, formatted terminal output with proper descriptions and parameter details.

## ⚙️ Options

[](#️-options)

| Option | Description |
|---|---|
| `--url URL [URL ...]` | **Required.** One or more SSE endpoint URLs |
| `-d, --detailed` | Output full tool descriptions and input schemas as pretty-printed JSON |
| `-r, --render` | Output human-readable formatted text with rendered newlines |

### Multiple servers

[](#multiple-servers)

```bash
uv run list_mcp_tools.py \
  --url http://server-a:8080/mcp/sse \
  http://server-b:9090/mcp/sse
```

Tools from all servers are combined into a single output. With `--render`, each server's tools are grouped under a header.

## 📁 Project Structure

[](#-project-structure)

```
mcp-explorer/
├── list_mcp_tools.py       # Main CLI tool
├── pyproject.toml          # Python package metadata
├── uv.lock                 # Dependency lockfile
├── README.md               # This file
└── LICENSE                 # Apache 2.0 License
```

## 📋 Requirements

[](#-requirements)

*   Python 3.9+
*   [uv](https://docs.astral.sh/uv/) package manager

## 🔧 Troubleshooting

[](#-trroubleshooting)

### Common Issues & Solutions

[](#common-issues--solutions)

**❌ Connection refused**

*   ✅ Verify the MCP server is running and the URL is correct
*   ✅ Check firewall rules and network connectivity

**❌ Empty tool list**

*   ✅ Confirm the server supports the `tools/list` MCP endpoint
*   ✅ Try `--detailed` to see the raw response

**❌ uv not found**

*   ✅ Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
*   ✅ Verify: `uv --version`

## 🚀 Use Cases

[](#-use-cases)

| Scenario | Command |
|---|---|
| Quick tool inventory | `uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse` |
| API documentation generation | `uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse --detailed > tools.json` |
| Terminal inspection | `uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse --render` |
| Filter by prefix | `uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse --detailed \| jq '.[] \| select(.name \| startswith("search_"))'` |
| Multi-server audit | `uv run list_mcp_tools.py --url http://a:8080/mcp http://b:9090/mcp` |

## 📜 License

[](#-license)

Apache License 2.0 — See [LICENSE](LICENSE) for details.

* * *

✨ **Ready to discover any MCP server's capabilities in seconds?** ✨  
🚀 **Just run `uv run list_mcp_tools.py --url http://localhost:8080/mcp/sse` and start integrating today!**
