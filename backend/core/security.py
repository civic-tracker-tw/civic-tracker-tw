"""
CivicTracker TW - Cybersecurity Hardening Module
Thread-safe Rate Limiting, OWASP Security Headers, Request Sanitization,
and Timing-Attack-Resistant Authentication Verification.
"""

import hmac
import os
import re
import threading
import time
from typing import Dict, Optional, Tuple

MAX_POST_BODY_BYTES: int = 65536  # 64 KB limit to prevent memory exhaustion / DoS
DEFAULT_ADMIN_TOKEN: str = "dev-admin-token-change-me"


class SecurityHeaders:
    """OWASP-recommended HTTP security headers."""

    HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    @classmethod
    def apply(cls, handler) -> None:
        """Applies security headers to an BaseHTTPRequestHandler instance."""
        for header, value in cls.HEADERS.items():
            handler.send_header(header, value)


class RateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter per client IP.
    Default: 120 requests per 60 seconds.
    """

    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, client_ip: str) -> Tuple[bool, int, int]:
        """
        Checks whether client_ip is allowed to make a request.
        Returns:
            (allowed: bool, remaining_requests: int, retry_after_sec: int)
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = self._requests.get(client_ip, [])
            # Filter out timestamps outside the active window
            active_timestamps = [t for t in timestamps if t > window_start]

            if len(active_timestamps) >= self.max_requests:
                # Calculate wait time until the oldest request leaves the window
                oldest_in_window = active_timestamps[0]
                retry_after = max(1, int(oldest_in_window + self.window_seconds - now))
                self._requests[client_ip] = active_timestamps
                return False, 0, retry_after

            # Allowed: record request
            active_timestamps.append(now)
            self._requests[client_ip] = active_timestamps
            remaining = self.max_requests - len(active_timestamps)
            return True, remaining, 0

    def reset(self) -> None:
        """Clears all stored rate limiting data."""
        with self._lock:
            self._requests.clear()


class InputSanitizer:
    """Sanitizes user input to mitigate XSS, control-character injection, and DoS."""

    # Disallow ASCII control characters (0-31 and 127) except tab/newline if needed
    _CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f]")

    @classmethod
    def sanitize_query_string(cls, query_str: Optional[str], max_len: int = 120) -> str:
        """
        Strips non-printable control characters and enforces length limits on query parameters.
        """
        if not query_str or not isinstance(query_str, str):
            return ""
        # Remove control characters
        cleaned = cls._CONTROL_CHAR_REGEX.sub("", query_str).strip()
        # Cap length
        return cleaned[:max_len]


def verify_admin_token(provided_token: Optional[str]) -> bool:
    """
    Timing-attack-resistant token verification using hmac.compare_digest.
    Compares against CIVIC_ADMIN_TOKEN environment variable.
    """
    if not provided_token or not isinstance(provided_token, str):
        return False

    expected_token = os.environ.get("CIVIC_ADMIN_TOKEN", DEFAULT_ADMIN_TOKEN)

    # Use constant-time comparison
    return hmac.compare_digest(
        provided_token.encode("utf-8"),
        expected_token.encode("utf-8"),
    )


# Global Singleton Rate Limiter
_GLOBAL_RATE_LIMITER: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _GLOBAL_RATE_LIMITER
    if _GLOBAL_RATE_LIMITER is None:
        _GLOBAL_RATE_LIMITER = RateLimiter(max_requests=120, window_seconds=60)
    return _GLOBAL_RATE_LIMITER
