"""Compatibility Engine Feature Module (Module 14)"""

from app.modules.compatibility.routes import router as compatibility_router
from app.modules.compatibility.schemas import (
    CompatibilityCheckRequest,
    CompatibilityResponse,
    RuleCheckResult,
    RuleIdentifier,
    RuleStatus,
)
from app.modules.compatibility.service import CompatibilityService

__all__ = [
    "compatibility_router",
    "CompatibilityService",
    "CompatibilityCheckRequest",
    "CompatibilityResponse",
    "RuleCheckResult",
    "RuleIdentifier",
    "RuleStatus",
]
