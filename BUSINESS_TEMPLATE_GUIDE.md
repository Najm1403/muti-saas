# How to build a new Business Template — Platform Dashboard

A step-by-step, verified-against-the-actual-code guide to creating a new **Business
Template** (e.g. "Retail / Apparel", "Pharmacy") that onboards correctly. Written for
whoever is at **Platform → Business Templates**. The guide contains only settings used by
the current application.

---

## 0. One template, two concerns

Module visibility is configured on the **Business Template** through
`config.modules.hidden`. A template controls both:

- What the tenant **sells**: Variant/Add-on shape, pricing rules, product fields,
  starting categories.
- Which **dashboard modules** the tenant can see at all (Kitchen Stations, Promotions,
  Reports, …) — see Section 4's `modules` entry.

Set at onboarding only (`Tenant.business_template_id`), effectively permanent for that
tenant — but the template's own `config` (including `modules.hidden`) is editable any
time from Platform → **Business Templates**, and the change applies immediately to
*every* tenant on that template. There is no per-tenant override any more: two tenants
on the same template always see the same modules.

---

## 1. Onboarding hierarchy — what must happen before what

Verified against the actual `create-tenant.html` wizard and the `OnboardingCreate` schema.

**Business Template must already exist before you touch Create Tenant.** It is not created
*during* tenant creation — it's a prerequisite you pick from a dropdown, so build it first
at Platform → Business Templates (this guide).

**Create Tenant then runs as one wizard, in this fixed order:**

1. **Business Info** — name, tenant code, **Business Template (required)**, country/timezone/currency
2. **Owner Account** — name/username/email
3. **Subscription** — Plan (optional, can be left empty), billing cycle, trial days
4. **Initial Branch** — name/code
5. Review & Confirm → submit

One API call (`POST /api/platform/onboarding/`) creates the Tenant + Business + the
template's seeded categories/Variant Option Groups/Add-on Groups + the first Branch + the
owner User + a Subscription, all together, in that single request.

**Module visibility isn't a separate step at all** — it's whatever `config.modules.hidden`
already says on the Business Template you picked in step 1. A freshly onboarded tenant
sees every module the template doesn't explicitly hide (absent/empty `hidden` = every
module) — nothing further to configure at onboarding time. To change it afterward, edit
the template's config from Platform → Business Templates; the tenant's own Modules tab
(Platform → Tenants → open the tenant → Modules) is read-only and just shows the result.

Dependency chain:

```
Business Template  (must pre-exist — its config.modules.hidden decides module visibility
                     for every tenant on it, from onboarding onward)
        │
        ▼
Create Tenant  (Business Template is required input; Plan is optional input)
```

**The one thing you genuinely cannot do out of order:** you cannot select a Business
Template that doesn't exist yet, and you cannot change a tenant's Business Template after
creation — no such flow exists; it's set once, at onboarding, permanently. Plan is freely
changeable later from the tenant's own platform pages.

---

## 2. Where you're working

