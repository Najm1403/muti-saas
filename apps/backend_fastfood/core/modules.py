# core/modules.py
#
# The canonical list of tenant-dashboard modules. Which of these a tenant may
# use is decided by its Business Template's config (`config.modules.hidden` —
# see services/business_policy.py) — an opt-out list, so an absent/empty list
# means every module is visible (matching the `variants.enabled` precedent).

from __future__ import annotations

# key, human label, group, mandatory (always on, cannot be disabled)
_MODULES: list[tuple[str, str, str, bool]] = [
    ("dashboard",    "Overview",              "Core",       True),
    ("subscription", "Subscription & Billing", "Core",       True),
    ("settings",     "Settings",              "Core",       True),

    ("sales",        "Sales",                 "Commerce",   False),
    ("menu",         "Menu / Catalog",        "Commerce",   False),
    ("promotions",   "Promotions",            "Commerce",   False),
    ("deals",        "Deals / Combos",        "Commerce",   False),
    ("reports",      "Reports",               "Commerce",   False),

    ("branches",     "Branches",              "Operations", False),
    ("devices",      "POS Devices",           "Operations", False),
    ("kitchen",      "Kitchen Stations / KDS", "Operations", False),
    ("inventory",    "Inventory",             "Operations", False),

    ("expenses",     "Expenses",              "Back office", False),
    ("employees",    "Employees (HR)",        "Back office", False),
    ("attendance",   "Attendance",            "Back office", False),
    ("salaries",     "Salaries (Payroll)",    "Back office", False),

    ("users",        "Users",                 "Access",     False),
    ("roles",        "Roles & Permissions",   "Access",     False),
    ("activity",     "Activity Log",          "Access",     False),
]

MODULE_KEYS: tuple[str, ...] = tuple(k for k, *_ in _MODULES)
MANDATORY_MODULES: frozenset[str] = frozenset(k for k, _l, _g, m in _MODULES if m)
MODULE_LABEL: dict[str, str] = {k: l for k, l, _g, _m in _MODULES}


def module_catalog() -> list[dict]:
    """The list the platform UI renders (key / label / group / mandatory)."""
    return [
        {"key": k, "label": l, "group": g, "mandatory": m}
        for k, l, g, m in _MODULES
    ]


def normalise_hidden_modules(keys) -> list[str]:
    """Clean an incoming `modules.hidden` list: keep only known, non-mandatory
    keys, preserve catalog order, de-dupe. A mandatory module can never be
    hidden — silently dropped here; callers that need to reject it outright
    (the business-template save endpoint) use enforce_module_hidden_list()
    in services/business_policy.py instead."""
    incoming = {str(x).strip().lower() for x in (keys or [])}
    return [k for k in MODULE_KEYS if k in incoming and k not in MANDATORY_MODULES]


def effective_modules_from_hidden(hidden) -> set[str]:
    """Resolve a Business Template's `config.modules.hidden` value to the set
    of modules actually visible to tenants on that template. Absent/empty
    hidden list → every module. Mandatory modules are always included even
    if a stale/invalid hidden list somehow names one."""
    return set(MODULE_KEYS) - set(normalise_hidden_modules(hidden))
