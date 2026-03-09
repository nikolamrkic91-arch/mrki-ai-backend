"""
Mrki API Middleware
===================

Authentication, rate limiting, and request tracking middleware.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict
from typing import Callable, Optional

import base64
import hmac
import json

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, HTTPBearer
from pydantic import BaseModel
import structlog

logger = structlog.get_logger("mrki.api.middleware")

# =============================================================================
# Configuration
# =============================================================================

SECRET_KEY = os.getenv("MRKI_SECRET_KEY", "change-this-in-production")
JWT_ALGORITHM = os.getenv("MRKI_JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("MRKI_JWT_EXPIRATION", "3600"))
API_KEY_HEADER = os.getenv("MRKI_API_KEY_HEADER", "X-API-Key")

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


# =============================================================================
# Auth Models
# =============================================================================

class TokenData(BaseModel):
    sub: str
    exp: float
    role: str = "user"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# =============================================================================
# JWT Utilities
# =============================================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * padding)


def create_access_token(subject: str, role: str = "user", expires_delta: Optional[int] = None) -> str:
    """Create a JWT access token using HMAC-SHA256."""
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    expire = time.time() + (expires_delta or JWT_EXPIRATION)
    payload_data = {"sub": subject, "exp": expire, "role": role, "iat": time.time()}
    payload = _b64url_encode(json.dumps(payload_data).encode())
    signature = hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), "sha256").digest()
    return f"{header}.{payload}.{_b64url_encode(signature)}"


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), "sha256").digest()
        if not hmac.compare_digest(_b64url_decode(sig), expected_sig):
            return None
        payload_data = json.loads(_b64url_decode(payload))
        if payload_data.get("exp", 0) < time.time():
            return None
        return TokenData(**payload_data)
    except Exception:
        return None


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = os.getenv("MRKI_SECRET_KEY", "default-salt")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


# =============================================================================
# API Key Validation
# =============================================================================

# In production, load valid API keys from database or config
_VALID_API_KEYS: set[str] = set()


def _load_api_keys():
    """Load API keys from environment."""
    keys_str = os.getenv("MRKI_API_KEYS", "")
    if keys_str:
        for key in keys_str.split(","):
            key = key.strip()
            if key:
                _VALID_API_KEYS.add(key)


_load_api_keys()


def validate_api_key(api_key: str) -> bool:
    """Validate an API key."""
    if not _VALID_API_KEYS:
        # If no API keys configured, accept any non-empty key in dev mode
        dev_mode = os.getenv("MRKI_SERVER_DEBUG", "false").lower() == "true"
        if dev_mode:
            return bool(api_key)
        return False
    return api_key in _VALID_API_KEYS


# =============================================================================
# Authentication Middleware
# =============================================================================

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/",
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}

# Path prefixes that don't require authentication
PUBLIC_PREFIXES = (
    "/docs",
    "/redoc",
    "/static",
    "/favicon",
)


class AuthMiddleware:
    """Authentication middleware supporting JWT and API key auth."""

    async def __call__(self, request: Request, call_next: Callable):
        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # Skip auth for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if auth is disabled (development mode)
        auth_enabled = os.getenv("MRKI_AUTH_ENABLED", "true").lower() == "true"
        if not auth_enabled:
            return await call_next(request)

        # Try API key auth first
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key and validate_api_key(api_key):
            request.state.user = {"sub": "api_key_user", "role": "admin"}
            return await call_next(request)

        # Try Bearer token auth
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            token_data = verify_token(token)
            if token_data:
                request.state.user = {"sub": token_data.sub, "role": token_data.role}
                return await call_next(request)

        # No valid auth found
        logger.warning("auth_failed", path=path, method=request.method)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Unauthorized", "detail": "Valid authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Rate Limiting Middleware
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, requests_per_window: int = 100, window_seconds: int = 60):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """Get a unique identifier for the client."""
        # Use API key if present, otherwise use IP
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key:
            return f"key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _clean_old_requests(self, client_id: str, now: float) -> None:
        """Remove requests outside the current window."""
        cutoff = now - self.window_seconds
        self._requests[client_id] = [
            ts for ts in self._requests[client_id] if ts > cutoff
        ]

    def is_rate_limited(self, request: Request) -> tuple[bool, dict]:
        """Check if request should be rate limited. Returns (limited, headers)."""
        now = time.time()
        client_id = self._get_client_id(request)

        self._clean_old_requests(client_id, now)

        current_count = len(self._requests[client_id])
        remaining = max(0, self.requests_per_window - current_count)
        reset_time = int(now + self.window_seconds)

        headers = {
            "X-RateLimit-Limit": str(self.requests_per_window),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if current_count >= self.requests_per_window:
            return True, headers

        self._requests[client_id].append(now)
        return False, headers


class RateLimitMiddleware:
    """Rate limiting middleware."""

    def __init__(self, requests_per_window: int = 100, window_seconds: int = 60):
        self.limiter = RateLimiter(requests_per_window, window_seconds)

    async def __call__(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/api/v1/health"):
            return await call_next(request)

        # Check if rate limiting is enabled
        enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        if not enabled:
            return await call_next(request)

        limited, headers = self.limiter.is_rate_limited(request)

        if limited:
            logger.warning(
                "rate_limited",
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Max {self.limiter.requests_per_window} requests per {self.limiter.window_seconds}s window.",
                },
            )
            for key, value in headers.items():
                response.headers[key] = value
            return response

        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value
        return response
