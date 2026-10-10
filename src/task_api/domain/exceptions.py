"""Expected failures raised by domain rules and application services."""


class DomainError(Exception):
    """Base class for failures callers can handle without a stack trace."""

    error_code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidTaskError(DomainError):
    """A task field violates an invariant."""

    error_code = "invalid_task"


class TaskNotFoundError(DomainError):
    """The requested task does not exist."""

    error_code = "not_found"


class ConflictError(DomainError):
    """The operation collides with existing state."""

    error_code = "conflict"
