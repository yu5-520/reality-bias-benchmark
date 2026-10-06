"""Standard-library HTTP entry point; no external package installation."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .checkout import create_checkout

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            return self.reply(200, {"service": "checkout", "version": "2.0"})
        if self.path in ("/", "/app.js"):
            name = "index.html" if self.path == "/" else "app.js"
            body = (WEB_ROOT / name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html" if name.endswith("html") else "text/javascript")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/checkout":
            return self.reply(404, {"error": "Not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 65536:
                raise ValueError("Request too large")
            payload = json.loads(self.rfile.read(size))
            result = create_checkout(payload["cart"], payload.get("method", "card"))
            self.reply(200, result)
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self.reply(400, {"error": str(exc)})

    def reply(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()


if __name__ == "__main__":
    main()
