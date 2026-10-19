import { SEVERITY_CLASS } from "../data/severity.js";

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function inline(text) {
  let out = esc(text);
  out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Wrap a bare severity word (table cell, or after a "Rating:" label) in a pill.
  out = out.replace(/\b(High|Medium|Low|Informational)\b/g, (m) => {
    const key = m.toLowerCase() === "informational" ? "info" : m.toLowerCase();
    const cls = SEVERITY_CLASS[key];
    return cls ? `<span class="sev ${cls}">${m}</span>` : m;
  });
  return out;
}

/** Tiny Markdown → HTML converter, tailored to exactly what
 * backend/app/reports/generator.py emits: #/##/### headings, pipe tables
 * with a --- separator row, **bold**, numbered-list lines, and plain
 * paragraphs. Not a general-purpose Markdown parser. */
function markdownToHtml(md) {
  const lines = md.split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    if (/^#\s+/.test(line)) { out.push(`<h1>${inline(line.replace(/^#\s+/, ""))}</h1>`); i++; continue; }
    if (/^##\s+/.test(line)) { out.push(`<h2>${inline(line.replace(/^##\s+/, ""))}</h2>`); i++; continue; }
    if (/^###\s+/.test(line)) { out.push(`<h3>${inline(line.replace(/^###\s+/, ""))}</h3>`); i++; continue; }

    if (/^\|/.test(line) && /^\|[\s:|-]+\|$/.test(lines[i + 1] || "")) {
      const headerCells = line.split("|").slice(1, -1).map((c) => c.trim());
      i += 2;
      const rows = [];
      while (i < lines.length && /^\|/.test(lines[i])) {
        rows.push(lines[i].split("|").slice(1, -1).map((c) => c.trim()));
        i++;
      }
      out.push(
        "<table><thead><tr>" + headerCells.map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>" +
        rows.map((r) => "<tr>" + r.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>").join("") +
        "</tbody></table>"
      );
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i++;
      }
      out.push("<ol>" + items.map((it) => `<li>${inline(it)}</li>`).join("") + "</ol>");
      continue;
    }

    if (line.trim() === "") { i++; continue; }

    // Plain paragraph: gather until the next blank line or block start.
    const para = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^#{1,3}\s|^\||^\d+\.\s/.test(lines[i])) {
      para.push(lines[i].replace(/\s{2,}$/, "")); // trailing "  " was a markdown line-break hint
      i++;
    }
    out.push(`<p>${para.map(inline).join("<br>")}</p>`);
  }
  return out.join("\n");
}

export function renderReport(container, markdown) {
  container.innerHTML = markdownToHtml(markdown) +
    `<div class="report-actions">
      <button type="button" data-action="copy">Copy as Markdown</button>
      <button type="button" data-action="print">Print or save as PDF</button>
    </div>`;

  container.querySelector('[data-action="copy"]')?.addEventListener("click", async (e) => {
    try {
      await navigator.clipboard.writeText(markdown);
      e.target.textContent = "Copied";
    } catch {
      e.target.textContent = "Copy is blocked here";
    }
  });
  container.querySelector('[data-action="print"]')?.addEventListener("click", () => {
    try { window.print(); } catch { /* ignore */ }
  });
}
