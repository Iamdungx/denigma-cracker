"""
Data models for wallet operations.
Uses dataclasses and enums for type safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Chain(Enum):
    """Supported blockchain networks."""
    
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    BNB = "bnb"
    LITECOIN = "litecoin"
    TRON = "tron"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def symbol(self) -> str:
        """Get the currency symbol for the chain."""
        symbols = {
            Chain.BITCOIN: "BTC",
            Chain.ETHEREUM: "ETH",
            Chain.BNB: "BNB",
            Chain.LITECOIN: "LTC",
            Chain.TRON: "TRX",
        }
        return symbols.get(self, self.value.upper())


class DerivationPath(Enum):
    """BIP derivation path standards."""
    
    BIP44 = "m/44'"  # Legacy
    BIP49 = "m/49'"  # SegWit compatible
    BIP84 = "m/84'"  # Native SegWit
    
    def __str__(self) -> str:
        return self.value


@dataclass
class WalletInfo:
    """Information about a generated wallet."""
    
    chain: Chain
    address: str
    derivation_path: str
    balance: float = 0.0
    balance_checked: bool = False
    error: Optional[str] = None
    
    @property
    def has_balance(self) -> bool:
        """Check if wallet has any balance."""
        return self.balance > 0
    
    @property
    def status(self) -> str:
        """Get human-readable status."""
        if self.error:
            return f"Error: {self.error}"
        if not self.balance_checked:
            return "Pending"
        if self.has_balance:
            return f"Found: {self.balance} {self.chain.symbol}"
        return "Empty"


@dataclass
class ScanResult:
    """Result of a wallet scan operation."""
    
    seed: str
    wallets: list[WalletInfo] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    scan_duration_ms: float = 0.0
    
    @property
    def has_any_balance(self) -> bool:
        """Check if any wallet has balance."""
        return any(w.has_balance for w in self.wallets)
    
    @property
    def total_wallets(self) -> int:
        """Get total number of wallets checked."""
        return len(self.wallets)
    
    @property
    def wallets_with_balance(self) -> list[WalletInfo]:
        """Get wallets that have balance."""
        return [w for w in self.wallets if w.has_balance]
    
    @property
    def masked_seed(self) -> str:
        """Get seed with middle words masked for security."""
        words = self.seed.split()
        if len(words) <= 4:
            return self.seed
        # Show first 2 and last 2 words
        masked = words[:2] + ["****"] * (len(words) - 4) + words[-2:]
        return " ".join(masked)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "seed": self.seed,
            "masked_seed": self.masked_seed,
            "timestamp": self.timestamp.isoformat(),
            "scan_duration_ms": self.scan_duration_ms,
            "wallets": [
                {
                    "chain": w.chain.value,
                    "address": w.address,
                    "derivation_path": w.derivation_path,
                    "balance": w.balance,
                    "symbol": w.chain.symbol,
                }
                for w in self.wallets
            ],
        }


@dataclass
class ScanStatistics:
    """Statistics for scanning session."""
    
    total_scanned: int = 0
    wallets_found: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def scan_rate(self) -> float:
        """Get scans per second."""
        elapsed = self.elapsed_seconds
        if elapsed == 0:
            return 0.0
        return self.total_scanned / elapsed
    
    def increment_scanned(self) -> None:
        """Increment scanned counter."""
        self.total_scanned += 1
    
    def increment_found(self) -> None:
        """Increment found counter."""
        self.wallets_found += 1
    
    def increment_errors(self) -> None:
        """Increment error counter."""
        self.errors += 1
