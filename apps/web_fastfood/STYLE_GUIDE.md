# FastFood SaaS — Frontend Style Guide

> **Purpose:** Single source of truth for all UI design decisions.
> Consult this before building any screen. Do not deviate without updating this file first.

---

## 1. Tech Stack

- **Markup:** HTML5
- **Styling:** Tailwind CSS (utility-first, no custom CSS unless unavoidable)
- **Behaviour:** Vanilla JavaScript — no framework unless explicitly decided
- **Comments:** Every section, component, and non-obvious JS block must have a clear comment/docstring

---

## 2. Visual Direction

| Attribute     | Value                                           |
|---------------|-------------------------------------------------|
| Style         | Modern SaaS / Clean Enterprise Dashboard        |
| Tone          | Minimal · Professional · Trustworthy · Fast     |
| Noise level   | Low — avoid decorative elements that add no info |
| Scan speed    | Layouts must be readable at a glance            |

---

## 3. Color System

### Primary (Brand Blue)

| Token          | Hex       | Tailwind Class          | Usage                                                        |
|----------------|-----------|-------------------------|--------------------------------------------------------------|
| Primary        | `#2563EB` | `blue-600`              | Main buttons, active sidebar item, links, selected tabs, focus states, important UI |
| Primary Dark   | `#1D4ED8` | `blue-700`              | Button hover states, pressed states                         |
| Primary Light  | `#DBEAFE` | `blue-100`              | Active sidebar background, selected row highlight, badge background |

### Neutral (Page Structure)

| Token          | Hex       | Tailwind Class          | Usage                                                   |
|----------------|-----------|-------------------------|---------------------------------------------------------|
| Background     | `#F8FAFC` | `slate-50`              | Page/app background                                     |
| Surface/Card   | `#FFFFFF` | `white`                 | Cards, modals, dropdowns, table rows                    |
| Border         | `#E2E8F0` | `slate-200`             | Card borders, dividers, input borders, table row lines  |

### Text

| Token          | Hex       | Tailwind Class          | Usage                                     |
|----------------|-----------|-------------------------|-------------------------------------------|
| Text Primary   | `#0F172A` | `slate-900`             | Headings, table data, main body text      |
| Text Secondary | `#475569` | `slate-600`             | Labels, metadata, helper text             |
| Text Muted     | `#94A3B8` | `slate-400`             | Placeholders, disabled states, timestamps |

### Semantic Colors

> **Rule:** Use semantic colors only to communicate state. Do not use them for decoration.

#### Success (Green)
| Token        | Hex       | Tailwind Class  | Used for                               |
|--------------|-----------|-----------------|----------------------------------------|
| Green        | `#16A34A` | `green-600`     | Active · Online · Paid · Completed     |
| Light Green  | `#DCFCE7` | `green-100`     | Badge/pill background for success states |

#### Warning (Amber)
| Token        | Hex       | Tailwind Class  | Used for                               |
|--------------|-----------|-----------------|----------------------------------------|
| Amber        | `#D97706` | `amber-600`     | Trial · Pending · Attention            |
| Light Amber  | `#FEF3C7` | `amber-100`     | Badge/pill background for warning states |

#### Danger (Red)
| Token        | Hex       | Tailwind Class  | Used for                                       |
|--------------|-----------|-----------------|------------------------------------------------|
| Red          | `#DC2626` | `red-600`       | Suspended · Failed · Cancelled · Delete action |
| Light Red    | `#FEE2E2` | `red-100`       | Badge/pill background for danger states        |

#### Info (Blue — same as Primary)
| Token        | Hex       | Tailwind Class  | Used for                          |
|--------------|-----------|-----------------|-----------------------------------|
| Blue         | `#2563EB` | `blue-600`      | Informational banners, info badges |
| Light Blue   | `#DBEAFE` | `blue-100`      | Info badge background             |

---

## 4. Typography

### Font Sizes & Weights

| Role             | Size  | Weight      | Tailwind Classes              |
|------------------|-------|-------------|-------------------------------|
| Page Title       | 24px  | 600 (Semi)  | `text-2xl font-semibold`      |
| Section Heading  | 18px  | 600 (Semi)  | `text-lg font-semibold`       |
| Card Heading     | 16px  | 600 (Semi)  | `text-base font-semibold`     |
| Normal Text      | 14px  | 400 (Reg)   | `text-sm font-normal`         |
| Secondary Text   | 13px  | 400 (Reg)   | `text-[13px] font-normal`     |
| Table Text       | 14px  | 400 (Reg)   | `text-sm font-normal`         |
| Small Labels     | 12px  | 500 (Med)   | `text-xs font-medium`         |

### Font Weight Reference

| Weight | Name     | Class           |
|--------|----------|-----------------|
| 400    | Regular  | `font-normal`   |
| 500    | Medium   | `font-medium`   |
| 600    | SemiBold | `font-semibold` |
| 700    | Bold     | `font-bold`     |

