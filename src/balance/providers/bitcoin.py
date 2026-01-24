"""
Bitcoin balance provider using Blockchain.info API.
"""

import logging

from .base import BalanceProvider, BalanceProviderError
from src.wallet.models import Chain


logger = logging.getLogger(__name__)


class BitcoinProvider(BalanceProvider):
    """
    Bitcoin balance provider using Blockchain.info API.
    
    API Documentation: https://www.blockchain.com/api/blockchain_api
    """
    
    SATOSHI_PER_BTC = 100_000_000
    
    def __init__(
        self,
        api_url: str = "https://blockchain.info",
        rate_limit: int = 10,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(
            api_url=api_url,
            api_key=None,  # Blockchain.info doesn't require API key
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
        )
    
    @property
    def chain(self) -> Chain:
        return Chain.BITCOIN
    
    @property
    def name(self) -> str:
        return "Blockchain.info"
    
    def _build_url(self, address: str) -> str:
        """Build Blockchain.info API URL for balance check."""
        return f"{self.api_url}/balance?active={address}"
    
    def _parse_response(self, data: dict) -> float:
        """
        Parse Blockchain.info API response.
        
        Response format:
        {
            "address": {
                "final_balance": balance_in_satoshi,
                "n_tx": number_of_transactions,
                "total_received": total_received_satoshi
            }
        }
        
        Note: The address is included in the data dict under the "_address" key
        to maintain compatibility with the base class interface.
        """
        # Check for API error response
        if "error" in data:
            raise BalanceProviderError(f"API error: {data['error']}")
        
        # Extract address from data (added by get_balance before calling this method)
        address = data.get("_address")
        if not address:
            raise BalanceProviderError("Address not found in response data")
        
        if address not in data:
            # Log available keys for debugging
            logger.debug(f"Response keys: {list(data.keys())}, expected: {address}")
            raise BalanceProviderError(f"Address {address[:10]}... not found in response")
        
        try:
            balance_satoshi = data[address]["final_balance"]
            return balance_satoshi / self.SATOSHI_PER_BTC
        except (KeyError, TypeError) as e:
            raise BalanceProviderError(f"Failed to parse balance: {e}")
    
    async def get_balance(self, address: str) -> float:
        """
        Get BTC balance for an address.
        
        Args:
            address: Bitcoin address
            
        Returns:
            Balance in BTC
        """
        url = self._build_url(address)
        data = await self._make_request(url)
        # Include address in data dict to maintain interface compatibility
        data["_address"] = address
        return self._parse_response(data)
    
    async def get_multi_balance(self, addresses: list[str]) -> dict[str, float]:
        """
        Get BTC balance for multiple addresses in a single request.
        
        Args:
            addresses: List of Bitcoin addresses
            
        Returns:
            Dictionary mapping addresses to balances
        """
        if not addresses:
            return {}
        
        # Blockchain.info supports multiple addresses separated by |
        address_str = "|".join(addresses)
        url = f"{self.api_url}/balance?active={address_str}"
        
        data = await self._make_request(url)
        
        result = {}
        for address in addresses:
            try:
                balance_satoshi = data[address]["final_balance"]
                result[address] = balance_satoshi / self.SATOSHI_PER_BTC
            except (KeyError, TypeError):
                result[address] = 0.0
        
        return result


class BlockstreamProvider(BalanceProvider):
    """
    Alternative Bitcoin provider using Blockstream API.
    Useful as fallback when Blockchain.info is rate limited.
    
    API Documentation: https://github.com/Blockstream/esplora/blob/master/API.md
    """
    
    SATOSHI_PER_BTC = 100_000_000
    
    def __init__(
        self,
        api_url: str = "https://blockstream.info/api",
        rate_limit: int = 10,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(
            api_url=api_url,
            api_key=None,
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
        )
    
    @property
    def chain(self) -> Chain:
        return Chain.BITCOIN
    
    @property
    def name(self) -> str:
        return "Blockstream"
    
    def _build_url(self, address: str) -> str:
        """Build Blockstream API URL for address info."""
        return f"{self.api_url}/address/{address}"
    
    def _parse_response(self, data: dict) -> float:
        """
        Parse Blockstream API response.
        
        Response contains chain_stats and mempool_stats
        """
        try:
            chain_stats = data.get("chain_stats", {})
            mempool_stats = data.get("mempool_stats", {})
            
            # Confirmed balance
            funded = chain_stats.get("funded_txo_sum", 0)
            spent = chain_stats.get("spent_txo_sum", 0)
            confirmed = funded - spent
            
            # Unconfirmed balance
            mempool_funded = mempool_stats.get("funded_txo_sum", 0)
            mempool_spent = mempool_stats.get("spent_txo_sum", 0)
            unconfirmed = mempool_funded - mempool_spent
            
            total_satoshi = confirmed + unconfirmed
            return total_satoshi / self.SATOSHI_PER_BTC
            
        except (KeyError, TypeError) as e:
            raise BalanceProviderError(f"Failed to parse balance: {e}")
    
    async def get_balance(self, address: str) -> float:
        """
        Get BTC balance for an address.
        
        Args:
            address: Bitcoin address
            
        Returns:
            Balance in BTC
        """
        url = self._build_url(address)
        data = await self._make_request(url)
        return self._parse_response(data)
