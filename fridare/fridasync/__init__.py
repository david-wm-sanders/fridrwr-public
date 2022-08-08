"""Initialise fridasync package."""
from .logging import FRIDAJS_DEBUG_LVL, FRIDAJS_INFO_LVL, FRIDAJS_WARN_LVL, FRIDAJS_PROCEXC_LVL, FRIDAJS_ERROR_LVL

import aiopath  # noqa
PKG_DIR = aiopath.AsyncPath(__file__).parent

import jinja2  # noqa
_FRIDAJS_TEMPLATES_DIR = PKG_DIR / "fridajs_templates"
jinja_fridajs_env = jinja2.Environment(loader=jinja2.FileSystemLoader(_FRIDAJS_TEMPLATES_DIR))

from .exceptions import FridAsyncException  # noqa
from .fridasync import FridAsync  # noqa

from .session import FAsyncSession  # noqa
from .patcher import PatchBuilder, PatchVarSpec  # noqa
