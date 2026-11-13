const enabled = document.getElementById("enabled");
const target = document.getElementById("target");

chrome.storage.sync.get({ enabled: true, target: "tr" }, (s) => {
  enabled.checked = s.enabled;
  target.value = s.target;
});

enabled.addEventListener("change", () => chrome.storage.sync.set({ enabled: enabled.checked }));
target.addEventListener("change", () => chrome.storage.sync.set({ target: target.value }));
