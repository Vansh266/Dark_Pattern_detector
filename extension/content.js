let lastResult = null;

const SEVERITY_COLORS = { high: "#d32f2f", medium: "#ef6c00", low: "#f9a825" };
const SEVERITY_RANK = { low: 1, medium: 2, high: 3 };
const LEAF_ONLY = ["div", "li", "td"]; // only read these when they hold just text, to avoid duplicates

function getLabelText(node) {
  const parentLabel = node.closest("label");
  if (parentLabel) return parentLabel.innerText.trim();
  if (node.id) {
    const label = document.querySelector('label[for="' + node.id + '"]');
    if (label) return label.innerText.trim();
  }
  return "";
}

function collectElements() {
  const selector =
    "button, a, label, h1, h2, h3, h4, p, span, strong, b, " +
    "div, li, td, small, del, s, strike, " +
    "input[type='checkbox'], input[type='radio'], " +
    "[class*='timer'], [class*='countdown'], [class*='urgent']";

  const nodes = document.querySelectorAll(selector);
  const elements = [];
  let counter = 0;

  for (const node of nodes) {
    if (elements.length >= 500) break; // safety limit

    const tag = node.tagName.toLowerCase();
    if (LEAF_ONLY.includes(tag) && node.children.length > 0) continue;

    const rect = node.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue; // invisible

    const isInput = tag === "input";
    const text = isInput ? getLabelText(node) : node.innerText.trim();
    if (text === "") continue;
    if (!isInput && text.length > 250) continue; // long paragraphs aren't buttons or labels

    const style = window.getComputedStyle(node);
    node.setAttribute("data-dpd-id", counter);

    elements.push({
      id: counter,
      tag: tag,
      text: text.slice(0, 300),
      checked: node.checked === true,
      inputType: isInput ? node.type : "",
disabled: isInput ? node.disabled === true : false,
required: isInput ? node.required === true : false,
      rect: {
        top: Math.round(rect.top + window.scrollY),
        left: Math.round(rect.left + window.scrollX),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      },
      styles: {
        fontSize: style.fontSize,
        color: style.color,
        backgroundColor: style.backgroundColor,
        opacity: style.opacity
      }
    });
    counter++;
  }
  return elements;
}

function clearHighlights() {
  document.querySelectorAll("[data-dpd-outlined]").forEach((n) => {
    n.style.removeProperty("outline");
    n.style.removeProperty("outline-offset");
    n.removeAttribute("data-dpd-outlined");
  });
}

// Outlines the real element on the page, so it can never drift out of place
function highlightFindings(findings) {
  clearHighlights();

  const worst = {}; // element id -> most severe level
  findings.forEach((f) => {
    const current = worst[f.element_id];
    if (!current || SEVERITY_RANK[f.severity] > SEVERITY_RANK[current]) {
      worst[f.element_id] = f.severity;
    }
  });

  Object.keys(worst).forEach((id) => {
    const node = document.querySelector('[data-dpd-id="' + id + '"]');
    if (!node) return;
    // for a checkbox, outline its whole label so the box is easy to see
    const target = (node.tagName === "INPUT" && node.closest("label")) || node;
    target.style.setProperty("outline", "3px solid " + SEVERITY_COLORS[worst[id]], "important");
    target.style.setProperty("outline-offset", "3px", "important");
    target.setAttribute("data-dpd-outlined", "1");
  });
}

function runScan() {
  clearHighlights();
  document.querySelectorAll("[data-dpd-id]").forEach((n) => n.removeAttribute("data-dpd-id"));

  const elements = collectElements();
  console.log("Dark Pattern Detector: collected", elements.length, "elements");

  chrome.runtime.sendMessage(
    { type: "ANALYZE", url: window.location.href, elements: elements },
    (response) => {
      if (!response || response.error || !response.findings) {
        console.log("Dark Pattern Detector: backend problem", response);
        return;
      }
      lastResult = response;
      console.log("Dark Pattern Detector: findings", response.findings);
      highlightFindings(response.findings);
    }
  );
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_RESULT") {
    sendResponse(lastResult);
  }
  if (msg.type === "FOCUS") {
    const node = document.querySelector('[data-dpd-id="' + msg.id + '"]');
    if (node) node.scrollIntoView({ behavior: "smooth", block: "center" });
  }
});

runScan();