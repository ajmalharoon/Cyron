/** A soft violet glow that trails the mouse across the whole page. The
 * native cursor is left alone (hiding it would break usability on text
 * inputs and buttons) — this is a decorative layer on top, with a tight
 * bright core and a larger, laggier blurred halo for a bit of depth. Does
 * nothing on touch-only devices, where there's no persistent pointer. */
export function initCursorGlow() {
  if (matchMedia("(hover: none), (pointer: coarse)").matches) return;
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const halo = document.createElement("div");
  const core = document.createElement("div");
  halo.className = "cursor-glow cursor-glow--halo";
  core.className = "cursor-glow cursor-glow--core";
  document.body.append(halo, core);

  let mx = innerWidth / 2, my = innerHeight / 2; // target (real cursor)
  let hx = mx, hy = my; // halo's current, lagging position
  let visible = false;

  addEventListener("mousemove", (e) => {
    mx = e.clientX; my = e.clientY;
    core.style.transform = `translate(${mx}px, ${my}px)`;
    if (!visible) { visible = true; halo.style.opacity = "1"; core.style.opacity = "1"; }
  }, { passive: true });

  addEventListener("mouseleave", () => { halo.style.opacity = "0"; core.style.opacity = "0"; });
  document.addEventListener("mousedown", () => halo.classList.add("is-active"));
  document.addEventListener("mouseup", () => halo.classList.remove("is-active"));

  if (reduceMotion) {
    halo.style.transform = `translate(${mx}px, ${my}px)`;
  } else {
    (function loop() {
      hx += (mx - hx) * 0.12;
      hy += (my - hy) * 0.12;
      halo.style.transform = `translate(${hx}px, ${hy}px)`;
      requestAnimationFrame(loop);
    })();
  }
}
