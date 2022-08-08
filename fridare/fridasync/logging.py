"""Defines FRIDARE loguru logging levels, generic handlers, and logging proxy classes."""
from loguru import logger
# Configure additional logging levels for frida-raised logs
FRIDAJS_DEBUG_LVL = logger.level("FDEBUG", no=11, color="<blue>", icon="👽‍")
FRIDAJS_INFO_LVL = logger.level("FINFO", no=21, color="<cyan>", icon="⚡️")
FRIDAJS_WARN_LVL = logger.level("FWARN", no=31, color="<yellow>", icon="💢")
FRIDAJS_PROCEXC_LVL = logger.level("PROCEXC", no=32, color="<yellow>", icon="🔴")
FRIDAJS_ERROR_LVL = logger.level("FERROR", no=41, color="<red>", icon="💥")


def generic_fridajs_log_handler(target, script_name, level, message):
    """Handle logs from fridajs logging via loguru emission."""
    _sctx = f"[{target}:{script_name}]"
    if level == "debug":
        logger.log(FRIDAJS_DEBUG_LVL.name, f"{_sctx} {message}")
    elif level == "info":
        logger.log(FRIDAJS_INFO_LVL.name, f"{_sctx} {message}")
    elif level == "warning":
        logger.log(FRIDAJS_WARN_LVL.name, f"{_sctx} {message}")
    elif level == "error":
        logger.log(FRIDAJS_ERROR_LVL.name, f"{_sctx} {message}")
    elif level == "process_exception":
        # addr = message["address"]
        logger.log(FRIDAJS_PROCEXC_LVL.name, f"{_sctx} {message}")
    else:
        logger.error(f"_generic_log_handler didn't understand '{level}' level "
                     f"with message: '{message}'")


def generic_on_msg_log_handler(target, script_name, message, data):
    """Handle messages from fridajs via loguru info emission."""
    logger.info(f"[{target}:{script_name}]: {message}, data: '{data}'")


# Configure additional logging levels for hypercorn logs
HYPERCORN_DEBUG_LVL = logger.level("HDEBUG", no=12)
HYPERCORN_INFO_LEVEL = logger.level("HINFO", no=22, icon="📡")
HYPERCORN_ACCESS_LVL = logger.level("HACCESS", no=23)
HYPERCORN_LOG_LVL = logger.level("HLOG", no=24)
HYPERCORN_WARN_LVL = logger.level("HWARN", no=33)
HYPERCORN_EXC_LVL = logger.level("HEXC", no=34)
HYPERCORN_ERROR_LVL = logger.level("HERROR", no=42)
HYPERCORN_CRIT_LVL = logger.level("HCRIT", no=51)


class LoguruHypercornProxy:
    """Proxies hypercorn logging into FRIDARE loguru system."""

    def __init__(self, s):
        """Initialise a LoguruHypercornProxy - set as hypercorn_cfg.logger_class and instantiated by hypercorn."""
        self._s = s

    async def access(self, request, response, request_time: float, *args, **kwargs):
        """Log on hypercorn access."""
        msg = f"HYPERCORN ACCESS LOG:\n{request=}\n{response=}\n{request_time=}"
        logger.log(HYPERCORN_ACCESS_LVL.name, msg, *args, *kwargs)

    async def critical(self, msg: str, *args, **kwargs):
        """Log on hypercorn critical."""
        logger.log(HYPERCORN_CRIT_LVL.name, msg, *args, **kwargs)

    async def error(self, msg: str, *args, **kwargs):
        """Log on hypercorn error."""
        logger.log(HYPERCORN_ERROR_LVL.name, msg, *args, **kwargs)

    async def warning(self, msg: str, *args, **kwargs):
        """Log on hypercorn warning."""
        logger.log(HYPERCORN_WARN_LVL.name, msg, *args, **kwargs)

    async def info(self, msg: str, *args, **kwargs):
        """Log on hypercorn info."""
        logger.log(HYPERCORN_INFO_LEVEL.name, msg, *args, **kwargs)

    async def debug(self, msg: str, *args, **kwargs):
        """Log on hypercorn debug."""
        logger.log(HYPERCORN_DEBUG_LVL.name, msg, *args, **kwargs)

    async def exception(self, msg: str, *args, **kwargs):
        """Log on hypercorn exception."""
        logger.log(HYPERCORN_EXC_LVL.name, msg, *args, **kwargs)

    async def log(self, lvl: int, msg: str, *args, **kwargs):
        """Log on hypercorn log."""
        logger.log(HYPERCORN_LOG_LVL.name, f"[{lvl}] {msg}", *args, **kwargs)
