# schemas/variant_option_group.py
#
# Business-level, shared, single-select Variant Option Groups (spec Part B).
# Deliberately no min_selections/max_selections/is_required here — those
# only make sense for multi-select, which belongs to Add-on Groups
# (schemas/addon_group.py). is_required is a per-product override, carried
# on ProductVariantOptionGroupCreate/Response below.

from typing import Literal
from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class VariantOptionGroupCreate(APIBaseSchema):
    """Data required to create a Variant Option Group under a Business."""

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class VariantOptionGroupUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class VariantOptionGroupResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    business_id: UUID
    name: str
    description: str | None
    is_active: bool


class ProductVariantOptionGroupAttach(APIBaseSchema):
    """Attach an existing (shared) Variant Option Group to a product."""

    option_group_id: UUID
    is_required: bool = True
    display_order: int = Field(default=0, ge=0)
    # Laptop Store shareable-inventory model (spec sections 17/18): what
    # this PRODUCT's use of this GROUP means — see
    # ProductVariantOptionGroup.usage_type. Defaults to 'inventory_component'
    # — the only mode the dashboard offers now. 'specification' stays a
    # valid value for backward compatibility with pre-existing attachments
    # and direct API callers, but nothing new is created that way.
    usage_type: Literal["specification", "inventory_component"] = "inventory_component"
    min_selections: int = Field(default=1, ge=0)
    max_selections: int = Field(default=1, ge=1)
    default_option_id: UUID | None = None


class ProductVariantOptionGroupUpdate(APIBaseSchema):
    """Change an existing attachment's rules without detaching/reattaching."""

    is_required: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    usage_type: Literal["specification", "inventory_component"] | None = None
    min_selections: int | None = Field(default=None, ge=0)
    max_selections: int | None = Field(default=None, ge=1)
    default_option_id: UUID | None = None


class ProductVariantOptionAllowedSet(APIBaseSchema):
    """Replaces the full allow-list of a group's shared options for this
    product (spec section 22 — "compatibility is product-specific"). An
    empty list means "no restriction — every option in the group is
    allowed", matching today's behavior."""

    variant_option_ids: list[UUID] = Field(default_factory=list)


class ProductVariantOptionGroupResponse(APIBaseSchema):
    id: UUID
    product_id: UUID
    option_group_id: UUID
    is_required: bool
    display_order: int
    usage_type: str
    min_selections: int
    max_selections: int
    default_option_id: UUID | None = None
    # Empty = every option in the group is allowed (no restriction yet).
    allowed_option_ids: list[UUID] = Field(default_factory=list)
    # Denormalized for convenience so the frontend doesn't need a second call.
    name: str
    description: str | None = None
    # Set when this attachment came from the product's category template
    # rather than a one-off manual attach — see CategoryVariantOptionGroup.
    # The dashboard uses this to show a "from category" badge and to decide
    # whether removing it here is really a per-product override.
    source_category_id: UUID | None = None


# ── Category-level templates ─────────────────────────────────
#
# Attaching a group to a Category materializes it onto every existing
# product in that category (see CategoryVariantOptionGroupService) — a
# convenience layer on top of ProductVariantOptionGroup, not a replacement
# for it. Always usage_type='inventory_component' (see
# CategoryVariantOptionGroup's model docstring), so there's no usage_type
# field here at all.

class CategoryVariantOptionGroupAttach(APIBaseSchema):
    """Attach an existing (shared) Variant Option Group to a category —
    cascades onto every product currently in that category."""

    option_group_id: UUID
    is_required: bool = True
    display_order: int = Field(default=0, ge=0)
    min_selections: int = Field(default=1, ge=0)
    max_selections: int = Field(default=1, ge=1)
    default_option_id: UUID | None = None


class CategoryVariantOptionGroupUpdate(APIBaseSchema):
    """Changes the category template's own rules. Deliberately NOT cascaded
    to products that already have this group attached — a product may have
    customized its own is_required/allowed-options since inheriting it, and
    a category edit shouldn't silently overwrite that. Only membership
    (attaching/detaching a group on the category) cascades; see
    CategoryVariantOptionGroupService.attach_to_category/detach_from_category.
    """

    is_required: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    min_selections: int | None = Field(default=None, ge=0)
    max_selections: int | None = Field(default=None, ge=1)
    default_option_id: UUID | None = None


class CategoryVariantOptionGroupResponse(APIBaseSchema):
    id: UUID
    category_id: UUID
    option_group_id: UUID
    is_required: bool
    display_order: int
    min_selections: int
    max_selections: int
    default_option_id: UUID | None = None
    name: str
    description: str | None = None
