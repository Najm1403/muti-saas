# api/v1/products.py
#
# Product management routes — tenant scoped.
#
# Position in hierarchy:
#   Tenant → Business → Category → Product
#
# category_id is required as a query param for list and create so the caller
# always provides the full hierarchy context.  GET/PATCH/DELETE/{id} need only
# the product UUID because the service scopes by tenant_id from the JWT.
#
# Connected services / dependencies:
#   - services/product_service.py  — ProductService (create, get, list, update, delete)
#   - api/dependencies.py          — get_current_user (extracts tenant_id from JWT)
#   - db/session.py                — get_db (provides AsyncSession per request)
#   - schemas/product.py           — ProductCreate, ProductUpdate, ProductResponse
#   - schemas/common.py            — MessageResponse
#
# Prefix: /api/v1/products

from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from core.exceptions import ValidationError
from db.session import get_db
from schemas.branch_assignment import BranchAssignmentResponse, BranchAssignmentUpdate
from schemas.common import MessageResponse
from schemas.product import ProductCreate, ProductResponse, ProductSkuSuggestion, ProductUpdate
from schemas.product_spec import ProductSpecCreate, ProductSpecResponse, ProductSpecUpdate
from services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

# Where uploaded product images land — served read-only at /media/products/<file>.
_MEDIA_DIR = Path(__file__).resolve().parents[2] / "media" / "products"
_ACCEPTED_UPLOAD_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024   # reject the raw upload above this
_IMAGE_MAX_EDGE = 900                # longest side after resize (px)
_JPEG_QUALITY = 82


def _process_image(raw: bytes) -> tuple[bytes, str]:
    """Normalise an uploaded image: fix orientation, downscale to <=900px on the
    long edge (never upscale), and re-encode. Photos become optimised JPEG;
    images with transparency stay PNG. Returns (bytes, extension)."""
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise ValidationError("That file is not a readable image.")

    img = ImageOps.exif_transpose(img)  # honour phone rotation

    has_alpha = img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    )
    img.thumbnail((_IMAGE_MAX_EDGE, _IMAGE_MAX_EDGE), Image.LANCZOS)

    buf = io.BytesIO()
    if has_alpha:
        img.convert("RGBA").save(buf, format="PNG", optimize=True)
        return buf.getvalue(), ".png"
    img.convert("RGB").save(
        buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True, progressive=True
    )
    return buf.getvalue(), ".jpg"


