"""
Flask-based APIRouter and Dependency Injection engine.
Provides declarative routing, dependency injection, and Pydantic validation
backed natively by Flask Blueprints, request context, and response handling.
"""
import inspect
import json
import re
from typing import Any, Dict, List, Optional, get_args, get_origin

from flask import (
    Flask,
    Blueprint,
    current_app,
    g,
    jsonify,
    make_response,
    request as flask_request,
)
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.core.exceptions import HTTPException
from app.core.status import status


class Depends:
    def __init__(self, dependency=None):
        self.dependency = dependency


class Security(Depends):
    def __init__(self, dependency=None, scopes=None):
        super().__init__(dependency=dependency)
        self.scopes = scopes or []


class Query:
    def __init__(
        self,
        default=...,
        *,
        description: Optional[str] = None,
        ge: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        alias: Optional[str] = None,
        **extra,
    ):
        self.default = default
        self.description = description
        self.ge = ge
        self.le = le
        self.min_length = min_length
        self.max_length = max_length
        self.alias = alias


class Header:
    def __init__(
        self,
        default=...,
        *,
        alias: Optional[str] = None,
        description: Optional[str] = None,
        **extra,
    ):
        self.default = default
        self.alias = alias
        self.description = description


class Body:
    def __init__(
        self,
        default=...,
        *,
        description: Optional[str] = None,
        embed: bool = False,
        **extra,
    ):
        self.default = default
        self.description = description
        self.embed = embed


class HTTPAuthorizationCredentials:
    def __init__(self, scheme: str, credentials: str):
        self.scheme = scheme
        self.credentials = credentials


class HTTPBearer:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    def __call__(self) -> Optional[HTTPAuthorizationCredentials]:
        auth = flask_request.headers.get("Authorization")
        if not auth:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        return HTTPAuthorizationCredentials(scheme=parts[0], credentials=parts[1])


def resolve_dependency(dep_func, context_cache=None, overrides=None):
    if context_cache is None:
        context_cache = {}

    if overrides and dep_func in overrides:
        target_dep = overrides[dep_func]
    else:
        target_dep = dep_func

    if target_dep in context_cache:
        return context_cache[target_dep]

    sig = inspect.signature(target_dep)
    kwargs = {}
    for p_name, param in sig.parameters.items():
        if isinstance(param.default, Depends):
            kwargs[p_name] = resolve_dependency(
                param.default.dependency, context_cache, overrides
            )

    res = target_dep(**kwargs)
    if inspect.isgenerator(res):
        val = next(res)
        if not hasattr(g, "_active_generators"):
            g._active_generators = []
        g._active_generators.append(res)
        context_cache[target_dep] = val
        return val

    context_cache[target_dep] = res
    return res


def clean_pydantic_errors(errs: Any) -> Any:
    if isinstance(errs, list):
        return [clean_pydantic_errors(item) for item in errs]
    if isinstance(errs, dict):
        return {k: clean_pydantic_errors(v) for k, v in errs.items()}
    if isinstance(errs, Exception):
        return str(errs)
    return errs


def _serialize_data(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, list):
        return [_serialize_data(item) for item in data]
    if isinstance(data, dict):
        return {k: _serialize_data(v) for k, v in data.items()}
    return data


