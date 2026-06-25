/**
 * PillNav — Vanilla JS port of the React Bits component.
 * Navigation bar with animated pill hover effects using GSAP.
 * 
 * Requires: GSAP (loaded via CDN)
 *
 * Usage:
 *   new PillNav(document.getElementById('nav-container'), {
 *     items: [
 *       { label: 'Dashboard', href: '/' },
 *       { label: 'Analytics', href: '/analytics' },
 *       { label: 'Leaderboard', href: '/leaderboard' },
 *       { label: 'Admin', href: '/admin' }
 *     ],
 *     activeHref: '/',
 *     baseColor: '#0a0e1a',
 *     pillColor: '#1e293b',
 *     hoveredPillTextColor: '#0a0e1a',
 *     pillTextColor: '#94a3b8'
 *   });
 */
class PillNav {
  constructor(container, options = {}) {
    this.container = container;
    this.items = options.items || [];
    this.activeHref = options.activeHref || window.location.pathname;
    this.baseColor = options.baseColor || '#0a0e1a';
    this.pillColor = options.pillColor || '#1e293b';
    this.hoveredPillTextColor = options.hoveredPillTextColor || '#0a0e1a';
    this.pillTextColor = options.pillTextColor || '#94a3b8';
    this.logoText = options.logoText || 'JS';
    this.ease = options.ease || 'power3.easeOut';

    this.circleEls = [];
    this.timelines = [];
    this.activeTweens = [];
    this.isMobileOpen = false;

    this._build();
    this._layout();

    window.addEventListener('resize', () => this._layout());
    if (document.fonts?.ready) {
      document.fonts.ready.then(() => this._layout()).catch(() => {});
    }
  }

  _build() {
    this.container.innerHTML = '';
    this.container.className = 'pill-nav-container';

    const nav = document.createElement('nav');
    nav.className = 'pill-nav';
    nav.setAttribute('aria-label', 'Primary');
    nav.style.setProperty('--base', this.baseColor);
    nav.style.setProperty('--pill-bg', this.pillColor);
    nav.style.setProperty('--hover-text', this.hoveredPillTextColor);
    nav.style.setProperty('--pill-text', this.pillTextColor);

    // Logo
    const logo = document.createElement('a');
    logo.className = 'pill-logo';
    logo.href = this.items[0]?.href || '/';
    logo.setAttribute('aria-label', 'Home');
    logo.innerHTML = `<span style="font-weight:800;font-size:16px;color:${this.pillTextColor};font-family:'Inter',sans-serif;">${this.logoText}</span>`;
    nav.appendChild(logo);

    // Desktop nav items
    const navItems = document.createElement('div');
    navItems.className = 'pill-nav-items desktop-only';

    const ul = document.createElement('ul');
    ul.className = 'pill-list';
    ul.setAttribute('role', 'menubar');

    this.items.forEach((item, i) => {
      const li = document.createElement('li');
      li.setAttribute('role', 'none');

      const a = document.createElement('a');
      a.setAttribute('role', 'menuitem');
      a.href = item.href;
      a.className = 'pill' + (this.activeHref === item.href ? ' is-active' : '');

      const circle = document.createElement('span');
      circle.className = 'hover-circle';
      circle.setAttribute('aria-hidden', 'true');
      this.circleEls.push(circle);

      const stack = document.createElement('span');
      stack.className = 'label-stack';

      const label = document.createElement('span');
      label.className = 'pill-label';
      label.textContent = item.label;

      const hoverLabel = document.createElement('span');
      hoverLabel.className = 'pill-label-hover';
      hoverLabel.setAttribute('aria-hidden', 'true');
      hoverLabel.textContent = item.label;

      stack.appendChild(label);
      stack.appendChild(hoverLabel);
      a.appendChild(circle);
      a.appendChild(stack);

      a.addEventListener('mouseenter', () => this._handleEnter(i));
      a.addEventListener('mouseleave', () => this._handleLeave(i));

      li.appendChild(a);
      ul.appendChild(li);
    });

    navItems.appendChild(ul);
    nav.appendChild(navItems);

    // Mobile hamburger button
    const hamburger = document.createElement('button');
    hamburger.className = 'mobile-menu-button mobile-only';
    hamburger.setAttribute('aria-label', 'Toggle menu');
    hamburger.innerHTML = '<span class="hamburger-line"></span><span class="hamburger-line"></span>';
    hamburger.addEventListener('click', () => this._toggleMobile());
    this.hamburgerEl = hamburger;
    nav.appendChild(hamburger);

    this.container.appendChild(nav);

    // Mobile menu popover
    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu-popover mobile-only';
    mobileMenu.style.setProperty('--base', this.baseColor);
    mobileMenu.style.setProperty('--pill-bg', this.pillColor);
    mobileMenu.style.setProperty('--hover-text', this.hoveredPillTextColor);
    mobileMenu.style.setProperty('--pill-text', this.pillTextColor);

    const mobileUl = document.createElement('ul');
    mobileUl.className = 'mobile-menu-list';

    this.items.forEach(item => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = item.href;
      a.className = 'mobile-menu-link' + (this.activeHref === item.href ? ' is-active' : '');
      a.textContent = item.label;
      li.appendChild(a);
      mobileUl.appendChild(li);
    });

