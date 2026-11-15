// M3U playlist parser. Works in the browser (window.GaryM3U) and in Node (module.exports).
(function (root) {
  const CATEGORY_TR = {
    General: "Genel", News: "Haber", Sports: "Spor", Music: "Müzik", Movies: "Film",
    Kids: "Çocuk", Animation: "Çocuk", Documentary: "Belgesel", Entertainment: "Eğlence",
    Religious: "Dini", Education: "Eğitim", Culture: "Kültür", Series: "Dizi",
    Travel: "Gezi", Lifestyle: "Yaşam", Business: "Ekonomi", Comedy: "Komedi",
    Cooking: "Yemek", Undefined: "Diğer", Auto: "Otomobil", Outdoor: "Doğa", Family: "Aile",
    Classic: "Klasik", Science: "Bilim", Shop: "Alışveriş", Weather: "Hava Durumu",
    Legislative: "Meclis", Relax: "Rahatlama", Public: "Kamu", Animals: "Hayvanlar",
    Interactive: "Etkileşimli", Adult: "Yetişkin", Kid: "Çocuk",
  };

  function parseAttrs(s) {
    const attrs = {};
    const re = /([\w-]+)="([^"]*)"/g;
    let m;
    while ((m = re.exec(s))) attrs[m[1].toLowerCase()] = m[2];
    return attrs;
  }

  function categoriesOf(group) {
    const parts = (group || "Undefined").split(";")
      // Provider groups often carry a country prefix such as "TR | SPOR" or "TR: Haber".
      .map((g) => g.trim().replace(/^\|?\s*TR\s*[|:\-]\s*/i, "").trim())
      .filter(Boolean);
    const out = [...new Set(parts.map((g) => CATEGORY_TR[g] || g))];
    return out.length ? out : ["Diğer"];
  }

  // Splits iptv-org style tags out of a name: "TRT 1 (1080p) [Geo-blocked]" -> "TRT 1", 1080, ["Bölge kısıtlı"].
  function cleanName(raw) {
    let height = 0;
    const notes = [];
    let name = String(raw).replace(/\((\d{3,4})p\)/i, (_, h) => { height = Number(h); return ""; });
    if (/\[geo-blocked\]/i.test(name)) notes.push("Bölge kısıtlı");
    if (/\[not 24\/7\]/i.test(name)) notes.push("7/24 değil");
    name = name.replace(/\[(geo-blocked|not 24\/7)\]/gi, "").replace(/\s{2,}/g, " ").trim();
    if (!height) {
      if (/\b(4K|UHD|2160p?)\b/i.test(name)) height = 2160;
      else if (/\b(FHD|1080p?)\b/i.test(name)) height = 1080;
      else if (/\bHD\b|\b720p\b/i.test(name)) height = 720;
    }
    return { name: name || String(raw).trim(), height, notes };
  }

  // Xtream-style URLs reveal whether an entry is a movie or a series episode.
  function kindOf(url) {
    if (/\/movie\//i.test(url)) return "movie";
    if (/\/series\//i.test(url)) return "episode";
    return "live";
  }

  function parseM3U(text, source) {
    const items = [];
    let cur = null;
    for (const raw of String(text).split(/\r?\n/)) {
      const line = raw.trim();
      if (!line) continue;
      if (line.startsWith("#EXTINF")) {
        // The display name follows the first comma outside quoted attributes; names may contain commas.
        let inQ = false, comma = -1;
        for (let i = 0; i < line.length; i++) {
          if (line[i] === '"') inQ = !inQ;
          else if (line[i] === "," && !inQ) { comma = i; break; }
        }
        const head = comma >= 0 ? line.slice(0, comma) : line;
        const attrs = parseAttrs(head);
        const name = (comma >= 0 ? line.slice(comma + 1) : "").trim() || attrs["tvg-name"] || "Kanal";
        cur = {
          name,
          logo: attrs["tvg-logo"] || "",
          id: attrs["tvg-id"] || "",
          categories: categoriesOf(attrs["group-title"]),
          source: source || "",
          geoBlocked: /\[geo-blocked\]/i.test(name),
          ua: attrs["http-user-agent"] || "",
          ref: attrs["http-referrer"] || "",
          url: "",
        };
      } else if (line.startsWith("#EXTVLCOPT:") && cur) {
        const [k, ...v] = line.slice(11).split("=");
        if (k === "http-user-agent") cur.ua = v.join("=");
        if (k === "http-referrer") cur.ref = v.join("=");
      } else if (line.startsWith("#")) {
        continue;
      } else if (cur) {
        cur.url = line;
        cur.kind = kindOf(line);
        cur.key = (source || "") + "|" + line;
        items.push(cur);
        cur = null;
      }
    }
    return items;
  }

  // Providers mark dubbed/subtitled titles in names or groups ("TR DUBLAJ", "Altyazılı", ...).
  function langTags(text) {
    const s = String(text).toLocaleLowerCase("tr")
      .replace(/ı/g, "i").replace(/ü/g, "u").replace(/ç/g, "c")
      .replace(/ş/g, "s").replace(/ğ/g, "g").replace(/ö/g, "o");
    const tags = [];
    if (/dublaj|\bdub\b|turkce ses|\btr ses|turkish audio|turkish dub/.test(s)) tags.push("dub");
    if (/altyazi|\bsub\b|turkish sub|\btr sub/.test(s)) tags.push("sub");
    return tags;
  }

  const api = { parseM3U, categoriesOf, kindOf, langTags, cleanName };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GaryM3U = api;
})(typeof window !== "undefined" ? window : globalThis);
