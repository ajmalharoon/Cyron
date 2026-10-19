/** Thin fetch wrapper around the Cyron API. Reads the backend URL and the
 * operator's API key from window.CYRON_ENV, written by env.js (see
 * frontend/public/env.js for local dev, frontend/docker-entrypoint.sh for
 * the container). */
const env = window.CYRON_ENV || { apiBase: "http://localhost:8000", apiKey: "" };

function headers(extra = {}) {
  const h = { "Content-Type": "application/json", ...extra };
  if (env.apiKey) h.Authorization = `Bearer ${env.apiKey}`;
  return h;
}

async function req(path, options = {}) {
  const res = await fetch(`${env.apiBase}${path}`, { ...options, headers: headers(options.headers) });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* no json body */ }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  health: () => req("/health"),
  getPhases: () => req("/api/phases"),
  createScan: (payload) => req("/api/scans", { method: "POST", body: JSON.stringify(payload) }),
  getScan: (id) => req(`/api/scans/${id}`),
  getFindings: (id) => req(`/api/scans/${id}/findings`),
  getReport: (id) => req(`/api/scans/${id}/report`),
  wsUrl: (id) => `${env.apiBase.replace(/^http/, "ws")}/ws/scans/${id}`,
};
