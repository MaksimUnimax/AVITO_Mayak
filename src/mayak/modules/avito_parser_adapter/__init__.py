"""Avito Parser Adapter module package."""

from mayak.platform.boundaries import AVITO_PARSER_ADAPTER_MODULE_ID

from .contracts import *  # noqa: F401,F403
from .contracts import __all__ as _contracts_all
from .fixtures import *  # noqa: F401,F403
from .fixtures import __all__ as _fixtures_all

MODULE_ID = AVITO_PARSER_ADAPTER_MODULE_ID

__all__ = ("MODULE_ID", *_contracts_all, *_fixtures_all)
