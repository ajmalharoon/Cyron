/** Lightweight 2D-canvas particle swarm for the hero backdrop. Not three.js —
 * this is cheap enough to run behind text without competing with the 3D map
 * for a WebGL context. Particles drift along a slowly rotating double-helix
 * path, echoing the flowing dust/comet shapes in the reference video. */
export function initParticles(canvas) {
  const ctx = canvas.getContext("2d");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let w = 0, h = 0, dpr = Math.min(devicePixelRatio || 1, 2);
  let particles = [];
  const COUNT = 260;

  function resize() {
    w = canvas.clientWidth;
    h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function seed() {
    particles = Array.from({ length: COUNT }, (_, i) => ({
      t: Math.random() * Math.PI * 2,
      band: i % 2, // two interleaved helix strands
      speed: 0.12 + Math.random() * 0.1,
      r: Math.random() * 1.6 + 0.4,
      depth: Math.random(),
    }));
  }

  let frame = 0;
  function draw() {
    frame += reduceMotion ? 0 : 1;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h * 0.52;
    const spanX = Math.min(w * 0.42, 420);
    const spanY = h * 0.34;

    for (const p of particles) {
      const t = p.t + frame * 0.0022 * p.speed;
      const x = cx + Math.sin(t * 2 + p.band * Math.PI) * spanX * (0.4 + 0.6 * p.depth);
      const y = cy + Math.cos(t) * spanY * p.depth - spanY * 0.5;
      const z = (Math.sin(t) + 1) / 2;
      const alpha = 0.12 + z * 0.5 * p.depth;
      const violet = p.band === 0;
      ctx.beginPath();
      ctx.arc(x, y, p.r * (0.6 + z * 0.8), 0, Math.PI * 2);
      ctx.fillStyle = violet
        ? `rgba(139,92,246,${alpha})`
        : `rgba(233,232,238,${alpha * 0.8})`;
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }

  resize();
  seed();
  draw();
  addEventListener("resize", resize);
}
