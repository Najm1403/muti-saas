# core/payment_methods.py
#
# Canonical list of sale payment methods (POS "Take Payment" + tenant dashboard
# manual payments). Fixed on purpose — every place that records a payment
# against a Sale validates against this list, so shift-close totals and the
# sales reports can sum "Cash" / "JazzCash" / etc. without guessing at
# free-text spellings.
#
# Historical rows created before this list existed (e.g. old "Card" / "Bank" /
# "Mobile" seed data) are NOT rejected on read — see `label_lenient()` — only
# NEW writes are constrained to this list.

from __future__ import annotations

PAYMENT_METHODS: list[str] = [
    "Cash",
    "JazzCash",
    "EasyPaisa",
    "Online Transfer",
    "Credit Card",
]

# free-text spellings (old client versions, seed data, manual entry) mapped
# onto the canonical label. Keys are UPPERCASE with whitespace collapsed.
_ALIASES: dict[str, str] = {
    "CASH": "Cash",
    "JAZZCASH": "JazzCash",
    "JAZZ CASH": "JazzCash",
    "EASYPAISA": "EasyPaisa",
    "EASY PAISA": "EasyPaisa",
    "ONLINE TRANSFER": "Online Transfer",
    "ONLINETRANSFER": "Online Transfer",
    "BANK": "Online Transfer",
    "BANK TRANSFER": "Online Transfer",
    "DIGITAL": "Online Transfer",
    "CREDIT CARD": "Credit Card",
    "CREDITCARD": "Credit Card",
    "CARD": "Credit Card",
}

_CANONICAL_BY_UPPER: dict[str, str] = {m.upper(): m for m in PAYMENT_METHODS}


def normalise_payment_method(raw: str) -> str:
    """Map input to one of the 5 canonical labels. Raises ValueError if unrecognised.

    Used to validate a payment at the point it is taken (POS checkout, tenant
    dashboard "record payment"). Case/spacing insensitive: "cash", "CASH",
    " Cash " all resolve to "Cash".

    "Free Guest" (a special zero-value payment method that forced a whole
    order to $0) is retired — replaced by a manual discount applied in the
    cart before checkout (services/discount_service.py). Historical "Free
    Guest" sales still display correctly via label_lenient() below; only new
    writes are affected.
    """
    key = " ".join((raw or "").strip().upper().split())
    canonical = _CANONICAL_BY_UPPER.get(key) or _ALIASES.get(key)
    if not canonical:
        raise ValueError(
            f"Unsupported payment method {raw!r}. Choose one of: {', '.join(PAYMENT_METHODS)}."
        )
    return canonical


def label_lenient(raw: str) -> str:
    """Best-effort canonical label for reporting over historical data.

    Never raises — a value that predates this list (or a corrupted string)
    is shown as-is instead of being dropped from totals.
    """
    try:
        return normalise_payment_method(raw)
    except ValueError:
        return (raw or "").strip() or "Unknown"
