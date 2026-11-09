#!/usr/bin/env python3
"""Statik dosyaları sunar ve /api/translate isteklerini Gemini'ye iletir (anahtar sunucuda kalır)."""
import json
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
PORT = int(os.environ.get("PORT", "8000"))
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def gemini_translate(text, source, target):
    prompt = (
        f"Translate the following text from {source} to {target}. "
        "Reply with only the translation, no quotes or explanations.\n\n" + text
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
    }).encode()
    req = urllib.request.Request(
        URL, body, {"Content-Type": "application/json", "x-goog-api-key": API_KEY}
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        data = json.load(res)
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


class Handler(SimpleHTTPRequestHandler):
    def _json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/config":
            return self._json(200, {"gemini": bool(API_KEY), "model": MODEL})
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/translate":
            return self._json(404, {"error": "not found"})
        if not API_KEY:
            return self._json(503, {"error": "GEMINI_API_KEY ayarlı değil"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(min(length, 10_000)))
            text = str(req["text"])[:2000]
            out = gemini_translate(text, str(req["from"]), str(req["to"]))
            self._json(200, {"translation": out})
        except urllib.error.HTTPError as e:
            self._json(502, {"error": f"Gemini HTTP {e.code}"})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"http://localhost:{PORT}  (Gemini: {'açık, ' + MODEL if API_KEY else 'KAPALI - GEMINI_API_KEY yok'})")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