**Platform → Business Templates** (`/platform/business-templates.html`). Only a **super**
platform admin sees the **New Template** button and can open a card to edit it — a
non-super admin can view the grid (name, summary chips, "View tenants using this
template") but not modify anything.

Each template is just two fields in the database:

```
BusinessTemplate { id, name, config (JSON), created_at, updated_at }
```

`name` must be unique across all templates (`ConflictError` if you reuse one). `config`
is **not schema-validated server-side**, with one exception: `modules.hidden` is checked
against the real module catalog (`enforce_module_hidden_list`) and rejects an unknown key
or a mandatory one (`dashboard`/`subscription`/`settings`) with a 422 — everything else
in `config` accepts any JSON object. The editor's "Not valid JSON" check is otherwise the
only validation that happens before save; a well-formed-but-wrong-shaped config (e.g. a
typo'd key outside `modules`) is saved silently and simply has no effect. Section 4 tells
you exactly which keys the rest of the app actually reads, so you know what a typo would
cost you.

---

## 3. Step-by-step: creating a template

1. Click **New Template**.
2. **Name** — this is what platform admins see in the Create-Tenant dropdown later
   (`Owner One creating "Demo Diner"` → picks "Fast Food" here). Make it recognizable to
   whoever onboards tenants, not just to you.
3. **Config (JSON)** — either:
   - Click **Load Fast Food preset** or **Load Laptop Business preset** to start from a
     real, working example (based on the JSON blocks from
     `COMPLETE-IMPLEMENTATION-SPEC.md` Part C, hardcoded into the page — the shipped
     Laptop Business preset seeds only a "Laptops" category, trimmed down from the
     spec doc's original Mobiles/Accessories example; add more categories manually per
     tenant if a shop also carries those), then edit it, or
   - Write the object from scratch using the shape reference in Section 4.
   - Click **Format** any time to pretty-print/validate the JSON without saving.
4. Click **Save**. On success the card appears in the grid immediately.
5. **You cannot test a Business Template without onboarding a tenant against it** — there
   is no "preview" mode. Go to **Create Tenant**, pick your new template from the
   **Business Template** dropdown (required field), and finish onboarding a real (or
   throwaway) tenant. Section 6 is a checklist for verifying it seeded correctly.

**Editing an existing template**: click its card (super admin only). The JSON editor
pre-fills with the current config (`JSON.stringify(t.config, null, 2)`). Save applies
immediately — **but see Section 5**, editing a template that tenants already use does
**not** retroactively change what was already seeded for them.

**Deleting**: blocked with a `ConflictError` ("used by N tenant(s)") while any non-deleted
tenant still references it. You cannot delete a template out from under a live tenant.

---

## 4. Supported config shape

Use the following application-backed keys:

```jsonc
{
  "variants": {
    "enabled": true,
    "seed_groups": [                // Read once at onboarding.
      { "name": "RAM", "values": ["4GB", "8GB", "16GB", "32GB"] }
      // Creates one shared VariantOptionGroup + one VariantOption per value, scoped to
      // the new tenant's Business. These become available in the tenant's "Variant
      // Options" library screen — tenants can add more later themselves.
    ]
  },
  "addons": {
    "enabled": true,
    "seed_groups": [                // Same seeding mechanism as variants.seed_groups,
                                     // but creates AddonGroup + AddonItem rows instead.
      { "name": "Toppings", "selection_type": "multiple", "min_select": 0, "max_select": 5,
        "items": [{ "name": "Extra Cheese", "price_delta": 100 }] }
    ]
  },
  "inventory": {
    "tracking_editable": true,
    "tracking_default_on": true,    // New products/variants start tracked; tenants may opt out.
    "tracking_forced_on": false,    // Use true only for a server-enforced mandate.
    "low_stock_threshold": 5        // Initial tenant threshold for tracked SKUs per branch.
  },
  "pricing": {
    "show_cost_price": true         // Shows/hides optional Cost Price fields.
  },
  "product_fields": {
    "sku": true,          // LIVE — menu.html / product-detail.html show/hide the SKU field.
    "specs": true,        // LIVE — shows/hides the repeatable key/value Specifications section.
    "warranty": true      // LIVE — shows/hides the Warranty field.
    // These fields and Cost Price remain optional.
  },
  "categories": {
    "default_categories": ["Laptops", "Mobiles", "Accessories"]
    // LIVE — one Category row per string, created once at onboarding, scoped to the new
    // tenant's Business. Just a head start; tenants can rename/add/remove afterward.
  },
  "modules": {
    "hidden": ["kitchen", "promotions"]
    // LIVE, SERVER-ENFORCED (core/modules.py, api/dependencies.tenant_enabled_modules).
    // Hides these dashboard sections from every tenant on this template — sidebar link
    // gone AND the routes themselves 403 with MODULE_DISABLED, not just a hidden link.
    // Also respected by the Flutter POS for "sales"/"promotions"/"deals" even though the
    // app has no client-side module concept (api/v1/pos/_guards.py, services/offer_service.py
    // both call the same enforcement function). Absent/empty = nothing hidden. The three
    // mandatory keys (dashboard/subscription/settings) can never appear here — rejected
    // at save time (see Section 2).
  }
}
```

### Changing `modules.hidden` on a template that's already in use — do this safely

Unlike Business Template assignment itself (permanent, set once at onboarding), the
`config` — including `modules.hidden` — is freely editable at any time, on any template,
**with no "in use" guard**: `BusinessTemplateService.update()` doesn't check whether a
tenant is on the template before applying the change (only `delete()` does that check).
That makes it easy to do, and just as easy to do carelessly — so two independent guards
are now *enforced*, not just advisory (both required together, on both delete and any
`modules.hidden` change):

- **A specific, grantable permission** (`PlatformAdmin.can_manage_business_templates`) —
  distinct from the coarse Owner/Manager/Viewer tier. Owners always have it implicitly; a
  Manager needs it explicitly granted from Platform Users (super-admin only to grant —
  `api/platform/platform_admins.py::update_platform_admin`). Without it,
  `require_business_template_manage()` 403s before the request is even considered
  (`code: "BUSINESS_TEMPLATE_MANAGE_REQUIRED"`).
- **A fresh password step-up**, every single time, regardless of how long the permission
  above has been held. `POST /api/platform/auth/step-up` re-verifies the caller's own
  current password and returns a 5-minute token scoped to the exact action + template
  (`core.security.create_platform_step_up_token`) — a token confirmed for deleting
  template A cannot be replayed against template B, a different action, or by a different
  admin. Deleting always requires it (`require_step_up`); an update only requires it when
  `config.modules.hidden` actually changes relative to what's currently stored
  (`BusinessTemplateService.update()` diffs old vs. new before writing anything) — editing
  `pricing`/`product_fields`/etc. still saves with no extra prompt. Missing/invalid/expired
  → `403 STEP_UP_REQUIRED`. In the UI this is one password-confirmation modal shared by
  both delete and a modules-changing save (`business-templates.html`'s `callGuarded()`).

Even with both guards enforced, exercise judgment before confirming:

1. **Check the blast radius first.** Click "View tenants using this template" — every
   tenant listed there gets the change **simultaneously**, the instant you confirm. There
   is no per-tenant override any more, so you cannot hide a module for one tenant on a
   shared template without hiding it for all of them — neither guard above checks this for
   you, they only confirm *you* meant to make *a* change, not that this particular blast
   radius is intended.
2. **It takes effect immediately, with no warning to the tenant.** The sidebar link
   disappears and the routes start 403ing on that tenant's *very next request* — no grace
   period, no notification to the tenant's admin or staff. If someone is mid-shift on a
   module you're about to hide, their page will flip to "This section is not part of your
   plan" the next time they navigate or the sidebar re-checks.
3. **Hiding `sales` is the highest-risk one — it isn't just a dashboard page.**
   `api/v1/pos/_guards.py`'s `operational_cashier()` calls the same enforcement, so hiding
   `sales` also blocks the Flutter POS from opening a cashier session — a shop cannot ring
   up sales at all until it's re-enabled. Hiding `promotions`/`deals` similarly makes
   `OfferService` silently stop applying active promotions/deals to live orders. Double
   check you mean to hide one of these three before confirming, especially outside a
   planned maintenance window.
4. **It's fully reversible.** Nothing is deleted — a hidden module's data (Kitchen Station
   configs, existing Promotions, etc.) is preserved untouched and simply becomes
   invisible/unreachable while hidden. Re-check the box and confirm again to restore it
   instantly (this also needs its own fresh step-up, same as hiding it did).
5. **Verify after saving**, don't just trust the checkbox: log in as (or impersonate) one
   affected tenant and confirm the sidebar and the page itself actually reflect the
   change — see Section 6's checklist, step 7.

**Practical rule of thumb:** use seed groups/default categories for onboarding data,
`tracking_default_on` for an editable creation default, `tracking_forced_on` and
`modules.hidden` for server policy, `variants.enabled` and
`addons.enabled` for feature availability, and `show_cost_price`/`product_fields.*` for
optional field visibility.

---

## 5. Seeding is one-shot, policy is live — know the difference

This trips people up because both flow from the same `config` object, but they behave
completely differently after onboarding:

- **Seeded data** (`variants.seed_groups`, `addons.seed_groups`,
  `categories.default_categories`) is copied into the tenant's own Business **once**, at
  the moment `POST /api/platform/onboarding/` runs. After that, it's the tenant's own data
  — editing the Business Template afterward does **not** add/remove/change anything for
  tenants who already onboarded. If you fix a typo in a seed category name after 5 tenants
  already used the template, those 5 tenants keep the typo; only tenants onboarded *after*
  your edit get the fix.
- **Policy/defaults** (`inventory.tracking_default_on`, `inventory.tracking_forced_on`,
  `product_fields.*`, `pricing.show_cost_price`) is **not** copied anywhere — it's
  re-read live from `Tenant.business_template_id → BusinessTemplate.config` on every
  relevant request (`load_business_policy()` in `services/business_policy.py`, called
  fresh each time). Editing these keys on an in-use template changes behavior for every
  tenant on it **immediately**, including tenants who onboarded months ago.

So: fixing a seed-data typo needs a fresh test tenant to verify. Fixing a
policy-key typo takes effect for real tenants the instant you hit Save — be careful
editing a template that's already in production use, and check "View tenants using this
template" first if you're unsure of the blast radius.

---

## 6. Verifying a new template end to end (checklist)

There's no dry-run mode, so verify with a real (throwaway) tenant:

1. **Onboard a test tenant** against the new template (Platform → Create Tenant). Use a
   throwaway tenant code you'll delete/deactivate afterward.
2. **Log into the tenant dashboard** as the new owner. Check:
   - **Categories** shows exactly your `default_categories`, nothing extra.
   - **Variant Options** (sidebar library screen) shows exactly your `variants.seed_groups`
     — each group with the right options.
   - **Add-on Groups** (sidebar library screen) shows exactly your `addons.seed_groups` —
     each group with the right items and prices; any `default_selected: true` items should
     show as pre-checked when later attached to a product.
3. **Create a product** in Menu:
   - Confirm the **SKU**/**Specifications**/**Warranty** fields show/hide exactly per your
     `product_fields` values.
   - Confirm the **Cost Price** field shows per `show_cost_price` and remains optional.
4. **Create a colored product in Add Product.** Select at least two Colors and enter each
   color's Sale Price and opening stock. Confirm color membership remains fixed there,
   prices remain editable, and Overall Stock shows
   all-color plus per-color/per-branch totals.
5. **Attach a Variant Selection group** and an **Add-on Group** separately. Confirm the
   former remains a shared inventory-component choice and the latter remains a price delta;
   neither generates color combinations or changes the product's own stock rows.
6. **Create a POS device**, activate it, and place a real order on the Flutter/web POS
   covering a plain product, a colored product, a product with a Variant Selection, and a
   product with Add-ons. Confirm the selected color SKU is the one whose quantity changes.
7. **If the template sets `modules.hidden`**: confirm each listed module's sidebar link
   is gone for the test tenant, and that navigating straight to its URL or calling its API
   shows the "not part of your plan" notice / 403s with `MODULE_DISABLED` rather than
   silently working.
8. **Clean up**: soft-delete/deactivate the test tenant when done (don't leave throwaway
   tenants around — see the pattern used throughout this session's own template testing).

---

## 7. Common mistakes

- **Forgetting `is_required` lives on the product↔group attachment, not the template.**
  `seed_groups` only creates the shared library group/options; whether a specific product
  must have a selection from that group is set per-product when it's attached
  (`ProductVariantOptionGroup.is_required`), not in the Business Template config.
- **Reusing a template name.** `create()` rejects a duplicate name outright — use a distinct
  name even for a near-duplicate variant of an existing template (e.g. "Laptop Business —
  Quantity Inventory").
- **Editing a live template's seed data expecting existing tenants to update.** They won't
  (Section 5) — you'd need a one-off script or manual dashboard edits per tenant to
  backfill them.
- **Trying to delete a template that's in use.** Reassign or deactivate the tenants first
  (there is currently no "move tenant to a different Business Template" flow — the field is
  set once at onboarding).
