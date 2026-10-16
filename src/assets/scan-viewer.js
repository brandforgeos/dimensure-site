/* Dimensure sample point-cloud viewer.
   Procedurally generated, illustrative scans drawn to a <canvas> - no libraries. */
(function () {
  'use strict';

  // deviation colour ramp: blue (low) -> mint (in tolerance) -> amber -> coral (high)
  var STOPS = [[-1, [111, 183, 255]], [-0.3, [142, 216, 191]], [0.3, [142, 216, 191]], [0.65, [242, 184, 75]], [1, [240, 138, 108]]];
  function ramp(t) {
    t = Math.max(-1, Math.min(1, t));
    for (var i = 0; i < STOPS.length - 1; i++) {
      var a = STOPS[i], b = STOPS[i + 1];
      if (t <= b[0]) {
        var k = (t - a[0]) / (b[0] - a[0]);
        return [a[1][0] + (b[1][0] - a[1][0]) * k, a[1][1] + (b[1][1] - a[1][1]) * k, a[1][2] + (b[1][2] - a[1][2]) * k];
      }
    }
    return STOPS[STOPS.length - 1][1];
  }
  var GREY = [205, 216, 214], DIM = [120, 140, 140], MINT = [142, 216, 191];

  // seeded random so every visitor sees the same sample
  function rng(seed) { return function () { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }; }
  function bump(x, z, cx, cz, r, h) { var d = ((x - cx) * (x - cx) + (z - cz) * (z - cz)) / (r * r); return h * Math.exp(-d); }

  function makeRoad() {
    var P = [], r = rng(7), L = 44, W = 7.3;
    for (var i = 0; i < 26000; i++) {
      var x = (r() - 0.5) * L, z = (r() - 0.5) * W;
      var camber = -Math.abs(z) * 0.025;
      var dev = bump(x, z, 9, 1.4, 2.6, 0.012) - bump(x, z, -12, -2, 2.2, 0.011) + bump(x, z, -3, 2.6, 1.5, 0.007) + (r() - 0.5) * 0.003;
      P.push([x, camber + dev, z, ramp(dev / 0.015)]);
    }
    for (i = 0; i < 9000; i++) { // kerbs and footpaths
      x = (r() - 0.5) * L; var side = r() < 0.5 ? -1 : 1, t = r();
      if (t < 0.35) P.push([x, -0.09 + 0.125 * r(), side * (W / 2 + 0.06 * r()), GREY]);
      else P.push([x, 0.03, side * (W / 2 + 0.15 + r() * 1.8), DIM]);
    }
    for (var h = -2; h <= 2; h++) { // house shells either side
      for (i = 0; i < 1300; i++) {
        var hx = h * 9 + (r() - 0.5) * 7, side2 = (h % 2 === 0) ? 1 : -1, face = r();
        var hz = side2 * (W / 2 + 7 + (face < 0.5 ? 0 : r() * 6)), hy = r() * 5.2;
        P.push([hx, hy, hz, face < 0.5 ? GREY : DIM]);
      }
    }
    return { pts: P, scale: 1 / 40, pitch: 0.62, yaw: 0.55, legend: true };
  }

  function makeSlab() {
    var P = [], r = rng(11), X = 10.4, Z = 8.2;
    for (var i = 0; i < 22000; i++) {
      var x = (r() - 0.5) * X, z = (r() - 0.5) * Z;
      var dev = bump(x, z, 2.6, -1.8, 1.8, 0.008) - bump(x, z, -3, 2, 1.4, 0.006) + (r() - 0.5) * 0.002;
      P.push([x, dev, z, ramp(dev / 0.01)]);
    }
    for (i = 0; i < 9000; i++) { // perimeter walls to DPC
      var e = Math.floor(r() * 4), t = (r() - 0.5), y = r() * 0.6;
      var px = e < 2 ? t * X : (e === 2 ? -X / 2 : X / 2), pz = e < 2 ? (e === 0 ? -Z / 2 : Z / 2) : t * Z;
      P.push([px + (r() - 0.5) * 0.1, y, pz + (r() - 0.5) * 0.1, GREY]);
    }
    for (i = 0; i < 2200; i++) { // internal wall line
      P.push([0.8 + (r() - 0.5) * 0.1, r() * 0.6, (r() - 0.5) * Z, DIM]);
    }
    [[-3.6, -2.4], [3.9, 2.8], [1.4, 3.1], [-1.2, -3.2]].forEach(function (c) {
      for (var k = 0; k < 900; k++) {
        var a = r() * Math.PI * 2;
        P.push([c[0] + Math.cos(a) * 0.11, r() * 0.4, c[1] + Math.sin(a) * 0.11, [255, 255, 255]]);
      }
    });
    return { pts: P, scale: 1 / 17, pitch: 0.78, yaw: 0.7, legend: true };
  }

  function makeGarden() {
    var P = [], r = rng(23), X = 14, Z = 22;
    function ground(x, z) { return 0.012 * z * z * 0 + z * 0.045 + bump(x, z, 3, 6, 4, 0.35) - bump(x, z, -4, -2, 3, 0.15); }
    for (var i = 0; i < 24000; i++) {
      var x = (r() - 0.5) * X, z = (r() - 0.5) * Z, y;
      if (z < -7) { y = ground(0, -7) - 0.02; P.push([x, y, z, [200, 205, 200]]); continue; } // patio
      y = ground(x, z);
      var t = (y + 0.4) / 1.3; // colour by height band
      var band = Math.floor(t * 8) % 2;
      P.push([x, y, z, band ? [120, 196, 168] : [150, 222, 196]]);
    }
    for (i = 0; i < 4000; i++) { // fence lines
      var s = r() < 0.5 ? -1 : 1;
      P.push([s * X / 2, ground(s * X / 2, 0) + r() * 1.8, (r() - 0.5) * Z, DIM]);
    }
    for (i = 0; i < 3500; i++) { // tree canopy
      var a = r() * 6.28, b = Math.acos(2 * r() - 1), rad = 1.8 + r() * 0.4;
      P.push([4 + rad * Math.sin(b) * Math.cos(a), 3.4 + rad * Math.cos(b) * 0.8, 7 + rad * Math.sin(b) * Math.sin(a), [110, 170, 140]]);
    }
    for (i = 0; i < 700; i++) P.push([4 + (r() - 0.5) * 0.25, ground(4, 7) + r() * 2, 7 + (r() - 0.5) * 0.25, DIM]);
    for (i = 0; i < 3000; i++) P.push([(r() - 0.5) * X, r() * 5, -Z / 2, GREY]); // house rear wall
    return { pts: P, scale: 1 / 30, pitch: 0.55, yaw: 0.9, legend: false };
  }

  function makeRoom() {
    var P = [], r = rng(31), X = 7.5, Z = 5.2, H = 2.4;
    for (var i = 0; i < 30000; i++) {
      var f = Math.floor(r() * 5), u = r() - 0.5, v = r(), x, y, z, c = GREY;
      if (f === 0) { x = u * X; y = 0; z = (r() - 0.5) * Z; c = DIM; }
      else if (f === 1) { x = u * X; y = v * H; z = -Z / 2; if (Math.abs(x - 1) < 0.9 && y > 0.9 && y < 2.1) continue; }
      else if (f === 2) { x = -X / 2; y = v * H; z = u * Z; if (Math.abs(z) < 0.5 && y < 2.05) continue; }
      else if (f === 3) { x = X / 2; y = v * H; z = u * Z; if (Math.abs(z + 0.4) < 1.5 && y < 2.1) continue; }
      else { x = u * X; y = v * H; z = Z / 2; c = DIM; if (r() < 0.6) continue; }
      P.push([x, y, z, c]);
    }
    for (i = 0; i < 5000; i++) { // kitchen run along back wall, highlighted
      P.push([-2.4 + r() * 3.0 - 1, r() < 0.5 ? 0.9 : r() * 0.9, -Z / 2 + 0.6 * r(), MINT]);
    }
    return { pts: P, scale: 1 / 13, pitch: 0.7, yaw: 0.75, legend: false };
  }

  var MAKERS = { road: makeRoad, slab: makeSlab, garden: makeGarden, room: makeRoom };

  function Viewer(fig) {
    var canvas = fig.querySelector('canvas'), ctx = canvas.getContext('2d');
    var legend = fig.querySelector('.viewer-legend'), cap = fig.querySelector('figcaption');
    var data, yaw, pitch, zoom = 1, dragging = false, lx = 0, ly = 0, auto = true, raf = 0, img, buf, W, H;
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var captions = {
      road: 'Sample scan: estate road sub-base against design levels.',
      slab: 'Sample scan: oversite slab flatness, drain collars ringed.',
      garden: 'Sample scan: rear garden levels in 100 mm bands.',
      room: 'Sample scan: kitchen and extension shell, units highlighted.'
    };

    function load(kind) {
      data = MAKERS[kind](); yaw = data.yaw; pitch = data.pitch; zoom = 1;
      if (legend) legend.style.display = data.legend ? '' : 'none';
      if (cap) cap.textContent = captions[kind] + ' Drag to rotate, scroll or pinch to zoom. Illustrative point cloud, not a client survey.';
      canvas.setAttribute('aria-label', captions[kind] + ' Drag to rotate.');
      fig.querySelectorAll('.viewer-tabs button').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.k === kind ? 'true' : 'false'); });
      draw();
    }
    function size() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2), w = canvas.clientWidth, h = canvas.clientHeight;
      W = canvas.width = Math.round(w * dpr); H = canvas.height = Math.round(h * dpr);
      img = ctx.createImageData(W, H); buf = new Uint32Array(img.data.buffer);
    }
    function draw() {
      if (!buf) size();
      buf.fill(0);
      var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      var f = W * 0.9 * zoom * data.scale, cx = W / 2, cyy = H / 2 + H * 0.06, P = data.pts;
      var dot = 2;
      for (var i = 0; i < P.length; i++) {
        var p = P[i], x = p[0] * cy - p[2] * sy, z0 = p[0] * sy + p[2] * cy;
        var y = p[1] * cp - z0 * sp, z = p[1] * sp + z0 * cp;
        var persp = 1 / (1 + z * data.scale * 0.35);
        var X = (cx + x * f * persp) | 0, Y = (cyy - y * f * persp) | 0;
        if (X < 0 || Y < 0 || X >= W - dot || Y >= H - dot) continue;
        var shade = Math.max(0.45, Math.min(1, 0.95 - z * data.scale * 0.6)), c = p[3];
        var col = (255 << 24) | ((c[2] * shade) << 16) | ((c[1] * shade) << 8) | (c[0] * shade);
        var o = Y * W + X;
        buf[o] = col; if (dot === 2) { buf[o + 1] = col; buf[o + W] = col; buf[o + W + 1] = col; }
      }
      ctx.putImageData(img, 0, 0);
    }
    function loop() {
      if (auto && !reduce) { yaw += 0.0035; draw(); }
      raf = requestAnimationFrame(loop);
    }
    canvas.addEventListener('pointerdown', function (e) { dragging = true; auto = false; lx = e.clientX; ly = e.clientY; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      yaw += (e.clientX - lx) * 0.008; pitch = Math.max(0.1, Math.min(1.45, pitch + (e.clientY - ly) * 0.006));
      lx = e.clientX; ly = e.clientY; draw();
    });
    canvas.addEventListener('pointerup', function () { dragging = false; });
    canvas.addEventListener('wheel', function (e) { e.preventDefault(); auto = false; zoom = Math.max(0.6, Math.min(3, zoom * (e.deltaY < 0 ? 1.08 : 0.92))); draw(); }, { passive: false });
    var pinch = 0;
    canvas.addEventListener('touchmove', function (e) {
      if (e.touches.length !== 2) return;
      var d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      if (pinch) { zoom = Math.max(0.6, Math.min(3, zoom * d / pinch)); draw(); }
      pinch = d;
    }, { passive: true });
    canvas.addEventListener('touchend', function () { pinch = 0; });
    fig.querySelectorAll('.viewer-tabs button').forEach(function (b) {
      b.addEventListener('click', function () { auto = true; load(b.dataset.k); });
    });
    window.addEventListener('resize', function () { size(); draw(); });
    // only animate while on screen
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) {
        en.forEach(function (x) { if (x.isIntersecting) { if (!raf) loop(); } else { cancelAnimationFrame(raf); raf = 0; } });
      }).observe(fig);
    } else loop();
    size(); load(fig.dataset.kind || 'road');
  }
  document.querySelectorAll('.viewer').forEach(function (f) { new Viewer(f); });
})();
