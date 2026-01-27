"""
Rate Limiter - Redis-based rate limiting with Trusted IP bypass
Protects API endpoints from abuse while allowing internal services to bypass limits
"""
import os
import logging
from ipaddress import ip_address, ip_network
from typing import Optional, Tuple
from functools import wraps

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .redis import get_redis

logger = logging.getLogger(__name__)


# Configuration
class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Global limits (per IP)
    GLOBAL_LIMIT = int(os.getenv("RATE_LIMIT_GLOBAL", "100"))  # requests
    GLOBAL_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Authenticated user limits (per user_id)
    AUTH_LIMIT = int(os.getenv("RATE_LIMIT_AUTH", "200"))  # requests
    AUTH_WINDOW = int(os.getenv("RATE_LIMIT_AUTH_WINDOW", "60"))  # seconds
    
    # Sensitive endpoint limits (stricter)
    SENSITIVE_LIMIT = int(os.getenv("RATE_LIMIT_SENSITIVE", "10"))  # requests
    SENSITIVE_WINDOW = int(os.getenv("RATE_LIMIT_SENSITIVE_WINDOW", "60"))  # seconds
    
    # Trusted IPs that bypass rate limiting (internal networks, VPS)
    TRUSTED_IPS = os.getenv(
        "TRUSTED_IPS", 
        "127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    ).split(",")
    
    # Enable/disable rate limiting
    ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"


def is_trusted_ip(client_ip: str) -> bool:
    """
    Check if an IP is in the trusted list (bypasses rate limiting)
    Used for internal services, benchmarks, and VPS-to-VPS communication
    """
    try:
        client = ip_address(client_ip)
        for trusted in RateLimitConfig.TRUSTED_IPS:
            trusted = trusted.strip()
            if not trusted:
                continue
            try:
                if "/" in trusted:
                    # It's a network (CIDR notation)
                    if client in ip_network(trusted, strict=False):
                        return True
                else:
                    # Single IP
                    if client == ip_address(trusted):
                        return True
            except ValueError:
                logger.warning(f"Invalid trusted IP/network: {trusted}")
                continue
        return False
    except ValueError:
        logger.warning(f"Invalid client IP: {client_ip}")
        return False


def get_client_ip(request: Request) -> str:
    """Extract real client IP from request, considering proxies"""
    # Check X-Forwarded-For header (set by Traefik/nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP in the list is the original client
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"


async def check_rate_limit(
    key: str,
    limit: int,
    window: int
) -> Tuple[bool, int, int]:
    """
    Check if a request is within rate limits using Redis sliding window
    
    Returns:
        Tuple of (is_allowed, current_count, time_until_reset)
    """
    import time
    
    redis = await get_redis()
    now = int(time.time())
    window_start = now - window
    
    # Redis key for this rate limit bucket
    rate_key = f"ratelimit:{key}"
    
    # Use a transaction for atomic operations
    async with redis.pipeline(transaction=True) as pipe:
        try:
            # Remove old entries outside the window
            await pipe.zremrangebyscore(rate_key, 0, window_start)
            
            # Count current requests in window
            await pipe.zcard(rate_key)
            
            # Execute the pipeline
            results = await pipe.execute()
            current_count = results[1]
            
            if current_count >= limit:
                # Over limit - calculate reset time
                oldest = await redis.zrange(rate_key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1]) + window - now
                else:
                    reset_time = window
                return False, current_count, reset_time
            
            # Add this request to the window
            await redis.zadd(rate_key, {f"{now}:{id(now)}": now})
            await redis.expire(rate_key, window + 1)
            
            return True, current_count + 1, 0
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis fails
            return True, 0, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for global rate limiting
    Applies to all requests unless from trusted IPs
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip if disabled
        if not RateLimitConfig.ENABLED:
            return await call_next(request)
        
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Skip rate limiting for trusted IPs (internal services, benchmarks)
        if is_trusted_ip(client_ip):
            logger.debug(f"Trusted IP bypass: {client_ip}")
            return await call_next(request)
        
        # Check global rate limit by IP
        is_allowed, count, reset_time = await check_rate_limit(
            key=f"ip:{client_ip}",
            limit=RateLimitConfig.GLOBAL_LIMIT,
            window=RateLimitConfig.GLOBAL_WINDOW
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} ({count} requests)")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": reset_time
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(RateLimitConfig.GLOBAL_LIMIT),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time)
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RateLimitConfig.GLOBAL_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(RateLimitConfig.GLOBAL_LIMIT - count)
        
        return response


def rate_limit(
    limit: Optional[int] = None,
    window: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """
    Decorator for endpoint-specific rate limiting
    
    Usage:
        @router.post("/sensitive")
        @rate_limit(limit=5, window=60)
        async def sensitive_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")
            
            if request and RateLimitConfig.ENABLED:
                client_ip = get_client_ip(request)
                
                # Skip for trusted IPs
                if not is_trusted_ip(client_ip):
                    # Generate rate limit key
                    if key_func:
                        key = key_func(request)
                    else:
                        key = f"endpoint:{request.url.path}:{client_ip}"
                    
                    is_allowed, count, reset_time = await check_rate_limit(
                        key=key,
                        limit=limit or RateLimitConfig.SENSITIVE_LIMIT,
                        window=window or RateLimitConfig.SENSITIVE_WINDOW
                    )
                    
                    if not is_allowed:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Too many requests. Retry after {reset_time} seconds.",
                            headers={"Retry-After": str(reset_time)}
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for common limits
def sensitive_endpoint(func):
    """Apply strict rate limiting for sensitive endpoints"""
    return rate_limit(
        limit=RateLimitConfig.SENSITIVE_LIMIT,
        window=RateLimitConfig.SENSITIVE_WINDOW
    )(func)
