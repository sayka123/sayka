const test = require("node:test");
const assert = require("node:assert");
const http = require("http");
const { createServer, rewritePlaylist } = require("../server.js");

test("rewritePlaylist routes segments, variants and keys through the proxy", () => {
  const out = rewritePlaylist(
    '#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="key.bin"\nlow/index.m3u8\nhttps://cdn.x/seg1.ts\n',
    "https://h.example/live/master.m3u8", "UA/1", ""
  ).split("\n");
  assert.strictEqual(out[0], "#EXTM3U");
  assert.match(out[1], /URI="\/proxy\?hls=1&url=https%3A%2F%2Fh\.example%2Flive%2Fkey\.bin&ua=UA%2F1"/);
  assert.strictEqual(out[2], "/proxy?hls=1&url=https%3A%2F%2Fh.example%2Flive%2Flow%2Findex.m3u8&ua=UA%2F1");
  assert.strictEqual(out[3], "/proxy?hls=1&url=https%3A%2F%2Fcdn.x%2Fseg1.ts&ua=UA%2F1");
});

function listen(server) {
  return new Promise((r) => server.listen(0, "127.0.0.1", () => r(server.address().port)));
}

test("proxy forwards user-agent, rewrites HLS, serves the app and blocks traversal", async () => {
  let seenUA = "";
  const upstream = http.createServer((req, res) => {
    seenUA = req.headers["user-agent"];
    if (req.url === "/a.m3u8") res.writeHead(200, { "content-type": "application/vnd.apple.mpegurl" }).end("#EXTM3U\nseg.ts\n");
    else res.writeHead(200, { "content-type": "video/mp2t" }).end("TSDATA");
  });
  const up = await listen(upstream);
  const app = createServer();
  const port = await listen(app);
  const base = `http://127.0.0.1:${port}`;
  try {
    const pl = await (await fetch(`${base}/proxy?hls=1&ua=GaryTest&url=${encodeURIComponent(`http://127.0.0.1:${up}/a.m3u8`)}`)).text();
    assert.strictEqual(seenUA, "GaryTest");
    const seg = pl.split("\n")[1];
    assert.ok(seg.startsWith("/proxy?"));
    assert.strictEqual(await (await fetch(base + seg)).text(), "TSDATA");
    assert.match(await (await fetch(base + "/")).text(), /Gary IPTV/);
    assert.strictEqual((await fetch(base + "/proxy?url=file:///etc/passwd")).status, 400);
    assert.strictEqual((await fetch(base + "/..%2f..%2fetc%2fpasswd")).status, 403);
    const checkRes = await fetch(`${base}/proxy/check`, {
      method: "POST",
      body: JSON.stringify([{ url: `http://127.0.0.1:${up}/a.m3u8` }, { url: "http://127.0.0.1:1/x.m3u8" }, { url: "file:///etc/passwd" }]),
    });
    const results = (await checkRes.text()).trim().split("\n").map((l) => JSON.parse(l)).sort((a, b) => a.i - b.i);
    assert.deepStrictEqual(results.map((r) => r.ok), [true, false, false]);
  } finally {
    app.close();
    upstream.close();
  }
});
