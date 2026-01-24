"""
Rate limiting utilities for API calls.
Implements token bucket algorithm for smooth rate limiting.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter for async operations.
    
    Ensures requests don't exceed the specified rate limit.
    """
    
    rate: float  # requests per second
    burst: int = 1  # max burst size
    _tokens: float = field(init=False)
    _last_update: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)
    
    def __post_init__(self):
        self._tokens = float(self.burst)
        self._last_update = time.monotonic()
    
    async def acquire(self) -> None:
        """
        Acquire a token, waiting if necessary.
        
        This method will block until a token is available.
        """
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last_update
                self._last_update = now
                
                # Add tokens based on elapsed time
                self._tokens = min(
                    self.burst,
                    self._tokens + elapsed * self.rate
                )
                
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                
                # Calculate wait time for next token
                wait_time = (1 - self._tokens) / self.rate
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class MultiRateLimiter:
    """
    Manages multiple rate limiters for different providers.
    """
    
    def __init__(self):
        self._limiters: dict[str, RateLimiter] = {}
    
    def get_limiter(self, name: str, rate: float, burst: int = 1) -> RateLimiter:
        """
        Get or create a rate limiter for the given name.
        
        Args:
            name: Identifier for the rate limiter
            rate: Requests per second
            burst: Max burst size
            
        Returns:
            RateLimiter instance
        """
        if name not in self._limiters:
            self._limiters[name] = RateLimiter(rate=rate, burst=burst)
        return self._limiters[name]
    
    async def acquire(self, name: str) -> None:
        """Acquire a token from the named rate limiter."""
        if name in self._limiters:
            await self._limiters[name].acquire()


# Global rate limiter instance
_global_limiter = MultiRateLimiter()


def get_rate_limiter() -> MultiRateLimiter:
    """Get the global rate limiter instance."""
    return _global_limiter
