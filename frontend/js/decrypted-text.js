/**
 * DecryptedText — Vanilla JS port of the React Bits component.
 * Reveals text with a scrambled-character "decryption" animation.
 *
 * Usage:
 *   new DecryptedText(document.getElementById('title'), {
 *     text: 'JAN SAHAYAK',
 *     speed: 50,
 *     animateOn: 'view',
 *     revealDirection: 'start',
 *     characters: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()',
 *     className: 'decrypted-char',
 *     encryptedClassName: 'encrypted-char'
 *   });
 */
class DecryptedText {
  constructor(element, options = {}) {
    this.el = element;
    this.text = options.text || element.textContent || '';
    this.speed = options.speed || 50;
    this.maxIterations = options.maxIterations || 10;
    this.sequential = options.sequential || false;
    this.revealDirection = options.revealDirection || 'start';
    this.useOriginalCharsOnly = options.useOriginalCharsOnly || false;
    this.characters = options.characters || 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+';
    this.className = options.className || '';
    this.encryptedClassName = options.encryptedClassName || '';
    this.parentClassName = options.parentClassName || '';
    this.animateOn = options.animateOn || 'view';

    this.displayText = this.text;
    this.isAnimating = false;
    this.revealedIndices = new Set();
    this.hasAnimated = false;
    this.isDecrypted = false;
    this.intervalId = null;

    this.availableChars = this.useOriginalCharsOnly
      ? [...new Set(this.text.split(''))].filter(c => c !== ' ')
      : this.characters.split('');

    if (this.parentClassName) {
      this.el.classList.add(...this.parentClassName.split(' ').filter(Boolean));
    }
    this.el.style.display = 'inline-block';
    this.el.style.whiteSpace = 'pre-wrap';

    this._init();
  }

  _init() {
    if (this.animateOn === 'view') {
      this._renderEncrypted();
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !this.hasAnimated) {
            this.hasAnimated = true;
            this._triggerDecrypt();
            observer.unobserve(this.el);
          }
        });
      }, { threshold: 0.1 });
      observer.observe(this.el);
    } else if (this.animateOn === 'hover') {
      this._renderDecrypted();
      this.el.addEventListener('mouseenter', () => this._triggerHoverDecrypt());
      this.el.addEventListener('mouseleave', () => this._resetToPlainText());
    } else if (this.animateOn === 'click') {
      this._renderEncrypted();
      this.el.style.cursor = 'pointer';
      this.el.addEventListener('click', () => {
        if (!this.isDecrypted) this._triggerDecrypt();
      });
    }
  }

  _shuffleText(revealed) {
    return this.text.split('').map((char, i) => {
      if (char === ' ') return ' ';
      if (revealed.has(i)) return this.text[i];
      return this.availableChars[Math.floor(Math.random() * this.availableChars.length)];
    }).join('');
  }

  _render(text, revealed, isDone) {
    this.el.innerHTML = '';
    const srSpan = document.createElement('span');
    srSpan.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0';
    srSpan.textContent = text;
    this.el.appendChild(srSpan);

    const ariaSpan = document.createElement('span');
    ariaSpan.setAttribute('aria-hidden', 'true');

    text.split('').forEach((char, index) => {
      const span = document.createElement('span');
      const isRevealed = revealed.has(index) || isDone;
      if (isRevealed && this.className) {
        span.className = this.className;
      } else if (!isRevealed && this.encryptedClassName) {
        span.className = this.encryptedClassName;
      }
      span.textContent = char;
      ariaSpan.appendChild(span);
    });

    this.el.appendChild(ariaSpan);
  }

  _renderEncrypted() {
    const emptySet = new Set();
    const scrambled = this._shuffleText(emptySet);
    this._render(scrambled, emptySet, false);
  }

  _renderDecrypted() {
    const fullSet = new Set();
    for (let i = 0; i < this.text.length; i++) fullSet.add(i);
    this._render(this.text, fullSet, true);
    this.isDecrypted = true;
  }

  _getNextIndex(revealedSet) {
    const len = this.text.length;
    switch (this.revealDirection) {
      case 'start': return revealedSet.size;
      case 'end': return len - 1 - revealedSet.size;
      case 'center': {
        const mid = Math.floor(len / 2);
        const offset = Math.floor(revealedSet.size / 2);
        const next = revealedSet.size % 2 === 0 ? mid + offset : mid - offset - 1;
        if (next >= 0 && next < len && !revealedSet.has(next)) return next;
        for (let i = 0; i < len; i++) { if (!revealedSet.has(i)) return i; }
        return 0;
      }
      default: return revealedSet.size;
    }
  }

  _triggerDecrypt() {
    if (this.isAnimating) return;
    this.isAnimating = true;
    this.revealedIndices = new Set();
    let currentIteration = 0;

    this.intervalId = setInterval(() => {
      if (this.sequential) {
        if (this.revealedIndices.size < this.text.length) {
          const nextIdx = this._getNextIndex(this.revealedIndices);
          this.revealedIndices.add(nextIdx);
          this.displayText = this._shuffleText(this.revealedIndices);
          this._render(this.displayText, this.revealedIndices, false);
        } else {
          this._finishDecrypt();
        }
      } else {
        this.displayText = this._shuffleText(this.revealedIndices);
        this._render(this.displayText, this.revealedIndices, false);
        currentIteration++;
        if (currentIteration >= this.maxIterations) {
          this._finishDecrypt();
        }
      }
    }, this.speed);
  }

  _finishDecrypt() {
    clearInterval(this.intervalId);
    this.isAnimating = false;
    this.isDecrypted = true;
    this._renderDecrypted();
  }

  _triggerHoverDecrypt() {
    if (this.isAnimating) return;
    this.revealedIndices = new Set();
    this.isDecrypted = false;
    this.isAnimating = true;
    let currentIteration = 0;

    this.intervalId = setInterval(() => {
      this.displayText = this._shuffleText(this.revealedIndices);
      this._render(this.displayText, this.revealedIndices, false);
      currentIteration++;
      if (currentIteration >= this.maxIterations) {
        this._finishDecrypt();
      }
    }, this.speed);
  }

  _resetToPlainText() {
    clearInterval(this.intervalId);
    this.isAnimating = false;
    this.revealedIndices = new Set();
    this._renderDecrypted();
  }
}

// Export for module usage, also attach to window for script-tag usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DecryptedText;
} else {
  window.DecryptedText = DecryptedText;
}
