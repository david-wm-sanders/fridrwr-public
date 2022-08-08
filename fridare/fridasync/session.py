"""Wraps frida.core.Session in some async sorcery."""
import functools

import trio
import frida

from loguru import logger

from . import PKG_DIR
from .logging import generic_fridajs_log_handler, generic_on_msg_log_handler
from .script import FAsyncScript
from .patcher import FAsyncPatcherScript, PatchBuilder, PatchVarSpec
from .utils import load_js_from_file


class FAsyncSessionFoundation:
    """Base class for frida.core.Session wrapper that provides the 'essential'(?) functionality."""

    def __init__(self, target: str, session: frida.core.Session):
        """Wrap a passed frida.core.Session object."""
        self._target = target
        self._session = session

        self.scripts = {}

        self._utils_script, self._init_complete = None, False
        self._frida_version, self._frida_script_runtime = None, None
        self._arch, self._platform = None, None
        self._page_size, self._pointer_size, self._code_signing_policy = None, None, None

    def __str__(self) -> str:
        """Return str(self: FAsyncSessionFoundation)."""
        return f"{self.target}[pid:{self.pid}]"

    @property
    def target(self) -> str:
        """Return the target name."""
        return self._target

    @property
    def session(self) -> frida.core.Session:
        """Return the underlying frida.core.Session."""
        return self._session

    @property
    def pid(self) -> int:
        """Return the pid of the targeted process."""
        return self._session._impl.pid  # noqa

    @property
    def init_complete(self) -> bool:
        """Return whether async init is complete."""
        return self._init_complete

    @property
    def frida_version(self) -> str:
        """Return the frida version."""
        return self._frida_version

    @property
    def frida_script_runtime(self) -> str:
        """Return the session frida script runtime."""
        return self._frida_script_runtime

    @property
    def arch(self) -> str:
        """Return the target process architecture."""
        return self._arch

    @property
    def platform(self) -> str:
        """Return the target process platform."""
        return self._platform

    @property
    def page_size(self) -> int:
        """Return the target process page size."""
        return self._page_size

    @property
    def pointer_size(self) -> int:
        """Return the target process pointer size."""
        return self._pointer_size

    @property
    def code_signing_policy(self) -> str:
        """Return the target process code signing policy."""
        return self._code_signing_policy

    # TODO: should this be an AsyncProperty?
    @property
    def frida_heap_size(self) -> int:
        """Return the frida heap size in target process."""
        _sctx = f"[{self.target}:_fridasync.js]"
        try:
            return self._utils_script.exports.frida_heap_size()
        except frida.InvalidOperationError as e:
            logger.error(f"[{_sctx}] frida: {e}")
            return 0

    # TODO: should this be an AsyncProperty?
    @property
    def debugger_attached(self) -> bool:
        """Return whether a debugger is attached to the target process."""
        _sctx = f"[{self.target}:_fridasync.js]"
        try:
            return self._utils_script.exports.is_debugger_attached()
        except frida.InvalidOperationError as e:
            logger.error(f"[{_sctx}] frida: {e}")
            return False

    async def _load_utils_js_script(self):
        """Load the _fridasync.js utils script into the wrapped frida.core.Session."""
        # Calculate the path for _fridasync.js and async load it
        fa_utils_js_path = PKG_DIR / "_fridasync.js"
        logger.debug(f"Loading _fridasync.js script from file...")
        fridasync_utils_js = await load_js_from_file(fa_utils_js_path)
        logger.success(f"Loaded _fridasync.js")
        # Create a partial function that sets the kw args for frida.Session.create_script
        pf = functools.partial(self._session.create_script, name="_fridasync.js", source=fridasync_utils_js)
        logger.debug(f"Creating _fridasync.js script in '{self}'...")
        self._utils_script: frida.core.Script = await trio.to_thread.run_sync(pf)
        logger.success(f"Created _fridasync.js script in '{self}'")
        # self._utils_script.set_log_handler(self._utils_log_handler)
        log_pf = functools.partial(generic_fridajs_log_handler, self.target, "_fridasync.js")
        self._utils_script.set_log_handler(log_pf)
        # self._utils_script.on("message", self._utils_on_msg)
        logger.debug(f"Loading _fridasync.js script in '{self}'...")
        await trio.to_thread.run_sync(self._utils_script.load)
        logger.success(f"Loaded _fridasync.js script in '{self}'")

    def _set_frida_session_static_info_properties(self):
        """Set frida session static info properties by running _fridasync.js rpc exports once."""
        self._frida_version = self._utils_script.exports.frida_version()
        self._frida_script_runtime = self._utils_script.exports.frida_script_runtime()
        self._arch = self._utils_script.exports.arch()
        self._platform = self._utils_script.exports.platform()
        self._page_size = self._utils_script.exports.page_size()
        self._pointer_size = self._utils_script.exports.pointer_size()
        self._code_signing_policy = self._utils_script.exports.code_signing_policy()

    def _pretty_frida_session_info(self):
        """Return a prettified frida session info summary."""
        session_info = f"version={self.frida_version}, runtime={self.frida_script_runtime}, " \
                       f"pid={self.pid}, arch={self.arch}, platform={self.platform}, " \
                       f"pagesize={self.page_size}, pointersize={self.pointer_size}, " \
                       f"csp={self.code_signing_policy}"
        return session_info

    async def init(self):
        """Perform async initialisation."""
        await self._load_utils_js_script()
        self._set_frida_session_static_info_properties()
        self._init_complete = True
        logger.debug(f"Initialised FAsyncSession(target={self.target}) [{self._pretty_frida_session_info()}]")

    async def create_script(self, name: str, source_js: str, script_class=FAsyncScript, *args, **kwargs):
        """Create a FAsyncScript (or subclass script_class) within the wrapped frida.core.Session."""
        f = functools.partial(self._session.create_script, name=name, source=source_js)
        _script = await trio.to_thread.run_sync(f)
        self.scripts[name] = script_class(name, source_js, _script)
        return self.scripts[name]


