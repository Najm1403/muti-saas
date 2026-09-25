/* tenant/hr-common.js — shared helpers for the Employees + Salaries pages.
   Mirrors the apiFetch / toast / sidebar conventions used across the tenant
   dashboard (see expenses.html). No build step. */

const BASE = '/api/v1';
function getToken() { return localStorage.getItem('tenant_token'); }

async function apiFetch(path, opts = {}) {
    const res = await fetch(BASE + path, {
        ...opts,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getToken(),
            ...(opts.headers || {}),
        },
    });
    if (res.status === 401) { localStorage.removeItem('tenant_token'); location.href = '/tenant/login.html'; throw new Error('Unauthorized'); }
    if (res.status === 204) return null;
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(errMsg(body, res.status, path));
    return body;
}
function errMsg(body, status, path) {
    const d = body && body.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length) return d.map(x => (x.loc ? x.loc.join('.') + ': ' : '') + (x.msg || JSON.stringify(x))).join('; ');
    if (d && typeof d === 'object') return JSON.stringify(d);
    return `HTTP ${status}${path ? ' on ' + path : ''}`;
}
function logout() { localStorage.removeItem('tenant_token'); localStorage.removeItem('tenant_me'); location.href = '/tenant/login.html'; }
function esc(s) { return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function qs(o) { return Object.entries(o).filter(([, v]) => v !== null && v !== undefined && v !== '').map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&'); }

function showToast(msg, type = 'success') {
    const c = document.getElementById('toastContainer'); if (!c) return;
    const t = document.createElement('div'); const ok = type === 'success';
    t.className = `px-4 py-3 rounded-lg shadow-lg text-sm font-medium border ${ok ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`;
    t.textContent = msg; c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
}

let CCY = 'Rs.';
function money(v) {
    const n = Number(v || 0);
    return `${CCY} ${n.toLocaleString('en-PK', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
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

/* A thin variant of apiFetch() that returns the raw Response (for a PDF
   blob) instead of parsing JSON — mirrors inventory.html's own copy. */
async function apiFetchRaw(path) {
    const res = await fetch(BASE + path, { headers: { Authorization: 'Bearer ' + getToken() } });
    if (res.status === 401) { localStorage.removeItem('tenant_token'); location.href = '/tenant/login.html'; throw new Error('Unauthorized'); }
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(errMsg(body, res.status, path));
    }
    return res;
}

/* Downloads a real, server-rendered A4 PDF report (services/
   pdf_report_service.py) — not a browser print-to-PDF — showing a loading
   state on [btn] while the request is in flight. */
async function downloadPdfReport(path, filename, btn) {
    const prevText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Preparing PDF…';
    try {
        const res = await apiFetchRaw(path);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        showToast(e.message || 'Could not generate the PDF.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = prevText;
    }
}

/* ── Sidebar ─────────────────────────────────────────────────
   Rendered into #sidebarNav. `active` is one of the hrefs' basenames. */
const NAV_ITEMS = [
    ['dashboard', '/tenant/dashboard.html', 'Overview', 'M3 13.5V19a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-5.5M9 21V12M3 9l9-6 9 6'],
    ['sales', '/tenant/sales.html', 'Sales', 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01'],
    ['reports', '/tenant/reports.html', 'Reports', 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'],
    ['menu', '/tenant/menu.html', 'Menu', 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z'],
    ['promotions', '/tenant/promotions.html', 'Promotions', 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z'],
    ['deals', '/tenant/deals.html', 'Deals', 'M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7'],
    ['branches', '/tenant/branches.html', 'Branches', 'M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21'],
    ['preparation-stations', '/tenant/preparation-stations.html', 'Kitchen Stations', 'M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z'],
    ['devices', '/tenant/devices.html', 'Devices', 'M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 8.25h3'],
    ['inventory', '/tenant/inventory.html', 'Inventory', 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4'],
    ['expenses', '/tenant/expenses.html', 'Expenses', 'M9 7h6m-6 4h6m-6 4h4M5 3h14a2 2 0 012 2v16l-3-2-2 2-2-2-2 2-2-2-3 2V5a2 2 0 012-2z'],
    ['employees', '/tenant/employees.html', 'Employees', 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z'],
    ['attendance', '/tenant/attendance.html', 'Attendance', 'M12 8v4l2.5 2.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z'],
    ['salaries', '/tenant/salaries.html', 'Salaries', 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z'],
    ['users', '/tenant/users.html', 'Users', 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z'],
    ['roles', '/tenant/roles.html', 'Roles', 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'],
    ['activity', '/tenant/activity.html', 'Activity', 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0'],
    ['subscription', '/tenant/subscription.html', 'Subscription', 'M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z'],
    ['settings', '/tenant/settings.html', 'Settings', 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z'],
];

function renderSidebarNav(active) {
    const nav = document.getElementById('sidebarNav');
    if (!nav) return;
    nav.innerHTML = NAV_ITEMS.map(([key, href, label, d]) => {
        const on = key === active;
        const cls = on
            ? 'bg-indigo-50 text-indigo-700 font-medium rounded-lg px-3 py-2 flex items-center gap-3 text-sm'
            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors rounded-lg px-3 py-2 flex items-center gap-3 text-sm';
        return `<a href="${href}" class="${cls}">
            <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${d}"/></svg>
            ${label}</a>`;
    }).join('');
}

async function initSidebar(active) {
    if (!getToken()) { location.href = '/tenant/login.html'; return null; }
    renderSidebarNav(active);
    try {
        const me = await apiFetch('/auth/me');
        CCY = me.currency || 'Rs.';
        document.getElementById('sidebarTenantName').textContent = me.tenant?.name || 'My Business';
        document.getElementById('sidebarTenantCode').textContent = me.tenant?.code || '';
        document.getElementById('sidebarUserName').textContent = me.full_name || me.username;
        document.getElementById('userInitial').textContent = (me.full_name || me.username || '?')[0].toUpperCase();
        document.getElementById('sidebarUserRoles').textContent = me.roles?.length ? me.roles.join(', ') : 'No roles';
        return me;
    } catch (e) { return null; }
}
