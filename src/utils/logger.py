"""
Logging configuration and utilities.
Provides structured logging with optional seed masking.
"""

import copy
import logging
import sys
from datetime import datetime
from typing import Optional

from src.config import AppConfig, LOGS_DIR


# Valid BIP39 seed phrase lengths
VALID_SEED_LENGTHS = {12, 15, 18, 21, 24}


class MaskedValue:
    """
    Wrapper class for values that should be masked in logs.
    Use this to explicitly mark sensitive values like seed phrases.
    
    Example:
        logger.info(f"Generated seed: {MaskedValue(seed)}")
    """
    
    def __init__(self, value: str):
        """
        Initialize masked value.
        
        Args:
            value: The sensitive value to mask
        """
        self.value = value
    
    def __str__(self) -> str:
        """Return masked representation."""
        return self._mask_seed_phrase(self.value)
    
    def __repr__(self) -> str:
        """Return masked representation."""
        return f"MaskedValue('{self.__str__()}')"
    
    @staticmethod
    def _mask_seed_phrase(seed: str) -> str:
        """
        Mask a seed phrase, showing only first 2 and last 2 words.
        
        Args:
            seed: Seed phrase string
            
        Returns:
            Masked seed phrase
        """
        words = seed.split()
        if len(words) <= 4:
            return seed  # Too short to mask meaningfully
        
        # Show first 2 and last 2 words, mask the rest
        masked = words[:2] + ["****"] * (len(words) - 4) + words[-2:]
        return " ".join(masked)


class SeedMaskingFilter(logging.Filter):
    """
    Logging filter that masks seed phrases for security.
    Only shows first 2 and last 2 words of seed phrases.
    
    Supports explicit masking via MaskedValue wrapper and heuristic
    detection for BIP39 seed phrases (12, 15, 18, 21, or 24 words).
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.enabled and hasattr(record, 'msg'):
            # Handle MaskedValue instances explicitly
            if isinstance(record.msg, MaskedValue):
                record.msg = str(record.msg)
            else:
                record.msg = self._mask_seed(str(record.msg))
        return True
    
    def _mask_seed(self, message: str) -> str:
        """
        Attempt to mask seed phrases in the message.
        
        Uses conservative heuristics:
        - Requires "seed" keyword in message (case-insensitive)
        - Only checks for valid BIP39 lengths (12, 15, 18, 21, 24 words)
        - All words must be lowercase alphabetic
        - More specific matching to reduce false positives
        
        Args:
            message: Log message to process
            
        Returns:
            Message with seed phrases masked if detected
        """
        # Only process if message contains "seed" keyword
        if "seed" not in message.lower():
            return message
        
        words = message.split()
        
        # Check for each valid seed length
        for seed_length in sorted(VALID_SEED_LENGTHS, reverse=True):
            if len(words) < seed_length:
                continue
            
            # Try to find a sequence of the exact seed length
            for i in range(len(words) - seed_length + 1):
                potential_seed = words[i:i+seed_length]
                
                # Check if all words are lowercase alphabetic (BIP39 words are lowercase)
                if all(w.isalpha() and w.islower() and len(w) >= 3 for w in potential_seed):
                    # Mask the seed phrase
                    masked = potential_seed[:2] + ["****"] * (seed_length - 4) + potential_seed[-2:]
                    words[i:i+seed_length] = masked
                    # Only mask the first match to avoid over-masking
                    break
        
        return " ".join(words)


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colored output for terminal.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, fmt: str, use_colors: bool = True):
        super().__init__(fmt)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors, without mutating the original record.
        
        Creates a copy of the record to avoid side effects on other handlers.
        """
        if self.use_colors and record.levelname in self.COLORS:
            # Create a copy to avoid mutating the original record
            # This prevents side effects on other handlers processing the same record
            record = copy.copy(record)
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    config: Optional[AppConfig] = None,
    log_level: str = "INFO",
    log_file: bool = True,
    log_console: bool = True,
    mask_seed: bool = True,
) -> logging.Logger:
    """
    Setup application logging.
    
    Args:
        config: Application configuration
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Enable file logging
        log_console: Enable console logging
        mask_seed: Enable seed phrase masking
        
    Returns:
        Root logger instance
    """
    if config:
        log_level = config.logging.level
        log_file = config.logging.file_enabled
        log_console = config.logging.console_enabled
        mask_seed = config.logging.mask_seed
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Add seed masking filter
    seed_filter = SeedMaskingFilter(enabled=mask_seed)
    
    # Console handler
    if log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(
            ColoredFormatter(log_format, use_colors=True)
        )
        console_handler.addFilter(seed_filter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        logs_dir = config.logs_dir if config else LOGS_DIR
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = logs_dir / f"denigmacracker_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        file_handler.addFilter(seed_filter)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"Logging to file: {log_file_path}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
