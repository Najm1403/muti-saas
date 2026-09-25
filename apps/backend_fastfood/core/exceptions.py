# core/exceptions.py
#
# Domain exceptions used across the service layer.
# These are HTTP-free; app/main.py maps them to status codes once.


class NotFoundError(Exception):
    """Raised when a requested resource does not exist (HTTP 404)."""


class ConflictError(Exception):
    """Raised when a unique constraint is violated (HTTP 409)."""


class ValidationError(Exception):
    """Raised when business-level validation fails (HTTP 422)."""


class AuthenticationError(Exception):
    """Raised when credentials are missing, invalid, or expired (HTTP 401)."""

    def __init__(self, message: str = "", *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class ForbiddenError(Exception):
    """Raised when an authenticated caller is not allowed (HTTP 403).

    An optional machine-readable ``code`` is surfaced in the response so
    clients can branch on device lifecycle and other authorization failures.
    """

    def __init__(self, message: str = "", *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code
