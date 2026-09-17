"""
BuildTech Backend - Flask Application Entrypoint
"""
from flask import Flask, g, jsonify
from flask_cors import CORS
from pydantic import ValidationError

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import HTTPException

app = Flask(
    __name__,
)
app.dependency_overrides = {}

# Enable CORS for secure cookie transmission and API access
CORS(
    app,
    origins=settings.BACKEND_CORS_ORIGINS,
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)


def include_router(router, prefix: str = ""):
    """Convenience helper to register an APIRouter blueprint on the Flask application."""
    app.register_blueprint(router.blueprint, url_prefix=prefix or None)


app.include_router = include_router


@app.teardown_request
def cleanup_request_dependencies(exception=None):
    """Closes and cleans up active generator dependencies (e.g., database sessions)."""
    generators = getattr(g, "_active_generators", [])
    for gen in reversed(generators):
        try:
            next(gen)
        except StopIteration:
            pass
    g._active_generators = []


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):
    """Serializes application HTTP exceptions preserving the standard {"detail": ...} JSON contract."""
    response = jsonify({"detail": exc.detail})
    response.status_code = exc.status_code
    for k, v in exc.headers.items():
        response.headers[k] = v
    return response


@app.errorhandler(ValidationError)
def handle_validation_error(exc: ValidationError):
    """Serializes Pydantic input validation errors as HTTP 422."""
    return jsonify({"detail": exc.errors()}), 422


@app.errorhandler(404)
def handle_not_found(exc):
    return jsonify({"detail": "Not found"}), 404


@app.errorhandler(405)
def handle_method_not_allowed(exc):
    return jsonify({"detail": "Method not allowed"}), 405


# Include API v1 routes from central feature router
app.register_blueprint(api_router.blueprint, url_prefix=settings.API_V1_STR)


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
    })
