"""Initialise systems that are required and/or provided by FRIDARE."""
# configure module logging
from loguru import logger
logger.disable("fridare")

# set up unit handling for the rest of the application
from pint import UnitRegistry, set_application_registry  # noqa
ureg = UnitRegistry()
Q_ = ureg.Quantity
# if pickling and unpickling quantities:
# set_application_registry(ureg)

# import and make an instance of FridAsync for frida interaction
from .fridasync import FridAsync  # noqa
fa = FridAsync()

# create FRIDARE QuartTrio app
import quart_trio  # noqa
app = quart_trio.QuartTrio(__name__)
# set up some development app config
app.config.update({"DEBUG": True})

# import db related stuff :?
from .db import db_connect  # noqa

# import other things to make them available at the module-level
from .tracer import TracerInstrument  # noqa
from . import routes, filters  # noqa
