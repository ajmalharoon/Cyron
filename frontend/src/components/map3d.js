/** 3D contact map: the target at the centre, one node per recon phase on a
 * sphere around it, findings orbiting their phase node. Violet = active,
 * silver = passive, octahedra mark high-severity findings. The whole scene
 * tilts gently toward the mouse even without dragging, and glow sprites
 * behind each node give it some bloom-like punch (three.js r128 has no
 * built-in post-processing bloom pass, so this fakes it with additive
 * blending). Drag for full manual rotation. */

let glowTexture = null;
function getGlowTexture(THREE) {
  if (glowTexture) return glowTexture;
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const ctx = c.getContext("2d");
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.35, "rgba(255,255,255,.55)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  glowTexture = new THREE.CanvasTexture(c);
  return glowTexture;
}

export function createMap3d(canvas) {
  if (!window.THREE) {
    return { setPhases() {}, setFindings() {}, resize() {} };
  }
  const THREE = window.THREE;
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.setClearColor(0x000000, 1);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1.3, 0.1, 50);
  camera.position.set(0, 0, 6.6);

  const world = new THREE.Group();
  const nodes = new THREE.Group();
  scene.add(world);
  world.add(nodes);

  // --- background starfield, pure shimmer, no interaction ---
  const STAR_COUNT = 420;
  const starPos = new Float32Array(STAR_COUNT * 3);
  for (let i = 0; i < STAR_COUNT; i++) {
    const r = 6 + Math.random() * 7;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    starPos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    starPos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    starPos[i * 3 + 2] = r * Math.cos(phi);
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
  const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({
    color: 0xcbb8ff, size: 0.028, transparent: true, opacity: 0.55, sizeAttenuation: true,
  }));
  scene.add(stars);

  const glowTex = getGlowTexture(THREE);
  const glowSpriteMat = (color, opacity) => new THREE.SpriteMaterial({
    map: glowTex, color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false,
  });

  const geoSphere = new THREE.SphereGeometry(1, 16, 12);
  const geoOcta = new THREE.OctahedronGeometry(1, 0);
  const VIOLET = 0x9b6bff, VIOLET_BRIGHT = 0xc9a6ff, SILVER = 0xf2f1f7;
  const matActive = new THREE.MeshBasicMaterial({ color: VIOLET_BRIGHT });
  const matPassive = new THREE.MeshBasicMaterial({ color: SILVER });
  const matGhost = new THREE.MeshBasicMaterial({ color: 0x4a4357 });
  const lineActive = new THREE.LineBasicMaterial({ color: VIOLET, transparent: true, opacity: 0.75 });
  const linePassive = new THREE.LineBasicMaterial({ color: SILVER, transparent: true, opacity: 0.5 });

  const core = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.46, 1),
    new THREE.MeshBasicMaterial({ color: VIOLET_BRIGHT, wireframe: true })
  );
  const coreGlow = new THREE.Sprite(glowSpriteMat(VIOLET, 0.9));
  coreGlow.scale.set(2.3, 2.3, 1);
  const coreDot = new THREE.Mesh(new THREE.IcosahedronGeometry(0.16, 0), matPassive);
  const haze = new THREE.Mesh(
    new THREE.SphereGeometry(2.6, 24, 16),
    new THREE.MeshBasicMaterial({ color: VIOLET, wireframe: true, transparent: true, opacity: 0.08 })
  );
  world.add(coreGlow, core, coreDot, haze);

  // --- interaction: drag for direct control, bare mouse-move for a gentle
  // continuous tilt toward the pointer (parallax), blended each frame ---
  let drag = null;
  let targetTiltX = 0, targetTiltY = 0;
  let tiltX = 0, tiltY = 0;

  canvas.addEventListener("pointerdown", (e) => { drag = [e.clientX, e.clientY]; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (drag) {
      world.rotation.y += (e.clientX - drag[0]) * 0.008;
      world.rotation.x += (e.clientY - drag[1]) * 0.008;
      drag = [e.clientX, e.clientY];
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    targetTiltY = nx * 0.5;
    targetTiltX = ny * 0.35;
  });
  canvas.addEventListener("pointerleave", () => { targetTiltX = 0; targetTiltY = 0; });
  canvas.addEventListener("pointerup", () => (drag = null));
  canvas.addEventListener("pointercancel", () => (drag = null));

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  addEventListener("resize", resize);
  resize();

  let phases = [];
  let findingsByPhase = {};

  function rebuild() {
    for (const o of [...nodes.children]) {
      nodes.remove(o);
      o.geometry?.dispose?.();
    }
    const n = phases.length || 1;
    phases.forEach((phase, i) => {
      const y = 1 - (2 * (i + 0.5)) / n;
      const radius = Math.sqrt(1 - y * y);
      const theta = i * 2.4;
      const pos = new THREE.Vector3(Math.cos(theta) * radius * 2.1, y * 2.1, Math.sin(theta) * radius * 2.1);
      const mat = phase.mode === "active" ? matActive : matPassive;
      const lineMat = phase.mode === "active" ? lineActive : linePassive;
      const glowColor = phase.mode === "active" ? VIOLET : SILVER;

      const finds = findingsByPhase[phase.id] || [];
      if (!finds.length && phase.status !== "completed") {
        const ghost = new THREE.Mesh(geoSphere, matGhost);
        ghost.position.copy(pos);
        ghost.scale.setScalar(0.035);
        nodes.add(ghost);
        return;
      }

      nodes.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), pos]), lineMat));

      const glow = new THREE.Sprite(glowSpriteMat(glowColor, 0.75));
      glow.position.copy(pos);
      glow.scale.set(0.55, 0.55, 1);
      nodes.add(glow);

      const node = new THREE.Mesh(geoSphere, mat);
      node.position.copy(pos);
      node.scale.setScalar(0.1);
      nodes.add(node);

      finds.forEach((f, j) => {
        const k = (j / Math.max(finds.length, 1)) * 6.283 + i;
        const off = pos.clone().add(new THREE.Vector3(Math.cos(k), Math.sin(k * 1.7), Math.sin(k)).multiplyScalar(0.45));
        const isHigh = f.severity === "high";
        const mesh = new THREE.Mesh(isHigh ? geoOcta : geoSphere, mat);
        mesh.position.copy(off);
        mesh.scale.setScalar(isHigh ? 0.13 : f.severity === "medium" ? 0.09 : 0.055);
        nodes.add(mesh);
        if (isHigh) {
          const fGlow = new THREE.Sprite(glowSpriteMat(0xffffff, 0.8));
          fGlow.position.copy(off);
          fGlow.scale.set(0.3, 0.3, 1);
          nodes.add(fGlow);
        }
        nodes.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([pos, off]), lineMat));
      });
    });
  }

  (function loop() {
    requestAnimationFrame(loop);
    if (!reduceMotion) {
      if (!drag) world.rotation.y += 0.0018;
      tiltX += (targetTiltX - tiltX) * 0.045;
      tiltY += (targetTiltY - tiltY) * 0.045;
      world.rotation.x = world.rotation.x * 0.95 + tiltX * 0.05;
      // Mouse-driven yaw rides on top of the slow auto-rotation rather than
      // fighting it: a separate offset, not a direct overwrite.
      world.rotation.y += (tiltY - (world.userData.lastTiltY || 0)) * 0.08;
      world.userData.lastTiltY = tiltY;
      core.rotation.y += 0.012;
      core.rotation.x += 0.006;
      stars.rotation.y += 0.00025;
    }
    renderer.render(scene, camera);
  })();

  return {
    setPhases(list) { phases = list; rebuild(); },
    setFindings(byPhase) { findingsByPhase = byPhase; rebuild(); },
    resize,
  };
}
