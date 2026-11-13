// Translation runs here because content scripts are bound by the page's CORS rules.
const cache = new Map();
const CACHE_LIMIT = 1000;

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type !== "translate") return;
  translate(msg.text, msg.target).then(
    (text) => sendResponse({ ok: true, text }),
    (err) => sendResponse({ ok: false, error: String(err) })
  );
  return true;
});

async function translate(text, target) {
  const key = target + "\u0000" + text;
  if (cache.has(key)) return cache.get(key);

  const url =
    "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&dt=t" +
    "&tl=" + encodeURIComponent(target) +
    "&q=" + encodeURIComponent(text);
  const res = await fetch(url);
  if (!res.ok) throw new Error("HTTP " + res.status);
  const data = await res.json();

  const sourceLang = data[2];
  // Already in the chosen language: nothing to show.
  const out = sourceLang && sourceLang.split("-")[0] === target.split("-")[0]
    ? null
    : (data[0] || []).map((part) => part[0]).join("");

  if (cache.size >= CACHE_LIMIT) cache.delete(cache.keys().next().value);
  cache.set(key, out);
  return out;
}
