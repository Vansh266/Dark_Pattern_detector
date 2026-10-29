function pretty(category) {
  return category.replace(/_/g, " ");
}

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tabId = tabs[0].id;
  const pageUrl = tabs[0].url;

  chrome.tabs.sendMessage(tabId, { type: "GET_RESULT" }, (result) => {
    if (chrome.runtime.lastError || !result) {
      document.getElementById("band").textContent = "No result yet";
      document.getElementById("summary").textContent =
        "Open a normal website, refresh it, then reopen this popup.";
      return;
    }
    if (result.error) {
      document.getElementById("band").textContent =
        "Analysis failed";

      document.getElementById("summary").textContent =
        result.error +
        " — Check that the FastAPI backend is running.";

      return;
    }
    document.getElementById("score").textContent = result.risk_score + " / 100";
    document.getElementById("band").textContent = "Manipulation risk: " + result.risk_band;
    document.getElementById("summary").textContent = result.summary;

    const button = document.getElementById("openReport");
    button.style.display = "inline-block";
    button.addEventListener("click", () => {
      chrome.storage.local.set({ report: result, pageUrl: pageUrl }, () => {
        chrome.tabs.create({ url: chrome.runtime.getURL("report.html") });
      });
    });

    const list = document.getElementById("findings");
    result.findings.forEach((f) => {
      const li = document.createElement("li");
      li.className = f.severity;

      const title = document.createElement("div");
      title.className = "title";
      title.textContent = pretty(f.category) + " (" + f.severity + ")";

      const evidence = document.createElement("div");
      evidence.className = "evidence";
      evidence.textContent = f.evidence;

      li.append(title, evidence);
      li.addEventListener("click", () => {
        chrome.tabs.sendMessage(tabId, { type: "FOCUS", id: f.element_id });
      });
      list.appendChild(li);
    });
  });
});