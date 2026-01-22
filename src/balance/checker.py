"""
Balance checking orchestrator.
Manages multiple providers and handles async balance checking.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from .providers.base import BalanceProvider
from .providers.ethereum import EthereumProvider
from .providers.bitcoin import BitcoinProvider
from .providers.bnb import BNBProvider
from src.wallet.models import Chain, WalletInfo, ScanResult
from src.config import AppConfig


logger = logging.getLogger(__name__)


class BalanceChecker:
    """
    Orchestrates balance checking across multiple blockchain providers.
    Handles rate limiting and provider fallback.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize balance checker with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.providers: dict[Chain, BalanceProvider] = {}
        self._setup_providers()
    
    def _setup_providers(self) -> None:
        """Setup providers based on configuration."""
        # Ethereum
        if self.config.ethereum.enabled:
            self.providers[Chain.ETHEREUM] = EthereumProvider(
                api_key=self.config.ethereum.api_key,
                api_url=self.config.ethereum.api_url,
                rate_limit=self.config.ethereum.rate_limit,
                timeout=self.config.ethereum.timeout,
                max_retries=self.config.ethereum.max_retries,
            )
        
        # Bitcoin
        if self.config.bitcoin.enabled:
            self.providers[Chain.BITCOIN] = BitcoinProvider(
                api_url=self.config.bitcoin.api_url,
                rate_limit=self.config.bitcoin.rate_limit,
                timeout=self.config.bitcoin.timeout,
                max_retries=self.config.bitcoin.max_retries,
            )
        
        # BNB Smart Chain
        if self.config.bnb.enabled:
            self.providers[Chain.BNB] = BNBProvider(
                api_key=self.config.bnb.api_key,
                api_url=self.config.bnb.api_url,
                rate_limit=self.config.bnb.rate_limit,
                timeout=self.config.bnb.timeout,
                max_retries=self.config.bnb.max_retries,
            )
        
        logger.info(f"Initialized {len(self.providers)} balance providers")
    
    def get_provider(self, chain: Chain) -> Optional[BalanceProvider]:
        """Get the provider for a specific chain."""
        return self.providers.get(chain)
    
    def get_enabled_chains(self) -> list[Chain]:
        """Get list of chains with enabled providers."""
        return list(self.providers.keys())
    
    async def check_balance(self, wallet: WalletInfo) -> WalletInfo:
        """
        Check balance for a single wallet.
        
        Args:
            wallet: Wallet info to check
            
        Returns:
            Updated wallet info with balance
        """
        # Skip wallets with empty address (failed generation)
        if not wallet.address:
            error_msg = wallet.error or "Wallet generation failed - empty address"
            logger.debug(f"Skipping {wallet.chain} wallet: {error_msg}")
            wallet.error = error_msg
            wallet.balance_checked = True
            return wallet
        
        provider = self.get_provider(wallet.chain)
        
        if provider is None:
            wallet.error = f"No provider for chain {wallet.chain}"
            wallet.balance_checked = True
            return wallet
        
        try:
            balance, error = await provider.check_balance(wallet.address)
            wallet.balance = balance
            wallet.error = error
            wallet.balance_checked = True
            
            if balance > 0:
                logger.info(
                    f"Found balance! {wallet.chain.symbol}: {wallet.address} = {balance}"
                )
            
        except Exception as e:
            logger.error(f"Error checking {wallet.chain} balance: {e}")
            wallet.error = str(e)
            wallet.balance_checked = True
        
        return wallet
    
    async def check_balances(self, wallets: list[WalletInfo]) -> list[WalletInfo]:
        """
        Check balances for multiple wallets concurrently.
        
        Args:
            wallets: List of wallets to check
            
        Returns:
            List of updated wallets with balances
        """
        tasks = [self.check_balance(wallet) for wallet in wallets]
        return await asyncio.gather(*tasks)
    
    async def scan_seed(
        self,
        seed: str,
        wallets: list[WalletInfo],
    ) -> ScanResult:
        """
        Scan all wallets derived from a seed.
        
        Args:
            seed: BIP39 mnemonic seed
            wallets: List of derived wallets
            
        Returns:
            ScanResult with all wallet balances
        """
        start_time = datetime.now()
        
        # Check all balances concurrently
        checked_wallets = await self.check_balances(wallets)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return ScanResult(
            seed=seed,
            wallets=checked_wallets,
            scan_duration_ms=duration_ms,
        )
    
    async def close(self) -> None:
        """Close all provider connections."""
        for provider in self.providers.values():
            await provider.close()
        logger.info("Closed all balance providers")
    
    async def __aenter__(self) -> "BalanceChecker":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
