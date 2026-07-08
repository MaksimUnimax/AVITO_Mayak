"""Platform-level error primitives."""


class MayakError(Exception):
    """Base error for the Mayak bootstrap."""


class BoundaryViolationError(MayakError):
    """Raised when an architectural boundary is broken."""


class UnsupportedDependencyError(MayakError):
    """Raised when a forbidden dependency is encountered."""
