/**
 * DotGrid — Vanilla JS port of the React Bits component.
 * Renders an interactive canvas dot grid that reacts to mouse proximity and clicks.
 * Uses GSAP for elastic return animations (no InertiaPlugin needed).
 *
 * Requires: GSAP (loaded via CDN)
 *
 * Usage:
 *   new DotGrid(document.getElementById('bg-container'), {
 *     dotSize: 3,
 *     gap: 25,
 *     baseColor: '#1e293b',
 *     activeColor: '#10b981',
 *     proximity: 100,
 *     shockRadius: 200,
 *     shockStrength: 4
 *   });
 */
class DotGrid {
  constructor(container, options = {}) {
    this.dotSize = options.dotSize || 3;
    this.gap = options.gap || 25;
    this.baseColor = options.baseColor || '#1e293b';
    this.activeColor = options.activeColor || '#10b981';
    this.proximity = options.proximity || 100;
    this.shockRadius = options.shockRadius || 200;
    this.shockStrength = options.shockStrength || 4;
    this.returnDuration = options.returnDuration || 1.5;
    this.resistance = options.resistance || 0.85;

    this.dots = [];
    this.pointer = { x: -9999, y: -9999, vx: 0, vy: 0, speed: 0, lastX: 0, lastY: 0, lastTime: 0 };

    this.baseRgb = this._hexToRgb(this.baseColor);
    this.activeRgb = this._hexToRgb(this.activeColor);

    // Build DOM
    this.section = document.createElement('section');
    this.section.className = 'dot-grid';
    if (options.className) this.section.classList.add(options.className);

    this.wrapper = document.createElement('div');
    this.wrapper.className = 'dot-grid__wrap';

    this.canvas = document.createElement('canvas');
    this.canvas.className = 'dot-grid__canvas';

    this.wrapper.appendChild(this.canvas);
    this.section.appendChild(this.wrapper);
    container.appendChild(this.section);

    this.ctx = null;
    this.animationId = null;

    this._buildGrid();
    this._startDrawLoop();
    this._bindEvents();

    // ResizeObserver
    if ('ResizeObserver' in window) {
      this.ro = new ResizeObserver(() => this._buildGrid());
      this.ro.observe(this.wrapper);
    } else {
      window.addEventListener('resize', () => this._buildGrid());
    }
  }

  _hexToRgb(hex) {
    const m = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
    if (!m) return { r: 0, g: 0, b: 0 };
    return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
  }

  _buildGrid() {
    const { width, height } = this.wrapper.getBoundingClientRect();
    if (width === 0 || height === 0) return;

    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.ctx = this.canvas.getContext('2d');
    this.ctx.scale(dpr, dpr);

    const cell = this.dotSize + this.gap;
    const cols = Math.floor((width + this.gap) / cell);
    const rows = Math.floor((height + this.gap) / cell);

    const gridW = cell * cols - this.gap;
    const gridH = cell * rows - this.gap;
    const startX = (width - gridW) / 2 + this.dotSize / 2;
    const startY = (height - gridH) / 2 + this.dotSize / 2;

    this.dots = [];
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        this.dots.push({
          cx: startX + x * cell,
          cy: startY + y * cell,
          xOffset: 0,
          yOffset: 0,
          _animating: false
        });
      }
    }

    this.canvasWidth = width;
    this.canvasHeight = height;
  }

  _startDrawLoop() {
    const proxSq = this.proximity * this.proximity;

    const draw = () => {
      if (!this.ctx) { this.animationId = requestAnimationFrame(draw); return; }

      this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
      const { x: px, y: py } = this.pointer;

      for (const dot of this.dots) {
        const ox = dot.cx + dot.xOffset;
        const oy = dot.cy + dot.yOffset;
        const dx = dot.cx - px;
        const dy = dot.cy - py;
        const dsq = dx * dx + dy * dy;

        let fillStyle = this.baseColor;
        if (dsq <= proxSq) {
          const dist = Math.sqrt(dsq);
          const t = 1 - dist / this.proximity;
          const r = Math.round(this.baseRgb.r + (this.activeRgb.r - this.baseRgb.r) * t);
          const g = Math.round(this.baseRgb.g + (this.activeRgb.g - this.baseRgb.g) * t);
          const b = Math.round(this.baseRgb.b + (this.activeRgb.b - this.baseRgb.b) * t);
          fillStyle = `rgb(${r},${g},${b})`;
        }

        this.ctx.fillStyle = fillStyle;
        this.ctx.beginPath();
        this.ctx.arc(ox, oy, this.dotSize / 2, 0, Math.PI * 2);
        this.ctx.fill();
      }

      this.animationId = requestAnimationFrame(draw);
    };

    draw();
  }

  _bindEvents() {
    let lastMoveTime = 0;

    const onMove = (e) => {
      const now = performance.now();
      if (now - lastMoveTime < 50) return;
      lastMoveTime = now;

      const rect = this.canvas.getBoundingClientRect();
      const pr = this.pointer;
      const dt = pr.lastTime ? now - pr.lastTime : 16;

      pr.vx = ((e.clientX - pr.lastX) / dt) * 1000;
      pr.vy = ((e.clientY - pr.lastY) / dt) * 1000;
      pr.speed = Math.hypot(pr.vx, pr.vy);
      pr.lastTime = now;
      pr.lastX = e.clientX;
      pr.lastY = e.clientY;
      pr.x = e.clientX - rect.left;
      pr.y = e.clientY - rect.top;

      // Speed-based push
      if (typeof gsap !== 'undefined' && pr.speed > 100) {
        for (const dot of this.dots) {
          const dist = Math.hypot(dot.cx - pr.x, dot.cy - pr.y);
          if (dist < this.proximity && !dot._animating) {
            dot._animating = true;
            const pushX = (dot.cx - pr.x) * 0.3 + pr.vx * 0.003;
            const pushY = (dot.cy - pr.y) * 0.3 + pr.vy * 0.003;

            gsap.killTweensOf(dot);
            gsap.to(dot, {
              xOffset: pushX * this.resistance,
              yOffset: pushY * this.resistance,
              duration: 0.15,
              ease: 'power2.out',
              onComplete: () => {
                gsap.to(dot, {
                  xOffset: 0, yOffset: 0,
                  duration: this.returnDuration,
                  ease: 'elastic.out(1,0.75)',
                  onComplete: () => { dot._animating = false; }
                });
              }
            });
          }
        }
      }
    };

    const onClick = (e) => {
      if (typeof gsap === 'undefined') return;
      const rect = this.canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;

      for (const dot of this.dots) {
        const dist = Math.hypot(dot.cx - cx, dot.cy - cy);
        if (dist < this.shockRadius) {
          const falloff = Math.max(0, 1 - dist / this.shockRadius);
          const pushX = (dot.cx - cx) * this.shockStrength * falloff;
          const pushY = (dot.cy - cy) * this.shockStrength * falloff;

          gsap.killTweensOf(dot);
          gsap.to(dot, {
            xOffset: pushX,
            yOffset: pushY,
            duration: 0.2,
            ease: 'power2.out',
            onComplete: () => {
              gsap.to(dot, {
                xOffset: 0, yOffset: 0,
                duration: this.returnDuration,
                ease: 'elastic.out(1,0.75)',
                onComplete: () => { dot._animating = false; }
              });
            }
          });
        }
      }
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('click', onClick);
  }

  destroy() {
    cancelAnimationFrame(this.animationId);
    if (this.ro) this.ro.disconnect();
    this.section.remove();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = DotGrid;
} else {
  window.DotGrid = DotGrid;
}
