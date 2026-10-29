chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== "ANALYZE") return;

  fetch("http://127.0.0.1:8000/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: msg.url,
      elements: msg.elements
    })
  })
    .then(async (response) => {
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          `Backend HTTP ${response.status}: ` +
          JSON.stringify(data.detail ?? data)
        );
      }

      sendResponse(data);
    })
    .catch((error) => {
      sendResponse({ error: error.message });
    });

  return true;
});