---

## 5. Color Usage Rules

1. **Don't use colors for decoration.** Color communicates state (success/warning/danger/info) — nothing else.
2. **Neutral greys carry the layout.** Background, cards, borders, and text use the neutral slate palette.
3. **Primary blue is the sole brand color.** One shade of interactive blue keeps the UI focused.
4. **Semantic = badge/status only.** Green/amber/red appear in status pills, alert banners, and icon indicators — not in headings, cards, or backgrounds.
5. **Low visual noise.** When in doubt, use less color.

---

## 6. Status Badge Pattern

Standard pill for entity status (tenant active/suspended, subscription state, etc.):

```html
<!-- Active / Paid / Completed -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
  Active
</span>

<!-- Trial / Pending / Attention -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
  Trial
</span>

<!-- Suspended / Failed / Cancelled -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
  Suspended
</span>

<!-- Info -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
  Info
</span>
```

---

## 7. Dashboard Scope (Screens to Build)

### SaaS Owner (Platform) Dashboard
These screens are served under `/platform/` and use the platform API (`/api/platform/`).

| Screen                  | API Endpoints Used                            |
|-------------------------|-----------------------------------------------|
| Login                   | `POST /api/platform/auth/login`               |
| Dashboard Overview      | Aggregated from tenants + subscriptions       |
| Tenants List            | `GET /api/platform/tenants`                   |
| Tenant Detail           | `GET /api/platform/tenants/{id}`              |
| Create Tenant           | `POST /api/platform/tenants`                  |
| Plans List              | `GET /api/platform/plans`                     |
| Create/Edit Plan        | `POST/PATCH /api/platform/plans`              |
| Subscriptions List      | `GET /api/platform/subscriptions`             |
| Subscription Detail     | `GET /api/platform/subscriptions/{id}`        |

> Tenant-facing (POS) screens come in a later phase.

---

## 8. Sidebar

The sidebar is dark — it creates a strong, professional contrast against the light content area.

### Colors

| Token               | Hex       | Tailwind Class    | Usage                                      |
|---------------------|-----------|-------------------|--------------------------------------------|
| Sidebar Background  | `#0F172A` | `slate-900`       | The sidebar's own background               |
| Sidebar Text        | `#CBD5E1` | `slate-300`       | Default nav item text and icons            |
| Active Item BG      | `#1E293B` | `slate-800`       | Background of the currently active item    |
| Active Icon/Text    | `#FFFFFF` | `white`           | Text and icon of the active item           |
| Primary Accent      | `#3B82F6` | `blue-500`        | Left border indicator on the active item   |

### Active Item Pattern

**Do not** make the entire active item bright blue. Use a dark background with a subtle blue left-border indicator:

```
┌────────────────────┐
│ ▌ 🏢 Tenants       │   ← 3px blue left border, dark bg, white text
└────────────────────┘

┌────────────────────┐
│   📋 Plans         │   ← no border, muted text (inactive)
└────────────────────┘
```

```html
<!-- Active sidebar item -->
<a class="flex items-center gap-3 px-4 py-2.5 rounded-lg
          bg-slate-800 text-white font-medium
          border-l-[3px] border-blue-500 pl-[13px]">
  <!-- icon + label -->
</a>

<!-- Inactive sidebar item -->
<a class="flex items-center gap-3 px-4 py-2.5 rounded-lg
          text-slate-300 hover:bg-slate-800 hover:text-white
          border-l-[3px] border-transparent pl-[13px]">
  <!-- icon + label -->
</a>
```

> The `border-l-[3px] border-transparent` on inactive items keeps horizontal alignment locked — text never shifts when an item activates.

### Sidebar Structure

```
┌──────────────────┐
│  Logo / App Name │  ← top, 64px tall, matches header height
├──────────────────┤
│  ▌ Dashboard     │  ← active
│    Tenants       │
│    Plans         │
│    Subscriptions │
├──────────────────┤
│    Settings      │  ← bottom section (optional separator)
│    Logout        │
└──────────────────┘
```

- Width: `w-64` (256px), fixed height `h-screen`, `overflow-y-auto`
- Logo area: same 64px height as the header so they align perfectly
- Section labels (e.g. "MANAGEMENT"): `text-xs font-medium text-slate-500 uppercase tracking-widest px-4 mb-1 mt-4`

---

## 9. Header

Clean white top bar — no color, no gradient, no shadow stack.

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Dashboard                        🔔   SuperAdmin ▼     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

| Property    | Value                         |
|-------------|-------------------------------|
| Background  | `#FFFFFF`                     |
| Bottom border | `1px solid #E2E8F0`         |
| Height      | `64px` (`h-16`)               |
| Left content | Page title (24px / 600)      |
| Right content | Notification bell + user menu |

