"""Wraps frida.core.Script in some async sorcery."""
import frida
import trio

from loguru import logger


class FAsyncScript:
    """Provides an asyncy wrapper around a frida.core.Script."""

    def __init__(self, name: str, source_js: str, script: frida.core.Script):
        """Wrap a passed frida.core.Script object."""
        self._name = name
        self._source_js = source_js
        self._script = script
        self._loaded = False

    def __str__(self):
        """Return str(self: FAsyncScript)."""
        return f"FAsyncScript({self.name=} [loaded:{self.loaded}] wrapping {self._script}"

    @property
    def name(self):
        """Return script name."""
        return self._name

    @property
    def source_js(self):
        """Return script source javascript."""
        return self._source_js

    @property
    def loaded(self):
        """Return whether the script is loaded inside the session it exists within."""
        return self._loaded

    def set_log_handler(self, handler_func):
        """Set the `sync` (atm?) handler func that will be used as the frida.core.Script log handler."""
        self._script.set_log_handler(handler_func)

    def on(self, signal: str, callback):
        """Bind the frida.core.Script signal to the `sync` (atm?) callback function."""
        self._script.on(signal, callback)

    async def load(self):
        """Await loading of the wrapped frida.core.Script async in bg thread."""
        logger.debug(f"Loading script '{self.name=}'...")
        await trio.to_thread.run_sync(self._script.load)
        self._loaded = True
        logger.debug(f"Loaded script '{self.name=}'")
