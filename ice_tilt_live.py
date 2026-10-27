"""Ice Tilt Live: serves ice_tilt_live.html and relays the NHL's public game feed to it.

Run:  python ice_tilt_live.py            (opens http://127.0.0.1:8765 here; phones/tablets on your Wi-Fi can use the printed address)
      python ice_tilt_live.py --local    (this computer only)
      python ice_tilt_live.py 9000       (use a different port)
      python ice_tilt_live.py --no-browser
Stop: Ctrl+C
"""
import json
import pathlib
import re
import socket
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
    (re.compile(r"^/api/box/(\d{10})$"), "gamecenter/{}/boxscore"),
    (re.compile(r"^/api/rail/(\d{10})$"), "gamecenter/{}/right-rail"),
    (re.compile(r"^/api/shifts/(\d{10})$"), "https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={}"),
]

# home-screen icon and manifest, so Add to Home Screen works from the local server too
STATIC = {
    "/manifest.webmanifest": "application/manifest+json",
    "/icons/icon-192.png": "image/png",
    "/icons/icon-512.png": "image/png",
    "/icons/apple-touch-icon.png": "image/png",
    "/icons/favicon-64.png": "image/png",
}

_cache = {}
_lock = threading.Lock()


def fetch(path):
    now = time.time()
    with _lock:
        hit = _cache.get(path)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    url = path if path.startswith("https://") else API + path
    req = urllib.request.Request(url, headers={"User-Agent": "ice-tilt-live/1.0"})
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
        if path in ("/", "/index.html", "/ice_tilt_live.html"):
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            return
        if path in STATIC:
            self.send(200, (HERE / path.lstrip("/")).read_bytes(), STATIC[path])
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


def lan_ip():
    # the address other devices on the network use to reach this computer (no traffic is sent)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def main():
    port = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8765)
    lan = "--local" not in sys.argv  # Wi-Fi devices allowed by default; --lan is still accepted
    server = ThreadingHTTPServer(("0.0.0.0" if lan else "127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Ice Tilt Live running at {url}  (Ctrl+C to stop)")
    if lan:
        ip = lan_ip()
        if ip:
            print(f"On your iPad or phone (same Wi-Fi): http://{ip}:{port}/")
        else:
            print("Couldn't work out this computer's network address. Check ipconfig for the IPv4 address.")
        print("If Windows asks about network access for Python, allow it on Private networks.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
