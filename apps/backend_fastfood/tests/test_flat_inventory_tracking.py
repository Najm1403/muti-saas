import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.exceptions import ConflictError, ValidationError
from models.business import Business
from models.branch import Branch
from models.category import Category
from models.product import Product
from models.product_variant_option_group import ProductVariantOptionGroup
from models.variant import Variant
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from models.variant_branch_stock import VariantBranchStock
from models.stock_adjustment import StockAdjustment
from services.variant_service import VariantService, aggregate_demand
from tests.test_platform_departments import AsyncSessionAdapter


class FlatInventoryTests(unittest.IsolatedAsyncioTestCase):
    """
    Exercises VariantService's stock ledger+cache (spec D2) directly against
    an in-memory SQLite DB — a scratch hierarchy built by hand rather than the
    Postgres-only `H` fixture, so these tests stay fast and dependency-free.

    Stock now lives in VariantBranchStock (a per-branch cache) backed by the
    StockAdjustment ledger — there is no more Variant.stock_quantity column,
    so every stock read here goes through
    VariantService.get_branch_stock_row(variant_id, branch_id).

    Business-template policy enforcement (spec D6) reads Tenant/BusinessTemplate,
    both Postgres-only JSONB models that don't compile under SQLite — this
    scratch hierarchy has no Tenant row anyway, so the policy lookup is
    patched to its natural "no template configured" result (`{}`) rather
    than standing up tables this test has no use for.
    """

    def setUp(self):
        self._policy_patch = patch("services.business_policy.load_business_policy", new=AsyncMock(return_value={}))
        self._policy_patch.start()
        self.engine = create_engine("sqlite://")
        for model in [
            Business, Branch, Category, Product,
            ProductVariantOptionGroup, VariantOption, VariantOptionGroup,
            Variant, VariantBranchStock,
            StockAdjustment,
        ]:
            model.__table__.create(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.db = AsyncSessionAdapter(self.session)
        self.tenant_id = uuid4()
        business = Business(id=uuid4(), tenant_id=self.tenant_id, name="Shop")
        branch = Branch(id=uuid4(), business_id=business.id, branch_code="MAIN", name="Main")
        category = Category(id=uuid4(), business_id=business.id, name="Electronics")
        self.product = Product(id=uuid4(), category_id=category.id, name="Laptop", product_code="L1",
                               allow_inventory_tracking=True)
        self.session.add_all([business, branch, category, self.product])
        self.session.commit()
        self.branch = branch
        self.service = VariantService(self.db)

    def tearDown(self):
        self._policy_patch.stop()
        self.session.close()
        self.engine.dispose()

    def variant(self, tracked=True, stock=5):
        row = Variant(product_id=self.product.id, option_value_ids=[], combination_key=str(uuid4()),
                      tracks_inventory=tracked, sale_price=Decimal("10.00"))
        self.session.add(row)
        self.session.flush()
        if tracked:
            self.session.add(VariantBranchStock(variant_id=row.id, branch_id=self.branch.id, stock_quantity=stock))
            self.session.flush()
        return row

    async def branch_stock(self, variant_id):
        row = await self.service.get_branch_stock_row(variant_id, self.branch.id)
        return row.stock_quantity if row else None

    async def test_duplicate_cart_lines_are_aggregated(self):
        variant = self.variant(stock=5)
        with self.assertRaises(ValidationError):
            await self.service.validate_stock(self.tenant_id, [(variant.id, 3), (variant.id, 3)], branch_id=self.branch.id)

    async def test_untracked_or_product_disabled_skips_stock(self):
        variant = self.variant(tracked=False, stock=0)
        await self.service.validate_stock(self.tenant_id, [(variant.id, 999999)], branch_id=self.branch.id)
        self.product.allow_inventory_tracking = False
        self.session.flush()
        await self.service.validate_stock(self.tenant_id, [(variant.id, 999999)], branch_id=self.branch.id)

    async def test_product_switch_preserves_variant_state(self):
        variant = self.variant(stock=7)
        self.product.allow_inventory_tracking = False
        self.session.flush()
        await self.service.validate_stock(self.tenant_id, [(variant.id, 100)], branch_id=self.branch.id)
        self.product.allow_inventory_tracking = True
        self.session.flush()
        await self.service.validate_stock(self.tenant_id, [(variant.id, 7)], branch_id=self.branch.id)
        self.assertEqual(await self.branch_stock(variant.id), 7)

    async def test_opening_stock_is_write_once_and_audited(self):
        variant = self.variant(tracked=False, stock=0)
        await self.service.set_tracking(self.tenant_id, variant.id, True, {str(self.branch.id): 12})
        self.assertEqual(await self.branch_stock(variant.id), 12)
        rows = self.session.scalars(select(StockAdjustment)).all()
        self.assertEqual([(row.adjustment_type, row.resulting_quantity) for row in rows], [("opening", 12)])
        with self.assertRaises(ValidationError):
            await self.service.set_tracking(self.tenant_id, variant.id, True, {str(self.branch.id): 20})

    async def test_increase_creates_missing_row_instead_of_rejecting(self):
        # Reproduces the real-world case: a variant was created tracked, but
        # opening stock was never recorded for this branch (e.g. the Add
        # Product form's opening-stock field was left blank), so no
        # VariantBranchStock row exists yet even though the branch is
        # genuinely valid for this product. Increase must treat that as an
        # implied zero, not reject with "not stocked at the selected branch".
        variant = Variant(product_id=self.product.id, option_value_ids=[], combination_key=str(uuid4()),
                          tracks_inventory=True, sale_price=Decimal("10.00"))
        self.session.add(variant)
        self.session.flush()
        self.assertIsNone(await self.branch_stock(variant.id))
        await self.service.adjust_stock(self.tenant_id, variant.id, "increase", 4, "Restock", branch_id=self.branch.id)
        self.assertEqual(await self.branch_stock(variant.id), 4)

    async def test_decrease_on_missing_row_fails_negative_not_not_stocked(self):
        variant = Variant(product_id=self.product.id, option_value_ids=[], combination_key=str(uuid4()),
                          tracks_inventory=True, sale_price=Decimal("10.00"))
        self.session.add(variant)
        self.session.flush()
        with self.assertRaisesRegex(ValidationError, "Stock cannot become negative"):
            await self.service.adjust_stock(self.tenant_id, variant.id, "decrease", 1, "Damage", branch_id=self.branch.id)

    async def test_manual_adjustments_and_history(self):
        variant = self.variant(stock=5)
        await self.service.adjust_stock(self.tenant_id, variant.id, "increase", 3, "Restock", branch_id=self.branch.id)
        await self.service.adjust_stock(self.tenant_id, variant.id, "decrease", 2, "Damage", branch_id=self.branch.id)
        await self.service.set_stock(self.tenant_id, variant.id, 20, "Count", branch_id=self.branch.id)
        rows = await self.service.history(self.tenant_id, variant.id)
        self.assertEqual([row.adjustment_type for row in rows], ["manual_set", "manual_decrease", "manual_increase"])
        self.assertEqual([row.resulting_quantity for row in rows], [20, 6, 8])

    async def test_sale_only_deducts_selected_variant_and_audits(self):
        first = self.variant(stock=5)
        second = self.variant(stock=9)
        await self.service.deduct(self.tenant_id, [(first.id, 2)], uuid4(), branch_id=self.branch.id)
        self.assertEqual(await self.branch_stock(first.id), 3)
        self.assertEqual(await self.branch_stock(second.id), 9)
        self.assertEqual(self.session.scalar(select(StockAdjustment.adjustment_type)), "sale")

    async def test_refund_guard_does_not_restore_untracked_line(self):
        variant = self.variant(stock=5)
        await self.service.restore(self.tenant_id, variant.id, 2, uuid4(), tracked_at_sale=False, branch_id=self.branch.id)
        self.assertEqual(await self.branch_stock(variant.id), 5)
        self.assertEqual(self.session.scalars(select(StockAdjustment)).all(), [])

    async def test_refund_guard_checks_product_switch_too(self):
        variant = self.variant(stock=5)
        self.product.allow_inventory_tracking = False
        self.session.flush()
        await self.service.restore(self.tenant_id, variant.id, 2, uuid4(), tracked_at_sale=True, branch_id=self.branch.id)
        self.assertEqual(await self.branch_stock(variant.id), 5)
        self.assertEqual(self.session.scalars(select(StockAdjustment)).all(), [])

    def test_aggregate_demand(self):
        variant_id = uuid4()
        self.assertEqual(aggregate_demand([(variant_id, 2), (variant_id, 4)])[variant_id], 6)

    async def test_create_opening_and_actor(self):
        actor = uuid4()
        svc = VariantService(self.db, created_by=actor)
        variant = await svc.create(self.tenant_id, self.product.id, [], sale_price=Decimal("10.00"),
                                    tracks_inventory=True, opening_stock_by_branch={str(self.branch.id): 11})
        self.assertEqual(await self.branch_stock(variant.id), 11)
        opening = await svc.opening_stock_snapshot(variant)
        self.assertEqual(opening, {str(self.branch.id): 11})
        rows = await svc.history(self.tenant_id, variant.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].change_type, rows[0].quantity_delta, rows[0].created_by), ('opening', 11, actor))
        await svc.set_stock(self.tenant_id, variant.id, 20, 'Count', branch_id=self.branch.id)
        opening = await svc.opening_stock_snapshot(variant)
        self.assertEqual(opening, {str(self.branch.id): 11})
        self.assertIsNone((await svc.history(self.tenant_id, variant.id))[0].quantity_delta)

    async def test_variant_disabled_refund_and_tracked_refund(self):
        variant = self.variant(tracked=False)
        await self.service.restore(self.tenant_id, variant.id, 2, uuid4(), tracked_at_sale=True, branch_id=self.branch.id)
        self.assertIsNone(await self.branch_stock(variant.id))
        self.assertEqual(await self.service.history(self.tenant_id, variant.id), [])
        variant.tracks_inventory = True
        await self.db.flush()
        reference = uuid4()
        await self.service.restore(self.tenant_id, variant.id, 2, reference, tracked_at_sale=True, branch_id=self.branch.id)
        row = (await self.service.history(self.tenant_id, variant.id))[0]
        self.assertEqual((row.change_type, row.quantity_delta, row.resulting_quantity, row.reference_id), ('refund', 2, 2, str(reference)))

    async def test_inventory_visibility_and_catalog_sync(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, patch
        from api.v1.variants import list_variants
        from services.pos_sync_service import PosSyncService
        variant = self.variant(stock=7)
        untracked = self.variant(tracked=False)
        current = SimpleNamespace(tenant_id=self.tenant_id, user_id=uuid4())
        scope = patch('api.branch_access.visible_branches', AsyncMock(return_value=None))
        scope.start()
        self.addCleanup(scope.stop)
        rows = await list_variants(current=current, db=self.db)
        self.assertEqual({v.id for v in rows}, {variant.id, untracked.id})
        tracked_row = next(row for row in rows if row.id == variant.id)
        self.assertEqual(tracked_row.product_name, self.product.name)
        self.assertEqual(tracked_row.variant_name, "Default variant")
        self.product.allow_inventory_tracking = False
        await self.db.flush()
        self.assertEqual({v.id for v in await list_variants(current=current, db=self.db)}, {variant.id, untracked.id})
        self.assertEqual(await list_variants(tracked_only=True, current=current, db=self.db), [])
        synced = await PosSyncService(self.db)._variants(self.tenant_id, [self.product], self.branch.id)
        self.assertTrue(all(v.sellable for v in synced))
        self.assertTrue(all(not v.allow_inventory_tracking for v in synced))
        self.assertTrue(variant.tracks_inventory)
        self.product.allow_inventory_tracking = True
        await self.db.flush()
        refreshed = await list_variants(tracked_only=True, current=current, db=self.db)
        self.assertEqual(next(v for v in refreshed if v.id == variant.id).stock_by_branch[str(self.branch.id)], 7)

    async def test_disabled_product_edit_preserves_stock_and_checkbox(self):
        variant = self.variant(stock=7)
        self.product.allow_inventory_tracking = False
        await self.db.flush()
        with self.assertRaises(ValidationError):
            await self.service.set_tracking(self.tenant_id, variant.id, True, {str(self.branch.id): 100})
        self.assertTrue(variant.tracks_inventory)
        self.assertEqual(await self.branch_stock(variant.id), 7)

    async def test_untracked_creation_ignores_stock(self):
        variant = await self.service.create(self.tenant_id, self.product.id, [], sale_price=Decimal("10.00"),
                                             tracks_inventory=False, opening_stock_by_branch={str(self.branch.id): 15})
        self.assertIsNone(await self.branch_stock(variant.id))
        self.assertEqual(await self.service.history(self.tenant_id, variant.id), [])

    async def test_duplicate_variant_create_is_conflict(self):
        await self.service.create(self.tenant_id, self.product.id, [], sale_price=Decimal("10.00"), tracks_inventory=False)
        with self.assertRaises(ConflictError):
            await self.service.create(self.tenant_id, self.product.id, [], sale_price=Decimal("10.00"),
                                       tracks_inventory=True, opening_stock_by_branch={str(self.branch.id): 4})

    def test_edit_cannot_bypass_stock_actions(self):
        from schemas.variant import VariantUpdate
        from pydantic import ValidationError as SchemaError
        with self.assertRaises(SchemaError):
            VariantUpdate(tracks_inventory=True, stock_quantity=100)

    async def test_menu_and_inventory_have_separate_access(self):
        from unittest.mock import AsyncMock, patch
        from httpx import ASGITransport, AsyncClient
        from api.dependencies import CurrentUser, get_current_user
        from app.main import app
        from db.session import get_db
        current = CurrentUser(uuid4(), self.tenant_id)
        variant = self.variant()
        untracked = self.variant(tracked=False)
        async def database():
            yield self.db
        app.dependency_overrides[get_db] = database
        app.dependency_overrides[get_current_user] = lambda: current
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                with patch('api.dependencies.tenant_enabled_modules', AsyncMock(return_value={'menu'})), patch('api.dependencies.get_user_permissions', AsyncMock(return_value={'products.view'})), patch('api.branch_access.visible_branches', AsyncMock(return_value=None)):
                    response = await client.get('/api/v1/variants', params={'product_id': str(self.product.id)})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual((await client.get('/api/v1/inventory/variants')).status_code, 404)
                with patch('api.dependencies.tenant_enabled_modules', AsyncMock(return_value={'inventory'})), patch('api.dependencies.get_user_permissions', AsyncMock(return_value={'inventory.view', 'inventory.manage'})), patch('api.branch_access.visible_branches', AsyncMock(return_value=None)):
                    response = await client.get('/api/v1/branches/')
                    self.assertEqual(response.status_code, 200, response.text)
                    response = await client.get('/api/v1/variants')
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual({row['id'] for row in response.json()}, {str(variant.id), str(untracked.id)})
                    response = await client.post(f'/api/v1/variants/{variant.id}/stock/increase',
                        params={'branch_id': str(self.branch.id)}, json={'quantity': 2})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()['stock_by_branch'][str(self.branch.id)], 7)
                    row = (await self.service.history(self.tenant_id, variant.id))[0]
                    self.assertEqual(row.created_by, current.user_id)
        finally:
            app.dependency_overrides.clear()

    async def test_frontend_inventory_assets_are_not_cached(self):
        from httpx import ASGITransport, AsyncClient
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            html = await client.get('/tenant/inventory.html')
            script = await client.get('/tenant/variant-inventory.js?v=18')
        self.assertEqual(html.status_code, 200)
        self.assertEqual(script.status_code, 200)
        self.assertEqual(html.headers.get('cache-control'), 'no-store')
        self.assertEqual(script.headers.get('cache-control'), 'no-store')
        self.assertIn('/tenant/variant-inventory.js?v=18', html.text)
        self.assertIn('value="low_stock"', html.text)
        self.assertIn("quantity > lowStockThreshold", script.text)
        self.assertNotIn('/variant-products', script.text)
        self.assertNotIn('/inventory/variants', script.text)
        self.assertNotIn('/serials', script.text)