class APIRouter:
    _instance_count = 0

    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        responses: Optional[Dict[Any, Any]] = None,
    ):
        APIRouter._instance_count += 1
        self.prefix = prefix
        self.tags = tags or []
        
        clean_prefix = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"<\1>", prefix)
        clean_name = (
            prefix.strip("/")
            .replace("/", "_")
            .replace("{", "")
            .replace("}", "")
            .replace("-", "_")
        )
        bp_name = f"bp_{clean_name}_{APIRouter._instance_count}" if clean_name else f"bp_root_{APIRouter._instance_count}"
        
        self.blueprint = Blueprint(
            bp_name,
            __name__,
            url_prefix=clean_prefix if clean_prefix else None,
        )

    def include_router(self, child_router: "APIRouter", prefix: str = ""):
        clean_child_prefix = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"<\1>", prefix) if prefix else None
        self.blueprint.register_blueprint(child_router.blueprint, url_prefix=clean_child_prefix)

    def _convert_path(self, path: str) -> str:
        return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"<\1>", path)

    def add_api_route(
        self,
        path: str,
        endpoint,
        methods: List[str],
        response_model: Any = None,
        status_code: int = 200,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ):
        converted_path = self._convert_path(path)
        sig = inspect.signature(endpoint)

        def view_func(**view_args):
            overrides = getattr(current_app, "dependency_overrides", {})
            dep_cache = {}
            call_kwargs = {}
            injected_response = make_response()

            # Pass 1: Resolve Dependencies first (enforces Auth/Permissions before request body validation)
            for name, param in sig.parameters.items():
                if isinstance(param.default, Depends):
                    call_kwargs[name] = resolve_dependency(
                        param.default.dependency, dep_cache, overrides
                    )

            # Pass 2: Resolve Request, Response, Headers, Path, Body, and Query parameters
            for name, param in sig.parameters.items():
                if isinstance(param.default, Depends):
                    continue

                annotation = param.annotation
                default = param.default

                if (
                    isinstance(annotation, type) and issubclass(annotation, BaseModel)
                ) or isinstance(default, Body):
                    body_json = flask_request.get_json(silent=True)
                    if body_json is None:
                        if flask_request.data:
                            try:
                                body_json = json.loads(flask_request.data.decode("utf-8"))
                            except Exception:
                                raise HTTPException(
                                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="Invalid JSON body",
                                )
                        else:
                            body_json = {}

                    if isinstance(default, Body) and not (
                        isinstance(annotation, type) and issubclass(annotation, BaseModel)
                    ):
                        if default.default is ... and not body_json and body_json != {}:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Body payload is required for '{name}'",
                            )
                        call_kwargs[name] = body_json
                    else:
                        try:
                            call_kwargs[name] = annotation.model_validate(body_json)
                        except ValidationError as ve:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=clean_pydantic_errors(ve.errors()),
                            )
                elif name in ("request", "_request") or (
                    annotation != inspect.Parameter.empty
                    and getattr(annotation, "__name__", "") in ("Request", "flask_request")
                ):
                    call_kwargs[name] = flask_request
                elif name in ("response", "_response") or (
                    annotation != inspect.Parameter.empty
                    and getattr(annotation, "__name__", "") in ("Response", "FlaskResponse")
                ):
                    call_kwargs[name] = injected_response
                elif name in view_args:
                    val = view_args[name]
                    if annotation != inspect.Parameter.empty:
                        try:
                            call_kwargs[name] = TypeAdapter(annotation).validate_python(val)
                        except ValidationError as ve:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=clean_pydantic_errors(ve.errors()),
                            )
                    else:
                        call_kwargs[name] = val
                elif isinstance(default, Header):
                    header_name = default.alias or name.replace("_", "-")
                    val = flask_request.headers.get(header_name)
                    if val is None:
                        if default.default is not ...:
                            val = default.default
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Header '{header_name}' is required.",
                            )
                    if val is not None and annotation != inspect.Parameter.empty:
                        try:
                            call_kwargs[name] = TypeAdapter(annotation).validate_python(val)
                        except ValidationError as ve:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=clean_pydantic_errors(ve.errors()),
                            )
                    else:
                        call_kwargs[name] = val
                else:
                    # Query parameter
                    query_def = default if isinstance(default, Query) else None
                    param_key = query_def.alias if (query_def and query_def.alias) else name

                    origin = get_origin(annotation)
                    if origin is list or origin is List:
                        raw_val = flask_request.args.getlist(param_key)
                    else:
                        raw_val = flask_request.args.get(param_key)

                    if raw_val is None or (isinstance(raw_val, list) and len(raw_val) == 0):
                        if query_def and query_def.default is not ...:
                            val = query_def.default
                        elif default is not inspect.Parameter.empty and default is not ...:
                            val = default
                        elif annotation != inspect.Parameter.empty and type(None) in get_args(annotation):
                            val = None
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Missing query parameter '{param_key}'",
                            )
                    else:
                        if annotation != inspect.Parameter.empty:
                            try:
                                val = TypeAdapter(annotation).validate_python(raw_val)
                            except ValidationError as ve:
                                raise HTTPException(
                                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=clean_pydantic_errors(ve.errors()),
                                )
                        else:
                            val = raw_val

                    if query_def:
                        if query_def.ge is not None and val is not None and val < query_def.ge:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Parameter '{param_key}' must be >= {query_def.ge}",
                            )
                        if query_def.le is not None and val is not None and val > query_def.le:
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Parameter '{param_key}' must be <= {query_def.le}",
                            )

                    call_kwargs[name] = val

            # Execute the endpoint handler
            result = endpoint(**call_kwargs)

            # Response serialization
            if result is None and status_code == 204:
                final_resp = make_response("", 204)
            elif hasattr(result, "status_code") and hasattr(result, "headers"):
                # Already a Response object
                return result
            else:
                if response_model is not None:
                    try:
                        validated = TypeAdapter(response_model).validate_python(result)
                        serialized = _serialize_data(validated)
                    except Exception:
                        serialized = _serialize_data(result)
                else:
                    serialized = _serialize_data(result)

                final_resp = make_response(jsonify(serialized), status_code)

            # Merge headers and cookies from injected_response
            for header_k, header_v in injected_response.headers:
                if header_k.lower() != "content-type":
                    final_resp.headers[header_k] = header_v

            for cookie_header in injected_response.headers.getlist("Set-Cookie"):
                final_resp.headers.add("Set-Cookie", cookie_header)

            return final_resp

        view_func.__name__ = f"{endpoint.__name__}_{id(view_func)}"
        rule = converted_path or "/"
        self.blueprint.add_url_rule(
            rule,
            endpoint=view_func.__name__,
            view_func=view_func,
            methods=methods,
            strict_slashes=False,
        )

    def get(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["GET"], **kwargs)
            return func
        return decorator

    def post(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["POST"], **kwargs)
            return func
        return decorator

    def put(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["PUT"], **kwargs)
            return func
        return decorator

    def patch(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["PATCH"], **kwargs)
            return func
        return decorator

    def delete(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["DELETE"], **kwargs)
            return func
        return decorator

    def options(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["OPTIONS"], **kwargs)
            return func
        return decorator

    def head(self, path: str, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=["HEAD"], **kwargs)
            return func
        return decorator
