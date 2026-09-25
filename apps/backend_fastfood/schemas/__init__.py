# schemas/__init__.py

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SoftDeleteResponseSchema,
    SyncResponseSchema,
    PaginatedResponse,
    MessageResponse,
)

from schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
)

from schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
)

from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRoleAssign,
    UserRoleRemove,
)

from schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RolePermissionAssign,
    RolePermissionRemove,
)

from schemas.permission import PermissionResponse

from schemas.business import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
)

from schemas.business_template import (
    BusinessTemplateCreate,
    BusinessTemplateUpdate,
    BusinessTemplateResponse,
)

from schemas.branch import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
)

from schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
)

from schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)

from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)

from schemas.variant_option_group import (
    VariantOptionGroupCreate,
    VariantOptionGroupUpdate,
    VariantOptionGroupResponse,
    ProductVariantOptionGroupAttach,
    ProductVariantOptionGroupResponse,
)

from schemas.variant_option import (
    VariantOptionCreate,
    VariantOptionUpdate,
    VariantOptionResponse,
)

from schemas.addon_group import (
    AddonGroupCreate,
    AddonGroupUpdate,
    AddonGroupResponse,
    ProductAddonGroupAttach,
    ProductAddonGroupResponse,
)

from schemas.addon_item import (
    AddonItemCreate,
    AddonItemUpdate,
    AddonItemResponse,
)

from schemas.sale import (
    SaleItemOptionCreate,
    SaleItemOptionResponse,
    SaleItemCreate,
    SaleItemResponse,
    SaleCreate,
    SaleStatusUpdate,
    SaleResponse,
    SaleListResponse,
)

from schemas.payment import (
    PaymentCreate,
    PaymentResponse,
)

from schemas.refund import (
    RefundItemCreate,
    RefundItemResponse,
    RefundCreate,
    RefundResponse,
)

from schemas.report import (
    ReportRequest,
    SalesSummaryReport,
    DailySalesRow,
    DailySalesReport,
    TopProductRow,
    TopProductsReport,
    CashierSalesRow,
    CashierSalesReport,
    PaymentMethodRow,
    PaymentMethodReport,
)

from schemas.audit_log import (
    AuditLogResponse,
    AuditLogFilter,
)

__all__ = [
    # common
    "APIBaseSchema",
    "UUIDResponseSchema",
    "TimestampResponseSchema",
    "SoftDeleteResponseSchema",
    "SyncResponseSchema",
    "PaginatedResponse",
    "MessageResponse",
    # auth
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "ChangePasswordRequest",
    # tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    # user
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserRoleAssign",
    "UserRoleRemove",
    # role
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RolePermissionAssign",
    "RolePermissionRemove",
    # permission
    "PermissionResponse",
    # business
    "BusinessCreate",
    "BusinessUpdate",
    "BusinessResponse",
    # business template
    "BusinessTemplateCreate",
    "BusinessTemplateUpdate",
    "BusinessTemplateResponse",
    # branch
    "BranchCreate",
    "BranchUpdate",
    "BranchResponse",
    # device
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    # category
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    # product
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    # variant option group
    "VariantOptionGroupCreate",
    "VariantOptionGroupUpdate",
    "VariantOptionGroupResponse",
    "ProductVariantOptionGroupAttach",
    "ProductVariantOptionGroupResponse",
    # variant option
    "VariantOptionCreate",
    "VariantOptionUpdate",
    "VariantOptionResponse",
    # addon group
    "AddonGroupCreate",
    "AddonGroupUpdate",
    "AddonGroupResponse",
    "ProductAddonGroupAttach",
    "ProductAddonGroupResponse",
    # addon item
    "AddonItemCreate",
    "AddonItemUpdate",
    "AddonItemResponse",
    # sale
    "SaleItemOptionCreate",
    "SaleItemOptionResponse",
    "SaleItemCreate",
    "SaleItemResponse",
    "SaleCreate",
    "SaleStatusUpdate",
    "SaleResponse",
    "SaleListResponse",
    # payment
    "PaymentCreate",
    "PaymentResponse",
    # refund
    "RefundItemCreate",
    "RefundItemResponse",
    "RefundCreate",
    "RefundResponse",
    # report
    "ReportRequest",
    "SalesSummaryReport",
    "DailySalesRow",
    "DailySalesReport",
    "TopProductRow",
    "TopProductsReport",
    "CashierSalesRow",
    "CashierSalesReport",
    "PaymentMethodRow",
    "PaymentMethodReport",
    # audit log
    "AuditLogResponse",
    "AuditLogFilter",
]
