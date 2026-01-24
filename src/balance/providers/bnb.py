"""
BNB Smart Chain balance provider using BscScan API.
"""

import logging

from .base import BalanceProvider, BalanceProviderError
from src.wallet.models import Chain


logger = logging.getLogger(__name__)


class BNBProvider(BalanceProvider):
    """
    BNB Smart Chain balance provider using BscScan API.
    
    API Documentation: https://docs.bscscan.com/api-endpoints/accounts
    """
    
    WEI_PER_BNB = 1e18
    
    def __init__(
        self,
        api_key: str = "",
        api_url: str = "https://api.bscscan.com/api",
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
            logger.warning("BscScan API key not provided. Rate limits will be strict.")
    
    @property
    def chain(self) -> Chain:
        return Chain.BNB
    
    @property
    def name(self) -> str:
        return "BscScan"
    
    def _build_url(self, address: str) -> str:
        """Build BscScan API URL for balance check."""
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
        Parse BscScan API response.
        
        Response format (same as Etherscan):
        {
            "status": "1",
            "message": "OK",
            "result": "balance_in_wei"
        }
        """
        if data.get("status") != "1":
            message = data.get("message", "Unknown error")
            result = data.get("result", "")
            raise BalanceProviderError(f"API error: {message} - {result}")
        
        try:
            balance_wei = int(data["result"])
            return balance_wei / self.WEI_PER_BNB
        except (KeyError, ValueError) as e:
            raise BalanceProviderError(f"Failed to parse balance: {e}")
    
    async def get_balance(self, address: str) -> float:
        """
        Get BNB balance for an address.
        
        Args:
            address: BSC address (0x...)
            
        Returns:
            Balance in BNB
        """
        url = self._build_url(address)
        data = await self._make_request(url)
        return self._parse_response(data)
    
    async def get_bep20_balance(
        self,
        address: str,
        contract_address: str,
    ) -> float:
        """
        Get BEP-20 token balance for an address.
        
        Args:
            address: Wallet address
            contract_address: Token contract address
            
        Returns:
            Token balance
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
