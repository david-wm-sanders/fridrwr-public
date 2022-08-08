"""Defines some fridasync utility coroutines."""
import aiopath

from loguru import logger

from .exceptions import FridAsyncException


async def load_js_from_file(path: str):
    """Load javascript from a specified file path with aiopath."""
    js_path: aiopath.AsyncPath = aiopath.AsyncPath(path)
    if not await js_path.exists():
        logger.error(f"Can't load js from non-existent path '{path}'")
        raise FridAsyncException(f"Can't load js from non-existent path '{path}'")
    return await js_path.read_text(encoding="utf8")
