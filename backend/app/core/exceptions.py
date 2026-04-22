class AppError(Exception):
    """Base error for the application."""

    message: str = "An unexpected error occurred"
    status_code: int = 500

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    message = "Resource not found"
    status_code = 404


class PermissionError(AppError):
    message = "Insufficient permissions"
    status_code = 403


class ConflictError(AppError):
    message = "Resource already exists"
    status_code = 409


class ValidationError(AppError):
    message = "Validation failed"
    status_code = 422


# --- Domain Specific Exceptions ---


class UserAlreadyExistsError(ConflictError):
    message = "A user with this email already exists"


class OrgAlreadyExistsError(ConflictError):
    message = "An organization with this slug already exists"


class MemberAlreadyExistsError(ConflictError):
    message = "User is already a member of this organization"


class InvitationAlreadyExistsError(ConflictError):
    message = "A pending invitation already exists for this email"


class InvitationInvalidError(PermissionError):
    message = "This invitation is not for you or is no longer valid"
