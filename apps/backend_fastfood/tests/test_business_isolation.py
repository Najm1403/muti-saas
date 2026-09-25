# tests/test_business_isolation.py
#
# Verifies that every business-module repository enforces tenant isolation.
# Each test uses the H fixture (two complete tenant hierarchies, rolled back
# after each function) and confirms that cross-tenant access returns None/[].

from __future__ import annotations

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.branch_repository import BranchRepository
from repositories.category_repository import CategoryRepository
from repositories.device_repository import DeviceRepository
from repositories.variant_option_group_repository import VariantOptionGroupRepository
from repositories.variant_option_repository import VariantOptionRepository
from repositories.payment_repository import PaymentRepository
from repositories.product_repository import ProductRepository
from repositories.refund_repository import RefundRepository
from repositories.sale_repository import SaleRepository

from models.category import Category
from models.product import Product
from models.variant_option_group import VariantOptionGroup
from models.variant_option import VariantOption
from models.sale import Sale
from models.sale_item import SaleItem
from models.payment import Payment
from models.refund import Refund


# ════════════════════════════════════════════════════════════════
# Branch isolation
# ════════════════════════════════════════════════════════════════

class TestBranchIsolation:
    """Branch belongs to Business which belongs to Tenant."""

    @pytest.mark.asyncio
    async def test_get_branch_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = BranchRepository(db)
        result = await repo.get_by_id(H["branch_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_branch_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = BranchRepository(db)
        result = await repo.get_by_id(H["branch_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["branch_a"].id

    @pytest.mark.asyncio
    async def test_list_branches_scoped_to_business(self, db: AsyncSession, H):
        repo = BranchRepository(db)
        branches_a = await repo.list(H["biz_a"].id, H["tenant_a"].id)
        branch_ids = [b.id for b in branches_a]
        assert H["branch_a"].id in branch_ids
        assert H["branch_b"].id not in branch_ids

    @pytest.mark.asyncio
    async def test_list_branches_cross_business_empty(self, db: AsyncSession, H):
        """Tenant A cannot list branches of Tenant B's business."""
        repo = BranchRepository(db)
        branches = await repo.list(H["biz_b"].id, H["tenant_a"].id)
        assert branches == []

    @pytest.mark.asyncio
    async def test_soft_delete_invisible_to_own_tenant(self, db: AsyncSession, H):
        repo = BranchRepository(db)
        deleted = await repo.soft_delete(H["branch_a"].id, H["tenant_a"].id)
        assert deleted is True
        result = await repo.get_by_id(H["branch_a"].id, H["tenant_a"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_soft_delete_wrong_tenant_fails(self, db: AsyncSession, H):
        repo = BranchRepository(db)
        deleted = await repo.soft_delete(H["branch_a"].id, H["tenant_b"].id)
        assert deleted is False


# ════════════════════════════════════════════════════════════════
# Device isolation
# ════════════════════════════════════════════════════════════════

class TestDeviceIsolation:
    """Device → Branch → Business → Tenant (3-level join)."""

    @pytest.mark.asyncio
    async def test_get_device_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = DeviceRepository(db)
        result = await repo.get_by_id(H["device_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_device_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = DeviceRepository(db)
        result = await repo.get_by_id(H["device_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["device_a"].id

    @pytest.mark.asyncio
    async def test_list_devices_scoped_to_branch(self, db: AsyncSession, H):
        repo = DeviceRepository(db)
        devices_a = await repo.list(H["branch_a"].id, H["tenant_a"].id)
        device_ids = [d.id for d in devices_a]
        assert H["device_a"].id in device_ids
        assert H["device_b"].id not in device_ids

    @pytest.mark.asyncio
    async def test_list_devices_cross_branch_empty(self, db: AsyncSession, H):
        repo = DeviceRepository(db)
        devices = await repo.list(H["branch_b"].id, H["tenant_a"].id)
        assert devices == []

    @pytest.mark.asyncio
    async def test_get_by_code_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = DeviceRepository(db)
        result = await repo.get_by_code(H["branch_a"].id, "DEV_A", H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = DeviceRepository(db)
        result = await repo.get_by_code(H["branch_a"].id, "DEV_A", H["tenant_a"].id)
        assert result is not None


# ════════════════════════════════════════════════════════════════
# Category isolation
# ════════════════════════════════════════════════════════════════

class TestCategoryIsolation:
    """Category → Business → Tenant (2-level join)."""

    @pytest.mark.asyncio
    async def test_get_category_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = CategoryRepository(db)
        result = await repo.get_by_id(H["cat_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_category_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = CategoryRepository(db)
        result = await repo.get_by_id(H["cat_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["cat_a"].id

    @pytest.mark.asyncio
    async def test_list_categories_scoped_to_business(self, db: AsyncSession, H):
        repo = CategoryRepository(db)
        cats_a = await repo.list(H["biz_a"].id, H["tenant_a"].id)
        cat_ids = [c.id for c in cats_a]
        assert H["cat_a"].id in cat_ids
        assert H["cat_b"].id not in cat_ids

    @pytest.mark.asyncio
    async def test_list_categories_cross_business_empty(self, db: AsyncSession, H):
        repo = CategoryRepository(db)
        cats = await repo.list(H["biz_b"].id, H["tenant_a"].id)
        assert cats == []

    @pytest.mark.asyncio
    async def test_same_category_name_allowed_in_different_tenants(
        self, db: AsyncSession, H
    ):
        """Two tenants can each have a category named "Burgers"."""
        repo = CategoryRepository(db)
        dup = Category(
            id=uuid4(),
            business_id=H["biz_b"].id,
            name="Burgers",
            display_order=1,
            is_active=True,
        )
        db.add(dup)
        await db.flush()

        result_a = await repo.get_by_id(H["cat_a"].id, H["tenant_a"].id)
        result_dup = await repo.get_by_id(dup.id, H["tenant_b"].id)
        assert result_a is not None
        assert result_dup is not None
        assert result_a.name == result_dup.name == "Burgers"

    @pytest.mark.asyncio
    async def test_soft_deleted_category_invisible(self, db: AsyncSession, H):
        repo = CategoryRepository(db)
        await repo.soft_delete(H["cat_a"].id, H["tenant_a"].id)
        result = await repo.get_by_id(H["cat_a"].id, H["tenant_a"].id)
        assert result is None


# ════════════════════════════════════════════════════════════════
# Product isolation
# ════════════════════════════════════════════════════════════════

class TestProductIsolation:
    """Product → Category → Business → Tenant (3-level join)."""

    @pytest.mark.asyncio
    async def test_get_product_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        result = await repo.get_by_id(H["prod_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_product_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        result = await repo.get_by_id(H["prod_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["prod_a"].id

    @pytest.mark.asyncio
    async def test_list_by_category_scoped_to_tenant(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        prods_a = await repo.list(H["cat_a"].id, H["tenant_a"].id)
        prod_ids = [p.id for p in prods_a]
        assert H["prod_a"].id in prod_ids
        assert H["prod_b"].id not in prod_ids

    @pytest.mark.asyncio
    async def test_list_by_category_cross_tenant_empty(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        prods = await repo.list(H["cat_b"].id, H["tenant_a"].id)
        assert prods == []

    @pytest.mark.asyncio
    async def test_list_by_business_scoped_to_tenant(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        prods_a = await repo.list_by_business(H["biz_a"].id, H["tenant_a"].id)
        prod_ids = [p.id for p in prods_a]
        assert H["prod_a"].id in prod_ids
        assert H["prod_b"].id not in prod_ids

    @pytest.mark.asyncio
    async def test_list_by_business_cross_tenant_empty(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        prods = await repo.list_by_business(H["biz_b"].id, H["tenant_a"].id)
        assert prods == []

    @pytest.mark.asyncio
    async def test_soft_deleted_product_invisible(self, db: AsyncSession, H):
        repo = ProductRepository(db)
        await repo.soft_delete(H["prod_a"].id, H["tenant_a"].id)
        result = await repo.get_by_id(H["prod_a"].id, H["tenant_a"].id)
        assert result is None


# ════════════════════════════════════════════════════════════════
# Variant option group isolation
# ════════════════════════════════════════════════════════════════

class TestOptionGroupIsolation:
    """VariantOptionGroup → Business → Tenant (2-level join, shared library — spec Part B)."""

    @pytest.mark.asyncio
    async def test_get_option_group_wrong_tenant_returns_none(
        self, db: AsyncSession, H
    ):
        repo = VariantOptionGroupRepository(db)
        result = await repo.get_by_id(H["og_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_option_group_correct_tenant_returns_record(
        self, db: AsyncSession, H
    ):
        repo = VariantOptionGroupRepository(db)
        result = await repo.get_by_id(H["og_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["og_a"].id

    @pytest.mark.asyncio
    async def test_list_option_groups_scoped_to_business(
        self, db: AsyncSession, H
    ):
        repo = VariantOptionGroupRepository(db)
        groups_a = await repo.list(H["biz_a"].id, H["tenant_a"].id)
        ids = [g.id for g in groups_a]
        assert H["og_a"].id in ids
        assert H["og_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_option_groups_cross_business_empty(
        self, db: AsyncSession, H
    ):
        repo = VariantOptionGroupRepository(db)
        groups = await repo.list(H["biz_b"].id, H["tenant_a"].id)
        assert groups == []


# ════════════════════════════════════════════════════════════════
# Variant option isolation
# ════════════════════════════════════════════════════════════════

class TestOptionIsolation:
    """VariantOption → VariantOptionGroup → Business → Tenant (3-level join)."""

    @pytest.mark.asyncio
    async def test_get_option_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = VariantOptionRepository(db)
        result = await repo.get_by_id(H["opt_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_option_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = VariantOptionRepository(db)
        result = await repo.get_by_id(H["opt_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["opt_a"].id

    @pytest.mark.asyncio
    async def test_list_options_scoped_to_option_group(self, db: AsyncSession, H):
        repo = VariantOptionRepository(db)
        opts_a = await repo.list(H["og_a"].id, H["tenant_a"].id)
        ids = [o.id for o in opts_a]
        assert H["opt_a"].id in ids
        assert H["opt_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_options_cross_option_group_empty(self, db: AsyncSession, H):
        repo = VariantOptionRepository(db)
        opts = await repo.list(H["og_b"].id, H["tenant_a"].id)
        assert opts == []


# ════════════════════════════════════════════════════════════════
# Sale isolation
# ════════════════════════════════════════════════════════════════

class TestSaleIsolation:
    """Sale → Branch → Business → Tenant (3-level join)."""

    @pytest.mark.asyncio
    async def test_get_sale_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = SaleRepository(db)
        result = await repo.get_by_id(H["sale_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_sale_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = SaleRepository(db)
        result = await repo.get_by_id(H["sale_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["sale_a"].id

    @pytest.mark.asyncio
    async def test_list_sales_scoped_to_branch(self, db: AsyncSession, H):
        repo = SaleRepository(db)
        sales_a = await repo.list(H["branch_a"].id, H["tenant_a"].id)
        ids = [s.id for s in sales_a]
        assert H["sale_a"].id in ids
        assert H["sale_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_sales_cross_branch_empty(self, db: AsyncSession, H):
        repo = SaleRepository(db)
        sales = await repo.list(H["branch_b"].id, H["tenant_a"].id)
        assert sales == []

    @pytest.mark.asyncio
    async def test_get_by_number_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = SaleRepository(db)
        result = await repo.get_by_number(H["branch_a"].id, "A-001", H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_number_correct_tenant_returns_record(
        self, db: AsyncSession, H
    ):
        repo = SaleRepository(db)
        result = await repo.get_by_number(H["branch_a"].id, "A-001", H["tenant_a"].id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_same_sale_number_allowed_across_branches(
        self, db: AsyncSession, H
    ):
        """Both tenants may independently use sale_number 'A-001'."""
        repo = SaleRepository(db)
        dup_sale = Sale(
            id=uuid4(),
            branch_id=H["branch_b"].id,
            device_id=H["device_b"].id,
            user_id=H["user_b"].id,
            sale_number="A-001",
            sold_at=datetime.now(timezone.utc),
            subtotal=Decimal("5.00"),
            discount=Decimal("0.00"),
            total=Decimal("5.00"),
            status="COMPLETED",
        )
        db.add(dup_sale)
        await db.flush()

        result_a = await repo.get_by_number(H["branch_a"].id, "A-001", H["tenant_a"].id)
        result_b = await repo.get_by_number(H["branch_b"].id, "A-001", H["tenant_b"].id)
        assert result_a is not None
        assert result_b is not None
        assert result_a.id != result_b.id


# ════════════════════════════════════════════════════════════════
# Payment isolation
# ════════════════════════════════════════════════════════════════

class TestPaymentIsolation:
    """Payment → Sale → Branch → Business → Tenant (4-level join)."""

    @pytest.mark.asyncio
    async def test_get_payment_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = PaymentRepository(db)
        result = await repo.get_by_id(H["pay_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_payment_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = PaymentRepository(db)
        result = await repo.get_by_id(H["pay_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["pay_a"].id

    @pytest.mark.asyncio
    async def test_get_by_sale_wrong_tenant_returns_empty(self, db: AsyncSession, H):
        repo = PaymentRepository(db)
        payments = await repo.get_by_sale(H["sale_a"].id, H["tenant_b"].id)
        assert payments == []

    @pytest.mark.asyncio
    async def test_get_by_sale_correct_tenant_returns_payments(
        self, db: AsyncSession, H
    ):
        repo = PaymentRepository(db)
        payments = await repo.get_by_sale(H["sale_a"].id, H["tenant_a"].id)
        assert len(payments) >= 1
        assert any(p.id == H["pay_a"].id for p in payments)

    @pytest.mark.asyncio
    async def test_get_by_sale_does_not_leak_other_tenant_payments(
        self, db: AsyncSession, H
    ):
        """Querying with tenant_a's sale_id but tenant_b's tenant_id returns []."""
        repo = PaymentRepository(db)
        payments = await repo.get_by_sale(H["sale_a"].id, H["tenant_b"].id)
        assert not any(p.id == H["pay_b"].id for p in payments)


# ════════════════════════════════════════════════════════════════
# Refund isolation
# ════════════════════════════════════════════════════════════════

class TestRefundIsolation:
    """Refund → Branch → Business → Tenant (3-level join)."""

    @pytest.mark.asyncio
    async def test_get_refund_wrong_tenant_returns_none(self, db: AsyncSession, H):
        repo = RefundRepository(db)
        result = await repo.get_by_id(H["refund_a"].id, H["tenant_b"].id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_refund_correct_tenant_returns_record(self, db: AsyncSession, H):
        repo = RefundRepository(db)
        result = await repo.get_by_id(H["refund_a"].id, H["tenant_a"].id)
        assert result is not None
        assert result.id == H["refund_a"].id

    @pytest.mark.asyncio
    async def test_list_refunds_scoped_to_branch(self, db: AsyncSession, H):
        repo = RefundRepository(db)
        refunds_a = await repo.list(H["branch_a"].id, H["tenant_a"].id)
        ids = [r.id for r in refunds_a]
        assert H["refund_a"].id in ids
        assert H["refund_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_refunds_cross_branch_empty(self, db: AsyncSession, H):
        repo = RefundRepository(db)
        refunds = await repo.list(H["branch_b"].id, H["tenant_a"].id)
        assert refunds == []

    @pytest.mark.asyncio
    async def test_get_by_sale_wrong_tenant_returns_empty(self, db: AsyncSession, H):
        repo = RefundRepository(db)
        refunds = await repo.get_by_sale(H["sale_a"].id, H["tenant_b"].id)
        assert refunds == []

    @pytest.mark.asyncio
    async def test_get_by_sale_correct_tenant_returns_refunds(
        self, db: AsyncSession, H
    ):
        repo = RefundRepository(db)
        refunds = await repo.get_by_sale(H["sale_a"].id, H["tenant_a"].id)
        assert any(r.id == H["refund_a"].id for r in refunds)


# ════════════════════════════════════════════════════════════════
# Full chain depth verification
# ════════════════════════════════════════════════════════════════

class TestFullChainIsolation:
    """
    Cross-entity leakage checks — verifies that knowing a foreign key
    from Tenant A gives zero access when authenticated as Tenant B.
    """

    @pytest.mark.asyncio
    async def test_option_deepest_join_no_cross_tenant_access(
        self, db: AsyncSession, H
    ):
        """3-level join: option_a's ID with tenant_b's credential → None."""
        repo = VariantOptionRepository(db)
        assert await repo.get_by_id(H["opt_a"].id, H["tenant_b"].id) is None
        assert await repo.get_by_id(H["opt_b"].id, H["tenant_a"].id) is None

    @pytest.mark.asyncio
    async def test_payment_four_level_join_no_cross_tenant_access(
        self, db: AsyncSession, H
    ):
        repo = PaymentRepository(db)
        assert await repo.get_by_id(H["pay_a"].id, H["tenant_b"].id) is None
        assert await repo.get_by_id(H["pay_b"].id, H["tenant_a"].id) is None

    @pytest.mark.asyncio
    async def test_product_using_wrong_tenant_category_id_returns_empty(
        self, db: AsyncSession, H
    ):
        """Tenant A's credentials + Tenant B's category_id → no products."""
        repo = ProductRepository(db)
        prods = await repo.list(H["cat_b"].id, H["tenant_a"].id)
        assert prods == []

    @pytest.mark.asyncio
    async def test_option_group_using_wrong_tenant_business_id_returns_empty(
        self, db: AsyncSession, H
    ):
        repo = VariantOptionGroupRepository(db)
        groups = await repo.list(H["biz_b"].id, H["tenant_a"].id)
        assert groups == []

    @pytest.mark.asyncio
    async def test_option_using_wrong_tenant_og_id_returns_empty(
        self, db: AsyncSession, H
    ):
        repo = VariantOptionRepository(db)
        opts = await repo.list(H["og_b"].id, H["tenant_a"].id)
        assert opts == []

    @pytest.mark.asyncio
    async def test_all_entities_bidirectional_isolation(self, db: AsyncSession, H):
        """
        Compact bidirectional check — every entity of tenant_a is invisible
        to tenant_b and vice versa.
        """
        branch_repo = BranchRepository(db)
        device_repo = DeviceRepository(db)
        cat_repo = CategoryRepository(db)
        prod_repo = ProductRepository(db)
        og_repo = VariantOptionGroupRepository(db)
        opt_repo = VariantOptionRepository(db)
        sale_repo = SaleRepository(db)
        pay_repo = PaymentRepository(db)
        refund_repo = RefundRepository(db)

        tid_a, tid_b = H["tenant_a"].id, H["tenant_b"].id

        checks = [
            # (repo.get_by_id(entity_id, wrong_tenant_id), expected None)
            await branch_repo.get_by_id(H["branch_a"].id, tid_b),
            await branch_repo.get_by_id(H["branch_b"].id, tid_a),
            await device_repo.get_by_id(H["device_a"].id, tid_b),
            await device_repo.get_by_id(H["device_b"].id, tid_a),
            await cat_repo.get_by_id(H["cat_a"].id, tid_b),
            await cat_repo.get_by_id(H["cat_b"].id, tid_a),
            await prod_repo.get_by_id(H["prod_a"].id, tid_b),
            await prod_repo.get_by_id(H["prod_b"].id, tid_a),
            await og_repo.get_by_id(H["og_a"].id, tid_b),
            await og_repo.get_by_id(H["og_b"].id, tid_a),
            await opt_repo.get_by_id(H["opt_a"].id, tid_b),
            await opt_repo.get_by_id(H["opt_b"].id, tid_a),
            await sale_repo.get_by_id(H["sale_a"].id, tid_b),
            await sale_repo.get_by_id(H["sale_b"].id, tid_a),
            await pay_repo.get_by_id(H["pay_a"].id, tid_b),
            await pay_repo.get_by_id(H["pay_b"].id, tid_a),
            await refund_repo.get_by_id(H["refund_a"].id, tid_b),
            await refund_repo.get_by_id(H["refund_b"].id, tid_a),
        ]

        for result in checks:
            assert result is None, f"Expected None but got {result}"
