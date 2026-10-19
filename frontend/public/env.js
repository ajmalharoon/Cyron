// Checked-in default for local development (e.g. `npm run dev`, or opening
// index.html directly). Inside Docker this file is overwritten at container
// start by docker-entrypoint.sh, from CYRON_API_BASE / CYRON_API_KEY.
window.CYRON_ENV = {
  apiBase: "http://localhost:8000",
  apiKey: ""
};
