import argparse
import json
import signal
import sys
import threading
import time
import requests

# Handle SIGPIPE so piping to jq or head doesn't raise BrokenPipeError
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

sse_url = "http://localhost:8080/mcp/sse"

# Threading synchronizers
message_url_event = threading.Event()
tools_received_event = threading.Event()
session_closed = threading.Event()
captured_url = None

# Global flags controlled by CLI options
SHOW_DETAILED = False
RENDER_TEXT = False

def log(message):
    """Pushes diagnostic text to stderr so stdout remains pure JSON for jq."""
    print(message, file=sys.stderr)

def format_tool_text(tools):
    """Render tools as human-readable text with real newlines in descriptions."""
    lines = []
    for tool in tools:
        name = tool.get("name", "(unnamed)")
        description = tool.get("description", "(no description)")
        lines.append(f"  \033[1m{name}\033[0m")
        # Replace escaped \n with real newlines and indent continuation lines
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
        lines.append("")  # blank line between tools
    return "\n".join(lines)

def hold_sse_stream_open():
    global captured_url
    log("1. [Background Thread] Opening live SSE stream connection...")

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
                            captured_url = f"http://localhost:8080{data_content}"
                        else:
                            captured_url = data_content

                        endpoint_set = True
                        log("-> [Background Thread] Session endpoint locked in.")
                        message_url_event.set()

                    elif data_content.startswith("{"):
                        try:
                            payload = json.loads(data_content)
                            if "result" in payload and "tools" in payload["result"]:
                                tools = payload["result"]["tools"]

                                # Apply output formatting based on CLI options
                                if RENDER_TEXT:
                                    print(format_tool_text(tools))
                                elif SHOW_DETAILED:
                                    print(json.dumps(tools, indent=2))
                                else:
                                    tool_names = [t.get("name") for t in tools if "name" in t]
                                    print(json.dumps(tool_names))

                                tools_received_event.set()
                            elif "error" in payload:
                                log(f"\n-> [Background Thread] Server Protocol Error: {payload['error']}")
                        except json.JSONDecodeError:
                            pass

    except Exception as e:
        if not session_closed.is_set():
            log(f"-> [Background Thread] Stream connection terminated: {e}")
    finally:
        message_url_event.set()
        tools_received_event.set()

# --- Main Thread ---

if __name__ == "__main__":
    # Configure Command Line Options
    parser = argparse.ArgumentParser(description="Query tools from an MCP SSE Server.")
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
    args = parser.parse_args()
    SHOW_DETAILED = args.detailed
    RENDER_TEXT = args.render

    # Start the event loop stream listener
    sse_thread = threading.Thread(target=hold_sse_stream_open, daemon=True)
    sse_thread.start()

    log("Waiting for server to assign dynamic session ID...")
    if not message_url_event.wait(timeout=5) or not captured_url:
        log("Error: Timed out waiting for the server to establish an active session.")
        exit(1)

    log(f"\n2. [Main Thread] Session alive. Multiplexing handshakes at: {captured_url}")
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
            log(f"Initialization handshake rejected by transport layer: {init_res.status_code}")
            exit(1)
        log("✓ Handshake initialization request sent successfully.")

        time.sleep(0.2)

        requests.post(captured_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers, timeout=5)
        log("✓ Handshake confirmation notification sent.")

        log("-> Requesting tools list payload...")
        tools_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        requests.post(captured_url, json=tools_payload, headers=headers, timeout=5)

        if not tools_received_event.wait(timeout=5):
            log("\nTimeout: Sent tools query, but the server didn't push tool arrays down the stream.")

    except Exception as e:
        log(f"Network error during protocol communication: {e}")
    finally:
        session_closed.set()
        log("\n3. Interaction finished. Connection closed.")
