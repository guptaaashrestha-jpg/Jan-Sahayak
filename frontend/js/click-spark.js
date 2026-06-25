/**
 * ClickSpark — Vanilla JS port of the React Bits component.
 * Creates burst-spark animations on every click within the target element.
 *
 * Usage:
 *   new ClickSpark(document.body, {
 *     sparkColor: '#10b981',
 *     sparkSize: 10,
 *     sparkRadius: 15,
 *     sparkCount: 8,
 *     duration: 400
 *   });
 */
class ClickSpark {
  constructor(container, options = {}) {
    this.container = container;
    this.sparkColor = options.sparkColor || '#10b981';
    this.sparkSize = options.sparkSize || 10;
    this.sparkRadius = options.sparkRadius || 15;
    this.sparkCount = options.sparkCount || 8;
    this.duration = options.duration || 400;
    this.easing = options.easing || 'ease-out';
    this.extraScale = options.extraScale || 1.0;

    this.sparks = [];
    this.canvas = null;
    this.ctx = null;
    this.animationId = null;

    this._init();
  }

  _init() {
    this.container.style.position = this.container.style.position || 'relative';

    this.canvas = document.createElement('canvas');
    this.canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999;display:block;';
    document.body.appendChild(this.canvas);

    this._resizeCanvas();
    window.addEventListener('resize', () => this._resizeCanvas());
    document.addEventListener('click', (e) => this._handleClick(e));
    this._draw();
  }

  _resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = window.innerWidth * dpr;
    this.canvas.height = window.innerHeight * dpr;
    this.canvas.style.width = window.innerWidth + 'px';
    this.canvas.style.height = window.innerHeight + 'px';
    this.ctx = this.canvas.getContext('2d');
    this.ctx.scale(dpr, dpr);
  }

  _easeFunc(t) {
    switch (this.easing) {
      case 'linear': return t;
      case 'ease-in': return t * t;
      case 'ease-in-out': return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      default: return t * (2 - t); // ease-out
    }
  }

  _handleClick(e) {
    const x = e.clientX;
    const y = e.clientY;
    const now = performance.now();

    for (let i = 0; i < this.sparkCount; i++) {
      this.sparks.push({
        x, y,
        angle: (2 * Math.PI * i) / this.sparkCount,
        startTime: now
      });
    }
  }

  _draw(timestamp) {
    if (!this.ctx) {
      this.animationId = requestAnimationFrame((ts) => this._draw(ts));
      return;
    }

    const dpr = window.devicePixelRatio || 1;
    this.ctx.clearRect(0, 0, this.canvas.width / dpr, this.canvas.height / dpr);

    this.sparks = this.sparks.filter(spark => {
      const elapsed = (timestamp || performance.now()) - spark.startTime;
      if (elapsed >= this.duration) return false;

      const progress = elapsed / this.duration;
      const eased = this._easeFunc(progress);

      const distance = eased * this.sparkRadius * this.extraScale;
      const lineLength = this.sparkSize * (1 - eased);

      const x1 = spark.x + distance * Math.cos(spark.angle);
      const y1 = spark.y + distance * Math.sin(spark.angle);
      const x2 = spark.x + (distance + lineLength) * Math.cos(spark.angle);
      const y2 = spark.y + (distance + lineLength) * Math.sin(spark.angle);

      this.ctx.strokeStyle = this.sparkColor;
      this.ctx.lineWidth = 2;
      this.ctx.beginPath();
      this.ctx.moveTo(x1, y1);
      this.ctx.lineTo(x2, y2);
      this.ctx.stroke();

      return true;
    });

    this.animationId = requestAnimationFrame((ts) => this._draw(ts));
  }

  destroy() {
    cancelAnimationFrame(this.animationId);
    this.canvas.remove();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = ClickSpark;
} else {
  window.ClickSpark = ClickSpark;
}
