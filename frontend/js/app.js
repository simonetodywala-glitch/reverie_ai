// ─────────────────────────────────────────
// REVERIE — app.js
// App init, theme switching (night/morning), nav active states
// ─────────────────────────────────────────

// ── THEME: switch between night and morning mode based on time ──
function applyTheme() {
  const hour = new Date().getHours();
  const isMorning = hour >= 6 && hour < 18;

  if (isMorning) {
    document.body.classList.add('morning');
  } else {
    document.body.classList.remove('morning');
  }

  // Set time-based greeting; the auth module will inject the real name
  const greetingEl = document.getElementById('greeting-text');
  if (greetingEl) {
    greetingEl.textContent = isMorning ? 'Good Morning!' : 'Good Night!';
  }
}

// ── NAV: highlight the active page link ──
function setActiveNav() {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href') || '';
    if (href.includes(currentPage) || (currentPage === 'index.html' && href === '../index.html')) {
      link.classList.add('active');
    }
  });
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  applyTheme();
  setActiveNav();
});
