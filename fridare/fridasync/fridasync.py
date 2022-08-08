"""Defines the FridAsync class that FRIDARE exposes as 'fa'."""
from typing import Union

import dataclasses
import functools

import trio
import frida
import aiopath

from loguru import logger

from .session import FAsyncSession
from .exceptions import FridAsyncException


class FridAsync:
    """Holds a dictionary of active FAsyncSession sessions."""

    def __init__(self):
        """Initialise a container for active FAsyncSession sessions."""
        # self._sessions_lock = trio.Lock()
        self.sessions: dict[str, FAsyncSession] = {}

    def _session_detached(self, target, *args):
        logger.debug(f"Session for '{target}' detached because: {args}")
        s = self.sessions.pop(target)

    async def create_session(self, target: str) -> Union[FAsyncSession, None]:
        """Create a FAsyncSession with frida.attach(target)."""
        # async with self._sessions_lock:
        if t := self.sessions.get(target, None):
            raise FridAsyncException(f"Session '{t.pid}' already targeting '{target}' :/")
        try:
            fsession = await trio.to_thread.run_sync(frida.attach, target)
            session = FAsyncSession(target, fsession)
            pf = functools.partial(self._session_detached, target)
            fsession.on("detached", pf)
            self.sessions[target] = session
            await self.sessions[target].init()
            return self.sessions[target]
        except frida.ProcessNotFoundError as e:
            logger.error(f"frida: {e}")
            raise e
