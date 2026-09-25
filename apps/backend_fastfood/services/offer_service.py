"""One set of offer calculations for POS previews and committed sales."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.promotion import Promotion
from models.deal import Deal
from models.branch_promotion import BranchPromotion
from models.branch_deal import BranchDeal
from models.product import Product
from models.category import Category
from models.business import Business
from models.variant import Variant
from models.product_variant_option_group import ProductVariantOptionGroup
from core.exceptions import ValidationError

CENT = Decimal("0.01")

def money(value): return max(Decimal(0), value).quantize(CENT, rounding=ROUND_HALF_UP)

class OfferService:
    def __init__(self, db): self.db = db

    async def _active(self, model, tenant_id, branch_id, *, lock=False):
        now = datetime.now(timezone.utc)
        statement = select(model).where(model.tenant_id == tenant_id, model.deleted_at.is_(None), model.is_active.is_(True))
        if model is Deal: statement = statement.options(selectinload(Deal.items))
        if lock: statement = statement.with_for_update(of=model)
        rows = (await self.db.scalars(statement)).all()
        out=[]
        for offer in rows:
            if (offer.valid_from and offer.valid_from > now) or (offer.valid_until and offer.valid_until < now): continue
            if not offer.all_branches:
                assignment, key = (BranchPromotion, BranchPromotion.promotion_id) if model is Promotion else (BranchDeal, BranchDeal.deal_id)
                if await self.db.scalar(select(key).where(key == offer.id, assignment.branch_id == branch_id)) is None: continue
            out.append(offer)
        return out

    async def _default_prices(self, product_ids):
        """Product.id -> its default variant's sale_price (spec D1 — no more base_price)."""
        if not product_ids:
            return {}
        rows = await self.db.execute(
            select(Product.id, Variant.sale_price)
            .join(Variant, Product.default_variant_id == Variant.id)
            .where(Product.id.in_(product_ids)))
        return {pid: price for pid, price in rows.all()}

    async def calculate(self, data, tenant_id, branch_id, *, commit=False, promo_code=None):
        from api.dependencies import tenant_enabled_modules
        modules = await tenant_enabled_modules(self.db, tenant_id)
        product_ids = [i.product_id for i in data.items]
        products = {p.id:p for p in (await self.db.scalars(select(Product).where(Product.id.in_(product_ids)))).all()}
        default_prices = await self._default_prices(product_ids)
        quantities={}
        for i in data.items: quantities[i.product_id]=quantities.get(i.product_id,Decimal(0))+i.quantity
        offers=[]
        promotions = await self._active(Promotion, tenant_id, branch_id, lock=commit) if "promotions" in modules else []
        for promo in promotions:
            if promo.max_uses is not None and promo.used_count >= promo.max_uses: continue
            if not commit and promo.promo_code and promo.promo_code != promo_code: continue
            reward=[]; eligible=dict(quantities); reward_value=Decimal(0)
            if promo.type in {"BXGY", "FREE_ITEM"}:
                reward_products = select(Product).join(Category, Product.category_id == Category.id).join(Business, Category.business_id == Business.id).where(
                    Business.tenant_id == tenant_id, Product.is_active.is_(True), Product.deleted_at.is_(None))
                if promo.reward_product_id: reward_products=reward_products.where(Product.id == promo.reward_product_id)
                elif promo.reward_category_id: reward_products=reward_products.where(Product.category_id == promo.reward_category_id)
                else: continue
                candidates=(await self.db.scalars(reward_products.order_by(Product.id))).all()
                if not candidates: continue
                candidate_prices = await self._default_prices([c.id for c in candidates])
                candidates = sorted(candidates, key=lambda c: (candidate_prices.get(c.id, Decimal(0)), c.id))
                chosen=next((p for p in candidates if p.id in quantities),candidates[0])
                chosen_price = candidate_prices.get(chosen.id, Decimal(0))
                qty=Decimal(promo.reward_quantity or 1)
                if qty<=0: continue
                if commit:
                    if eligible.get(chosen.id,0)<qty: continue
                    eligible[chosen.id]-=qty
                else:
                    # Preview adds a distinct reward line; checkout revalidates the full cart.
                    required=await self.db.scalar(select(ProductVariantOptionGroup.id).where(
                        ProductVariantOptionGroup.product_id==chosen.id, ProductVariantOptionGroup.is_required.is_(True)).limit(1))
                    if required: continue
                    reward=[{"product_id":str(chosen.id),"variant_id":str(chosen.default_variant_id) if chosen.default_variant_id else None,"product_name":chosen.name,"unit_price":str(chosen_price),"quantity":str(qty)}]
                reward_value=chosen_price*qty
                if promo.reward_discount_type == "PERCENTAGE": reward_value*=min(Decimal(100),promo.reward_discount_value or 0)/100
                elif promo.reward_discount_type == "FLAT_AMOUNT": reward_value=min(reward_value,promo.reward_discount_value or 0)
            matching=sum(q for pid,q in eligible.items() if
                (not promo.trigger_product_id or pid==promo.trigger_product_id) and
                (not promo.trigger_category_id or (pid in products and products[pid].category_id==promo.trigger_category_id)))
            if (promo.trigger_product_id or promo.trigger_category_id) and matching<=0: continue
            if promo.trigger_min_qty and matching<promo.trigger_min_qty: continue
            trigger_total=data.subtotal-(reward_value if commit and promo.type in {"BXGY","FREE_ITEM"} else 0)
            if promo.trigger_min_amount and trigger_total<promo.trigger_min_amount: continue
            discount = (data.subtotal*promo.discount_value/100 if promo.type=="PERCENTAGE" else
                min(data.subtotal,promo.discount_value) if promo.type=="FLAT_AMOUNT" else reward_value)
            offers.append({"kind":"promotion","id":str(promo.id),"name":promo.name,"discount":str(money(discount)),"rewards":reward,"model":promo})
        deals = await self._active(Deal, tenant_id, branch_id, lock=commit) if "deals" in modules else []
        for deal in deals:
            remaining=dict(quantities); bundle=Decimal(0); free=Decimal(0); valid=True
            parts=[part for part in deal.items if part.deleted_at is None]
            if not parts: continue
            for part in sorted(parts,key=lambda p:(p.product_id is None,p.sort_order)):
                need=Decimal(part.quantity)
                for pid in sorted(remaining,key=str):
                    product=products.get(pid)
                    if product is None or (part.product_id and pid!=part.product_id) or (part.category_id and product.category_id!=part.category_id): continue
                    taken=min(need,remaining[pid]); need-=taken; remaining[pid]-=taken
                    price = default_prices.get(pid, Decimal(0))
                    bundle+=taken*price
                    if part.is_free: free+=taken*price
                if need>0: valid=False; break
            if not valid: continue
            if deal.fixed_price is not None: discount=max(Decimal(0),bundle-deal.fixed_price)
            elif deal.discount_type=="PERCENTAGE": discount=free+(bundle-free)*(deal.discount_value or 0)/100
            else: discount=free+(deal.discount_value or 0)
            offers.append({"kind":"deal","id":str(deal.id),"name":deal.name,"discount":str(money(min(bundle,discount))),"rewards":[],"model":deal})
        return offers

    async def validate(self, data, tenant_id, branch_id, user_id):
        from api.dependencies import get_user_permissions
        if data.promotion_id and data.deal_id: raise ValidationError("Choose one offer per order.")
        if data.promotion_id or data.deal_id:
            offers=await self.calculate(data,tenant_id,branch_id,commit=True)
            chosen=next((o for o in offers if o["id"]==str(data.promotion_id or data.deal_id)),None)
            if chosen is None or abs(Decimal(chosen["discount"])-data.discount)>CENT or any(i.discount for i in data.items):
                raise ValidationError("Offer no longer matches this cart. Reapply it before checkout.")
            if chosen["kind"]=="promotion": chosen["model"].used_count+=1
        elif data.discount or any(i.discount for i in data.items):
            permissions=await get_user_permissions(self.db,user_id,tenant_id)
            if "*" not in permissions and "sales.discount" not in permissions:
                raise ValidationError("Manual discounts require permission.")
            if "*" not in permissions and data.subtotal>0:
                from models.user import User
                cap=await self.db.scalar(select(User.max_discount_percent).where(User.id==user_id))
                if cap is not None and (data.discount/data.subtotal)*100>cap:
                    raise ValidationError(f"Discount exceeds your maximum of {cap}%.")
