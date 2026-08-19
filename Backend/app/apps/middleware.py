"""
Rate Limiting Middleware for Crop Recommendation API
===================================================
Simple rate limiting for small traffic applications.
"""

import time
import logging
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Simple rate limits for small traffic
RATE_LIMITS = {
    '/api/predict/': {'requests': 20, 'window': 60},   # 20 requests per minute
    '/api/crops/': {'requests': 100, 'window': 60},   # 100 requests per minute
    '/api/health/': {'requests': 1000, 'window': 60}, # 1000 requests per minute
    'default': {'requests': 60, 'window': 60},        # 60 requests per minute
}


class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for health checks from Render
        if request.path == '/api/health/' and 'render' in request.META.get('HTTP_USER_AGENT', '').lower():
            return self.get_response(request)
        
        # Get client IP
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', 'unknown')
        
        # Get rate limit configuration
        rate_config = self._get_rate_limit_config(request.path)
        
        # Check rate limit
        if self._is_rate_limited(ip, request.path, rate_config):
            logger.warning("Rate limit exceeded for IP %s on %s", ip, request.path)
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Maximum {rate_config["requests"]} requests per {rate_config["window"]} seconds.',
                'retry_after': rate_config["window"]
            }, status=429)
        
        return self.get_response(request)
    
    def _get_rate_limit_config(self, path):
        """Get rate limit configuration for the given path."""
        for pattern, config in RATE_LIMITS.items():
            if pattern != 'default' and path.startswith(pattern):
                return config
        return RATE_LIMITS['default']
    
    def _is_rate_limited(self, ip, path, config):
        """Check if the IP has exceeded the rate limit."""
        cache_key = f"rate_limit:{ip}:{path}"
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        try:
            # Get existing requests from cache
            requests = cache.get(cache_key, [])
            
            # Remove old requests outside the window
            requests = [req_time for req_time in requests if req_time > window_start]
            
            # Check if limit exceeded
            if len(requests) >= config['requests']:
                return True
            
            # Add current request
            requests.append(current_time)
            cache.set(cache_key, requests, config['window'])
            
        except Exception:
            # Fail open - if cache fails, don't block requests
            return False
        
        return False
