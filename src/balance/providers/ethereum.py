"""
Ethereum balance provider using Etherscan API.
"""

import logging
from typing import Optional

from .base import BalanceProvider, BalanceProviderError
from src.wallet.models import Chain


logger = logging.getLogger(__name__)


class EthereumProvider(BalanceProvider):
    """
    Ethereum balance provider using Etherscan API.
    
    API Documentation: https://docs.etherscan.io/api-endpoints/accounts
    """
    
    WEI_PER_ETH = 1e18
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.etherscan.io/api",
        rate_limit: int = 5,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        if not api_key:
            logger.warning("Etherscan API key not provided. Rate limits will be strict.")
    
    @property
    def chain(self) -> Chain:
        return Chain.ETHEREUM
    
    @property
    def name(self) -> str:
        return "Etherscan"
    
    def _build_url(self, address: str) -> str:
        """Build Etherscan API URL for balance check."""
        params = [
            f"module=account",
            f"action=balance",
            f"address={address}",
            f"tag=latest",
        ]
        
        if self.api_key:
            params.append(f"apikey={self.api_key}")
        
        return f"{self.api_url}?{'&'.join(params)}"
    
    def _parse_response(self, data: dict) -> float:
        """
        Parse Etherscan API response.
        
        Response format:
        {
            "status": "1",
            "message": "OK",
            "result": "balance_in_wei"
        }
        """
        if data.get("status") != "1":
            message = data.get("message", "Unknown error")
            result = data.get("result", "")
            
            # Handle specific error cases
            if "Max rate limit reached" in str(result):
                raise BalanceProviderError("Rate limit exceeded")
            
            raise BalanceProviderError(f"API error: {message} - {result}")
        
        try:
            balance_wei = int(data["result"])
            return balance_wei / self.WEI_PER_ETH
        except (KeyError, ValueError) as e:
            raise BalanceProviderError(f"Failed to parse balance: {e}")
    
    async def get_balance(self, address: str) -> float:
        """
        Get ETH balance for an address.
        
        Args:
            address: Ethereum address (0x...)
            
        Returns:
            Balance in ETH
        """
        url = self._build_url(address)
        data = await self._make_request(url)
        return self._parse_response(data)
    
    async def get_token_balance(
        self,
        address: str,
        contract_address: str,
    ) -> float:
        """
        Get ERC-20 token balance for an address.
        
        Args:
            address: Wallet address
            contract_address: Token contract address
            
        Returns:
            Token balance (may need to adjust for decimals)
        """
        params = [
            f"module=account",
            f"action=tokenbalance",
            f"contractaddress={contract_address}",
            f"address={address}",
            f"tag=latest",
        ]
        
        if self.api_key:
            params.append(f"apikey={self.api_key}")
        
        url = f"{self.api_url}?{'&'.join(params)}"
        data = await self._make_request(url)
        
        if data.get("status") != "1":
            raise BalanceProviderError(f"API error: {data.get('message')}")
        
        return float(data["result"])
