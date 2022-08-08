"""Provides Quart app CLI commands for FRIDARE database management."""
import pathlib

from .. import app
from . import db_connect


SCRIPT_DIR = pathlib.Path(__file__).parent


@app.cli.command("create_db")
def create_db():
    """Make a db connection and create tables."""
    db = db_connect()
    with (SCRIPT_DIR / "sql_scripts/create_db.sql").open(mode="r", encoding="utf8") as f:
        db.cursor().executescript(f.read())
    db.commit()
