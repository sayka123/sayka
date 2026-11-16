(function () {
  const LIVE_SOURCES = [
    { code: "tr", label: "🇹🇷 Türkiye", url: "https://iptv-org.github.io/iptv/countries/tr.m3u" },
    { code: "tur", label: "🗣️ Türkçe (dünya)", url: "https://iptv-org.github.io/iptv/languages/tur.m3u" },
    { code: "bg", label: "🇧🇬 Bulgaristan", url: "https://iptv-org.github.io/iptv/countries/bg.m3u" },
    { code: "sport", label: "⚽ Spor (dünya)", url: "https://iptv-org.github.io/iptv/categories/sports.m3u" },
  ];
  // SHA-256 of "gary:lord" so the credentials are not stored in plain text.
  const LOGIN_HASH = "0a7393790866dba8be60c34dbcd96d8e57cd499fab9aa05c226d20fe18a84d63";
  const LS = {
    auth: "garyiptv.auth", fav: "garyiptv.favs", last: "garyiptv.last",
    custom: "garyiptv.custom", xtream: "garyiptv.xtream",
  };
  const MODES = { live: "📡 Canlı TV", movie: "🎬 Filmler", series: "📺 Diziler" };
  const NOUN = { live: "kanal", movie: "film", series: "dizi" };
  const LANGS = { all: "🌐 Tüm diller", dub: "🔊 Türkçe Dublaj", sub: "💬 Türkçe Altyazı" };
  const RENDER_LIMIT = 600;

  const $ = (id) => document.getElementById(id);
  const video = $("video"), overlay = $("overlay"), list = $("list");
  const st = {
    mode: "live", items: { live: [], movie: [], series: [] }, sources: [],
    source: "all", lang: "all", category: "Tümü", query: "", series: null, current: null,
    onlyWorking: true, checking: 0, checkGen: 0,
  };
  const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
  let favs = new Set(load(LS.fav, []));
  let hls = null, visible = [], proxy = false, subChoice = null;

  // ---------- login ----------
  async function sha256(s) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  function enter() {
    document.body.classList.add("authed");
    start();
  }
  $("login").onsubmit = async (e) => {
    e.preventDefault();
    const h = await sha256($("user").value.trim().toLocaleLowerCase("tr") + ":" + $("pass").value);
    if (h !== LOGIN_HASH) { $("loginErr").textContent = "Kullanıcı adı veya parola yanlış"; return; }
    ($("remember").checked ? localStorage : sessionStorage).setItem(LS.auth, h);
    enter();
  };
  $("logout").onclick = () => {
    localStorage.removeItem(LS.auth);
    sessionStorage.removeItem(LS.auth);
    location.reload();
  };

  // ---------- network ----------
  async function detectProxy() {
    if (!location.protocol.startsWith("http")) return false;
    try { const r = await fetch("/proxy/ping"); return r.ok && (await r.text()) === "ok"; } catch { return false; }
  }
  function viaProxy(url, extra) {
    const q = new URLSearchParams({ url });
    for (const [k, v] of Object.entries(extra || {})) if (v) q.set(k, v);
    return "/proxy?" + q;
  }
  async function fetchText(url) {
    const r = await fetch(proxy ? viaProxy(url) : url);
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.text();
  }
  const fetchJSON = async (url) => JSON.parse(await fetchText(url));
  const arr = (x) => (Array.isArray(x) ? x : []);

  // ---------- Xtream Codes ----------
  function normServer(s) {
    s = s.trim().replace(/\/+$/, "").replace(/\/player_api\.php.*$/, "");
    return /^https?:\/\//i.test(s) ? s : "http://" + s;
  }
  const xtApi = (a, action, extra = "") =>
    `${a.server}/player_api.php?username=${encodeURIComponent(a.user)}&password=${encodeURIComponent(a.pass)}` +
    (action ? `&action=${action}` : "") + extra;
  const xtPath = (a, type, id, ext) =>
    `${a.server}/${type}/${encodeURIComponent(a.user)}/${encodeURIComponent(a.pass)}/${id}.${ext}`;

  async function loadXtream(a, code) {
    const get = (action) => fetchJSON(xtApi(a, action)).catch(() => []);
    const [lc, vc, sc, live, vod, series] = await Promise.all([
      get("get_live_categories"), get("get_vod_categories"), get("get_series_categories"),
      get("get_live_streams"), get("get_vod_streams"), get("get_series"),
    ]);
    const map = (cats) => Object.fromEntries(arr(cats).map((c) => [String(c.category_id), c.category_name]));
    const [L, V, S] = [map(lc), map(vc), map(sc)];
    const cat = (m, id) => GaryM3U.categoriesOf(m[String(id)] || "Undefined");
    return [
      ...arr(live).map((s) => ({
        kind: "live", source: code, name: s.name, logo: s.stream_icon || "", categories: cat(L, s.category_id),
        url: xtPath(a, "live", s.stream_id, "m3u8"), key: `${code}|l${s.stream_id}`,
      })),
      ...arr(vod).map((s) => ({
        kind: "movie", source: code, name: s.name, logo: s.stream_icon || "", categories: cat(V, s.category_id),
        url: xtPath(a, "movie", s.stream_id, s.container_extension || "mp4"), key: `${code}|m${s.stream_id}`,
        rating: s.rating,
      })),
      ...arr(series).map((s) => ({
        kind: "series", source: code, name: s.name, logo: s.cover || "", categories: cat(S, s.category_id),
        seriesId: s.series_id, account: a, key: `${code}|s${s.series_id}`, rating: s.rating,
      })),
    ];
  }

  async function openSeries(s) {
    overlay.textContent = "Bölümler yükleniyor…";
    try {
      const info = await fetchJSON(xtApi(s.account, "get_series_info", `&series_id=${s.seriesId}`));
      const episodes = [];
      for (const [season, eps] of Object.entries(info.episodes || {})) {
        for (const ep of arr(eps)) {
          episodes.push({
            kind: "episode", source: s.source, logo: ep.info?.movie_image || s.logo,
            name: `${season}. Sezon ${ep.episode_num}. Bölüm${ep.title ? " · " + ep.title : ""}`,
            categories: [`${season}. Sezon`], tags: s.tags,
            url: xtPath(s.account, "series", ep.id, ep.container_extension || "mp4"),
            key: `${s.source}|e${ep.id}`,
          });
        }
      }
      st.series = { title: s.name, episodes };
      overlay.textContent = episodes.length ? "Bir bölüm seçin" : "Bu dizinin bölümü yok";
    } catch {
      overlay.textContent = "Bölümler alınamadı";
    }
    renderList();
  }

  // ---------- loading ----------
  async function loadAll() {
    overlay.textContent = "Kanallar yükleniyor…";
    const accounts = load(LS.xtream, []);
    const sources = [...LIVE_SOURCES];
    const tasks = LIVE_SOURCES.map(async (s) => GaryM3U.parseM3U(await fetchText(s.url), s.code));
    const custom = localStorage.getItem(LS.custom);
    if (custom) {
      sources.push({ code: "my", label: "📺 M3U listem" });
      tasks.push(Promise.resolve(GaryM3U.parseM3U(custom, "my")));
    }
    accounts.forEach((a, i) => {
      sources.push({ code: "xt" + i, label: "🔑 " + (a.name || a.server.replace(/^https?:\/\//, "")) });
      tasks.push(loadXtream(a, "xt" + i));
    });
    const res = await Promise.allSettled(tasks);

    const items = { live: [], movie: [], series: [] };
    const seen = new Set();
    const best = new Map();
    for (const r of res) {
      if (r.status !== "fulfilled") continue;
      for (const it of r.value) {
        if (seen.has(it.url || it.key)) continue;
        seen.add(it.url || it.key);
        const cn = GaryM3U.cleanName(it.name);
        it.name = cn.name;
        it.height = cn.height;
        it.notes = cn.notes;
        it.geoBlocked = cn.notes.includes("Bölge kısıtlı");
        it.tags = GaryM3U.langTags(it.name + " " + it.categories.join(" "));
        const bucket = items[it.kind === "episode" ? "series" : it.kind];
        if (it.kind === "live" && it.id) {
          // Same channel listed in several qualities: keep only the sharpest copy.
          // Lists overlap (for example, Turkish channels also occur in the global sports list).
          // Use the common tvg id to show just the highest-quality copy to the user.
          const dk = it.id.split("@")[0];
          const prev = best.get(dk);
          if (prev && prev.height >= it.height) continue;
          if (prev) bucket.splice(bucket.indexOf(prev), 1);
          best.set(dk, it);
        }
        bucket.push(it);
      }
    }
    for (const k of Object.keys(items)) items[k].sort((a, b) => a.name.localeCompare(b.name, "tr"));
    st.items = items;
    st.sources = sources;
    const failed = res.filter((r) => r.status === "rejected").length;
    overlay.textContent = failed ? "Bazı listeler yüklenemedi, internet bağlantınızı kontrol edin." : "Soldan seçim yapın";
    renderAll();
    const last = localStorage.getItem(LS.last);
    const lastCh = last && items.live.find((c) => c.key === last);
    if (lastCh) play(lastCh);
    if (proxy) checkHealth(items.live.filter((c) => LIVE_SOURCES.some((s) => s.code === c.source)));
  }

  // Probe free channels in the background; dead ones are hidden, working ones listed first.
  async function checkHealth(channels) {
    const gen = ++st.checkGen;
    st.checking = channels.length;
    let timer = null;
    const refresh = () => { if (!timer) timer = setTimeout(() => { timer = null; if (gen === st.checkGen) renderList(); }, 800); };
    try {
      const r = await fetch("/proxy/check", {
        method: "POST",
        body: JSON.stringify(channels.map((c) => ({ url: c.url, ua: c.ua, ref: c.ref }))),
      });
      const reader = r.body.pipeThrough(new TextDecoderStream()).getReader();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done || gen !== st.checkGen) break;
        buf += value;
        let nl;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const res = JSON.parse(buf.slice(0, nl));
          buf = buf.slice(nl + 1);
          const c = channels[res.i];
          if (c) { c.status = res.ok ? "ok" : "down"; c.ms = res.ms; }
          st.checking--;
        }
        refresh();
      }
    } catch {}
    if (gen !== st.checkGen) return;
    st.checking = 0;
    const rank = (c) => (c.status === "ok" ? 0 : c.status === "down" ? 2 : 1);
    st.items.live.sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name, "tr"));
    renderAll();
  }

  // ---------- rendering ----------
  function chip(label, active, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    if (active) b.className = "active";
    b.onclick = onClick;
    return b;
  }
  const set = (patch) => { Object.assign(st, patch); renderAll(); };

  function renderAll() {
    $("modes").replaceChildren(...Object.entries(MODES).map(([m, l]) =>
      chip(`${l} (${st.items[m].length})`, st.mode === m, () =>
        set({ mode: m, source: "all", category: "Tümü", lang: "all", series: null }))));

    const pool = st.items[st.mode];
    const srcs = [{ code: "all", label: "Hepsi" }, { code: "fav", label: "★ Favoriler" },
      ...st.sources.filter((s) => pool.some((c) => c.source === s.code))];
    $("sources").replaceChildren(...srcs.map((s) =>
      chip(s.label, st.source === s.code, () => set({ source: s.code, category: "Tümü", series: null }))));
    if (st.mode === "live" && proxy) {
      $("sources").append(chip("✅ Sadece çalışanlar", st.onlyWorking, () => set({ onlyWorking: !st.onlyWorking })));
    }

    const showLang = st.mode !== "live";
    $("langs").replaceChildren(...(showLang ? Object.entries(LANGS).map(([k, l]) =>
      chip(l, st.lang === k, () => set({ lang: k, series: null }))) : []));

    const counts = {};
    for (const c of pool) if (inSource(c)) for (const k of c.categories) counts[k] = (counts[k] || 0) + 1;
    const cats = Object.keys(counts).sort((a, b) => (a === "Spor" ? -1 : b === "Spor" ? 1 : counts[b] - counts[a]));
    $("categories").replaceChildren(...["Tümü", ...cats].map((k) =>
      chip(k, st.category === k, () => set({ category: k, series: null }))));
    renderList();
  }

  function inSource(c) {
    if (st.source === "fav") return favs.has(c.key);
    return st.source === "all" || c.source === st.source;
  }
  function matches(c) {
    if (!inSource(c)) return false;
    if (st.mode === "live" && st.onlyWorking && c.status === "down") return false;
    if (st.lang !== "all" && !c.tags.includes(st.lang)) return false;
    if (st.category !== "Tümü" && !c.categories.includes(st.category)) return false;
    return !st.query || c.name.toLocaleLowerCase("tr").includes(st.query);
  }

  const qualityOf = (h) => (h >= 2160 ? "4K" : h >= 1080 ? "FHD" : h >= 720 ? "HD" : h > 0 ? "SD" : "");
  const el = (tag, className, text) => Object.assign(document.createElement(tag), { className, textContent: text || "" });

  function row(c, onClick, meta) {
    const li = document.createElement("li");
    if (st.current && st.current.key === c.key) li.className = "playing";
    const box = () => el("div", "noLogo", c.name.slice(0, 2).toLocaleUpperCase("tr"));
    let logo = box();
    if (c.logo) {
      logo = Object.assign(document.createElement("img"), { src: c.logo, loading: "lazy", alt: "" });
      logo.onerror = () => logo.replaceWith(box());
    }
    if (st.mode !== "live" && !st.series) li.classList.add("poster");
    const txt = el("div", "name");
    const title = el("div", "title", c.name);
    const q = qualityOf(c.height);
    if (q) title.prepend(el("span", "badge q" + q, q));
    if (c.status) title.prepend(el("span", "dot " + c.status, ""));
    txt.append(title, el("div", "meta", meta));
    li.append(logo, txt);
    if (c.kind !== "episode") {
      const fav = Object.assign(el("button", "fav" + (favs.has(c.key) ? " on" : ""), "★"), { type: "button", title: "Favorilere ekle" });
      fav.onclick = (e) => { e.stopPropagation(); toggleFav(c); };
      li.append(fav);
    }
    li.onclick = onClick;
    return li;
  }

  function metaOf(c) {
    const parts = [c.categories.join(", ")];
    if (c.tags.includes("dub")) parts.push("Dublaj");
    if (c.tags.includes("sub")) parts.push("Altyazı");
    if (c.rating) parts.push("★ " + c.rating);
    const origin = st.sources.find((s) => s.code === c.source)?.label;
    if (origin && c.source !== "tr") parts.push(origin.replace(/^\S+\s/, ""));
    parts.push(...(c.notes || []));
    return parts.join(" · ");
  }

  function renderList() {
    const frag = document.createDocumentFragment();
    $("side").classList.toggle("grid", st.mode !== "live" && !st.series);
    if (st.series) {
      const back = el("li", "back", "← " + st.series.title);
      back.onclick = () => set({ series: null });
      frag.append(back);
      visible = st.series.episodes.filter((e) => !st.query || e.name.toLocaleLowerCase("tr").includes(st.query));
      for (const e of visible) frag.append(row(e, () => play(e), e.categories[0]));
      $("count").textContent = visible.length + " bölüm";
    } else {
      const pool = st.items[st.mode];
      const all = pool.filter(matches);
      visible = all.slice(0, RENDER_LIMIT);
      for (const c of visible) frag.append(row(c, () => (c.kind === "series" && c.seriesId ? openSeries(c) : play(c)), metaOf(c)));
      let txt = `${all.length} ${NOUN[st.mode]}`;
      if (all.length > RENDER_LIMIT) txt += ` (ilk ${RENDER_LIMIT} gösteriliyor, arayarak daraltın)`;
      if (st.mode === "live" && st.checking > 0) txt += ` · yayınlar kontrol ediliyor (${st.checking} kaldı)…`;
      if (!pool.length && st.mode !== "live") txt = `Film ve dizi için "+ Hesap ekle" ile IPTV aboneliğinizi ekleyin.`;
      $("count").textContent = txt;
    }
    const top = list.scrollTop;
    list.replaceChildren(frag);
    list.scrollTop = top;
  }

  function toggleFav(c) {
    favs.has(c.key) ? favs.delete(c.key) : favs.add(c.key);
    localStorage.setItem(LS.fav, JSON.stringify([...favs]));
    renderList();
  }

  // ---------- player ----------
  const isTurkish = (t) => /^(tr|tur|turkish|türkçe|turkce)/i.test(`${t.lang || ""} ${t.name || ""}`.trim()) ||
    /t(ü|u)rk/i.test(t.name || "");

  function fillSelect(sel, opts, value, onChange) {
    sel.replaceChildren(...opts.map(([v, l]) => Object.assign(document.createElement("option"), { value: v, textContent: l })));
    sel.value = String(value);
    sel.hidden = opts.length < 2;
    sel.onchange = () => onChange(Number(sel.value));
  }

  function setupTracks() {
    const empty = () => ["audioSel", "subSel", "qualitySel"].forEach((id) => ($(id).hidden = true));
    if (!hls) {
      empty();
      // Native playback (mp4/mkv files): pick Turkish audio if the browser exposes tracks.
      const at = video.audioTracks;
      if (at && at.length > 1) for (let i = 0; i < at.length; i++) at[i].enabled = isTurkish({ lang: at[i].language, name: at[i].label });
      for (const t of video.textTracks || []) if (isTurkish({ lang: t.language, name: t.label })) t.mode = "showing";
      return;
    }
    const levels = hls.levels.map((l, i) => [i, l.height ? `${l.height}p` : `${Math.round(l.bitrate / 1000)} kbps`]);
    fillSelect($("qualitySel"), [[-1, "Kalite: Otomatik"], ...levels.reverse()], hls.autoLevelEnabled ? -1 : hls.currentLevel,
      (v) => { hls.currentLevel = v; });

    const audio = hls.audioTracks.map((t, i) => [i, "🔊 " + (t.name || t.lang || `Ses ${i + 1}`)]);
    const trAudio = hls.audioTracks.findIndex(isTurkish);
    if (trAudio >= 0 && hls.audioTrack !== trAudio) hls.audioTrack = trAudio;
    fillSelect($("audioSel"), audio, hls.audioTrack, (v) => { hls.audioTrack = v; });

    const subs = [[-1, "💬 Altyazı kapalı"], ...hls.subtitleTracks.map((t, i) => [i, "💬 " + (t.name || t.lang || `Altyazı ${i + 1}`)])];
    // hls.js may drop a subtitle choice made before media attaches, so remember and re-apply it.
    if (subChoice === null && hls.subtitleTracks.length) subChoice = hls.subtitleTracks.findIndex(isTurkish);
    if (subChoice !== null && hls.subtitleTrack !== subChoice) { hls.subtitleTrack = subChoice; hls.subtitleDisplay = subChoice >= 0; }
    fillSelect($("subSel"), subs, subChoice ?? -1, (v) => { subChoice = v; hls.subtitleTrack = v; hls.subtitleDisplay = v >= 0; });
  }

  function play(c) {
    st.current = c;
    if (c.kind === "live") localStorage.setItem(LS.last, c.key);
    $("nowPlaying").textContent = c.name;
    overlay.textContent = "Bağlanıyor…";
    if (hls) { hls.destroy(); hls = null; }
    subChoice = null;
    video.removeAttribute("src");
    video.load();
    setupTracks();

    const src = proxy ? viaProxy(c.url, { hls: "1", ua: c.ua, ref: c.ref }) : c.url;
    const fail = () => {
      if (st.current !== c) return;
      let msg = "Bu yayın şu an açılamıyor";
      if (c.geoBlocked) msg += " (yalnızca kendi ülkesinden izlenebilir)";
      if (!proxy) msg += ". Gary IPTV'yi Baslat dosyasıyla açarsanız daha çok yayın çalışır";
      overlay.textContent = msg + ".";
    };
    video.onplaying = () => { if (st.current === c) overlay.textContent = ""; };
    video.onwaiting = () => { if (st.current === c && video.currentTime > 0) overlay.textContent = "Yükleniyor…"; };
    video.onloadedmetadata = () => { if (!hls) setupTracks(); };
    video.onerror = () => { if (!hls) fail(); };

    const isFile = /\.(mp4|mkv|webm|avi|mov|m4v)(\?|$)/i.test(c.url);
    if (!isFile && window.Hls && Hls.isSupported()) {
      hls = new Hls({
        // Larger buffers trade a little delay for fewer stalls on slow IPTV servers.
        maxBufferLength: 60, maxMaxBufferLength: 120, backBufferLength: 30,
        startLevel: -1, capLevelToPlayerSize: false, abrEwmaDefaultEstimate: 5e6,
        manifestLoadingMaxRetry: 3, levelLoadingMaxRetry: 4, fragLoadingMaxRetry: 6,
        enableWorker: true, lowLatencyMode: false,
      });
      let mediaRecoveries = 0, netRecoveries = 0;
      hls.on(Hls.Events.ERROR, (_, d) => {
        if (!d.fatal) return;
        if (d.type === Hls.ErrorTypes.MEDIA_ERROR && mediaRecoveries++ < 3) hls.recoverMediaError();
        else if (d.type === Hls.ErrorTypes.NETWORK_ERROR && video.currentTime > 0 && netRecoveries++ < 5) hls.startLoad();
        else fail();
      });
      for (const ev of [Hls.Events.MANIFEST_PARSED, Hls.Events.MEDIA_ATTACHED, Hls.Events.AUDIO_TRACKS_UPDATED, Hls.Events.SUBTITLE_TRACKS_UPDATED, Hls.Events.LEVEL_SWITCHED]) {
        hls.on(ev, setupTracks);
      }
      hls.loadSource(src);
      hls.attachMedia(video);
    } else {
      video.src = src;
    }
    video.play().catch(() => {});
    renderList();
  }

  function step(delta) {
    const playable = visible.filter((c) => c.kind !== "series");
    if (!playable.length) return;
    const i = st.current ? playable.findIndex((c) => c.key === st.current.key) : -1;
    play(playable[(i + delta + playable.length) % playable.length]);
    list.querySelector(".playing")?.scrollIntoView({ block: "nearest" });
  }

  // ---------- add accounts ----------
  const dlg = $("addDialog");
  function renderAccounts() {
    const rows = load(LS.xtream, []).map((a, i) => [`🔑 ${a.server} (${a.user})`, () => {
      const accs = load(LS.xtream, []);
      accs.splice(i, 1);
      localStorage.setItem(LS.xtream, JSON.stringify(accs));
    }]);
    if (localStorage.getItem(LS.custom)) rows.push(["📺 M3U listem", () => localStorage.removeItem(LS.custom)]);
    $("accounts").replaceChildren(...(rows.length ? rows.map(([label, del]) => {
      const li = Object.assign(document.createElement("li"), { textContent: label + " " });
      li.append(chip("Sil", false, () => { del(); renderAccounts(); loadAll(); }));
      return li;
    }) : [Object.assign(document.createElement("li"), { textContent: "Henüz hesap yok" })]));
  }
  $("addBtn").onclick = () => { $("addErr").textContent = ""; renderAccounts(); dlg.showModal(); };
  $("addConfirm").onclick = async (e) => {
    e.preventDefault();
    const err = $("addErr");
    err.textContent = "Kontrol ediliyor…";
    try {
      if ($("xtServer").value.trim()) {
        const a = { server: normServer($("xtServer").value), user: $("xtUser").value.trim(), pass: $("xtPass").value };
        const info = await fetchJSON(xtApi(a, ""));
        if (!info.user_info || String(info.user_info.auth) !== "1") throw new Error("auth");
        localStorage.setItem(LS.xtream, JSON.stringify([...load(LS.xtream, []), a]));
      } else {
        const file = $("m3uFile").files[0];
        const url = $("m3uUrl").value.trim();
        const text = file ? await file.text() : url ? await fetchText(url) : "";
        if (!GaryM3U.parseM3U(text).length) throw new Error("empty");
        localStorage.setItem(LS.custom, text);
      }
      for (const id of ["xtServer", "xtUser", "xtPass", "m3uUrl", "m3uFile"]) $(id).value = "";
      dlg.close();
      loadAll();
    } catch (x) {
      err.textContent = x.message === "auth"
        ? "Kullanıcı adı veya parola kabul edilmedi."
        : "Bağlanılamadı. Bilgileri kontrol edin" + (proxy ? "." : " veya programı Baslat dosyasıyla açın.");
    }
  };

  // ---------- startup ----------
  $("search").oninput = (e) => { st.query = e.target.value.trim().toLocaleLowerCase("tr"); renderList(); };
  document.addEventListener("keydown", (e) => {
    if (!document.body.classList.contains("authed") || /INPUT|SELECT/.test(e.target.tagName) || dlg.open) return;
    if (e.key === "ArrowDown" || e.key === "PageDown") { e.preventDefault(); step(1); }
    if (e.key === "ArrowUp" || e.key === "PageUp") { e.preventDefault(); step(-1); }
    if (e.key === "f") video.requestFullscreen?.();
  });

  let started = false;
  async function start() {
    if (started) return;
    started = true;
    proxy = await detectProxy();
    loadAll();
  }
  if ([localStorage, sessionStorage].some((s) => s.getItem(LS.auth) === LOGIN_HASH)) enter();
})();