class FAsyncSession(FAsyncSessionFoundation):
    """Extend FAsyncSessionFoundation to provide extra magic over the wrapped frida.core.Session."""

    def __init__(self, target: str, session: frida.core.Session):
        """Wrap a passed frida.core.Session object."""
        super().__init__(target, session)
        self._patch_builder = PatchBuilder()
        self.patches = {}

    async def create_jmp_patch(self, name: str, module_name: str, target_pattern: str,
                               vars_spec: list[PatchVarSpec], relocate_target: bool,
                               patch_mem_size: int, return_offset: int,
                               cw_patch_func: str) -> FAsyncPatcherScript:
        """Create a jmp patch (script) within the target session."""
        # TODO: make create_jmp_patch_js async again!
        script_name, js = self._patch_builder.gen_jmp_patch_js(name, module_name, target_pattern,
                                                               vars_spec, relocate_target,
                                                               patch_mem_size, return_offset,
                                                               cw_patch_func)
        logger.debug(f"Creating {script_name} script in '{self.session}'...")
        patch_script = await self.create_script(name=script_name, source_js=js,
                                                script_class=FAsyncPatcherScript)
        logger.success(f"Created {script_name} script in '{self.session}'")
        logger.debug(f"Configuring log handler and binding callbacks for {script_name}...")
        # Bind the handler and configure the callbacks xd
        log_pf = functools.partial(generic_fridajs_log_handler, self.target, script_name)
        patch_script.set_log_handler(log_pf)
        msg_pf = functools.partial(generic_on_msg_log_handler, self.target, script_name)
        patch_script.on("message", msg_pf)
        # Load the patch now!
        await patch_script.load()
        self.patches[name] = patch_script
        return patch_script

    async def create_nop_patch(self, name: str, module_name: str, target_pattern: str,
                               nop_offset: int, nop_length: int) -> FAsyncPatcherScript:
        """Create a nop patch (script) within the target session."""
        script_name, js = self._patch_builder.gen_nop_patch_js(name, module_name, target_pattern,
                                                               nop_offset, nop_length)
        logger.debug(f"Creating {script_name} script in '{self.session}'...")
        patch_script = await self.create_script(name=script_name, source_js=js,
                                                script_class=FAsyncPatcherScript)
        logger.success(f"Created {script_name} script in '{self.session}'")
        logger.debug(f"Configuring log handler and binding callbacks for {script_name}...")
        # Bind the handler and configure the callbacks xd
        log_pf = functools.partial(generic_fridajs_log_handler, self.target, script_name)
        patch_script.set_log_handler(log_pf)
        msg_pf = functools.partial(generic_on_msg_log_handler, self.target, script_name)
        patch_script.on("message", msg_pf)
        # Load the patch now!
        await patch_script.load()
        self.patches[name] = patch_script
        return patch_script

    # TODO: perhaps clear_all_patches should call special clear_sync method instead?
    async def clear_all_patches(self):
        """Clear all applied patches within the target session."""
        for patch in self.patches.values():
            if patch.applied:
                await patch.clear()
