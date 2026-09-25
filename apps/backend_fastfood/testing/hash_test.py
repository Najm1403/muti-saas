import sys
sys.path.insert(0, "E:/multi-saas/backend_fastfood")
###################################################

from core.security import (
    hash_password,
    verify_password,
)

password = "MyPassword123"

hashed = hash_password(password)

print(hashed)

print(
    verify_password(
        password,
        hashed,
    )
)

print(
    verify_password(
        "WrongPassword",
        hashed,
    )
)