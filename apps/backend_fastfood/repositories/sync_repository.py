from __future__ import annotations
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.category import Category
from models.payment import Payment
from models.product import Product
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from models.refund import Refund
from models.refund_item import RefundItem
from models.sale import Sale
from models.sale_item import SaleItem
from models.sale_item_option import SaleItemOption
from schemas.payment import PaymentCreate
from schemas.refund import RefundCreate
from schemas.sale import SaleCreate


class SyncRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def push_sale(self, data: SaleCreate) -> tuple[Sale, bool]:
        if data.id:
            stmt = (
                select(Sale)
                .where(Sale.id == data.id)
                .options(
                    selectinload(Sale.items).selectinload(SaleItem.options),
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                if (
                    existing.branch_id != data.branch_id
                    or existing.sale_number != data.sale_number
                    or existing.total != data.total
                    or existing.sold_at != data.sold_at
                ):
                    raise ValueError(
                        f"Sale id={data.id} already exists with conflicting data."
                    )
                return existing, True

        sale = Sale(
            id=data.id or uuid4(),
            branch_id=data.branch_id,
            device_id=data.device_id,
            user_id=data.user_id,
            sale_number=data.sale_number,
            sold_at=data.sold_at,
            subtotal=data.subtotal,
            discount=data.discount,
            total=data.total,
            status=data.status,
        )
        self.db.add(sale)
        await self.db.flush()

        for item_data in data.items:
            item = SaleItem(
                id=item_data.id or uuid4(),
                sale_id=sale.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                discount=item_data.discount,
                total=item_data.total,
            )
            self.db.add(item)
            await self.db.flush()

            for opt_data in item_data.options:
                option = SaleItemOption(
                    id=opt_data.id or uuid4(),
                    sale_item_id=item.id,
                    variant_option_id=opt_data.variant_option_id,
                    option_name=opt_data.option_name,
                )
                self.db.add(option)

        await self.db.flush()
        await self.db.refresh(sale)
        return sale, False

    async def push_payment(self, data: PaymentCreate) -> tuple[Payment, bool]:
        if data.id:
            stmt = select(Payment).where(Payment.id == data.id)
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                if (
                    existing.sale_id != data.sale_id
                    or existing.payment_method != data.payment_method
                    or existing.amount != data.amount
                ):
                    raise ValueError(
                        f"Payment id={data.id} already exists with conflicting data."
                    )
                return existing, True

        payment = Payment(
            id=data.id or uuid4(),
            sale_id=data.sale_id,
            payment_method=data.payment_method,
            amount=data.amount,
            reference=data.reference,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment, False

    async def push_refund(self, data: RefundCreate) -> tuple[Refund, bool]:
        if data.id:
            stmt = (
                select(Refund)
                .where(Refund.id == data.id)
                .options(selectinload(Refund.items))
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                if (
                    existing.sale_id != data.sale_id
                    or existing.refund_number != data.refund_number
                    or existing.amount != data.amount
                    or existing.refunded_at != data.refunded_at
                ):
                    raise ValueError(
                        f"Refund id={data.id} already exists with conflicting data."
                    )
                return existing, True

        refund = Refund(
            id=data.id or uuid4(),
            sale_id=data.sale_id,
            branch_id=data.branch_id,
            device_id=data.device_id,
            refund_number=data.refund_number,
            refunded_at=data.refunded_at,
            amount=data.amount,
            refund_method=data.refund_method,
            reason=data.reason,
        )
        self.db.add(refund)
        await self.db.flush()

        for item_data in data.items:
            item = RefundItem(
                id=uuid4(),
                refund_id=refund.id,
                sale_item_id=item_data.sale_item_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=item_data.amount,
            )
            self.db.add(item)

        await self.db.flush()
        await self.db.refresh(refund)
        return refund, False

    async def pull_menu(
        self, business_id: UUID, since: datetime | None = None
    ) -> dict:
        cat_conditions = [
            Category.business_id == business_id,
            Category.deleted_at.is_(None),
            Category.is_active.is_(True),
        ]
        if since:
            cat_conditions.append(Category.updated_at > since)
        cat_stmt = select(Category).where(*cat_conditions).order_by(Category.display_order)
        cat_result = await self.db.execute(cat_stmt)
        categories = cat_result.scalars().all()

        category_ids = [c.id for c in categories]

        products: list[Product] = []
        option_groups: list[VariantOptionGroup] = []
        options: list[VariantOption] = []

        if category_ids:
            prod_conditions = [
                Product.category_id.in_(category_ids),
                Product.deleted_at.is_(None),
                Product.is_active.is_(True),
            ]
            if since:
                prod_conditions.append(Product.updated_at > since)
            prod_stmt = (
                select(Product).where(*prod_conditions).order_by(Product.display_order)
            )
            prod_result = await self.db.execute(prod_stmt)
            products = list(prod_result.scalars().all())

            # Variant Option Groups are Business-level now, not owned by a
            # single product — pull every active group for this business
            # rather than filtering by product_id.
            og_conditions = [
                VariantOptionGroup.business_id == business_id,
                VariantOptionGroup.deleted_at.is_(None),
                VariantOptionGroup.is_active.is_(True),
            ]
            if since:
                og_conditions.append(VariantOptionGroup.updated_at > since)
            og_stmt = select(VariantOptionGroup).where(*og_conditions)
            og_result = await self.db.execute(og_stmt)
            option_groups = list(og_result.scalars().all())

            og_ids = [og.id for og in option_groups]

            if og_ids:
                opt_conditions = [
                    VariantOption.option_group_id.in_(og_ids),
                    VariantOption.deleted_at.is_(None),
                    VariantOption.is_active.is_(True),
                ]
                if since:
                    opt_conditions.append(VariantOption.updated_at > since)
                opt_stmt = (
                    select(VariantOption)
                    .where(*opt_conditions)
                    .order_by(VariantOption.display_order)
                )
                opt_result = await self.db.execute(opt_stmt)
                options = list(opt_result.scalars().all())

        return {
            "categories": categories,
            "products": products,
            "option_groups": option_groups,
            "options": options,
        }
