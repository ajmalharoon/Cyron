const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/** Renders the phase rail for one mode, with each phase's tools as
 * individually selectable chips.
 *
 * `runState` maps phase_id -> { status, toolsUsed, findingCount }.
 * `selection` maps phase_id -> Set<string> of tool labels to run; a phase
 * absent from `selection` is treated as "every tool selected" (the default).
 * `locked`, while true, renders the chips inert (a scan is in flight, so
 * toggling them now wouldn't affect it).
 *
 * Returns the list of phases actually rendered (for the caller's own use). */
export function renderPhaseList(container, phases, mode, runState = {}, selection = {}, locked = false) {
  const inMode = phases.filter((p) => p.mode === mode);
  container.innerHTML = inMode.map((p) => {
    const state = runState[p.id] || { status: "pending", toolsUsed: [], findingCount: 0 };
    const cls = state.status === "running" ? "running" : state.status === "completed" ? "done" : "";
    const pct = state.status === "completed" ? 100 : state.status === "running" ? 60 : 0;
    const meta = state.status === "completed"
      ? (state.findingCount == null ? "completed" : `${state.findingCount} finding${state.findingCount === 1 ? "" : "s"}`)
      : state.status === "running" ? "running…" : esc(p.description);
    const picked = selection[p.id]; // Set | undefined (undefined = all on)
    const selectedCount = picked ? picked.size : p.tools.length;

    return `<div class="phase-row ${cls}" data-phase="${p.id}">
      <div class="phase-name">${esc(p.name)}</div>
      <div class="phase-meta">${meta} <span class="tool-count">· ${selectedCount}/${p.tools.length} tools</span></div>
      <div class="phase-tools">${p.tools.map((t) => {
        const on = picked ? picked.has(t) : true;
        return `<button type="button" class="phase-tool-chip" data-phase="${p.id}" data-tool="${esc(t)}"
          aria-pressed="${on}" ${locked ? "disabled" : ""}>${esc(t)}</button>`;
      }).join("")}</div>
      <div class="phase-bar"><i style="width:${pct}%"></i></div>
    </div>`;
  }).join("");
  return inMode;
}
