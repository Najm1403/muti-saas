"""Request-level branch boundaries, independent of role permissions."""
from uuid import UUID
from sqlalchemy import select
from models.user import User
from models.user_branch import UserBranch
from models.branch import Branch
from models.business import Business
from core.exceptions import ForbiddenError, NotFoundError

# Modules whose id-path-param resource carries a plain branch_id column
# directly — resolving "this one" is a single one-row lookup with no need
# for path-based sub-dispatch or a join. Add the next such module here.
# ("devices" and "sales" are NOT here — see _resolve_resource_branch's
# bespoke handling below, since "sales" resolves to one of three different
# models depending on the URL and "employees"/"expenses" below cover the
# direct case; keeping the declarative table small and exhaustive is more
# valuable than forcing every module through one shape.)
async def _direct_branch_models():
    from models.device import Device
    from models.employee import Employee
    from models.expense import Expense
    return {"devices": Device, "employees": Employee, "expenses": Expense}


async def _resolve_resource_branch(db, module: str, path: str, resource):
    """Best-effort: the branch_id of the single resource this request acts
    on (its "{id}" path param), or None if this module isn't one we know
    how to resolve that way — the caller then falls back to any explicit
    branch_id in the query string or JSON body, exactly as before this
    function existed, so an unhandled module's behavior is unchanged.

    This exists specifically so the next branch-scoped resource type is one
    new entry/branch here, not a forgotten case that silently reproduces
    the bug already fixed once for /refunds/sale/{sale_id} (see
    enforce_branch_request's sale_resource handling): a differently-named
    or differently-shaped id path param resolving to nothing, and every
    branch-scoped user then hitting the unconditional "no branch" 403 below
    for an endpoint they actually have access to.
    """
    direct = await _direct_branch_models()
    if module in direct:
        model = direct[module]
        return await db.scalar(select(model.branch_id).where(model.id == resource))
    if module == "sales":
        from models.sale import Sale
        from models.refund import Refund
        from models.payment import Payment
        if "/payments/" in path:
            return await db.scalar(
                select(Sale.branch_id).join(Payment, Payment.sale_id == Sale.id)
                .where(Payment.id == resource)
            )
        model = Refund if "/refunds/" in path else Sale
        return await db.scalar(select(model.branch_id).where(model.id == resource))
    if module == "salaries":
        # SalaryPayment has no branch_id of its own — it belongs to an
        # Employee, whose branch is the one that matters here.
        from models.employee import Employee
        from models.salary_payment import SalaryPayment
        return await db.scalar(
            select(Employee.branch_id).join(SalaryPayment, SalaryPayment.employee_id == Employee.id)
            .where(SalaryPayment.id == resource)
        )
    return None


async def visible_branches(db, current):
    user=await db.scalar(select(User).where(User.id==current.user_id,User.tenant_id==current.tenant_id,User.deleted_at.is_(None)))
    if user and user.all_branches: return None
    return set((await db.scalars(select(UserBranch.branch_id).join(Branch,UserBranch.branch_id==Branch.id)
        .join(Business,Branch.business_id==Business.id).where(UserBranch.user_id==current.user_id,
            Business.tenant_id==current.tenant_id,Branch.deleted_at.is_(None)))).all())

async def enforce_branch_request(request, db, current, module):
    if module not in {"branches","devices","sales","reports","inventory","kitchen","expenses","employees","salaries"}: return
    allowed=await visible_branches(db,current)
    if allowed is None: return
    path=request.url.path.rstrip("/")
    # Report routes apply the complete assigned-branch set in their queries so
    # "All Branches" means every branch this user is assigned to. Variant list
    # responses likewise filter each stock_by_branch snapshot in the router.
    if module=="reports": return
    if module=="inventory" and request.method=="GET" and path=="/api/v1/variants": return
    if request.method=="GET" and path in {"/api/v1/branches","/api/v1/branches/stats","/api/v1/devices","/api/v1/devices/sync-health"}: return
    branch=request.path_params.get("branch_id") or request.query_params.get("branch_id")
    data={}
    if request.method in {"POST","PUT","PATCH"} and "application/json" in request.headers.get("content-type",""):
        try: data=await request.json()
        except Exception: pass
    if not isinstance(data,dict): data={}
    if module=="inventory" and path.endswith("/transfer"):
        try:
            transfer_branches={UUID(str(data.get("from_branch_id"))),UUID(str(data.get("to_branch_id")))}
        except (ValueError,TypeError):
            raise NotFoundError("Branch not found.")
        if not transfer_branches.issubset(allowed):
            raise ForbiddenError("No access to one or more transfer branches.")
        return
    branch=branch or data.get("branch_id")
    resource=request.path_params.get("id")
    # GET /refunds/sale/{sale_id} carries the Sale's id under "sale_id", not
    # "id" — it is not a Refund's own id, so it must resolve through Sale,
    # never through the Refund branch below (that would look up a Refund row
    # by a Sale id and always find nothing, which used to fall through to the
    # unconditional "no branch" 403 for every branch-scoped user).
    sale_resource=request.path_params.get("sale_id")
    if module=="branches" and resource: branch=resource
    elif resource:
        # Only overwrite an explicit branch_id already found (query/body)
        # when resolution actually finds one — an unhandled module or an
        # unresolved resource must fall back to that value, not silently
        # discard it and force the "no branch" 403 below.
        resolved = await _resolve_resource_branch(db, module, path, resource)
        branch = resolved or branch
    elif sale_resource and module=="sales":
        from models.sale import Sale
        branch=await db.scalar(select(Sale.branch_id).where(Sale.id==sale_resource))
    if not branch:
        raise ForbiddenError("Choose an assigned branch; tenant-wide access is not granted.")
    try: branch=UUID(str(branch))
    except ValueError: raise NotFoundError("Branch not found.")
    if branch not in allowed: raise ForbiddenError("No access to this branch.")
