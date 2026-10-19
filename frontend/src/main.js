import { api } from "./api.js";
import { initParticles } from "./components/particles.js";
import { createMap3d } from "./components/map3d.js";
import { renderMap2d } from "./components/map2d.js";
import { renderPhaseList } from "./components/phaseList.js";
import { renderReport } from "./components/report.js";
import { initCursorGlow } from "./components/cursorGlow.js";

const $ = (sel) => document.querySelector(sel);

const els = {
  apiStatus: $("#api-status"),
  modeBtns: document.querySelectorAll(".mode-btn"),
  form: $("#target-form"),
  input: $("#target-input"),
  consent: $("#consent-check"),
  runBtn: $("#run-btn"),
  formMsg: $("#form-msg"),
  phaseModeLabel: $("#phase-mode-label"),
  phaseCount: $("#phase-count"),
  phaseList: $("#phase-list"),
  tabs: document.querySelectorAll(".tab"),
  views: { map3d: $("#view-map3d"), map2d: $("#view-map2d"), log: $("#view-log") },
  map3dCanvas: $("#map3d-canvas"),
  map2dSvg: $("#map2d"),
  runLog: $("#run-log"),
  reportBody: $("#report-body"),
  footMode: $("#foot-mode"),
};

let allPhases = [];
let mode = "active";
let currentScanId = null;
let currentTarget = "";
let ws = null;
let pollTimer = null;
let busy = false;
const runState = {}; // phase_id -> { status, toolsUsed, findingCount }
const toolSelection = {}; // phase_id -> Set<string> of selected tool labels; absent = all selected
let findingsByPhase = {};

const map3d = createMap3d(els.map3dCanvas);
initParticles($("#particles"));
initCursorGlow();

function phasesWithStatus() {
  return allPhases.map((p) => ({ ...p, status: runState[p.id]?.status || "pending" }));
}

function refreshRail() {
  const count = allPhases.filter((p) => p.mode === mode).length;
  els.phaseModeLabel.textContent = mode === "active" ? "Active phases" : "Passive phases";
  els.phaseCount.textContent = count ? `${count} phases` : "";
  renderPhaseList(els.phaseList, allPhases, mode, runState, toolSelection, busy);
}

function refreshMaps() {
  const withStatus = phasesWithStatus();
  map3d.setPhases(withStatus);
  map3d.setFindings(findingsByPhase);
  renderMap2d(els.map2dSvg, withStatus, findingsByPhase, currentTarget);
}

function setMode(next) {
  mode = next;
  els.modeBtns.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
  els.runBtn.textContent = `Run ${mode} recon`;
  els.footMode.textContent = `MODE: ${mode.toUpperCase()}`;
  refreshRail();
}

function appendLog(line) {
  const ts = new Date().toLocaleTimeString([], { hour12: false });
  const text = els.runLog.textContent === "No run yet. Enter a target above and start a scan."
    ? "" : els.runLog.textContent;
  els.runLog.textContent = `${text}${text ? "\n" : ""}${ts}  ${line}`;
  els.runLog.scrollTop = els.runLog.scrollHeight;
}

function guessTargetType(value) {
  if (/^\d{1,3}(\.\d{1,3}){3}\/\d{1,2}$/.test(value)) return "cidr";
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(value)) return "ip";
  return "domain";
}

function phaseMeta(phaseId) {
  return allPhases.find((p) => p.id === phaseId);
}

/** Toggles one tool chip. The selection set is materialized lazily — a
 * phase with no entry in `toolSelection` means "every tool on", so the
 * first click on one of its chips has to build the full set before
 * removing the one that was just clicked. */
function toggleTool(phaseId, tool) {
  if (busy) return;
  const phase = phaseMeta(phaseId);
  if (!phase) return;
  if (!toolSelection[phaseId]) toolSelection[phaseId] = new Set(phase.tools);
  const set = toolSelection[phaseId];
  if (set.has(tool)) set.delete(tool); else set.add(tool);
  refreshRail();
}

/** Converts the Set-based selection into the API's {phase_id: [tool,...]}
 * shape. Only phases the operator actually touched are included — an
 * untouched phase runs every tool, which the backend already defaults to. */
function buildToolsPayload() {
  const out = {};
  for (const [phaseId, set] of Object.entries(toolSelection)) out[phaseId] = [...set];
  return Object.keys(out).length ? out : undefined;
}

function connectSocket(scanId) {
  ws?.close();
  ws = new WebSocket(api.wsUrl(scanId));
  ws.onmessage = (ev) => {
    let evt;
    try { evt = JSON.parse(ev.data); } catch { return; }
    const phase = evt.phase_id ? phaseMeta(evt.phase_id) : null;
    const verb = phase?.mode === "passive" ? "listen" : "emit  ";
    switch (evt.event) {
      case "scan.started":
        appendLog(`scan started on ${evt.target}`);
        break;
      case "phase.started":
        runState[evt.phase_id] = { status: "running", toolsUsed: [], findingCount: null };
        refreshRail();
        appendLog(`${verb}  phase: ${evt.phase_name}`);
        break;
      case "tool.skipped":
        appendLog(`skip   ${(evt.tool || "").padEnd(22)} ${evt.reason || "unavailable"}`);
        break;
      case "tool.finished":
        appendLog(`${verb}  ${(evt.tool || "").padEnd(22)} ${evt.findings} finding(s)`);
        break;
      case "phase.finished":
        if (runState[evt.phase_id]) {
          runState[evt.phase_id].status = "completed";
          runState[evt.phase_id].toolsUsed = evt.tools_used || [];
        }
        refreshRail();
        break;
      case "scan.completed":
        appendLog(`scan completed — exposure score ${evt.exposure_score}/100`);
        break;
      default:
        break;
    }
  };
}

