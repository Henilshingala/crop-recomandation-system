"""Custom middleware — rate limiting, API key validation."""

import logging
import time
from collections import defaultdict

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

_RATE_LIMIT_REQUESTS = 60
_RATE_LIMIT_WINDOW = 60  # seconds
_ip_timestamps: dict[str, list[float]] = defaultdict(list)


def _get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class ApiKeyMiddleware:
    """Validate X-API-Key header for /api/predict/ when API_KEYS is configured."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_keys = getattr(settings, "API_KEYS", None) or []
        if not api_keys:
            return self.get_response(request)

        if request.path.startswith("/api/predict"):
            key = request.META.get("HTTP_X_API_KEY", "").strip()
            if not key or key not in api_keys:
                return JsonResponse(
                    {"error": "Missing or invalid API key. Provide X-API-Key header."},
                    status=401,
                )
        return self.get_response(request)


class RateLimitMiddleware:
    """Limit /api/predict/ to 60 requests per minute per IP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/predict"):
            ip = _get_client_ip(request)
            now = time.monotonic()
            cutoff = now - _RATE_LIMIT_WINDOW

            timestamps = _ip_timestamps[ip]
            timestamps[:] = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= _RATE_LIMIT_REQUESTS:
                from django.http import JsonResponse
                response = JsonResponse(
                    {"error": "Too many requests. Try again later."},
                    status=429,
                )
                response["Retry-After"] = str(_RATE_LIMIT_WINDOW)
                return response
            timestamps.append(now)

        return self.get_response(request)
