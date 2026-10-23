function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

chrome.storage.local.get(["report", "pageUrl"], (data) => {
  const r = data.report;
  const root = document.getElementById("root");

  if (!r) {
    root.append(el("p", "", "No report found. Scan a page, then click Open full report in the popup."));
    return;
  }

  root.append(el("h1", "", "Manipulation Risk Report"));
  root.append(el("div", "url", data.pageUrl || ""));

  const bandClass = "band-" + r.risk_band.replace(/\s/g, "").toLowerCase();
  const scoreBox = el("div", "scorebox " + bandClass);
  scoreBox.append(el("div", "score", r.risk_score + " / 100"));
  scoreBox.append(el("div", "band", r.risk_band));
  root.append(scoreBox);

  const bar = el("div", "bar");
  const fill = el("div", "fill");
  fill.style.width = r.risk_score + "%";
  bar.append(fill);
  root.append(bar);

  root.append(el("p", "summary", r.summary));

  root.append(el("h2", "", "How this page tries to influence you"));
  if (r.tactics.length === 0) {
    root.append(el("p", "", "Nothing was flagged."));
  }
  r.tactics.forEach((t) => {
    const card = el("div", "card sev-" + t.worst_severity);
    card.append(el("h3", "", t.title + " (" + t.count + " found, " + t.worst_severity + " severity)"));
    card.append(el("p", "", t.how_it_works));
    const list = el("ul");
    t.examples.forEach((e) => list.append(el("li", "", "Evidence: " + e)));
    card.append(list);
    card.append(el("p", "advice", "What you can do: " + t.advice));
    root.append(card);
  });

  root.append(el("h2", "", "All findings"));
  const table = el("table");
  const head = el("tr");
  ["Pattern", "Severity", "Method", "Confidence", "Evidence"].forEach((h) => head.append(el("th", "", h)));
  table.append(head);
  r.findings.forEach((f) => {
    const row = el("tr");
    row.append(el("td", "", f.category.replace(/_/g, " ")));
    row.append(el("td", "", f.severity));
    row.append(el("td", "", f.method));
    row.append(el("td", "", f.confidence == null ? "n/a (rule)" : Math.round(f.confidence * 100) + "%"));
    row.append(el("td", "", f.evidence));
    table.append(row);
  });
  root.append(table);

  root.append(el("h2", "", "What this report does not cover"));
  const limits = el("ul");
  [
    "Only visible text, buttons, links, labels and headings are checked. Images, videos and content loaded after the scan are not analysed.",
    "It cannot verify claims such as stock levels or deadlines, so urgency findings are low severity.",
    "Rule-based findings have no confidence value. Machine-learning findings show the model's confidence, which is not a guarantee.",
    "The score reflects how manipulative the design looks, not the intent or honesty of the site's owner."
  ].forEach((t) => limits.append(el("li", "", t)));
  root.append(limits);
});