async function pollUntilDone(scanId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    let scan;
    try { scan = await api.getScan(scanId); } catch { return; }
    for (const pr of scan.phase_results || []) {
      runState[pr.phase_id] = {
        status: pr.status,
        toolsUsed: pr.tools_used || [],
        findingCount: runState[pr.phase_id]?.findingCount ?? null,
      };
    }
    refreshRail();
    if (scan.status === "completed" || scan.status === "failed" || scan.status === "cancelled") {
      clearInterval(pollTimer);
      ws?.close();
      await finishScan(scanId, scan.status);
    }
  }, 1200);
}

async function finishScan(scanId, status) {
  busy = false;
  els.runBtn.disabled = false;
  els.runBtn.textContent = `Run ${mode} recon`;

  if (status !== "completed") {
    appendLog(`scan ended with status: ${status}`);
    refreshRail();
    return;
  }

  let scan, findings;
  try {
    [scan, findings] = await Promise.all([api.getScan(scanId), api.getFindings(scanId)]);
  } catch (err) {
    appendLog(`could not load results: ${err.message}`);
    refreshRail();
    return;
  }

  // The findings endpoint doesn't carry phase_id, so findings are bucketed
  // into the phase whose [started_at, finished_at] window contains their
  // created_at timestamp. Phases run strictly one after another, so this is
  // exact, not a guess.
  findingsByPhase = {};
  const windows = (scan.phase_results || [])
    .filter((pr) => pr.started_at)
    .map((pr) => ({ id: pr.phase_id, start: new Date(pr.started_at), end: new Date(pr.finished_at || Date.now()) }));

  for (const f of findings) {
    const created = new Date(f.created_at);
    const win = windows.find((w) => created >= w.start && created <= w.end) || windows[windows.length - 1];
    if (!win) continue;
    (findingsByPhase[win.id] ||= []).push(f);
  }

  for (const pr of scan.phase_results || []) {
    runState[pr.phase_id] = {
      status: pr.status,
      toolsUsed: pr.tools_used || [],
      findingCount: (findingsByPhase[pr.phase_id] || []).length,
    };
  }
  refreshRail();
  refreshMaps();

  try {
    const report = await api.getReport(scanId);
    renderReport(els.reportBody, report.content);
  } catch (err) {
    els.reportBody.innerHTML = `<p class="muted">The report could not be generated: ${err.message}</p>`;
  }
}

async function onSubmit(e) {
  e.preventDefault();
  const value = els.input.value.trim();
  els.formMsg.textContent = "";
  if (!value) { els.formMsg.textContent = "Enter a target domain or IP address."; return; }
  if (!els.consent.checked) { els.formMsg.textContent = "Confirm you are authorized to test this target."; return; }

  if (value !== currentTarget) {
    for (const k of Object.keys(runState)) delete runState[k];
    findingsByPhase = {};
    els.runLog.textContent = "No run yet. Enter a target above and start a scan.";
  }
  currentTarget = value;

  busy = true;
  els.runBtn.disabled = true;
  els.runBtn.textContent = "Running…";
  refreshRail();

  try {
    const scan = await api.createScan({
      target: value,
      target_type: guessTargetType(value),
      modes: [mode],
      authorized: true,
      tools: buildToolsPayload(),
    });
    currentScanId = scan.id;
    connectSocket(scan.id);
    pollUntilDone(scan.id);
  } catch (err) {
    busy = false;
    els.formMsg.textContent = `Could not start the scan: ${err.message}`;
    els.runBtn.disabled = false;
    els.runBtn.textContent = `Run ${mode} recon`;
    refreshRail();
  }
}

function wireTabs() {
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      els.tabs.forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
      Object.entries(els.views).forEach(([key, el]) => (el.hidden = key !== tab.dataset.view));
      if (tab.dataset.view === "map3d") map3d.resize();
    });
  });
}

function wireToolChips() {
  els.phaseList.addEventListener("click", (e) => {
    const chip = e.target.closest(".phase-tool-chip");
    if (!chip || chip.disabled) return;
    toggleTool(chip.dataset.phase, chip.dataset.tool);
  });
}

async function init() {
  wireTabs();
  wireToolChips();
  els.modeBtns.forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  els.form.addEventListener("submit", onSubmit);

  api.health()
    .then(() => (els.apiStatus.textContent = "api connected"))
    .catch(() => (els.apiStatus.textContent = "api unreachable — run: docker compose up"));

  try {
    allPhases = await api.getPhases();
  } catch (err) {
    els.phaseList.innerHTML = `<p class="muted">Could not load the phase registry: ${err.message}</p>`;
    return;
  }
  setMode("active");
  refreshMaps();
}

init();
