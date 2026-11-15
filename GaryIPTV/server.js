// Gary IPTV local server: serves the app and proxies playlists/streams so that
// channels without browser (CORS) support or with User-Agent requirements still play.
const http = require("http");
const fs = require("fs");
const path = require("path");
const { Readable } = require("stream");

const ROOT = __dirname;
const DEFAULT_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36";
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
};

function proxied(url, ua, ref) {
  const q = new URLSearchParams({ hls: "1", url });
  if (ua) q.set("ua", ua);
  if (ref) q.set("ref", ref);
  return "/proxy?" + q;
}

// Point every URI inside an HLS playlist back through the proxy, keeping headers.
function rewritePlaylist(text, baseUrl, ua, ref) {
  const abs = (u) => proxied(new URL(u, baseUrl).href, ua, ref);
  return text
    .split(/\r?\n/)
    .map((line) => {
      const t = line.trim();
      if (!t) return line;
      if (!t.startsWith("#")) return abs(t);
      return line.replace(/URI="([^"]+)"/g, (_, u) => `URI="${abs(u)}"`);
    })
    .join("\n");
}

function upstreamHeaders(params, req) {
  const headers = { "user-agent": params.get("ua") || DEFAULT_UA };
  if (params.get("ref")) headers.referer = params.get("ref");
  if (req && req.headers.range) headers.range = req.headers.range;
  return headers;
}

// Reports whether a stream answers with data, and how fast, so the app can hide dead channels.
async function checkOne({ url, ua, ref }) {
  const t0 = Date.now();
  let ok = false;
  if (/^https?:\/\//i.test(url || "")) {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 8000);
    try {
      const params = new URLSearchParams();
      if (ua) params.set("ua", ua);
      if (ref) params.set("ref", ref);
      const up = await fetch(url, { headers: upstreamHeaders(params), redirect: "follow", signal: ac.signal });
      if (up.ok && up.body) {
        const reader = up.body.getReader();
        const { value } = await reader.read();
        ok = Boolean(value && value.length);
        reader.cancel().catch(() => {});
      }
    } catch {}
    clearTimeout(timer);
  }
  return { ok, ms: Date.now() - t0 };
}

// POST a JSON list of {url, ua, ref}; results stream back as one JSON line each, using a single
// browser connection so checks never starve actual playback.
async function handleCheck(req, res) {
  let body = "";
  for await (const chunk of req) {
    body += chunk;
    if (body.length > 5e6) return res.writeHead(413).end();
  }
  let list;
  try { list = JSON.parse(body); } catch { list = null; }
  if (!Array.isArray(list)) return res.writeHead(400).end("bad body");
  res.writeHead(200, { "content-type": "application/x-ndjson", "cache-control": "no-store" });
  let next = 0, closed = false;
  res.on("close", () => { closed = true; });
  const worker = async () => {
    while (next < list.length && !closed) {
      const i = next++;
      const r = await checkOne(list[i] || {});
      if (!closed) res.write(JSON.stringify({ i, ...r }) + "\n");
    }
  };
  await Promise.all(Array.from({ length: 16 }, worker));
  res.end();
}

async function handleProxy(req, res, params) {
  const target = params.get("url") || "";
  if (!/^https?:\/\//i.test(target)) {
    res.writeHead(400).end("bad url");
    return;
  }
  const ua = params.get("ua") || "";
  const ref = params.get("ref") || "";
  const headers = upstreamHeaders(params, req);

  const ac = new AbortController();
  req.on("close", () => ac.abort());
  const up = await fetch(target, { headers, redirect: "follow", signal: ac.signal });
  const type = up.headers.get("content-type") || "";
  const out = { "access-control-allow-origin": "*", "cache-control": "no-store" };

  const isPlaylist =
    params.get("hls") === "1" && (/mpegurl/i.test(type) || /\.m3u8(\?|$)/i.test(new URL(up.url).pathname));
  if (isPlaylist && up.ok) {
    const body = rewritePlaylist(await up.text(), up.url, ua, ref);
    res.writeHead(200, { ...out, "content-type": "application/vnd.apple.mpegurl" }).end(body);
    return;
  }
  for (const h of ["content-type", "content-length", "content-range", "accept-ranges"]) {
    const v = up.headers.get(h);
    if (v) out[h] = v;
  }
  res.writeHead(up.status, out);
  if (up.body) Readable.fromWeb(up.body).on("error", () => res.destroy()).pipe(res);
  else res.end();
}

function handleStatic(res, pathname) {
  const file = path.normalize(path.join(ROOT, pathname === "/" ? "index.html" : decodeURIComponent(pathname)));
  if (!file.startsWith(ROOT + path.sep)) {
    res.writeHead(403).end();
    return;
  }
  fs.readFile(file, (err, data) => {
    if (err) res.writeHead(404).end("not found");
    else res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" }).end(data);
  });
}

function createServer() {
  return http.createServer((req, res) => {
    const u = new URL(req.url, "http://localhost");
    if (u.pathname === "/proxy/ping") return res.writeHead(200).end("ok");
    if (u.pathname === "/proxy/check" && req.method === "POST") {
      return handleCheck(req, res).catch(() => res.destroy());
    }
    if (u.pathname === "/proxy") {
      return handleProxy(req, res, u.searchParams).catch(() => {
        if (!res.headersSent) res.writeHead(502).end("upstream error");
        else res.destroy();
      });
    }
    handleStatic(res, u.pathname);
  });
}

if (require.main === module) {
  const port = Number(process.env.PORT) || 8080;
  // Localhost only by default: the proxy would otherwise be open to the whole network.
  const host = process.env.HOST || "127.0.0.1";
  createServer().listen(port, host, () => console.log(`Gary IPTV hazır: http://localhost:${port}`));
}

module.exports = { createServer, rewritePlaylist };
