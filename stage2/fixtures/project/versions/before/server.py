"""Runnable checkout v1.9 snapshot from before the upgrade.

Run `python versions/before/server.py` in the project root. This older service
listens on 8081 so its behavior can be compared with the new service on 8080.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            return self.reply(200, {"service": "checkout", "version": "1.9"})
        self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/checkout":
            return self.reply(404, {"error": "Not found"})
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            items = payload["cart"]["items"]
            if not items:
                raise ValueError("Cart is empty")
            amount = sum(item["price_cents"] * item["quantity"] for item in items)
            self.reply(200, {"status": "pending_payment", "amount_cents": amount, "method": "card"})
        except (KeyError, ValueError, TypeError) as exc:
            self.reply(400, {"error": str(exc)})

    def reply(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8081), Handler).serve_forever()
