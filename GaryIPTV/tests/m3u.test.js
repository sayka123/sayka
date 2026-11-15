const test = require("node:test");
const assert = require("node:assert");
const { parseM3U, langTags } = require("../m3u.js");

const SAMPLE = `#EXTM3U
#EXTINF:-1 tvg-id="TRTSpor.tr@SD" tvg-logo="https://x/l.png" group-title="Sports",TRT Spor (720p)
https://example.com/trtspor.m3u8
#EXTINF:-1 tvg-id="A" http-user-agent="Mozilla/5.0 (X, Y)" group-title="Culture;General",Kanal, Virgüllü [Geo-blocked]
#EXTVLCOPT:http-referrer=https://x
https://example.com/b.m3u8

#EXTINF:-1,Sadece İsim
http://example.com/c.ts
`;

test("parses channels with attributes and Turkish categories", () => {
  const ch = parseM3U(SAMPLE, "tr");
  assert.strictEqual(ch.length, 3);
  assert.deepStrictEqual(
    { name: ch[0].name, logo: ch[0].logo, cats: ch[0].categories, url: ch[0].url, source: ch[0].source },
    { name: "TRT Spor (720p)", logo: "https://x/l.png", cats: ["Spor"], url: "https://example.com/trtspor.m3u8", source: "tr" }
  );
});

test("handles commas inside quotes and in names, geo-block flag", () => {
  const ch = parseM3U(SAMPLE)[1];
  assert.strictEqual(ch.name, "Kanal, Virgüllü [Geo-blocked]");
  assert.deepStrictEqual(ch.categories, ["Kültür", "Genel"]);
  assert.strictEqual(ch.geoBlocked, true);
  assert.strictEqual(ch.url, "https://example.com/b.m3u8");
});

test("channel without attributes falls into Diğer", () => {
  const ch = parseM3U(SAMPLE)[2];
  assert.strictEqual(ch.name, "Sadece İsim");
  assert.deepStrictEqual(ch.categories, ["Diğer"]);
});

test("reads user-agent/referrer options and detects movies and series", () => {
  const ch = parseM3U(`#EXTM3U
#EXTINF:-1 group-title="Sports",beIN
#EXTVLCOPT:http-user-agent=Agent/1.0 (a=b)
#EXTVLCOPT:http-referrer=https://ref.example/
https://x/live.m3u8
#EXTINF:-1 group-title="TR DUBLAJ FİLMLER",Film
http://srv:8080/movie/u/p/12.mkv
#EXTINF:-1,Dizi S01E01
http://srv:8080/series/u/p/99.mp4
`);
  assert.strictEqual(ch[0].ua, "Agent/1.0 (a=b)");
  assert.strictEqual(ch[0].ref, "https://ref.example/");
  assert.deepStrictEqual(ch.map((c) => c.kind), ["live", "movie", "episode"]);
});

test("langTags separates Turkish dub and subtitle titles", () => {
  assert.deepStrictEqual(langTags("TÜRKÇE DUBLAJ FİLMLER"), ["dub"]);
  assert.deepStrictEqual(langTags("Inception (TR Dub)"), ["dub"]);
  assert.deepStrictEqual(langTags("YABANCI DİZİLER | ALTYAZILI"), ["sub"]);
  assert.deepStrictEqual(langTags("Matrix [Türkçe Dublaj + Altyazı]"), ["dub", "sub"]);
  assert.deepStrictEqual(langTags("Submarine Documentary"), []);
});

test("cleanName extracts quality and translates tags; categories drop TR prefix", () => {
  const { cleanName, categoriesOf } = require("../m3u.js");
  assert.deepStrictEqual(cleanName("TRT 1 (1080p) [Geo-blocked]"), { name: "TRT 1", height: 1080, notes: ["Bölge kısıtlı"] });
  assert.deepStrictEqual(cleanName("360 (720p) [Not 24/7]"), { name: "360", height: 720, notes: ["7/24 değil"] });
  assert.strictEqual(cleanName("TR: beIN Sports 1 4K").height, 2160);
  assert.strictEqual(cleanName("Film [Türkçe Dublaj]").name, "Film [Türkçe Dublaj]");
  assert.deepStrictEqual(categoriesOf("TR | SPOR"), ["SPOR"]);
  assert.deepStrictEqual(categoriesOf("Outdoor;Family"), ["Doğa", "Aile"]);
});
