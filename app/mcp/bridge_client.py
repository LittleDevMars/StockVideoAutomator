"""TCP client for communicating with the Qt app's bridge server."""

import json
import socket
from typing import Any

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 19384
TIMEOUT = 30  # seconds


class BridgeClient:
    """Sends JSON-RPC requests to the Qt app's BridgeServer over TCP."""

    def __init__(self, host: str = BRIDGE_HOST, port: int = BRIDGE_PORT):
        self.host = host
        self.port = port
        self._req_id = 0

    def send_request(self, method: str, params: dict | None = None) -> Any:
        self._req_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": method,
            "params": params or {},
        }
        payload = json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n"

        with socket.create_connection((self.host, self.port), timeout=TIMEOUT) as sock:
            sock.sendall(payload)

            # Read response (newline-delimited JSON)
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed by server")
                buf += chunk

            line = buf.split(b"\n", 1)[0]
            resp = json.loads(line.decode("utf-8"))

        if "error" in resp:
            err = resp["error"]
            raise RuntimeError(f"Bridge error: {err.get('message', 'Unknown error')}")

        return resp.get("result")
