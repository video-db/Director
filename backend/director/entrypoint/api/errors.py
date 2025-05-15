import logging


from flask import current_app as app, json, Response
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error

    if e.code != 404:
        logger.exception(e)

    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "message": e.description,
        }
    )
    response.content_type = "application/json"
    return response


@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON instead of HTML for non-HTTP errors."""
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    logger.exception(e)

    # now handling non-HTTP exceptions only
    resp = Response()
    resp.response = json.dumps(
        {
            "message": "internal server error",
            "detail": f"{type(e).__name__}: {e}",
        }
    )
    resp.status_code = 500
    resp.mimetype = "application/json"
    return resp


# handle pideantic validation error
@app.errorhandler(ValidationError)
def handle_validation_exception(error):
    """Handles all Pydantic validation errors."""

    logger.exception(error)

    resp = Response()
    resp.response = json.dumps(
        {"status": "error", "message": str(error), "detail": error.errors()}
    )
    resp.status = 400
    resp.mimetype = "application/json"
    return resp
