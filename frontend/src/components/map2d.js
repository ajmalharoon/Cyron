const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/** Renders the same phase/finding data as a flat SVG radial map — the
 * fallback view for browsers or devices where the 3D map is heavier than
 * it's worth. */
export function renderMap2d(svg, phases, findingsByPhase, targetLabel) {
  const cx = 380, cy = 310;
  const n = phases.length || 1;
  let body = "";

  phases.forEach((phase, i) => {
    const finds = findingsByPhase[phase.id] || [];
    if (!finds.length && phase.status !== "completed") return;
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    const color = phase.mode === "active" ? "var(--violet)" : "var(--silver)";
    const x = cx + 150 * Math.cos(angle);
    const y = cy + 150 * Math.sin(angle);
    const cosA = Math.cos(angle);
    body += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="${color}" stroke-width="1.5" opacity=".55"/>`;

    finds.forEach((f, j) => {
      const b = angle + (j - (finds.length - 1) / 2) * 0.12;
      const lx = x + 90 * Math.cos(b), ly = y + 90 * Math.sin(b);
      const r = f.severity === "high" ? 7 : f.severity === "medium" ? 5 : 3.5;
      body += `<line x1="${x}" y1="${y}" x2="${lx}" y2="${ly}" stroke="${color}" stroke-opacity=".4"/>` +
        `<circle cx="${lx}" cy="${ly}" r="${r}" fill="${color}" stroke="#050506"><title>${esc(f.title)}</title></circle>`;
    });

    body += `<circle cx="${x}" cy="${y}" r="7" fill="${color}"/>` +
      `<text x="${cx + 190 * cosA}" y="${cy + 190 * Math.sin(angle) + 4}" text-anchor="${Math.abs(cosA) < 0.3 ? "middle" : cosA > 0 ? "start" : "end"}" class="map2d-label">${esc(phase.name)}</text>`;
  });

  svg.innerHTML = `<style>.map2d-label{font:600 11px 'JetBrains Mono',monospace;fill:var(--silver)}</style>` +
    body +
    `<circle cx="${cx}" cy="${cy}" r="40" fill="#0B0B0F" stroke="var(--violet)"/>` +
    `<text x="${cx}" y="${cy + 4}" text-anchor="middle" class="map2d-label">${esc((targetLabel || "target").slice(0, 14))}</text>`;
}
