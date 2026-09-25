"""Server-authoritative catalog checks shared by sale entry points.

Variant identity/price and Add-on price verification are NOT done here —
those are VariantService.validate_variant_selection() (spec D4) and
PosSaleService.resolve_addon_price_deltas() (spec D7) respectively. This
function only confirms the product itself is real, active, and available at
the branch — the shared precondition for every sale-creation path.
"""
from sqlalchemy import select
from models.product import Product
from models.category import Category
from models.business import Business
from models.product_branch import ProductBranch
from core.exceptions import ValidationError

async def validate_catalog(db, data, tenant_id, branch_id):
    ids = {i.product_id for i in data.items}
    products = {p.id: p for p in (await db.scalars(select(Product)
        .join(Category, Product.category_id == Category.id)
        .join(Business, Category.business_id == Business.id).where(
            Product.id.in_(ids), Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None), Category.deleted_at.is_(None),
            Category.is_active.is_(True), Product.deleted_at.is_(None), Product.is_active.is_(True)))).all()}
    if set(products) != ids:
        raise ValidationError("Product is unavailable in this tenant.")
    for item in data.items:
        product = products[item.product_id]
        if not product.all_branches and await db.scalar(select(ProductBranch.product_id).where(
            ProductBranch.product_id == product.id, ProductBranch.branch_id == branch_id,
            ProductBranch.is_active.is_(True))) is None:
            raise ValidationError("Product is unavailable at this branch.")
    return products
