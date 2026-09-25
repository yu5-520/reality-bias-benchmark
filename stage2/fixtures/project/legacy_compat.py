"""Old v1 HTTP path, retained temporarily across the upgrade."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LegacyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(410)
        self.end_headers()
        self.wfile.write(b"Legacy checkout retired")


def main():
    ThreadingHTTPServer(("127.0.0.1", 8080), LegacyHandler).serve_forever()
