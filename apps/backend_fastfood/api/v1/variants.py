from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, require_any_module, require_permission, require_module
from core.exceptions import ValidationError
from db.session import get_db
from models.product import Product
from models.category import Category
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from models.business import Business
from models.variant import Variant
from schemas.variant import (
    VariantCreate,
    VariantUpdate,
    VariantResponse,
    VariantStockUpdate,
    VariantStockAdjustment,
    VariantStockTransfer,
)
from services.variant_service import VariantService

router = APIRouter(tags=['Variant inventory'], dependencies=[Depends(require_module('inventory'))])
menu_router = APIRouter(tags=['Product variants'], dependencies=[Depends(require_module('menu'))])
catalog_router = APIRouter(tags=['Product variants'], dependencies=[Depends(require_any_module('menu', 'inventory'))])
view = require_permission('inventory.view')
manage = require_permission('inventory.manage')


async def _variant_display_names(db: AsyncSession, variant: Variant, product: Product) -> tuple[str, str]:
    """(product_name, variant_name) for exactly one variant.

    Mirrors list_variants()'s batch computation below, just scoped to a
    single variant/product — every mutation endpoint (create/update/
    set-stock/increase/decrease/transfer) needs this too, not only the list
    endpoint. Before this helper existed, those endpoints returned
    product_name/variant_name as null (schemas/variant.py's declared
    default), and the tenant dashboard's optimistic row-merge
    (`{...cachedRow, ...serverResponse}`) then overwrote the previously
    correct cached name with null, showing "SKU <id-prefix>" in its place
    after any stock action.
    """
    option_ids = [UUID(str(oid)) for oid in (variant.option_value_ids or [])]
    option_names: dict[str, str] = {}
    if option_ids:
        rows = (await db.execute(
            select(VariantOption, VariantOptionGroup)
            .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
            .where(VariantOption.id.in_(option_ids))
        )).all()
        option_names = {str(option.id): f"{group.name}: {option.name}" for option, group in rows}

    # A product that is itself a shared inventory component (e.g. "RAM 12 GB")
    # is labeled with the option/group that references it, same as list_variants().
    component_row = (await db.execute(
        select(VariantOptionGroup.name, VariantOption.name)
        .select_from(VariantOption)
        .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
        .where(VariantOption.component_product_id == product.id)
        .limit(1)
    )).first()
    product_name = f"{component_row[0]}: {component_row[1]}" if component_row else product.name

    parts = [option_names.get(str(oid), 'Archived option') for oid in option_ids]
    variant_name = ' + '.join(parts) if parts else 'Default variant'
    return product_name, variant_name


async def _to_response(
    svc: VariantService, variant: Variant, sellability: tuple[bool, str | None] | None = None,
    branch_ids: set[UUID] | None = None, product: Product | None = None, compute_names: bool = True,
) -> VariantResponse:
    resp = VariantResponse.model_validate(variant)
    resp.stock_by_branch = await svc.stock_snapshot(variant, branch_ids=branch_ids)
    if sellability is None:
        sellability = (await svc.compute_sellability([variant]))[variant.id]
    resp.sellable, resp.sellable_reason = sellability
    if compute_names:
        # list_variants() already computes these in batch for its whole page
        # and overrides them afterward (compute_names=False there) — doing it
        # again per-row here would be an avoidable N+1 query.
        if product is None:
            product = await svc.db.scalar(select(Product).where(Product.id == variant.product_id))
        if product is not None:
            resp.product_name, resp.variant_name = await _variant_display_names(svc.db, variant, product)
    return resp


