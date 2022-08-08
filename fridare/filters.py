"""Define filters for web templates."""
from . import app


@app.template_filter()
def jinja_dir(o):
    """Return dir(o) for templates."""
    return dir(o)
