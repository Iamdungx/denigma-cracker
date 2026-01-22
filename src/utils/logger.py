"""
Logging configuration and utilities.
Provides structured logging with optional seed masking.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import AppConfig, LOGS_DIR


class SeedMaskingFilter(logging.Filter):
    """
    Logging filter that masks seed phrases for security.
    Only shows first 2 and last 2 words of seed phrases.
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.enabled and hasattr(record, 'msg'):
            record.msg = self._mask_seed(str(record.msg))
        return True
    
    def _mask_seed(self, message: str) -> str:
        """Attempt to mask seed phrases in the message."""
        # Simple heuristic: look for sequences of 12+ words
        words = message.split()
        
        # Check if this looks like a seed phrase log
        if "seed" in message.lower() and len(words) >= 12:
            # Try to identify and mask the seed portion
            for i in range(len(words) - 11):
                potential_seed = words[i:i+12]
                # If all words are lowercase and alphabetic, likely a seed
                if all(w.isalpha() and w.islower() for w in potential_seed):
                    masked = potential_seed[:2] + ["****"] * 8 + potential_seed[-2:]
                    words[i:i+12] = masked
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
        if self.use_colors and record.levelname in self.COLORS:
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
