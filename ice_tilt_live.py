"""Ice Tilt Live: serves ice_tilt_live.html and relays the NHL's public game feed to it.

Run:  python ice_tilt_live.py            (opens http://127.0.0.1:8765 in your browser)
      python ice_tilt_live.py 9000       (use a different port)
      python ice_tilt_live.py --no-browser
Stop: Ctrl+C
"""
import json
import pathlib
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "ice_tilt_live.html"
API = "https://api-web.nhle.com/v1/"
CACHE_SECONDS = 5

ROUTES = [
    (re.compile(r"^/api/score/(\d{4}-\d{2}-\d{2})$"), "score/{}"),
    (re.compile(r"^/api/pbp/(\d{10})$"), "gamecenter/{}/play-by-play"),
]

_cache = {}
_lock = threading.Lock()


def fetch(path):
    now = time.time()
    with _lock:
        hit = _cache.get(path)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    req = urllib.request.Request(API + path, headers={"User-Agent": "ice-tilt-live/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read()
    with _lock:
        _cache[path] = (now, body)
    return body


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            return
        for rx, tpl in ROUTES:
            m = rx.match(path)
            if not m:
                continue
            try:
                self.send(200, fetch(tpl.format(m.group(1))), "application/json")
            except urllib.error.HTTPError as e:
                self.send(e.code, json.dumps({"error": f"NHL feed returned {e.code}"}).encode(), "application/json")
            except Exception as e:  # network down, timeout
                self.send(502, json.dumps({"error": str(e)}).encode(), "application/json")
            return
        self.send(404, b"Not found", "text/plain")

    def log_message(self, *args):
        pass


def main():
    port = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8765)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Ice Tilt Live running at {url}  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
