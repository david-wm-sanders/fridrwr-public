"""Defines a trio tracing instrument that logs via loguru."""
import trio
from loguru import logger

from . import ureg


TRIO_TRACE_LVL = logger.level("TRIOINS", no=9, color="<yellow>", icon="🐍")
SUPPRESSED_TASK_NAMES = [  # TRIO TASKS
                            "<init>", "<TrioToken.run_sync_soon",
                            "trio._highlevel_serve_listeners.",
                            "trio.serve_listeners",
                           # HYPERCORN TASKS
                            "hypercorn.trio.serve",
                            "hypercorn.trio.lifespan.Lifespan",
                            "hypercorn.trio.tcp_server._call_later",
                            "hypercorn.trio.task_group._handle",
                            "hypercorn.trio.context._handle",
                            "hypercorn.protocol.h2.H2Protocol.send_task",
                           # QUART-TRIO TASKS
                            "quart_trio.asgi.TrioASGIHTTPConnection.handle_"
                        ]


class TracerInstrument(trio.abc.Instrument):
    """Subclasses trio.abc.Instrument interface to provide an implementation."""

    def __init__(self, suppressed_task_names: list[str]):
        """Initialise TracerInstrument instance variables."""
        self._sleep_time = 0
        self._suppressed_task_names = SUPPRESSED_TASK_NAMES
        self._suppressed_task_names.extend(suppressed_task_names)

    def _log_task(self, task, message: str):
        task_name = task.name
        if not any(task_name.startswith(prefix) for prefix in self._suppressed_task_names):
            logger.log(TRIO_TRACE_LVL.name, message)

    def before_run(self):
        """Log before trio begins its event loop."""
        logger.log(TRIO_TRACE_LVL.name, "📢  Beginning async magic...")

    def task_spawned(self, task):
        """Log when a tank is spawned."""
        self._log_task(task, f"🐍  Spawning new task '{task.name}'...")

    def task_scheduled(self, task):
        """Log when a task is scheduled."""
        self._log_task(task, f"◈  Scheduling task '{task.name}'...")

    def before_task_step(self, task):
        """Log before a step of a task is run."""
        self._log_task(task, f"⟶  Running a step of task '{task.name}'...")

    def after_task_step(self, task):
        """Log after a step of a task is run."""
        self._log_task(task, f"⟵  Finished a step of '{task.name}'")

    def task_exited(self, task):
        """Log when a task is exited."""
        self._log_task(task, f"⏹  Exiting task '{task.name}'...")

    # def before_io_wait(self, timeout: int):
    #     """Log before trio begins an io wait."""
    #     if timeout:
    #         _t = timeout * ureg.seconds
    #         # make a fancy string to represent this data - `~P:.2f` for pint pretty abbreviated .2 float acc. form
    #         # `.to_compact()` is pint magic that picks the best prefix for humans
    #         logger.log(TRIO_TRACE_LVL.name, f"⏰  Waiting for I/O for up to {_t.to_compact():~P.2f} seconds...")
    #     else:
    #         # logger.log(TRIO_TRACE_LVL.name, "📡  Doing a quick check for I/O...")
    #         pass
    #     self._sleep_time = trio.current_time()

    # def after_io_wait(self, timeout):
    #     duration = trio.current_time() - self._sleep_time
    #     _d = duration * ureg.seconds
    #     logger.log(TRIO_TRACE_LVL.name, f"⏰  Finished I/O check (took {_d.to_compact():~P.2f} seconds)")

    def after_run(self):
        """Log after trio finishes running a cacophony of tasks."""
        logger.log(TRIO_TRACE_LVL.name, "📢  Finished async magic")
