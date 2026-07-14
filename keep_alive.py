from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import logging
import pathlib

LANDING_DIR = pathlib.Path(__file__).resolve().parent / "landing"

class LandingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif self.path == "/style.css":
            self._serve_file("style.css", "text/css; charset=utf-8")
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def _serve_file(self, name, content_type):
        path = LANDING_DIR / name
        if not path.exists():
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()
        with open(path, "rb") as f:
            self.wfile.write(f.read())

    def log_message(self, format, *args):
        pass

def run():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), LandingHandler)
    logging.info(f"Landing page server on port {port}")
    server.serve_forever()

def keep_alive():
    t = threading.Thread(target=run, daemon=True)
    t.start()