@catalog_router.get('/variants', response_model=list[VariantResponse])
async def list_variants(
    product_id: UUID | None = None,
    tracked_only: bool = False,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from api.branch_access import visible_branches
    svc = VariantService(db, created_by=current.user_id)
    branch_ids = await visible_branches(db, current)
    stmt = select(Variant, Product).join(Product, Variant.product_id == Product.id).join(
        Category, Product.category_id == Category.id
    ).join(Business, Category.business_id == Business.id).where(
        Business.tenant_id == current.tenant_id,
        Variant.deleted_at.is_(None),
        Product.deleted_at.is_(None),
        Category.deleted_at.is_(None),
        Business.deleted_at.is_(None),
    )
    if product_id:
        stmt = stmt.where(Variant.product_id == product_id)
    if tracked_only:
        stmt = stmt.where(
            Product.allow_inventory_tracking.is_(True),
            Variant.tracks_inventory.is_(True),
        )
    rows = (await db.execute(stmt.order_by(Product.name, Variant.combination_key))).all()
    variants = [variant for variant, _ in rows]
    option_ids = {UUID(str(option_id)) for variant in variants for option_id in (variant.option_value_ids or [])}
    option_names = {}
    if option_ids:
        options = (await db.execute(
            select(VariantOption, VariantOptionGroup)
            .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
            .where(VariantOption.id.in_(option_ids))
        )).all()
        option_names = {str(option.id): f"{group.name}: {option.name}" for option, group in options}

    product_ids = {product.id for _, product in rows}
    component_labels = {}
    if product_ids:
        component_rows = (await db.execute(
            select(VariantOption, VariantOptionGroup)
            .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
            .where(VariantOption.component_product_id.in_(product_ids))
        )).all()
        component_labels = {
            option.component_product_id: f"{group.name}: {option.name}" for option, group in component_rows
        }

    sellability = await svc.compute_sellability(variants)
    result = []
    for variant, product in rows:
        parts = [option_names.get(str(option_id), 'Archived option') for option_id in (variant.option_value_ids or [])]
        response = await _to_response(
            svc, variant, sellability=sellability[variant.id], branch_ids=branch_ids, compute_names=False,
        )
        result.append(response.model_copy(update={
            'product_name': component_labels.get(product.id, product.name),
            'variant_name': ' + '.join(parts) if parts else 'Default variant',
        }))
    return result


@menu_router.post('/products/{product_id}/variants', response_model=VariantResponse)
async def create_variant(product_id: UUID, data: VariantCreate, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = VariantService(db, created_by=current.user_id)
    variant = await svc.create(current.tenant_id, product_id, data.option_ids,
        sale_price=data.sale_price, cost_price=data.cost_price, tracks_inventory=data.tracks_inventory,
        opening_stock_by_branch=data.opening_stock_by_branch)
    await db.commit()
    from api.branch_access import visible_branches
    return await _to_response(svc, variant, branch_ids=await visible_branches(db, current))


@menu_router.patch('/variants/{variant_id}', response_model=VariantResponse)
async def update_variant(variant_id: UUID, data: VariantUpdate, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from services.business_policy import enforce_pricing_policy
    svc = VariantService(db, created_by=current.user_id)
    variant = await svc.get(current.tenant_id, variant_id, lock=True)
    if data.tracks_inventory is not None:
        variant = await svc.set_tracking(current.tenant_id, variant_id, data.tracks_inventory, data.opening_stock_by_branch)
    for field in ("sale_price", "cost_price", "compare_price"):
        value = getattr(data, field)
        if value is not None:
            setattr(variant, field, value)
    await enforce_pricing_policy(db, current.tenant_id, variant.cost_price)
    await db.commit()
    from api.branch_access import visible_branches
    return await _to_response(svc, variant, branch_ids=await visible_branches(db, current))


@menu_router.delete('/variants/{variant_id}', status_code=204)
async def delete_variant(variant_id: UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Removes a Variant that was never usable — most commonly the zero-option
    default Variant left permanently unsellable once a required Variant Option
    Group is attached and real combinations take over. Blocked (409) if it was
    ever sold, still carries stock anywhere, or is the product's last Variant.
    """
    await VariantService(db, created_by=current.user_id).delete(current.tenant_id, variant_id)
    await db.commit()


@router.post('/variants/{variant_id}/stock', response_model=VariantResponse)
async def set_stock(variant_id: UUID, data: VariantStockUpdate, branch_id: UUID | None = None, current: CurrentUser = Depends(manage), db: AsyncSession = Depends(get_db)):
    svc = VariantService(db, created_by=current.user_id)
    variant = await svc.set_stock(current.tenant_id, variant_id, data.stock_quantity, data.note, branch_id=branch_id)
    await db.commit()
    from api.branch_access import visible_branches
    return await _to_response(svc, variant, branch_ids=await visible_branches(db, current))


@router.post('/variants/{variant_id}/stock/increase', response_model=VariantResponse)
async def increase_stock(variant_id: UUID, data: VariantStockAdjustment, branch_id: UUID | None = None, current: CurrentUser = Depends(manage), db: AsyncSession = Depends(get_db)):
    svc = VariantService(db, created_by=current.user_id)
    variant = await svc.adjust_stock(current.tenant_id, variant_id, 'increase', data.quantity, data.note, branch_id=branch_id)
    await db.commit()
    from api.branch_access import visible_branches
    return await _to_response(svc, variant, branch_ids=await visible_branches(db, current))


@router.post('/variants/{variant_id}/stock/decrease', response_model=VariantResponse)
async def decrease_stock(variant_id: UUID, data: VariantStockAdjustment, branch_id: UUID | None = None, current: CurrentUser = Depends(manage), db: AsyncSession = Depends(get_db)):
    svc = VariantService(db, created_by=current.user_id)
    variant = await svc.adjust_stock(current.tenant_id, variant_id, 'decrease', data.quantity, data.note, branch_id=branch_id)
    await db.commit()
    from api.branch_access import visible_branches
    return await _to_response(svc, variant, branch_ids=await visible_branches(db, current))


@router.post('/variants/{variant_id}/transfer', response_model=VariantResponse,
    summary="Move stock between branches",
    description=(
        "Moves stock for one Variant from one branch to another. Works identically for a "
        "'fixed' product's own stock and an 'upgradable' product's shared linked-component "
        "stock — both are just Variant stock underneath, so there is no separate endpoint "
        "for transferring a component."
    ))
async def transfer_stock(variant_id: UUID, data: VariantStockTransfer, current: CurrentUser = Depends(manage), db: AsyncSession = Depends(get_db)):
    svc = VariantService(db, created_by=current.user_id)
    variant = await svc.transfer_stock(
        current.tenant_id, variant_id, data.from_branch_id, data.to_branch_id, data.quantity, note=data.note)
    await db.commit()
    from api.branch_access import visible_branches
    return await _to_response(svc, variant, branch_ids=await visible_branches(db, current))


@router.get('/variants/{variant_id}/history')
async def history(variant_id: UUID, branch_id: UUID | None = None, current: CurrentUser = Depends(view), db: AsyncSession = Depends(get_db)):
    rows = await VariantService(db, created_by=current.user_id).history(current.tenant_id, variant_id, branch_id=branch_id)
    return [{'id': r.id, 'variant_id': r.variant_id, 'change_type': r.adjustment_type, 'quantity_delta': r.quantity_change, 'reference_id': r.reference_id, 'created_by': r.created_by, 'adjustment_type': r.adjustment_type, 'quantity_change': r.quantity_change,
             'resulting_quantity': r.resulting_quantity, 'note': r.note, 'created_at': r.created_at, 'branch_id': r.branch_id} for r in rows]
