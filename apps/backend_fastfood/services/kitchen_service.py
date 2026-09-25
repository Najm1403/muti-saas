"""Branch-isolated operational preparation queue."""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.sale import Sale
from models.sale_item import SaleItem
from models.branch import Branch
from models.business import Business
from models.user import User
from models.user_branch import UserBranch
from core.exceptions import ForbiddenError, NotFoundError, ValidationError

class KitchenService:
    def __init__(self, db): self.db = db

    async def _access(self, branch_id, current):
        from services.ownership import tenant_branches
        await tenant_branches(self.db, current.tenant_id, [branch_id])
        user = await self.db.get(User, current.user_id)
        if user is None or user.tenant_id != current.tenant_id:
            raise ForbiddenError("User is unavailable.")
        if not user.all_branches and await self.db.scalar(select(UserBranch.user_id).where(
            UserBranch.user_id == user.id, UserBranch.branch_id == branch_id)) is None:
            raise ForbiddenError("No access to this branch.")

    def _query(self, branch_id, tenant_id):
        return select(SaleItem, Sale.sale_number, Sale.sold_at).join(Sale, SaleItem.sale_id == Sale.id)            .join(Branch, Sale.branch_id == Branch.id).join(Business, Branch.business_id == Business.id)            .where(Sale.branch_id == branch_id, Business.tenant_id == tenant_id,
                Sale.deleted_at.is_(None), SaleItem.deleted_at.is_(None), Sale.status == "COMPLETED")

    async def queue(self, branch_id, current):
        await self._access(branch_id, current)
        rows = (await self.db.execute(self._query(branch_id, current.tenant_id)
            .where(SaleItem.preparation_status.in_(["PENDING", "PREPARING", "READY"]))
            .options(selectinload(SaleItem.options)).order_by(Sale.sold_at))).all()
        return [{"id": i.id, "sale_number": number, "sold_at": at, "product_name": i.product_name,
            "quantity": i.quantity, "station_id": i.kitchen_station_id, "status": i.preparation_status,
            "options": [o.option_name for o in i.options]} for i, number, at in rows]

    async def advance(self, branch_id, item_id, status, current):
        await self._access(branch_id, current)
        row = (await self.db.execute(self._query(branch_id, current.tenant_id)
            .where(SaleItem.id == item_id).with_for_update(of=SaleItem))).first()
        if row is None: raise NotFoundError("Kitchen item not found.")
        item = row[0]
        transitions = {"PENDING": "PREPARING", "PREPARING": "READY", "READY": "SERVED"}
        if transitions.get(item.preparation_status) != status:
            raise ValidationError("Invalid kitchen status transition.")
        item.preparation_status = status
        await self.db.commit()
        return {"id": item.id, "status": item.preparation_status}
