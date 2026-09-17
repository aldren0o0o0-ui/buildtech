"""
Application exceptions module.
Provides HTTPException with status_code, detail, and headers for JSON error handling.
"""
from typing import Any, Dict, Optional


class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(str(detail))
