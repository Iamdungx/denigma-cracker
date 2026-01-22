"""
Base class for blockchain balance providers.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.wallet.models import Chain


logger = logging.getLogger(__name__)


class BalanceProviderError(Exception):
    """Base exception for balance provider errors."""
    pass


class RateLimitError(BalanceProviderError):
    """Raised when API rate limit is exceeded."""
    pass


class BalanceProvider(ABC):
    """
    Abstract base class for blockchain balance providers.
    All providers must implement this interface.
    """
    
    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        rate_limit: int = 5,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize balance provider.
        
        Args:
            api_url: Base URL for the API
            api_key: Optional API key for authentication
            rate_limit: Maximum requests per second
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    @abstractmethod
    def chain(self) -> Chain:
        """Get the blockchain chain this provider supports."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        pass
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    @abstractmethod
    async def get_balance(self, address: str) -> float:
        """
        Get the balance for an address.
        
        Args:
            address: Wallet address to check
            
        Returns:
            Balance in the native currency (e.g., ETH, BTC)
        """
        pass
    
    @abstractmethod
    def _build_url(self, address: str) -> str:
        """Build the API URL for balance check."""
        pass
    
    @abstractmethod
    def _parse_response(self, data: dict) -> float:
        """Parse the API response and extract balance."""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, TimeoutError)),
        reraise=True,
    )
    async def _make_request(self, url: str) -> dict:
        """
        Make an HTTP request with retry logic.
        
        Args:
            url: URL to request
            
        Returns:
            JSON response as dictionary
        """
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error from {self.name}: {e.status} - {e.message}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Request error from {self.name}: {e}")
            raise
    
    async def check_balance(self, address: str) -> tuple[float, Optional[str]]:
        """
        Check balance with error handling.
        
        Args:
            address: Wallet address to check
            
        Returns:
            Tuple of (balance, error_message)
        """
        try:
            balance = await self.get_balance(address)
            return balance, None
        except RateLimitError:
            return 0.0, "Rate limit exceeded"
        except Exception as e:
            logger.error(f"Error checking balance for {address}: {e}")
            return 0.0, str(e)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(chain={self.chain}, api_url={self.api_url})"
