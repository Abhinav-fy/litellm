#!/usr/bin/env python3
"""
Relay: receives LiteLLM alerts ({"text": "..."}) and forwards to Rover360
in the expected format: {"message": "...", "thread_title": "...", "alarm_type": 1, "service_name": "fia"}
Run: python rover360_relay.py
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error

ROVER360_URL = "http://internal-trading-internal-ALB-1101911574.ap-south-1.elb.amazonaws.com/rover360/alert/send-alert?type=with_thread"
THREAD_TITLE = "LiteLLM-test"
ALARM_TYPE = 1
SERVICE_NAME = "fia"
PORT = 9999


class RelayHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/" and self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            text = data.get("text", str(data))
        except json.JSONDecodeError:
            text = body.decode("utf-8", errors="replace")

        payload = {
            "message": text,
            "thread_title": THREAD_TITLE,
            "alarm_type": ALARM_TYPE,
            "service_name": SERVICE_NAME,
        }
        req = urllib.request.Request(
            ROVER360_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
        except urllib.error.HTTPError as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e.read().decode())}).encode())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        print(f"[Relay] {args[0]}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), RelayHandler)
    print(f"Rover360 relay listening on http://0.0.0.0:{PORT}")
    print(f"Forwards to: {ROVER360_URL}")
    server.serve_forever()
