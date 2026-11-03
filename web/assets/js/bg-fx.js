// td2 hero background: a quiet tactical "radar network" — small drifting nodes,
// linked by faint lines when close, like a HUD scan. No external assets, no game
// footage (keeps this copyright-clean and bandwidth-free on Cloudflare Pages).
(() => {
  const canvas = document.getElementById("td2-hero-canvas");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  const hero = canvas.closest(".td2-hero");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
  let nodes = [];
  const LINK_DIST = 130;
  const SPEED = 0.18;

  function sizeCanvas() {
    const r = hero.getBoundingClientRect();
    w = r.width; h = r.height;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function makeNodes() {
    const density = 16000; // px^2 per node
    const count = Math.max(14, Math.min(60, Math.round((w * h) / density)));
    nodes = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * SPEED,
      vy: (Math.random() - 0.5) * SPEED,
    }));
  }

  function step() {
    ctx.clearRect(0, 0, w, h);
    for (const n of nodes) {
      n.x += n.vx; n.y += n.vy;
      if (n.x < 0 || n.x > w) n.vx *= -1;
      if (n.y < 0 || n.y > h) n.vy *= -1;
      n.x = Math.max(0, Math.min(w, n.x));
      n.y = Math.max(0, Math.min(h, n.y));
    }
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < LINK_DIST) {
          ctx.strokeStyle = `rgba(255,109,16,${(1 - dist / LINK_DIST) * 0.22})`;
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    for (const n of nodes) {
      ctx.fillStyle = "rgba(255,138,61,.55)";
      ctx.beginPath(); ctx.arc(n.x, n.y, 1.6, 0, Math.PI * 2); ctx.fill();
    }
  }

  function drawStaticFrame() {
    sizeCanvas();
    makeNodes();
    step();
  }

  if (reduce) { drawStaticFrame(); return; }

  let raf = null;
  function loop() { step(); raf = requestAnimationFrame(loop); }
  function start() { if (raf === null) loop(); }
  function stop() { if (raf !== null) { cancelAnimationFrame(raf); raf = null; } }

  sizeCanvas();
  makeNodes();
  start();

  let resizeT;
  window.addEventListener("resize", () => {
    clearTimeout(resizeT);
    resizeT = setTimeout(() => { sizeCanvas(); makeNodes(); }, 150);
  });
  document.addEventListener("visibilitychange", () => {
    document.hidden ? stop() : start();
  });
})();
