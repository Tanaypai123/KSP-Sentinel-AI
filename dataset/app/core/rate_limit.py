"""FastAPI Rate Limiting Middleware.

Implements client-IP sliding window rate limiting. Kept disabled by default,
can be enabled in configs or main.py.
"""

from __future__ import annotations

import time
from typing import Dict, List, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window IP rate limiter middleware."""

    def __init__(
        self,
        app: Any,
        enabled: bool = False,
        rate_limit: int = 100,
        window_seconds: int = 60
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.rate_limit = rate_limit
        self.window = window_seconds
        self.requests: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if not self.enabled:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Initialize and clean old entries in sliding window
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < self.window
        ]

        if len(self.requests[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Too Many Requests",
                    "message": "API rate limit exceeded. Please retry later.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "timestamp": str(int(time.time()))
                }
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
