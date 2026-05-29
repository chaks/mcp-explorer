import argparse
import json
import signal
import sys
import threading
import time
import requests
from urllib.parse import urlparse

# Handle SIGPIPE so piping to jq or head doesn't raise BrokenPipeError
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# Global flags controlled by CLI options
SHOW_DETAILED = False
RENDER_TEXT = False

def log(message):
    """Pushes diagnostic text to stderr so stdout remains pure JSON for jq."""
    print(message, file=sys.stderr)

def format_tool_text(tools):
    """Render tool as human-readable text with real newlines in descriptions."""
    lines = []
    for tool in tools:
        name = tool.get("name", "(unnamed)")
        description = tool.get("description", "(no description)")
        lines.append(f"  \033[1m{name}\033[0m")
        desc_lines = description.split("\n")
        for i, dline in enumerate(desc_lines):
            if i == 0:
                lines.append(f"    {dline}")
            else:
                lines.append(f"    {dline}")
        if "inputSchema" in tool:
            schema = tool["inputSchema"]
            if "properties" in schema:
                props = schema["properties"]
                required = schema.get("required", [])
                lines.append(f"    Parameters:")
                for pname, pinfo in props.items():
                    req_marker = " (required)" if pname in required else ""
                    ptype = pinfo.get("type", "any")
                    pdesc = pinfo.get("description", "")
                    lines.append(f"      {pname}: {ptype}{req_marker} {pdesc}")
        lines.append("")
    return "\n".join(lines)

def query_tools(sse_url):
    """Connect to an SSE endpoint and return the list of tool dicts."""
    message_url_event = threading.Event()
    tools_received_event = threading.Event()
    session_closed = threading.Event()
    captured_url = None
    tools_result = [None]

    def sse_thread_target():
        nonlocal captured_url
        log(f"  Opening SSE stream: {sse_url}")

        endpoint_set = False
        try:
            with requests.get(sse_url, stream=True, timeout=15) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if session_closed.is_set():
                        break
                    if not line:
                        continue

                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data:"):
                        data_content = decoded_line.replace("data:", "").strip()

                        if not endpoint_set and not data_content.startswith("{"):
                            if data_content.startswith("/"):
                                parsed = urlparse(sse_url)
                                base = f"{parsed.scheme}://{parsed.netloc}"
                                captured_url = f"{base}{data_content}"
                            else:
                                captured_url = data_content

                            endpoint_set = True
                            log("  Session endpoint locked in.")
                            message_url_event.set()

                        elif data_content.startswith("{"):
                            try:
                                payload = json.loads(data_content)
                                if "result" in payload and "tools" in payload["result"]:
                                    tools_result[0] = payload["result"]["tools"]
                                    tools_received_event.set()
                                elif "error" in payload:
                                    log(f"  Server error: {payload['error']}")
                            except json.JSONDecodeError:
                                pass

        except Exception as e:
            if not session_closed.is_set():
                log(f"  Stream terminated: {e}")
        finally:
            message_url_event.set()
            tools_received_event.set()

    sse_thread = threading.Thread(target=sse_thread_target, daemon=True)
    sse_thread.start()

    if not message_url_event.wait(timeout=5) or not captured_url:
        log(f"  Timeout waiting for session from {sse_url}")
        session_closed.set()
        return None

    log(f"  Session at: {captured_url}")
    headers = {"Content-Type": "application/json"}

    try:
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "python-cli-client", "version": "1.0.0"}
            }
        }
        init_res = requests.post(captured_url, json=init_payload, headers=headers, timeout=5)
        if init_res.status_code not in [200, 202, 204]:
            log(f"  Init rejected: {init_res.status_code}")
            session_closed.set()
            return None
        log("  Initialized.")

        time.sleep(0.2)
        requests.post(captured_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers, timeout=5)

        log("  Requesting tools...")
        tools_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        requests.post(captured_url, json=tools_payload, headers=headers, timeout=5)

        if not tools_received_event.wait(timeout=5):
            log("  Timeout: no tools received.")

    except Exception as e:
        log(f"  Network error: {e}")
    finally:
        session_closed.set()

    return tools_result[0]

def format_url_label(url):
    """Short label from URL for multi-server output."""
    parsed = urlparse(url)
    label = parsed.netloc
    if parsed.path:
        label += parsed.path
    return label

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query tools from one or more MCP SSE Servers.")
    parser.add_argument(
        "-d", "--detailed",
        action="store_true",
        help="Include full tool descriptions, input schemas, and argument specifications (JSON output)."
    )
    parser.add_argument(
        "-r", "--render",
        action="store_true",
        help="Render tools as human-readable text with formatted output (newlines rendered in descriptions)."
    )
    parser.add_argument(
        "--url",
        nargs="+",
        default=["http://localhost:8080/mcp/sse"],
        help="One or more SSE endpoint URLs."
    )
    args = parser.parse_args()
    SHOW_DETAILED = args.detailed
    RENDER_TEXT = args.render

    all_tools = []
    for i, url in enumerate(args.url):
        if len(args.url) > 1:
            log(f"\n--- [{i+1}/{len(args.url)}] Server: {format_url_label(url)} ---")
        tools = query_tools(url)
        if tools:
            for tool in tools:
                tool["_server"] = url
            all_tools.extend(tools)
        else:
            log(f"  No tools from {url}")

    if not all_tools:
        log("No tools received from any server.")
        exit(1)

    if RENDER_TEXT:
        for i, url in enumerate(args.url):
            server_tools = [t for t in all_tools if t["_server"] == url]
            if not server_tools:
                continue
            if len(args.url) > 1:
                print(f"\n# {format_url_label(url)}\n")
            print(format_tool_text(server_tools))
    elif SHOW_DETAILED:
        tools_output = [{k: v for k, v in t.items() if k != "_server"} for t in all_tools]
        print(json.dumps(tools_output, indent=2))
    else:
        tool_names = [t.get("name") for t in all_tools if "name" in t]
        print(json.dumps(tool_names))