def _svc(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Dependency that instantiates ProductService with the request's DB session."""
    return ProductService(db)


@router.get(
    "/",
    response_model=list[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List products",
    description=(
        "Returns all active products under the given category. "
        "Pass include_inactive=true to include deactivated products. "
        "category_id must belong to the current tenant's business."
    ),
)
async def list_products(
    category_id: UUID,
    include_inactive: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> list[ProductResponse]:
    return await svc.list(
        category_id=category_id,
        tenant_id=current_user.tenant_id,
        include_inactive=include_inactive,
    )


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description=(
        "Creates a product under the specified category. "
        "product_code must be unique within the category. "
        "The category must belong to the current tenant. "
        "price seeds the auto-created default Variant's sale_price."
    ),
)
async def create_product(
    category_id: UUID,
    data: ProductCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    return await svc.create(
        category_id=category_id,
        tenant_id=current_user.tenant_id,
        data=data,
    )


@router.get(
    "/generate-sku",
    response_model=ProductSkuSuggestion,
    status_code=status.HTTP_200_OK,
    summary="Suggest a SKU for a new product",
    description=(
        "Returns a suggested, currently-unused SKU (<CATEGORY-PREFIX>-<seq>) for a "
        "product about to be created in the given category. Convenience only — the "
        "tenant may edit or replace it before saving; sku has no DB-level uniqueness "
        "constraint. Registered before /{id} so 'generate-sku' is never parsed as a "
        "product UUID."
    ),
)
async def generate_product_sku(
    category_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductSkuSuggestion:
    sku = await svc.generate_sku(category_id=category_id, tenant_id=current_user.tenant_id)
    return ProductSkuSuggestion(sku=sku)


@router.get(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product branch assignment",
)
async def get_product_branches(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.get_branch_assignment(product_id=id, tenant_id=current_user.tenant_id)


@router.put(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Set product branch assignment",
)
async def set_product_branches(
    id: UUID,
    data: BranchAssignmentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.set_branch_assignment(
        product_id=id,
        tenant_id=current_user.tenant_id,
        all_branches=data.all_branches,
        branch_ids=data.branch_ids,
    )


@router.get(
    "/{id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product",
    description="Returns a single product. Returns 404 if it belongs to a different tenant.",
)
async def get_product(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product",
    description="Partially update a product. Only provided fields are changed.",
)
async def update_product(
    id: UUID,
    data: ProductUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post(
    "/{id}/activate",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate product",
    description="Set is_active=true. The product will appear in menu listings.",
)
async def activate_product(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/deactivate",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate product",
    description="Set is_active=false. The product is hidden from menu listings but not deleted.",
)
async def deactivate_product(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete product",
    description=(
        "Soft-deletes the product. Variant Option Groups and Add-on Groups are "
        "shared at the business level and are NOT deleted, only their attachment "
        "to this product. Historical sale items referencing this product are preserved."
    ),
)
async def delete_product(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Product deleted.")


@router.post(
    "/{id}/image",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload product image",
    description=(
        "Upload a JPG/PNG/WebP/GIF (max 5 MB). The image is auto-oriented, "
        "downscaled to at most 900 px on the long edge, and re-encoded (optimised "
        "JPEG, or PNG when it has transparency), then stored under /media/products/. "
        "The product's image_path is set to the served URL and synced to POS devices."
    ),
)
async def upload_product_image(
    id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    if (file.content_type or "").lower() not in _ACCEPTED_UPLOAD_TYPES:
        raise ValidationError("Image must be JPG, PNG, WebP or GIF.")

    data = await file.read()
    if len(data) > _MAX_IMAGE_BYTES:
        raise ValidationError("Image is larger than 5 MB.")

    # Ensure the product exists / belongs to this tenant before writing anything.
    await svc.get(id=id, tenant_id=current_user.tenant_id)

    processed, ext = _process_image(data)   # auto-resize + re-encode

    _MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    # New random suffix on every upload so the served URL is always fresh — this
    # defeats browser / Flutter image caching that would otherwise keep showing
    # the previous photo. Drop every earlier file for this product first.
    for old in list(_MEDIA_DIR.glob(f"{id}.*")) + list(_MEDIA_DIR.glob(f"{id}-*")):
        old.unlink(missing_ok=True)
    filename = f"{id}-{uuid4().hex[:8]}{ext}"
    (_MEDIA_DIR / filename).write_bytes(processed)

    image_path = f"/media/products/{filename}"
    return await svc.update(
        id=id,
        tenant_id=current_user.tenant_id,
        data=ProductUpdate(image_path=image_path),
    )


@router.get(
    "/{id}/specs",
    response_model=list[ProductSpecResponse],
    status_code=status.HTTP_200_OK,
    summary="List product specs",
    description="Repeatable key/value rows (spec Part B / G2) — gated by "
                "template.config.product_fields.specs on the frontend, never required.",
)
async def list_product_specs(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> list[ProductSpecResponse]:
    return await svc.list_specs(product_id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/specs",
    response_model=ProductSpecResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product spec row",
)
async def add_product_spec(
    id: UUID,
    data: ProductSpecCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductSpecResponse:
    return await svc.add_spec(product_id=id, tenant_id=current_user.tenant_id, data=data)


@router.patch(
    "/{id}/specs/{spec_id}",
    response_model=ProductSpecResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a product spec row",
)
async def update_product_spec(
    id: UUID,
    spec_id: UUID,
    data: ProductSpecUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductSpecResponse:
    return await svc.update_spec(product_id=id, spec_id=spec_id, tenant_id=current_user.tenant_id, data=data)


@router.delete(
    "/{id}/specs/{spec_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a product spec row",
)
async def delete_product_spec(
    id: UUID,
    spec_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> MessageResponse:
    await svc.delete_spec(product_id=id, spec_id=spec_id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Spec deleted.")


@router.delete(
    "/{id}/image",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove product image",
)
async def delete_product_image(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: ProductService = Depends(_svc),
) -> ProductResponse:
    await svc.get(id=id, tenant_id=current_user.tenant_id)
    for old in list(_MEDIA_DIR.glob(f"{id}.*")) + list(_MEDIA_DIR.glob(f"{id}-*")):
        old.unlink(missing_ok=True)
    return await svc.update(
        id=id,
        tenant_id=current_user.tenant_id,
        data=ProductUpdate(image_path=None),
    )
