"""
DentalAI - Domain Errors
Business-rule failures raised by services and mapped to HTTP codes in main.py,
so routers stay thin and never need try/except for expected failures.
"""


class DomainError(Exception):
    """Base class for expected business-rule failures."""


class NotFoundError(DomainError):
    """A referenced record does not exist (HTTP 404)."""


class ConflictError(DomainError):
    """The request is valid but the record's current state forbids it (HTTP 409)."""


class RuleViolationError(DomainError):
    """The request breaks a clinical-safety rule, e.g. a missing override reason (HTTP 422)."""


class UpstreamError(DomainError):
    """A dependency (the ML service, storage) failed; the request may be retried (HTTP 502)."""
