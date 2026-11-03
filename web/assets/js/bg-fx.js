// td2 Division background — the one piece of this atmosphere that needs JS:
// a quiet drift of dust and ember particles across the whole viewport.
// Everything else (glow blobs, map, SHD rings, scan pass, grain) is CSS/SVG,
// cheap and GPU-composited. This stays a single <canvas>, driven by
// requestAnimationFrame, with no external assets and no game footage —
// copyright-clean and zero extra bandwidth on Cloudflare Pages.
//
// Tuning knobs live in DIVISION_FX below; everything else reads from it.
(() => {
  const canvas = document.getElementById("td2-bg-canvas");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");

  const reduceQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const mobileQuery = window.matchMedia("(max-width: 700px)");

  // ---- configuration (safe to tweak) ----------------------------------
  const DIVISION_FX = {
    particleCount: { desktop: [25, 45], mobile: [8, 15] }, // [min, max], scaled by viewport area
    particleSpeed: 0.09,     // px/frame base drift speed
    emberRatio: 0.16,        // share of particles rendered as a warm ember instead of grey dust
    parallaxStrength: 6,     // px, desktop pointer parallax cap (see index.html hero script — unrelated layer, kept separate)
    maxPixelRatio: 1.5,      // perf cap: never render the canvas sharper than this, even on hi-dpi screens
  };

  let w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, DIVISION_FX.maxPixelRatio);
  let particles = [];
  let reduce = reduceQuery.matches;
  let mobile = mobileQuery.matches;

  function sizeCanvas() {
    dpr = Math.min(window.devicePixelRatio || 1, DIVISION_FX.maxPixelRatio);
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function makeParticles() {
    const [min, max] = mobile ? DIVISION_FX.particleCount.mobile : DIVISION_FX.particleCount.desktop;
    const density = 22000; // px^2 per particle — sparse, never a snowstorm
    const count = Math.max(min, Math.min(max, Math.round((w * h) / density)));
    particles = Array.from({ length: count }, () => spawnParticle(Math.random() * h));
  }

  function spawnParticle(y) {
    const isEmber = Math.random() < DIVISION_FX.emberRatio;
    const size = isEmber ? 1 + Math.random() * 1.6 : 0.7 + Math.random() * 1.3;
    const speed = DIVISION_FX.particleSpeed * (0.5 + Math.random());
    return {
      x: Math.random() * w,
      y: y === undefined ? h + size * 4 : y,
      size,
      isEmber,
      // mostly drifting up, with a gentle diagonal sway — never straight rain/snow
      vx: (Math.random() - 0.5) * speed * 0.6,
      vy: -speed * (0.7 + Math.random() * 0.6),
      drift: Math.random() * Math.PI * 2,
      driftSpeed: 0.002 + Math.random() * 0.004,
      baseOpacity: isEmber ? 0.35 + Math.random() * 0.35 : 0.12 + Math.random() * 0.22,
    };
  }

  function step(t) {
    ctx.clearRect(0, 0, w, h);
    for (const p of particles) {
      p.drift += p.driftSpeed;
      p.x += p.vx + Math.sin(p.drift) * 0.05;
      p.y += p.vy;
      // gently recycle off the top (or sides) back in at the bottom — no jarring reset visible mid-view
      if (p.y < -p.size * 4 || p.x < -10 || p.x > w + 10) {
        Object.assign(p, spawnParticle());
      }
      const flicker = p.isEmber ? 0.8 + Math.sin(t / 900 + p.drift) * 0.2 : 1;
      ctx.globalAlpha = p.baseOpacity * flicker;
      ctx.fillStyle = p.isEmber ? "rgba(255,138,61,1)" : "rgba(215,222,227,1)";
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  function renderStaticFrame() {
    sizeCanvas();
    makeParticles();
    step(0);
  }

  if (reduce) { renderStaticFrame(); return; }

  let raf = null;
  function loop(t) { step(t); raf = requestAnimationFrame(loop); }
  function start() { if (raf === null && !reduce) raf = requestAnimationFrame(loop); }
  function stop() { if (raf !== null) { cancelAnimationFrame(raf); raf = null; } }

  sizeCanvas();
  makeParticles();
  start();

  let resizeT;
  window.addEventListener("resize", () => {
    clearTimeout(resizeT);
    resizeT = setTimeout(() => {
      mobile = mobileQuery.matches;
      sizeCanvas();
      makeParticles();
    }, 150);
  }, { passive: true });

  document.addEventListener("visibilitychange", () => {
    document.hidden ? stop() : start();
  });

  // live-toggle if the OS-level reduced-motion preference changes mid-session
  reduceQuery.addEventListener?.("change", (e) => {
    reduce = e.matches;
    if (reduce) { stop(); renderStaticFrame(); } else { start(); }
  });
})();
