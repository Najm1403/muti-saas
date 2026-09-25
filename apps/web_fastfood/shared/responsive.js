/* shared/responsive.js
 *
 * Injects a mobile top bar (hamburger + page title) and a backdrop, and turns
 * the page's single top-level <aside> nav into an off-canvas drawer on small
 * screens. All styling lives in shared/responsive.css (inside an @media block),
 * so this script is inert on desktop even though the elements are always added.
 *
 * Include after responsive.css:
 *   <script src="/shared/responsive.js" defer></script>
 */
(function () {
  'use strict';

  function init() {
    if (document.body.dataset.rnavReady) return;

    // The nav sidebar every dashboard page renders. Login pages have none.
    var aside =
      document.querySelector('body > aside') ||
      document.querySelector('aside.w-64') ||
      document.querySelector('aside');
    if (!aside) return;

    document.body.dataset.rnavReady = '1';

    var titleText =
      (document.querySelector('h1') &&
        document.querySelector('h1').textContent.trim()) ||
      (document.title || '').split('—')[0].trim() ||
      'Menu';

    // ── Top bar ──────────────────────────────────────────────────────────
    var bar = document.createElement('div');
    bar.className = 'rnav-bar';
    bar.innerHTML =
      '<button type="button" aria-label="Toggle menu" aria-expanded="false">' +
      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
      '<path d="M4 6h16M4 12h16M4 18h16"/></svg></button>' +
      '<span class="rnav-title"></span>';
    bar.querySelector('.rnav-title').textContent = titleText;

    var backdrop = document.createElement('div');
    backdrop.className = 'rnav-backdrop';

    var btn = bar.querySelector('button');

    function open() {
      document.body.classList.add('nav-open');
      btn.setAttribute('aria-expanded', 'true');
    }
    function close() {
      document.body.classList.remove('nav-open');
      btn.setAttribute('aria-expanded', 'false');
    }
    function toggle() {
      document.body.classList.contains('nav-open') ? close() : open();
    }

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      toggle();
    });
    backdrop.addEventListener('click', close);

    // Tapping a nav link closes the drawer (SPA-less: the page navigates anyway,
    // but this keeps it tidy for in-page anchors).
    aside.addEventListener('click', function (e) {
      if (e.target.closest('a')) close();
    });

    // Esc closes; leaving mobile width closes.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
    var mq = window.matchMedia('(max-width: 767px)');
    (mq.addEventListener
      ? mq.addEventListener.bind(mq, 'change')
      : mq.addListener.bind(mq))(function (ev) {
      if (!(ev.matches || mq.matches)) close();
    });

    document.body.appendChild(bar);
    document.body.appendChild(backdrop);
  }

  // ── Module gating (tenant dashboard only) ────────────────────────────────
  //
  // The platform controls which modules a tenant may use (industry templates).
  // GET /api/v1/auth/me returns `modules` — hide the sidebar links for the ones
  // that are off, and show a notice if the current page itself is disabled.
  // The backend also 403s the routes, so this is convenience, not the guard.

  // module key -> tenant page basenames it owns
  var MODULE_PAGES = {
    dashboard: ['dashboard'], subscription: ['subscription'], settings: ['settings'],
    sales: ['sales'], reports: ['reports', 'shifts'],
    menu: ['menu', 'product-detail', 'variant-options', 'addon-groups'],
    promotions: ['promotions'], deals: ['deals'],
    branches: ['branches'], devices: ['devices'],
    kitchen: ['preparation-stations', 'kitchen'], inventory: ['inventory'],
    expenses: ['expenses'], employees: ['employees'], attendance: ['attendance'],
    salaries: ['salaries'],
    users: ['users'], roles: ['roles'], activity: ['activity']
  };
  // Business-template capabilities can hide individual pages inside an
  // otherwise enabled module. For example, Add-on Groups belongs to Menu,
  // but a variant-only business must not see that page in its navigation.
  var FEATURE_PAGES = {
    addons: ['addon-groups'],
    variants: ['variant-options']
  };
  var ALWAYS = ['dashboard', 'subscription', 'settings', 'login'];

  function currentBasename() {
    var p = location.pathname.replace(/\/+$/, '');
    return (p.split('/').pop() || 'dashboard').replace(/\.html$/, '');
  }

  function applyAccess(modules, businessFeatures) {
    var allowedPages = {};
    ALWAYS.forEach(function (n) { allowedPages[n] = 1; });
    (modules || []).forEach(function (k) {
      (MODULE_PAGES[k] || []).forEach(function (n) { allowedPages[n] = 1; });
    });
    Object.keys(FEATURE_PAGES).forEach(function (feature) {
      // An omitted feature is enabled for backward compatibility with older
      // servers and templates. Only an explicit false removes its pages.
      if (!businessFeatures || businessFeatures[feature] !== false) return;
      FEATURE_PAGES[feature].forEach(function (n) { delete allowedPages[n]; });
    });

    // Hide disabled links in the sidebar.
    var links = document.querySelectorAll('aside a[href^="/tenant/"]');
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute('href') || '';
      var base = href.split('/').pop().replace(/\.html$/, '').replace(/[?#].*$/, '');
      if (base && !allowedPages[base]) {
        links[i].hidden = true;
        links[i].classList.add('hidden');
      }
    }

    // If THIS page is a disabled module, replace the main content with a notice.
    var here = currentBasename();
    if (allowedPages[here]) return;
    var main = document.querySelector('main') || document.querySelector('body > div.flex-1') || document.body;
    main.innerHTML =
      '<div style="max-width:460px;margin:80px auto;padding:32px;background:#fff;border:1px solid #e2e8f0;' +
      'border-radius:12px;text-align:center;font-family:system-ui,sans-serif">' +
      '<div style="font-size:32px">🔒</div>' +
      '<h2 style="margin:12px 0 6px;font-size:18px;color:#0f172a">This section is not part of your plan</h2>' +
      '<p style="margin:0 0 18px;font-size:14px;color:#64748b">Ask the platform administrator to enable it for your account.</p>' +
      '<a href="/tenant/dashboard.html" style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;' +
      'font-size:14px;font-weight:600;padding:10px 18px;border-radius:8px">Back to Overview</a></div>';
  }

  // ── Billing / admin-message popup ─────────────────────────────────────
  //
  // Shown once per session per distinct message — a sessionStorage key
  // fingerprints the exact content (subscription status + expiry + the
  // admin's message + when it was set), so it reappears if anything about
  // it changes (e.g. PAST_DUE -> SUSPENDED, or the admin edits the notice)
  // even if the tenant already dismissed an earlier version this session,
  // but never nags again for the SAME unchanged notice on every page nav.
  function billingText(sub) {
    if (!sub) return null;
    if (sub.status === 'PAST_DUE') {
      var days = sub.days_overdue || 0;
      var graceLeft = sub.grace_ends_at
        ? Math.max(0, Math.ceil((new Date(sub.grace_ends_at) - new Date()) / 86400000))
        : null;
      return 'Your subscription payment is ' + days + ' day' + (days === 1 ? '' : 's') +
        ' overdue.' + (graceLeft !== null
          ? ' Please pay within ' + graceLeft + ' day' + (graceLeft === 1 ? '' : 's') +
            ' to avoid your POS terminals being suspended.'
          : ' Please pay to avoid your POS terminals being suspended.');
    }
    if (sub.status === 'SUSPENDED') {
      return 'Your subscription is suspended and POS terminals are locked. ' +
        'Please contact your account manager to reactivate.';
    }
    return null;
  }

  function showNoticePopup(html, dismissKey) {
    if (document.getElementById('rnavNoticeOverlay')) return;
    var overlay = document.createElement('div');
    overlay.id = 'rnavNoticeOverlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(15,23,42,.5);' +
      'display:flex;align-items:center;justify-content:center;padding:16px;font-family:system-ui,sans-serif;';
    overlay.innerHTML =
      '<div style="max-width:440px;width:100%;background:#fff;border-radius:12px;padding:26px;' +
      'box-shadow:0 20px 25px -5px rgba(0,0,0,.2)">' + html +
      '<button id="rnavNoticeDismiss" style="margin-top:18px;width:100%;background:#4f46e5;color:#fff;' +
      'border:none;border-radius:8px;padding:10px 16px;font-size:14px;font-weight:600;cursor:pointer">' +
      'OK, got it</button></div>';
    document.body.appendChild(overlay);
    document.getElementById('rnavNoticeDismiss').addEventListener('click', function () {
      try { sessionStorage.setItem('rnav_notice_dismissed', dismissKey); } catch (e) {}
      overlay.remove();
    });
  }

  function maybeShowNotice(me) {
    var sub = me.subscription || null;
    var billing = billingText(sub);
    var custom = me.admin_message || null;
    if (!billing && !custom) return;

    var key = [
      sub ? sub.status : '', sub ? sub.expires_at : '',
      custom || '', me.admin_message_set_at || '',
    ].join('|');
    var already;
    try { already = sessionStorage.getItem('rnav_notice_dismissed'); } catch (e) { already = null; }
    if (already === key) return;

    var sections = '';
    if (billing) {
      var urgent = sub.status === 'SUSPENDED';
      sections +=
        '<div style="display:flex;gap:10px;align-items:flex-start;' +
        (custom ? 'margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #e2e8f0;' : '') + '">' +
        '<span style="font-size:20px;line-height:1">' + (urgent ? '\u{1F512}' : '⚠️') + '</span>' +
        '<div><p style="margin:0 0 2px;font-size:14px;font-weight:700;color:' +
        (urgent ? '#b91c1c' : '#b45309') + '">' +
        (urgent ? 'Subscription suspended' : 'Payment overdue') + '</p>' +
        '<p style="margin:0;font-size:13px;color:#475569;line-height:1.5">' + esc(billing) + '</p></div></div>';
    }
    if (custom) {
      sections +=
        '<div style="display:flex;gap:10px;align-items:flex-start">' +
        '<span style="font-size:20px;line-height:1">\u{1F4E2}</span>' +
        '<div><p style="margin:0 0 2px;font-size:14px;font-weight:700;color:#0f172a">Message from support</p>' +
        '<p style="margin:0;font-size:13px;color:#475569;line-height:1.5;white-space:pre-wrap">' +
        esc(custom) + '</p></div></div>';
    }
    showNoticePopup(sections, key);
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function gateModules() {
    if (!location.pathname.startsWith('/tenant/')) return;
    if (currentBasename() === 'login') return;
    var token;
    try { token = localStorage.getItem('tenant_token'); } catch (e) { token = null; }
    if (!token) return;                       // the page's own boot handles the redirect
    fetch('/api/v1/auth/me', { headers: { Authorization: 'Bearer ' + token } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (me) {
        if (!me) return;
        maybeShowNotice(me);
        // Older servers may omit `modules`; otherwise apply the exact list.
        if (!Array.isArray(me.modules)) return;
        applyAccess(me.modules, me.business_features);
      })
      .catch(function () { /* offline / error — leave the sidebar as-is */ });
  }

  function boot() { init(); gateModules(); }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
