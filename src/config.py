"""
Configuration management using Pydantic Settings.
Supports environment variables, .env files, and YAML config.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


# Base directory for configuration files
BASE_DIR = Path(__file__).resolve().parent.parent


# Base paths
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"


class ChainConfig(BaseSettings):
    """Configuration for a specific blockchain."""
    
    enabled: bool = True
    rate_limit: int = 5  # requests per second
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: int = 5  # seconds


class EthereumConfig(ChainConfig):
    """Ethereum-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="ETH_",
        extra="ignore"
    )
    
    api_key: str = Field(default="", alias="ETHERSCAN_API_KEY")
    api_url: str = "https://api.etherscan.io/v2/api"
    
    @field_validator("api_key", mode="before")
    @classmethod
    def validate_etherscan_api_key(cls, v: str) -> str:
        """Validate and load Etherscan API key from environment if not set."""
        return v or os.getenv("ETHERSCAN_API_KEY", "")


class BitcoinConfig(ChainConfig):
    """Bitcoin-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="BTC_",
        extra="ignore"
    )
    
    api_url: str = "https://blockchain.info"


class BNBConfig(ChainConfig):
    """BNB Smart Chain configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="BNB_",
        extra="ignore"
    )
    
    api_key: str = Field(default="", alias="BSCSCAN_API_KEY")
    api_url: str = "https://api.bscscan.com/api"
    enabled: bool = False  # Disabled by default
    
    @field_validator("api_key", mode="before")
    @classmethod
    def validate_bscscan_api_key(cls, v: str) -> str:
        """Validate and load BscScan API key from environment if not set."""
        return v or os.getenv("BSCSCAN_API_KEY", "")


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="LOG_",
        extra="ignore"
    )
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True
    mask_seed: bool = True  # Mask seed phrases in logs for security


class ScannerConfig(BaseSettings):
    """Scanner-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="SCANNER_",
        extra="ignore"
    )
    
    workers: int = 4
    batch_size: int = 10
    save_progress: bool = True
    progress_file: str = "progress.json"


class NotificationConfig(BaseSettings):
    """Notification configuration for alerts."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_prefix="NOTIFY_",
        extra="ignore"
    )
    
    enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook_url: Optional[str] = None


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # App metadata
    app_name: str = "DEnigmaCracker"
    version: str = "2.0.0-beta"
    debug: bool = False
    
    # Paths
    output_dir: Path = OUTPUT_DIR
    logs_dir: Path = LOGS_DIR
    
    # Sub-configurations
    ethereum: EthereumConfig = Field(default_factory=EthereumConfig)
    bitcoin: BitcoinConfig = Field(default_factory=BitcoinConfig)
    bnb: BNBConfig = Field(default_factory=BNBConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "AppConfig":
        """Load configuration from a YAML file."""
        if not yaml_path.exists():
            return cls()
        
        with open(yaml_path, "r") as f:
            yaml_config = yaml.safe_load(f) or {}
        
        return cls(**yaml_config)
    
    def get_enabled_chains(self) -> list[str]:
        """Get list of enabled blockchain chains."""
        chains = []
        if self.ethereum.enabled:
            chains.append("ethereum")
        if self.bitcoin.enabled:
            chains.append("bitcoin")
        if self.bnb.enabled:
            chains.append("bnb")
        return chains


@lru_cache()
def get_config() -> AppConfig:
    """
    Get cached application configuration.
    Uses lru_cache to ensure singleton pattern.
    """
    # Try to load from YAML first, then fall back to env
    yaml_path = ASSETS_DIR / "config.yaml"
    if yaml_path.exists():
        return AppConfig.from_yaml(yaml_path)
    return AppConfig()


# Convenience function
def load_config() -> AppConfig:
    """Load and return application configuration."""
    return get_config()