```html
<!-- Header -->
<header class="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
  <!-- Left: current page title -->
  <h1 class="text-2xl font-semibold text-slate-900">Dashboard</h1>

  <!-- Right: actions -->
  <div class="flex items-center gap-4">
    <!-- Notification bell -->
    <button class="text-slate-400 hover:text-slate-600">
      <!-- bell icon -->
    </button>
    <!-- User menu -->
    <button class="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-slate-900">
      SuperAdmin
      <!-- chevron-down icon -->
    </button>
  </div>
</header>
```

---

## 10. Cards

Cards group related information. Keep them understated.

| Property       | Value                        | Tailwind                                   |
|----------------|------------------------------|--------------------------------------------|
| Background     | `#FFFFFF`                    | `bg-white`                                 |
| Border         | `1px solid #E2E8F0`          | `border border-slate-200`                  |
| Border Radius  | `10px`                       | `rounded-[10px]`                           |
| Shadow         | Very subtle                  | `shadow-sm`                                |
| Padding        | `20px`                       | `p-5`                                      |

> **Do not** use `rounded-2xl` or larger. `rounded-[10px]` is the max throughout the app.

### Stat Card Pattern (Dashboard KPIs)

```
┌──────────────────────────┐
│ TOTAL TENANTS            │  ← label: 12px / 500 / slate-500 / uppercase
│                          │
│ 24                       │  ← value: 32px / 700 / slate-900
│ ↑ 3 this month           │  ← trend: 13px / green-600 or red-600
└──────────────────────────┘
```

```html
<!-- Stat card -->
<div class="bg-white border border-slate-200 rounded-[10px] shadow-sm p-5">
  <p class="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Tenants</p>
  <p class="mt-2 text-3xl font-bold text-slate-900">24</p>
  <p class="mt-1 text-[13px] text-green-600">↑ 3 this month</p>
</div>
```

---

## 11. Buttons

| Variant    | Background  | Text      | Border             | Radius | Height |
|------------|-------------|-----------|--------------------|--------|--------|
| Primary    | `#2563EB`   | `#FFFFFF` | none               | `8px`  | `40px` |
| Secondary  | `#FFFFFF`   | `#334155` | `1px solid #CBD5E1`| `8px`  | `40px` |
| Danger     | `#DC2626`   | `#FFFFFF` | none               | `8px`  | `40px` |

```html
<!-- Primary -->
<button class="h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
  + Create Tenant
</button>

<!-- Secondary -->
<button class="h-10 px-4 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg transition-colors">
  Cancel
</button>

<!-- Danger -->
<button class="h-10 px-4 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors">
  Delete
</button>
```

---

## 12. Tables

Tables are the primary data display surface for the SuperAdmin.

| Property        | Value       | Tailwind                               |
|-----------------|-------------|----------------------------------------|
| Header BG       | `#F8FAFC`   | `bg-slate-50`                          |
| Header Text     | `#475569`   | `text-slate-600 text-xs font-medium uppercase tracking-wider` |
| Body BG         | `#FFFFFF`   | `bg-white`                             |
| Row Border      | `#E2E8F0`   | `border-b border-slate-200`            |
| Row Hover       | `#F8FAFC`   | `hover:bg-slate-50`                    |
| Body Text       | `#0F172A`   | `text-slate-900 text-sm`               |

> **No alternating row colors.** Row hover on `#F8FAFC` is the only row-level color change.

```
┌───────────────────────────────────────────────────────────────┐
│ BUSINESS        CODE      OWNER      PLAN      STATUS         │  ← slate-50 bg
├───────────────────────────────────────────────────────────────┤
│ ABC Restaurant  ABC001    Ali        Pro       ● Active        │  ← white bg
│ XYZ Restaurant  XYZ001    Ahmed      Basic     ● Trial         │
└───────────────────────────────────────────────────────────────┘
```

```html
<!-- Table skeleton -->
<div class="bg-white border border-slate-200 rounded-[10px] overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-slate-50 border-b border-slate-200">
      <tr>
        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Business</th>
        <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-slate-200 bg-white">
      <tr class="hover:bg-slate-50 transition-colors">
        <td class="px-6 py-4 text-sm text-slate-900">ABC Restaurant</td>
        <td class="px-6 py-4">
          <!-- status badge here -->
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 13. General Component Rules

- **Page background:** `bg-slate-50 min-h-screen`
- **Input field:** `border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`
- **Card (standard):** `bg-white border border-slate-200 rounded-[10px] shadow-sm p-5`
- **Max border radius anywhere:** `rounded-[10px]` — never `rounded-2xl` or `rounded-3xl`

---

## 14. Spacing & Layout

- Use Tailwind's default 4px spacing scale (`p-4` = 16px, `p-5` = 20px, `p-6` = 24px)
- Card padding: `p-5` (20px)
- Page content padding: `p-6` or `p-8`
- Gap between stat cards: `gap-5` or `gap-6`
- Sidebar width: `w-64` (256px), fixed
- Header height: `h-16` (64px)

---

*Last updated: 2026-08-17*
*Covers: SaaS Owner (Platform) dashboard phase.*
