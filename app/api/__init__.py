# app/api/__init__.py
from .flags import router as flags_router
router = flags_router
__all__ = ["flags_router", "router"]