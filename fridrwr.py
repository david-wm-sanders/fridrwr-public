"""FRIDRWR app constructor."""
import pathlib
import sys

import frida
import trio
import hypercorn
import hypercorn.trio

from typing import Optional

from loguru import logger

from fridare import fa, app, TracerInstrument
from fridare.fridasync import FridAsyncException, FAsyncSession, PatchBuilder, PatchVarSpec
from fridare.fridasync.logging import LoguruHypercornProxy

# this magic allows for Ctrl+C to PyCharm run console to be handled nicely
try:
    from console_thrift import KeyboardInterruptException as KeyboardInterrupt  # noqa
except ImportError:
    pass

SCRIPT_DIR = pathlib.Path(__file__).parent


anti_fog_range_var = PatchVarSpec("range", "float", 4, "600.0")
anti_fog_offset_var = PatchVarSpec("offset", "float", 4, "-100.0")
anti_fog_patch_cw_func = """
// patch the range
cw.putBytes(X86_32_OP.FLD_DWORDPTR_ADDR);
// write the range addr for the FLD
_putPointer(cw, vars.get("range").mem);
// write the instruction to store-pop the float to ecx+4c for range
cw.putBytes(X86_32_OP.FSTP_DWORDPTR_ECX_OFFSET);
cw.putBytes([0x4C]);
// patch the offset
cw.putBytes(X86_32_OP.FLD_DWORDPTR_ADDR);
// write the range addr for the FLD
_putPointer(cw, vars.get("offset").mem);
// write the instruction to store-pop the float to ecx+50 for offset
cw.putBytes(X86_32_OP.FSTP_DWORDPTR_ECX_OFFSET);
cw.putBytes([0x50]);
cw.flush();
"""


async def fridrwr_manage_session(game: FAsyncSession):
    """Manage a FAsyncSession 'game' that is targeting a RWR client game."""

    logger.debug("Creating anti fog patch...")
    anti_fog_patch = await game.create_jmp_patch("anti_fog", "rwr_game.exe",
                                                 "D9 44 24 08 D9 59 4C D9 44 24 04 D9 59 50",
                                                 [anti_fog_range_var, anti_fog_offset_var],
                                                 False, 32, 14, anti_fog_patch_cw_func)
    logger.success(f"Created anti fog patch: {anti_fog_patch}")

    # logger.debug(f"{game=}\n{game.scripts=}\n{game.patches=}")
    # apply the following patches by default in the managed session
    await anti_fog_patch.apply()
    if anti_fog_patch.applied:
        logger.success("Applied anti fog patch")


async def fridrwr_setup():
    """Attempt creation of "rwr_game.exe" session and manage if created successfully."""
    target = "rwr_game.exe"
    game = None
    while True:
        try:
            if target not in fa.sessions:
                logger.debug(f"FRIDRWR creating session for '{target}'... ")
                game = await fa.create_session(target)
                if game:
                    logger.success(f"We have a rwr_game session with pid '{game.pid}'!")
                    await fridrwr_manage_session(game)
            else:
                # wait some time before checking again...
                await trio.sleep(15)
        except FridAsyncException as e:
            logger.error(f"FRIDRWR setup! fridasync exception: {e}")
            break
        except frida.ProcessNotFoundError as e:
            logger.warning(f"FRIDRWR target '{target}' process not found, wait 15 seconds and retry... :)")
            await trio.sleep(15)
        except trio.Cancelled:
            g = fa.sessions.get(target, None)
            if g:
                # clear all patches from session so that target doesn't get memory access exception
                # when frida has left but the edits to game memory at patch point still exist
                logger.info("FRIDRWR setup cancelled, clearing applied patches...")
                await g.clear_all_patches()
            else:
                logger.debug("FRIDRWR setup cancelled, no patches applied so nothing to clear :)")
            raise


async def start_fridrwr_app(hypercorn_config: hypercorn.Config):
    """Open app server nursery that starts FRIDRWR and the web app server."""
    async with trio.open_nursery() as tn_app_server:
        tn_app_server.start_soon(fridrwr_setup)
        tn_app_server.start_soon(hypercorn.trio.serve, app, hypercorn_config)


if __name__ == '__main__':
    suppressed_task_names = ["__main__.start_fridrwr_app", "__main__.fridrwr_setup"]

    # configure logging
    log_fmt_c = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | " \
                "<level>{level: <8}</level> |{level.icon}  " \
                "<level>{message}</level>"
    log_fmt_f = "{time:YYYY-MM-DD HH:mm:ss.SSS} | " \
                "<level>{level: <8}</level> |{level.icon}  " \
                "<level>{message}</level> [{name}:{function}:{line}]"
    # clean up the default logger
    logger.remove()
    logger.configure(handlers=[{"sink": sys.stderr, "format": log_fmt_c, "level": "TRIOINS"}])
    logger.add("fridrwr.log", format=log_fmt_f, level="DEBUG", retention="1 day", rotation="12 hours")
    logger.level("INFO", icon="🔔")
    # enable the library logging for CLI mode
    logger.enable("fridare")

    logger.info(f"Starting FRIDRWR...")
    hypercorn_cfg = hypercorn.Config()
    hypercorn_cfg.logger_class = LoguruHypercornProxy
    hypercorn_cfg.bind = ["127.0.0.1:5000"]
    try:
        trio.run(start_fridrwr_app, hypercorn_cfg, instruments=[TracerInstrument(suppressed_task_names)])
    except KeyboardInterrupt:
        logger.info(f"FRIDRWR was cancelled by KeyboardInterrupt")
