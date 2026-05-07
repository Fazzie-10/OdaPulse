from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import logging

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        # Disable noisy HTTP logging so it doesn't spam the console
        pass

def run():
    # Render assigns a dynamic port via the PORT environment variable
    # We default to 8080 for local testing
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    logging.info(f"Started keep-alive web server on port {port} (for Render deployment)")
    server.serve_forever()

def keep_alive():
    """Starts a lightweight web server in a background thread to satisfy Render."""
    t = threading.Thread(target=run, daemon=True)
    t.start()
