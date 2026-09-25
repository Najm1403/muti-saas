# services/business_policy.py
#
# Business-template policy enforcement (spec D6) — a disabled checkbox in the
# form is not a real rule on its own; these checks re-verify server-side.

from sqlalchemy import select

from core.exceptions import ValidationError
from models.business_template import BusinessTemplate
from models.tenant import Tenant


async def load_business_policy(db, tenant_id) -> dict:
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        return {}
    template = await db.scalar(select(BusinessTemplate).where(BusinessTemplate.id == tenant.business_template_id))
    return (template.config if template else {}) or {}


def business_feature_flags(policy: dict | None) -> dict[str, bool]:
    """Return the small, non-sensitive capability set needed by shared UI.

    Missing settings stay enabled for backward compatibility with templates
    created before these switches existed.
    """
    policy = policy or {}
    return {
        "variants": policy.get("variants", {}).get("enabled") is not False,
        "addons": policy.get("addons", {}).get("enabled") is not False,
    }


async def enforce_tracking_policy(db, tenant_id, tracks_inventory: bool) -> None:
    policy = await load_business_policy(db, tenant_id)
    if policy.get("inventory", {}).get("tracking_forced_on") and not tracks_inventory:
        raise ValidationError("This business type requires inventory tracking on every variant.")


async def resolve_and_enforce_tracking(db, tenant_id, requested: bool | None, product_allows_tracking: bool) -> bool:
    """
    Resolves the effective tracks_inventory for a new variant, then enforces
    the mandatory-tracking policy against it (spec D6, item 3) — one DB-backed
    policy lookup, so callers never need their own load_business_policy() call
    (which would also bypass test patches applied to this module's copy of it).

    - requested=None (caller expressed no preference, e.g. the tenant dashboard's
      "Create a variant" form) defaults to tracked whenever the business template
      forces tracking on, or the product itself already has tracking enabled —
      matching the product's own auto-seeded default variant (services/product_service.py).
      This is what "auto-trackable when settings allow it" means.
    - An explicit True/False from the caller is honored as-is (the user may still
      manually untrack a specific variant) — except a product with tracking
      disabled outright can never have a tracked variant.
    - Raises ValidationError if the resolved value still violates tracking_forced_on
      (can only happen for an explicit False from the caller).
    """
    policy = await load_business_policy(db, tenant_id)
    forced_on = bool(policy.get("inventory", {}).get("tracking_forced_on"))
    resolved = forced_on or product_allows_tracking if requested is None else requested
    if not product_allows_tracking:
        resolved = False
    if forced_on and not resolved:
        raise ValidationError("This business type requires inventory tracking on every variant.")
    return resolved


async def enforce_pricing_policy(db, tenant_id, cost_price) -> None:
    """Compatibility hook: Cost Price is always optional.

    Older templates may still contain ``pricing.require_cost_price=true``.
    That legacy flag is intentionally ignored so existing tenant data cannot
    turn an optional accounting field into a catalog/variant blocker.
    """
    return None


async def enforce_variants_enabled(db, tenant_id) -> None:
    """
    Some business types (e.g. Fast Food) rely on Product + delta-priced
    Add-ons only and turn Variant Option Groups off entirely
    (config.variants.enabled: false). Mirrors the dashboard's own gating
    (which hides the "Attach Option Group" UI under such a template) so a
    direct API call can't bypass it. Missing/true means enabled — this is
    an opt-out, not a default-off switch.
    """
    policy = await load_business_policy(db, tenant_id)
    if policy.get("variants", {}).get("enabled") is False:
        raise ValidationError("This business type does not use Variant Option Groups — use Add-ons instead.")


async def enforce_addons_enabled(db, tenant_id) -> None:
    """
    Mirrors enforce_variants_enabled: a business type may turn Add-on Groups
    off entirely (config.addons.enabled: false) when it relies on Variant
    Option Groups for every price-affecting choice instead. Missing/true
    means enabled — this is an opt-out, not a default-off switch.
    """
    policy = await load_business_policy(db, tenant_id)
    if policy.get("addons", {}).get("enabled") is False:
        raise ValidationError("This business type does not use Add-on Groups — use Variant Options instead.")


def enforce_module_hidden_list(hidden) -> None:
    """Validates a candidate `config.modules.hidden` list before it's saved
    onto a Business Template — every entry must be a real, non-mandatory
    module key (core/modules.MODULE_KEYS minus MANDATORY_MODULES). Raises
    naming every offending key at once rather than one at a time, since this
    runs once per save, not per request like the other enforce_* checks here.
    """
    if not hidden:
        return
    from core.modules import MANDATORY_MODULES, MODULE_KEYS

    unknown = [k for k in hidden if k not in MODULE_KEYS]
    mandatory = [k for k in hidden if k in MANDATORY_MODULES]
    if unknown:
        raise ValidationError(f"Unknown module key(s) in config.modules.hidden: {', '.join(unknown)}.")
    if mandatory:
        raise ValidationError(f"These modules are mandatory and cannot be hidden: {', '.join(mandatory)}.")
