/* ============================================================
   EXPENSE TRACKER — ANIMATIONS JS
   Handles: page transitions, counters, toasts, scroll reveal,
            AI typing, skeleton loaders, chart hooks
   ============================================================ */

// ── 1. PAGE FADE IN / OUT ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Fade in on load
  document.body.classList.add('page-ready');

  // Fade out on navigation
  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    // Only internal links, skip anchors, external, logout
    if (!href || href.startsWith('#') || href.startsWith('http') ||
        href.startsWith('mailto') || href.includes('logout')) return;
    link.addEventListener('click', function(e) {
      const target = this.getAttribute('href');
      e.preventDefault();
      document.body.classList.add('page-leaving');
      setTimeout(() => { window.location.href = target; }, 220);
    });
  });
});

// ── 2. NUMBER COUNTER ANIMATION ─────────────────────────────
/**
 * animateCounter(el, targetValue, prefix, suffix, duration)
 * el: DOM element
 * targetValue: final number
 * prefix: e.g. "₹"
 * suffix: e.g. ""
 * duration: ms (default 1200)
 */
function animateCounter(el, targetValue, prefix = '₹', suffix = '', duration = 1200) {
  if (!el) return;
  const start = 0;
  const startTime = performance.now();
  const isFloat = !Number.isInteger(targetValue);

  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = easeOut(progress);
    const current = start + (targetValue - start) * eased;

    if (isFloat || targetValue > 100) {
      el.textContent = prefix + current.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }) + suffix;
    } else {
      el.textContent = prefix + Math.round(current) + suffix;
    }

    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = prefix + targetValue.toLocaleString('en-IN', {
      minimumFractionDigits: isFloat ? 2 : 0,
      maximumFractionDigits: isFloat ? 2 : 0
    }) + suffix;
  }

  requestAnimationFrame(update);
}

// ── 3. TOAST NOTIFICATIONS ───────────────────────────────────
// Usage: showToast('Expense added!', 'success')
// Types: success | error | info
function showToast(message, type = 'success', duration = 3000) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast-msg ${type}`;

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.innerHTML = `${icons[type] || ''} ${message}`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

// ── 4. FORM ERROR SHAKE ──────────────────────────────────────
function shakeElement(el) {
  if (!el) return;
  el.classList.remove('shake');
  void el.offsetWidth; // force reflow
  el.classList.add('shake');
  setTimeout(() => el.classList.remove('shake'), 500);
}

// ── 5. AI TYPING ANIMATION ───────────────────────────────────
/**
 * typeText(el, text, speed)
 * Types text letter by letter into el
 */
function typeText(el, text, speed = 18) {
  if (!el) return;
  el.textContent = '';
  el.classList.add('typing-cursor');
  let i = 0;
  const interval = setInterval(() => {
    el.textContent += text[i];
    i++;
    if (i >= text.length) {
      clearInterval(interval);
      el.classList.remove('typing-cursor');
    }
  }, speed);
}

// ── 6. SKELETON LOADER ───────────────────────────────────────
function showSkeleton(containerId, rows = 3) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = Array(rows).fill(`
    <div class="skeleton skeleton-card mb-2"></div>
  `).join('');
}

function hideSkeleton(containerId) {
  // Content replaces skeleton naturally when data loads
}

// ── 7. SCROLL REVEAL ─────────────────────────────────────────
function initScrollReveal() {
  const elements = document.querySelectorAll('.reveal');
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  elements.forEach(el => observer.observe(el));
}

document.addEventListener('DOMContentLoaded', initScrollReveal);

// ── 8. CHART ANIMATION HELPER ────────────────────────────────
// Call this on any canvas wrapper to add fade-up class
function animateChartSection(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const wrapper = canvas.closest('.card') || canvas.parentElement;
  if (wrapper) wrapper.classList.add('chart-animate');
}

// ── 9. PROGRESS BAR ANIMATED FILL ────────────────────────────
function fillProgressBar(barEl, targetPct, delay = 100) {
  if (!barEl) return;
  barEl.style.width = '0%';
  setTimeout(() => {
    barEl.style.width = Math.min(targetPct, 100) + '%';
  }, delay);
}

// ── 10. SAVE BUTTON PULSE ────────────────────────────────────
function pulseSaveBtn(btn) {
  if (!btn) return;
  btn.classList.remove('save-pulse');
  void btn.offsetWidth;
  btn.classList.add('save-pulse');
  setTimeout(() => btn.classList.remove('save-pulse'), 700);
}

// ── 11. SETTLEMENT FLASH ─────────────────────────────────────
function flashSettle(rowEl) {
  if (!rowEl) return;
  rowEl.classList.add('settle-flash');
  setTimeout(() => rowEl.classList.remove('settle-flash'), 800);
}

// ── 12. ROW ENTRY (mess / history rows) ──────────────────────
function animateNewRow(trEl) {
  if (!trEl) return;
  trEl.classList.add('row-entry');
}

// ── 13. AI RESULT REVEAL ─────────────────────────────────────
function revealAIResult(el) {
  if (!el) return;
  el.classList.add('ai-reveal');
}

// ── 14. CARD STAGGER HELPER ───────────────────────────────────
// Add .anim-card to cards dynamically rendered by JS
function staggerCards(containerSelector) {
  const cards = document.querySelectorAll(containerSelector);
  cards.forEach((card, i) => {
    card.classList.add('anim-card');
    card.style.animationDelay = (i * 0.07) + 's';
  });
}
