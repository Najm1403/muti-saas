/* platform/hr-common.js — shared helpers for the platform Employees + Salaries
   pages. Matches the dark-sidebar platform dashboard conventions (see plans.html). */

const token = localStorage.getItem('platform_token');
if (!token) { window.location.href = '/platform/login.html'; }

const API_BASE = window.API_BASE_URL ?? '';

function logout() {
    localStorage.removeItem('platform_token');
    window.location.href = '/platform/login.html';
}

async function apiFetch(path, options = {}) {
    const res = await fetch(API_BASE + path, {
        ...options,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        },
    });
    if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
    if (res.status === 204) return null;
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
        const err = new Error(errMsg(body, res.status, path));
        // Machine-readable error code from ForbiddenError (app/main.py's
        // forbidden_handler), e.g. "STEP_UP_REQUIRED" — lets a caller branch
        // on it (open the password-confirm modal) instead of string-matching.
        if (body && body.code) err.code = body.code;
        throw err;
    }
    return body;
}
function errMsg(body, status, path) {
    const d = body && body.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length) return d.map(x => (x.loc ? x.loc.join('.') + ': ' : '') + (x.msg || JSON.stringify(x))).join('; ');
    if (d && typeof d === 'object') return JSON.stringify(d);
    return `Request failed (${status})`;
}
function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function qs(o) { return Object.entries(o).filter(([, v]) => v !== null && v !== undefined && v !== '').map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&'); }

function money(v) {
    const n = Number(v || 0);
    return 'Rs ' + n.toLocaleString('en-PK', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function showToast(msg, type = 'success') {
    const c = document.getElementById('toastContainer'); if (!c) { alert(msg); return; }
    const t = document.createElement('div'); const ok = type === 'success';
    t.className = `px-4 py-3 rounded-lg shadow-lg text-sm font-medium border ${ok ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`;
    t.textContent = msg; c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
}

function downloadCsv(name, headers, rows) {
    const q = s => `"${String(s ?? '').replace(/"/g, '""')}"`;
    const csv = [headers.map(q).join(','), ...rows.map(r => r.map(q).join(','))].join('\r\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${name}-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); a.remove();
}

/* ── Sidebar (dark) ──────────────────────────────────────────
   Rendered into #sidebarNav. Sections + items mirror the other platform pages. */
const NAV_SECTIONS = [
    ['Overview', [
        ['dashboard', '/platform/dashboard.html', 'Dashboard', 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'],
    ]],
    ['Management', [
        ['tenants', '/platform/tenants.html', 'Tenants', 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4'],
        ['business-templates', '/platform/business-templates.html', 'Business Templates', 'M20 7h-4V5a3 3 0 00-3-3h-2a3 3 0 00-3 3v2H4a2 2 0 00-2 2v9a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM10 5a1 1 0 011-1h2a1 1 0 011 1v2h-4V5z'],
        ['config-reference', '/platform/config-reference.html', 'Config Reference', 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s4.332.477 5.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'],
        ['platform_users', '/platform/platform_users.html', 'Platform Users', 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z'],
    ]],
    ['Billing', [
        ['plans', '/platform/plans.html', 'Plans', 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01'],
        ['subscriptions', '/platform/subscriptions.html', 'Subscriptions', 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z'],
    ]],
    ['Human Resources', [
        ['employees', '/platform/employees.html', 'Employees', 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z'],
        ['salaries', '/platform/salaries.html', 'Salaries', 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z'],
    ]],
    ['System', [
        ['reports', '/platform/reports.html', 'Reports', 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'],
        ['activity', '/platform/activity.html', 'Activity Logs', 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9'],
        ['sync-health', '/platform/sync-health.html', 'Sync Health', 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15'],
        ['settings', '/platform/settings.html', 'Settings', 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'],
    ]],
];

function renderPlatformSidebarNav(active) {
    const nav = document.getElementById('sidebarNav');
    if (!nav) return;
    nav.innerHTML = NAV_SECTIONS.map(([title, items]) => {
        const links = items.map(([key, href, label, d]) => {
            const on = key === active;
            const cls = on
                ? 'flex items-center gap-3 pl-[13px] pr-4 py-2.5 rounded-card bg-slate-800 text-white font-medium border-l-[3px] border-blue-500'
                : 'flex items-center gap-3 pl-[13px] pr-4 py-2.5 rounded-card text-slate-300 hover:bg-slate-800 hover:text-white border-l-[3px] border-transparent transition-colors';
            return `<a href="${href}" class="${cls}">
                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="${d}"/></svg>
                <span class="text-sm">${label}</span></a>`;
        }).join('');
        return `<p class="text-[11px] font-medium text-slate-500 uppercase tracking-widest px-[13px] pt-5 pb-2 first:pt-1">${title}</p>${links}`;
    }).join('');
}
