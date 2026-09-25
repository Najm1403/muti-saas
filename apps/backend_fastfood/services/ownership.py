"""Shared validation for cross-record tenant relationships."""
from sqlalchemy import select
from models.branch import Branch
from models.business import Business
from core.exceptions import NotFoundError

async def tenant_branches(db, tenant_id, branch_ids):
    ids = list(dict.fromkeys(branch_ids))
    if ids:
        owned = (await db.scalars(select(Branch.id).join(Business, Branch.business_id == Business.id)
            .where(Branch.id.in_(ids), Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None), Branch.deleted_at.is_(None)))).all()
        if set(owned) != set(ids):
            raise NotFoundError("Branch not found in this tenant.")
    return ids


async def catalog_references(db, tenant_id, values):
    from models.category import Category
    from models.product import Product
    from models.preparation_station import PreparationStation
    for field, value in values.items():
        if not value: continue
        if field in {"product_id", "trigger_product_id", "reward_product_id"}:
            stmt=select(Product.id).join(Category, Product.category_id==Category.id).join(Business,Category.business_id==Business.id).where(Product.id==value,Product.deleted_at.is_(None),Business.tenant_id==tenant_id)
        elif field in {"category_id", "trigger_category_id", "reward_category_id"}:
            stmt=select(Category.id).join(Business,Category.business_id==Business.id).where(Category.id==value,Category.deleted_at.is_(None),Business.tenant_id==tenant_id)
        elif field=="preparation_station_id":
            stmt=select(PreparationStation.id).join(Branch,PreparationStation.branch_id==Branch.id).join(Business,Branch.business_id==Business.id).where(PreparationStation.id==value,PreparationStation.deleted_at.is_(None),Business.tenant_id==tenant_id)
        else: continue
        if await db.scalar(stmt) is None: raise NotFoundError(f"Invalid {field} for this tenant.")
