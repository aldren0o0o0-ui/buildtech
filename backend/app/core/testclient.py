"""
Flask-based TestClient for BuildTech backend.
Provides a clean, convenient test client interface wrapping Flask's test_client.
"""
from http.cookies import SimpleCookie
from typing import Any, Dict, Optional


class CallableDict(dict):
    def __call__(self, *args, **kwargs):
        return self


class CallableList(list):
    def __call__(self, *args, **kwargs):
        return self


def _make_callable_json(val: Any) -> Any:
    if isinstance(val, dict):
        cd = CallableDict()
        for k, v in val.items():
            cd[k] = _make_callable_json(v)
        return cd
    if isinstance(val, list):
        cl = CallableList()
        for item in val:
            cl.append(_make_callable_json(item))
        return cl
    return val


class ResponseCookies(dict):
    def get(self, key: str, default: Any = None) -> Any:
        return super().get(key, default)


class TestResponseWrapper:
    def __init__(self, flask_response):
        self._resp = flask_response
        self.status_code = flask_response.status_code
        self.headers = flask_response.headers
        self._parsed_cookies = None

    @property
    def text(self) -> str:
        return self._resp.get_data(as_text=True)

    @property
    def content(self) -> bytes:
        return self._resp.get_data(as_text=False)

    @property
    def data(self) -> bytes:
        return self._resp.data

    @property
    def json(self):
        raw_json = self._resp.json
        return _make_callable_json(raw_json)

    @property
    def cookies(self) -> ResponseCookies:
        if self._parsed_cookies is None:
            c = ResponseCookies()
            for header in self.headers.getlist("Set-Cookie"):
                sc = SimpleCookie()
                sc.load(header)
                for k, m in sc.items():
                    c[k] = m.value
            self._parsed_cookies = c
        return self._parsed_cookies


class CookieJarProxy:
    def __init__(self, flask_client):
        self._client = flask_client

    def set(self, key: str, value: str, **kwargs):
        self._client.set_cookie(key=key, value=value, **kwargs)

    def get(self, key: str, default: Any = None) -> Any:
        cookie = self._client.get_cookie(key)
        return cookie.value if cookie else default

    def clear(self):
        self._client.cookie_jar.clear()


class TestClient:
    __test__ = False

    def __init__(self, app, base_url: str = "http://testserver", raise_server_exceptions: bool = True):
        self.app = app
        self.base_url = base_url
        self._flask_client = app.test_client()
        self.cookies = CookieJarProxy(self._flask_client)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if "params" in kwargs:
            kwargs["query_string"] = kwargs.pop("params")
        return kwargs

    def get(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.get(url, *args, **kwargs))

    def post(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.post(url, *args, **kwargs))

    def put(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.put(url, *args, **kwargs))

    def patch(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.patch(url, *args, **kwargs))

    def delete(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.delete(url, *args, **kwargs))

    def options(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.options(url, *args, **kwargs))

    def head(self, url: str, *args, **kwargs) -> TestResponseWrapper:
        kwargs = self._prepare_kwargs(kwargs)
        return TestResponseWrapper(self._flask_client.head(url, *args, **kwargs))