    mobileMenu.appendChild(mobileUl);
    this.container.appendChild(mobileMenu);
    this.mobileMenuEl = mobileMenu;

    if (typeof gsap !== 'undefined') {
      gsap.set(mobileMenu, { visibility: 'hidden', opacity: 0 });
    }
  }

  _layout() {
    if (typeof gsap === 'undefined') return;

    this.circleEls.forEach((circle, index) => {
      if (!circle.parentElement) return;

      const pill = circle.parentElement;
      const rect = pill.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      const R = (w * w / 4 + h * h) / (2 * h);
      const D = Math.ceil(2 * R) + 2;
      const delta = Math.ceil(R - Math.sqrt(Math.max(0, R * R - w * w / 4))) + 1;
      const originY = D - delta;

      circle.style.width = D + 'px';
      circle.style.height = D + 'px';
      circle.style.bottom = '-' + delta + 'px';

      gsap.set(circle, { xPercent: -50, scale: 0, transformOrigin: `50% ${originY}px` });

      const label = pill.querySelector('.pill-label');
      const hoverLabel = pill.querySelector('.pill-label-hover');

      if (label) gsap.set(label, { y: 0 });
      if (hoverLabel) gsap.set(hoverLabel, { y: h + 12, opacity: 0 });

      if (this.timelines[index]) this.timelines[index].kill();

      const tl = gsap.timeline({ paused: true });
      tl.to(circle, { scale: 1.2, xPercent: -50, duration: 2, ease: this.ease, overwrite: 'auto' }, 0);
      if (label) tl.to(label, { y: -(h + 8), duration: 2, ease: this.ease, overwrite: 'auto' }, 0);
      if (hoverLabel) {
        gsap.set(hoverLabel, { y: Math.ceil(h + 100), opacity: 0 });
        tl.to(hoverLabel, { y: 0, opacity: 1, duration: 2, ease: this.ease, overwrite: 'auto' }, 0);
      }

      this.timelines[index] = tl;
    });
  }

  _handleEnter(i) {
    const tl = this.timelines[i];
    if (!tl) return;
    if (this.activeTweens[i]) this.activeTweens[i].kill();
    this.activeTweens[i] = tl.tweenTo(tl.duration(), { duration: 0.3, ease: this.ease, overwrite: 'auto' });
  }

  _handleLeave(i) {
    const tl = this.timelines[i];
    if (!tl) return;
    if (this.activeTweens[i]) this.activeTweens[i].kill();
    this.activeTweens[i] = tl.tweenTo(0, { duration: 0.2, ease: this.ease, overwrite: 'auto' });
  }

  _toggleMobile() {
    if (typeof gsap === 'undefined') return;

    this.isMobileOpen = !this.isMobileOpen;
    const lines = this.hamburgerEl.querySelectorAll('.hamburger-line');

    if (this.isMobileOpen) {
      gsap.to(lines[0], { rotation: 45, y: 3, duration: 0.3, ease: this.ease });
      gsap.to(lines[1], { rotation: -45, y: -3, duration: 0.3, ease: this.ease });
      gsap.set(this.mobileMenuEl, { visibility: 'visible' });
      gsap.fromTo(this.mobileMenuEl,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.3, ease: this.ease, transformOrigin: 'top center' }
      );
    } else {
      gsap.to(lines[0], { rotation: 0, y: 0, duration: 0.3, ease: this.ease });
      gsap.to(lines[1], { rotation: 0, y: 0, duration: 0.3, ease: this.ease });
      gsap.to(this.mobileMenuEl, {
        opacity: 0, y: 10, duration: 0.2, ease: this.ease, transformOrigin: 'top center',
        onComplete: () => gsap.set(this.mobileMenuEl, { visibility: 'hidden' })
      });
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = PillNav;
} else {
  window.PillNav = PillNav;
}
