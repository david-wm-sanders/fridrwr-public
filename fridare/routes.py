"""Defines routes for FRIDARE."""
# TODO: separate fridrwr routes out into blueprint
from loguru import logger

from quart import g, session, request
from quart import render_template, abort, flash, redirect, url_for
from quart import websocket

from . import app, fa
from . import db_connect


def get_db():
    """Get Quart context global g.fridare_db, initialising a db connection if necessary."""
    if not hasattr(g, "fridare_db"):
        g.fridare_db = db_connect()
    return g.fridare_db


def _log_request_view():
    """Log access data for current context request."""
    # logger.debug(dir(request))
    r = request
    logger.info(f"Processing [HTTP{r.http_version}:{r.endpoint}]'{r.url}' request from '{r.remote_addr}'...")
    logger.debug(f"{r.is_secure=} {r.authorization=} {r.cookies=}")
    # logger.debug(f"{r.access_control_request_headers=}")


@app.route("/")
async def index_view():
    """Render the index/home view."""
    _log_request_view()
    # logger.info(f"Serving '{request.host_url}' to '{request.remote_addr}' [{request.user_agent}]...")
    return await render_template("index.html", title="Index", fa=fa)


@app.route("/fridrwr")
async def fridrwr_view():
    """Render the fridrwr root view."""
    _log_request_view()
    # logger.info(f"Serving '{request.host_url}' to '{request.remote_addr}' [{request.user_agent}]...")
    rwr_session = fa.sessions.get("rwr_game.exe", None)
    return await render_template("fridrwr.html", title="RWR", rwr_session=rwr_session)
