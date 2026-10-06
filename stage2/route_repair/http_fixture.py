"""Loopback socket fixture. It never reports a real model call or actual exit."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from stage2.route_repair.branch_fields import require


class FixtureHTTPServer:
    def __init__(self, rows, *, port=0):
        self.rows = rows; self.requests = []; self.position = 0
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                owner.requests.append(raw)
                if self.path != '/chat/completions' or owner.position >= len(owner.rows):
                    self.send_response_only(503); self.send_header('Content-Length', '0'); self.end_headers(); return
                row = owner.rows[owner.position]; owner.position += 1
                body = row['body']
                self.send_response_only(row.get('status', 200))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(row.get('declared_length', len(body))))
                self.end_headers(); self.wfile.write(body); self.wfile.flush(); self.close_connection = True
        self.server = HTTPServer(('127.0.0.1', port), Handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self): self.thread.start(); return self
    def __exit__(self, *args): self.server.shutdown(); self.server.server_close(); self.thread.join()


def fixture_reply(content, *, status=200, model='deepseek-flash'):
    require(isinstance(content, str), 'FIXTURE_CONTENT_TEXT_REQUIRED')
    return {'status': status, 'body': json.dumps({'id': 'loopback-fixture-response', 'model': model,
        'choices': [{'message': {'role': 'assistant', 'content': content}, 'finish_reason': 'stop'}],
        'usage': {'fixture': True}}, ensure_ascii=False, sort_keys=True).encode()}
