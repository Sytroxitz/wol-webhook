#!/usr/bin/env python3
"""Minimal Wake-on-LAN webhook (standard library only)."""
import hmac
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_KEY = os.environ.get("API_KEY", "")
PORT = int(os.environ.get("PORT", "8080"))
BROADCAST = os.environ.get("BROADCAST", "255.255.255.255")
# Format: "pc=AA:BB:CC:DD:EE:FF,laptop=11:22:33:44:55:66"
# Only devices listed here can be woken (no arbitrary MAC input).
DEVICES = {}
for item in os.environ.get("DEVICES", "").split(","):
    if "=" in item:
        name, mac = item.split("=", 1)
        DEVICES[name.strip().lower()] = mac.strip()

if len(API_KEY) < 24:
    raise SystemExit("API_KEY is missing or too short (min. 24 characters).")


def send_magic_packet(mac: str) -> None:
    raw = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    if len(raw) != 6:
        raise ValueError("Invalid MAC address")
    packet = b"\xff" * 6 + raw * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(packet, (BROADCAST, 9))


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        header = self.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        return hmac.compare_digest(token, API_KEY)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"status": "ok"})
        if not self._authorized():
            return self._json(401, {"error": "unauthorized"})
        if self.path == "/devices":
            return self._json(200, {"devices": sorted(DEVICES)})
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._authorized():
            return self._json(401, {"error": "unauthorized"})
        if self.path.startswith("/wake/"):
            name = self.path[len("/wake/"):].strip().lower()
            mac = DEVICES.get(name)
            if not mac:
                return self._json(404, {"error": "unknown device"})
            try:
                send_magic_packet(mac)
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"error": str(exc)})
            return self._json(200, {"status": "magic packet sent", "device": name})
        self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    print(f"WoL webhook listening on :{PORT}, devices: {sorted(DEVICES)}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
