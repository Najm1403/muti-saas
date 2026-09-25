# api/v1/pos/router.py
#
# Aggregates all POS sub-routers under /api/v1/pos.

from fastapi import APIRouter

from api.v1.pos import attendance, auth, sync, sales, session, device

router = APIRouter(prefix="/pos")

router.include_router(auth.router)
router.include_router(sync.router)
router.include_router(sales.router)
router.include_router(session.router)
router.include_router(device.router)
router.include_router(attendance.router)
