"""
Output management for scan results.
Handles file output, progress saving, and notifications.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from src.wallet.models import ScanResult, ScanStatistics
from src.config import AppConfig


logger = logging.getLogger(__name__)


class OutputManager:
    """
    Manages output operations for scan results.
    Handles file writing, progress tracking, and optional notifications.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize output manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Output files
        self.wallets_file = self.output_dir / "wallets_with_balance.txt"
        self.results_json = self.output_dir / "results.json"
        self.progress_file = self.output_dir / config.scanner.progress_file
        
        # Statistics
        self.stats = ScanStatistics()
    
    def save_result(self, result: ScanResult) -> None:
        """
        Save a scan result with balance.
        
        Args:
            result: Scan result to save
        """
        if not result.has_any_balance:
            return
        
        # Update statistics
        self.stats.increment_found()
        
        # Write to text file (human readable)
        self._write_text_result(result)
        
        # Write to JSON file (machine readable)
        self._write_json_result(result)
        
        logger.info(f"Saved result with balance to {self.wallets_file}")
    
    def _write_text_result(self, result: ScanResult) -> None:
        """Write result in human-readable text format."""
        with open(self.wallets_file, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Timestamp: {result.timestamp.isoformat()}\n")
            f.write(f"Seed: {result.seed}\n")
            f.write("-" * 40 + "\n")
            
            for wallet in result.wallets_with_balance:
                f.write(f"  Chain: {wallet.chain.value}\n")
                f.write(f"  Address: {wallet.address}\n")
                f.write(f"  Balance: {wallet.balance} {wallet.chain.symbol}\n")
                f.write(f"  Path: {wallet.derivation_path}\n")
                f.write("-" * 40 + "\n")
            
            f.write("\n")
    
    def _write_json_result(self, result: ScanResult) -> None:
        """Write result in JSON format."""
        # Load existing results or create new list
        results = []
        if self.results_json.exists():
            try:
                with open(self.results_json, "r", encoding="utf-8") as f:
                    results = json.load(f)
            except json.JSONDecodeError:
                results = []
        
        # Add new result
        results.append(result.to_dict())
        
        # Write back
        with open(self.results_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def save_progress(self, scanned: int, found: int) -> None:
        """
        Save scanning progress for resume capability.
        
        Args:
            scanned: Total wallets scanned
            found: Wallets with balance found
        """
        if not self.config.scanner.save_progress:
            return
        
        progress = {
            "scanned": scanned,
            "found": found,
            "last_update": datetime.now().isoformat(),
        }
        
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
    
    def load_progress(self) -> Optional[dict]:
        """
        Load previous progress if exists.
        
        Returns:
            Progress dict or None if not found
        """
        if not self.progress_file.exists():
            return None
        
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def get_statistics(self) -> ScanStatistics:
        """Get current scanning statistics."""
        return self.stats
    
    def update_statistics(
        self,
        scanned: int = 0,
        found: int = 0,
        errors: int = 0,
    ) -> None:
        """
        Update scanning statistics.
        
        Args:
            scanned: Number of wallets scanned
            found: Number of wallets with balance found
            errors: Number of errors
        """
        self.stats.total_scanned += scanned
        self.stats.wallets_found += found
        self.stats.errors += errors
    
    def print_summary(self) -> None:
        """Print scanning summary to console."""
        stats = self.stats
        
        # Format numbers with commas for readability
        scanned_str = f"{stats.total_scanned:,}"
        found_str = f"{stats.wallets_found:,}"
        errors_str = f"{stats.errors:,}"
        duration_str = f"{stats.elapsed_seconds:.1f}s"
        rate_str = f"{stats.scan_rate:.2f}/s"
        
        # Calculate dynamic width based on actual values to ensure proper alignment
        # Use a minimum width of 15 to handle large numbers gracefully
        value_width = max(
            15,
            len(scanned_str),
            len(found_str),
            len(errors_str),
            len(duration_str),
            len(rate_str),
        )
        
        # Label width (longest label is "Total Scanned:" = 14 chars)
        label_width = 14
        
        # Calculate table width: "║  " (3) + label + ": " (2) + value + " ║" (2)
        table_width = 3 + label_width + 2 + value_width + 2
        
        summary = f"""
╔{'═' * (table_width - 2)}╗
║{'SCAN SUMMARY':^{table_width - 2}}║
╠{'═' * (table_width - 2)}╣
║  {'Total Scanned:':<{label_width}} {scanned_str:>{value_width}} ║
║  {'Wallets Found:':<{label_width}} {found_str:>{value_width}} ║
║  {'Errors:':<{label_width}} {errors_str:>{value_width}} ║
║  {'Duration:':<{label_width}} {duration_str:>{value_width}} ║
║  {'Rate:':<{label_width}} {rate_str:>{value_width}} ║
╚{'═' * (table_width - 2)}╝
"""
        print(summary)
        logger.info(f"Scan complete. Scanned: {stats.total_scanned}, Found: {stats.wallets_found}")
