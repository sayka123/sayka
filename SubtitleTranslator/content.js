(() => {
  // Sites that draw captions as page elements instead of <track> cues.
  const DOM_CAPTION_SELECTORS = [
    ".ytp-caption-window-container .ytp-caption-segment", // YouTube
    ".player-timedtext .player-timedtext-text-container", // Netflix
    ".atvwebplayersdk-captions-text",                     // Prime Video
    ".dss-subtitle-renderer-line",                        // Disney+
    ".vjs-text-track-display .vjs-text-track-cue",        // Video.js players
    ".jw-text-track-container .jw-text-track-cue",        // JW Player
  ];

  let settings = { enabled: true, target: "tr" };
  let lastSource = "";
  let requestId = 0;
  let overlay = null;
  const liftedCues = new Set();

  chrome.storage.sync.get(settings, (s) => { settings = s; });
  chrome.storage.onChanged.addListener((changes) => {
    for (const [k, v] of Object.entries(changes)) settings[k] = v.newValue;
    lastSource = "";
    hide();
  });

  function largestVideo() {
    let best = null, bestArea = 0;
    for (const v of document.querySelectorAll("video")) {
      const r = v.getBoundingClientRect();
      const area = r.width * r.height;
      if (area > bestArea) { best = v; bestArea = area; }
    }
    return bestArea > 0 ? best : null;
  }

  function cleanText(s) {
    return s.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
  }

  function domCaptionText() {
    for (const sel of DOM_CAPTION_SELECTORS) {
      const nodes = document.querySelectorAll(sel);
      if (nodes.length) {
        const text = cleanText(Array.from(nodes, (n) => n.textContent).join(" "));
        if (text) return text;
      }
    }
    return "";
  }

  function trackCaptionText(video) {
    for (const track of video.textTracks) {
      if (track.mode === "disabled") continue;
      if (track.kind !== "subtitles" && track.kind !== "captions") continue;
      const cues = track.activeCues;
      if (cues && cues.length) {
        // Raise native cues so the translation can sit beneath them.
        for (const c of cues) {
          if (c.line === "auto") {
            c.snapToLines = false;
            c.lineAlign = "end";
            c.line = 80; // % of video height; translation occupies the band below
            liftedCues.add(c);
          }
        }
        return cleanText(Array.from(cues, (c) => c.text || "").join(" "));
      }
    }
    return "";
  }

  function ensureOverlay() {
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "subtr-overlay";
      const line = document.createElement("span");
      line.className = "subtr-line";
      overlay.appendChild(line);
    }
    const host = document.fullscreenElement || document.body;
    if (overlay.parentNode !== host) host.appendChild(overlay);
    return overlay;
  }

  function hide() {
    if (overlay) overlay.style.display = "none";
    for (const c of liftedCues) {
      c.snapToLines = true;
      c.lineAlign = "start";
      c.line = "auto";
    }
    liftedCues.clear();
    document.documentElement.classList.remove("subtr-active");
  }

  function show(text, video) {
    const el = ensureOverlay();
    el.firstChild.textContent = text;
    const r = video.getBoundingClientRect();
    el.style.left = r.left + "px";
    el.style.width = r.width + "px";
    el.style.top = r.bottom - r.height * 0.04 + "px";
    el.style.fontSize = Math.max(14, Math.min(34, r.height * 0.045)) + "px";
    el.style.display = "block";
    document.documentElement.classList.add("subtr-active");
  }

  function tick() {
    const video = settings.enabled ? largestVideo() : null;
    if (!video) { hide(); return; }

    const source = domCaptionText() || trackCaptionText(video);
    if (!source) { lastSource = ""; hide(); return; }

    if (source === lastSource) {
      if (overlay && overlay.style.display === "block") show(overlay.firstChild.textContent, video);
      return;
    }
    lastSource = source;
    const id = ++requestId;
    chrome.runtime.sendMessage({ type: "translate", text: source, target: settings.target }, (res) => {
      if (chrome.runtime.lastError || id !== requestId) return;
      if (res?.ok && res.text) show(res.text, video);
      else hide();
    });
  }

  setInterval(tick, 250);
})();
