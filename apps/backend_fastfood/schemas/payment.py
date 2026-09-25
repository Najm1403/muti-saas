# schemas/payment.py

from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from core.payment_methods import PAYMENT_METHODS, normalise_payment_method
from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class PaymentCreate(APIBaseSchema):
    """
    A payment made against a sale.

    Multiple payments may exist for one sale (split payment).
    Designed for both online and offline-first flows.

    payment_method must be one of core.payment_methods.PAYMENT_METHODS
    (Cash / JazzCash / EasyPaisa / Online Transfer / Credit Card) — case and
    spacing insensitive, normalised to the canonical label on the way in.
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    sale_id: UUID
    payment_method: str = Field(..., max_length=50, examples=PAYMENT_METHODS)
    amount: Decimal = Field(..., gt=Decimal("0"))
    reference: str | None = Field(
        None,
        max_length=150,
        description="Transaction or receipt reference for card/digital payments.",
    )

    @field_validator("payment_method", mode="before")
    @classmethod
    def _normalise_method(cls, v: str) -> str:
        return normalise_payment_method(v) if isinstance(v, str) else v


class PaymentResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Payment record returned by the API.
    """

    sale_id: UUID
    payment_method: str
    amount: Decimal
    reference: str | None
