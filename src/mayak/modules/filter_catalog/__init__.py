"""Filter Catalog module package."""

from mayak.platform.boundaries import FILTER_CATALOG_AND_BUILDER_MODULE_ID

from .contracts import *  # noqa: F401,F403
from .contracts import __all__ as _contracts_all
from .evidence_approval import *  # noqa: F401,F403
from .evidence_approval import __all__ as _evidence_approval_all

MODULE_ID = FILTER_CATALOG_AND_BUILDER_MODULE_ID

__all__ = ("MODULE_ID", *_contracts_all, *_evidence_approval_all)
