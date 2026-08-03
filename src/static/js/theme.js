(function () {
  var STORAGE_KEY = 'bldng-theme';
  var DEFAULT_THEME = 'dark';

  function preferredTheme() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) { /* ignore */ }
    return DEFAULT_THEME;
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      var icon = btn.querySelector('[data-theme-icon]');
      var label = btn.querySelector('[data-theme-label]');
      var isDark = theme === 'dark';
      if (icon) icon.textContent = isDark ? 'light_mode' : 'dark_mode';
      if (label) label.textContent = isDark ? 'Claro' : 'Oscuro';
      btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      btn.setAttribute('title', isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
    }
  }

  function toggleTheme() {
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem(STORAGE_KEY, next); } catch (e) { /* ignore */ }
    applyTheme(next);
  }

  function wrapTables() {
    var tables = document.querySelectorAll('table.table1, table.erp-table');
    tables.forEach(function (table) {
      var parent = table.parentElement;
      if (!parent) return;
      if (
        parent.classList.contains('table-wrap') ||
        parent.classList.contains('table-container') ||
        parent.classList.contains('scrollable-table')
      ) {
        return;
      }
      var wrap = document.createElement('div');
      wrap.className = 'table-wrap';
      parent.insertBefore(wrap, table);
      wrap.appendChild(table);
    });
  }

  applyTheme(preferredTheme());

  document.addEventListener('DOMContentLoaded', function () {
    applyTheme(preferredTheme());
    wrapTables();
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.addEventListener('click', toggleTheme);
  });
})();
