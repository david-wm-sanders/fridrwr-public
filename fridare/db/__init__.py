"""Provides a database system for FRIDARE."""
import pathlib
from sqlite3 import dbapi2 as sqlite3

from .. import app


SCRIPT_DIR = pathlib.Path(__file__).parent
app.config.update({"DATABASE": SCRIPT_DIR / "fridare.db"})


def db_connect():
    """Create a sqlite3 connection to db at app.config["DATABASE"]."""
    engine = sqlite3.connect(app.config["DATABASE"])
    engine.row_factory = sqlite3.Row
    return engine


from . import cli  # noqa
