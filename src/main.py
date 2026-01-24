"""
DEnigmaCracker v2.0 - Main entry point.
A cryptocurrency wallet scanner for educational purposes.
"""

import asyncio
import signal
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from src import __version__
from src.config import load_config, AppConfig
from src.wallet import WalletGenerator, Chain, DerivationPath
from src.balance import BalanceChecker
from src.utils import setup_logging, get_logger, OutputManager


# Initialize Typer app and Rich console
app = typer.Typer(
    name="denigmacracker",
    help="DEnigmaCracker - Cryptocurrency wallet scanner for educational purposes.",
    add_completion=False,
)
console = Console()
logger = get_logger(__name__)

# Thread-safe event for graceful shutdown
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    shutdown_event.set()
    console.print("\n[yellow]Shutdown requested. Finishing current scan...[/yellow]")


def create_status_table(stats: dict) -> Table:
    """Create a status table for the live display."""
    table = Table(title="Scan Status", show_header=True, header_style="bold cyan")
    
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Scanned", f"{stats.get('scanned', 0):,}")
    table.add_row("Wallets Found", f"[green]{stats.get('found', 0)}[/green]")
    table.add_row("Errors", f"[red]{stats.get('errors', 0)}[/red]")
    table.add_row("Rate", f"{stats.get('rate', 0):.2f}/s")
    table.add_row("Elapsed", f"{stats.get('elapsed', 0):.0f}s")
    
    # Add separator row
    table.add_row("", "")
    
    # Add quit instruction
    table.add_row(
        "[dim]Quit[/dim]",
        "[yellow]Press Ctrl+C[/yellow]"
    )
    
    # Add author info
    table.add_row(
        "[dim]Author[/dim]",
        "[link=https://github.com/Iamdungx][bold bright_blue]@Iamdungx[/bold bright_blue][/link]"
    )
    
    return table


def create_chains_table(chains: list[str]) -> Table:
    """Create a table showing enabled chains."""
    table = Table(title="Enabled Chains", show_header=True, header_style="bold green")
    
    table.add_column("Chain", style="cyan")
    table.add_column("Status", justify="center")
    
    for chain in chains:
        table.add_row(chain.upper(), "[green]Active[/green]")
    
    return table


async def run_scanner(
    config: AppConfig,
    workers: int,
    chains: list[Chain],
    derivations: list[DerivationPath],
) -> None:
    """
    Run the main scanning loop with concurrent workers.
    
    Args:
        config: Application configuration
        workers: Number of concurrent workers
        chains: Blockchain chains to scan
        derivations: Derivation paths to use
    """
    # Initialize components
    output_manager = OutputManager(config)
    
    # Shared statistics with lock for thread-safe updates
    stats = {
        "scanned": 0,
        "found": 0,
        "errors": 0,
        "rate": 0.0,
        "elapsed": 0.0,
    }
    stats_lock = asyncio.Lock()
    
    start_time = time.time()
    
    async def worker_loop(worker_id: int, checker: BalanceChecker) -> None:
        """Worker loop that runs scanning tasks concurrently."""
        worker_generator = WalletGenerator(words_num=12)
        
        while not shutdown_event.is_set():
            try:
                # Generate mnemonic
                mnemonic = worker_generator.generate_mnemonic()
                
                # Derive wallets for all enabled chains
                wallets = worker_generator.derive_all_wallets(
                    mnemonic=mnemonic,
                    chains=chains,
                    derivations=derivations,
                )
                
                # Check balances
                result = await checker.scan_seed(mnemonic, wallets)
                
                # Update statistics atomically
                async with stats_lock:
                    stats["scanned"] += 1
                    stats["elapsed"] = time.time() - start_time
                    stats["rate"] = stats["scanned"] / max(stats["elapsed"], 1)
                    
                    if result.has_any_balance:
                        stats["found"] += 1
                        output_manager.save_result(result)
                        console.print(
                            f"[bold green]Found wallet with balance![/bold green] "
                            f"Seed: {result.masked_seed}"
                        )
                    
                    # Count errors
                    stats["errors"] += sum(1 for w in result.wallets if w.error)
                    
                    # Save progress periodically
                    if stats["scanned"] % 100 == 0:
                        output_manager.save_progress(stats["scanned"], stats["found"])
                
            except Exception as e:
                logger.error(f"Error in worker {worker_id} scan loop: {e}")
                async with stats_lock:
                    stats["errors"] += 1
                await asyncio.sleep(1)
    
    async with BalanceChecker(config) as checker:
        # Create worker tasks
        worker_tasks = [
            asyncio.create_task(worker_loop(worker_id, checker))
            for worker_id in range(workers)
        ]
        
        # Update display in a separate task
        async def update_display(live: Live):
            """Update the live display periodically."""
            while not shutdown_event.is_set():
                # Acquire lock to safely read stats (prevents race conditions)
                async with stats_lock:
                    # Create a copy of stats to avoid holding lock during display update
                    current_stats = stats.copy()
                
                layout = Layout()
                layout.split_column(
                    Layout(Panel(
                        Text("DEnigmaCracker v2.0", justify="center", style="bold cyan"),
                        title="Running",
                        border_style="cyan"
                    ), size=3),
                    Layout(create_status_table(current_stats)),
                )
                live.update(layout)
                await asyncio.sleep(0.25)  # Update every 250ms
        
        # Run display updates and workers concurrently
        with Live(console=console, refresh_per_second=4) as live:
            display_task = asyncio.create_task(update_display(live))
            
            try:
                # Wait for all workers to complete (they run until shutdown_event is set)
                await asyncio.gather(*worker_tasks, return_exceptions=True)
            finally:
                # Cancel display task
                display_task.cancel()
                try:
                    await display_task
                except asyncio.CancelledError:
                    pass
        
        # Final summary - acquire lock to safely read final stats
        async with stats_lock:
            output_manager.stats.total_scanned = stats["scanned"]
            output_manager.stats.wallets_found = stats["found"]
            output_manager.stats.errors = stats["errors"]
        output_manager.print_summary()


@app.command()
def scan(
    workers: int = typer.Option(
        4, "--workers", "-w",
        help="Number of concurrent workers"
    ),
    chains: Optional[list[str]] = typer.Option(
        None, "--chain", "-c",
        help="Chains to scan (btc, eth, bnb). Can specify multiple."
    ),
    derivation: str = typer.Option(
        "bip44", "--derivation", "-d",
        help="Derivation path standard (bip44, bip49, bip84)"
    ),
    config_file: Optional[Path] = typer.Option(
        None, "--config", "-f",
        help="Path to YAML configuration file"
    ),
    debug: bool = typer.Option(
        False, "--debug",
        help="Enable debug logging"
    ),
):
    """
    Start scanning for cryptocurrency wallets with balance.
    
    This tool generates random BIP39 seed phrases and checks if the
    derived wallet addresses have any balance on supported blockchains.
    """
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load configuration
    if config_file and config_file.exists():
        config = AppConfig.from_yaml(config_file)
    else:
        config = load_config()
    
    if debug:
        config.logging.level = "DEBUG"
    
    # Setup logging
    setup_logging(config)
    
    # Print colorful banner with gradient effect
    banner_lines = [
        ("╔═══════════════════════════════════════════════════════════════╗", "bright_cyan"),
        ("║                                                               ║", "bright_cyan"),
        ("║     ██████╗ ███████╗███╗   ██╗██╗ ██████╗ ███╗   ███╗ █████╗  ║", "cyan"),
        ("║     ██╔══██╗██╔════╝████╗  ██║██║██╔════╝ ████╗ ████║██╔══██╗ ║", "bright_cyan"),
        ("║     ██║  ██║█████╗  ██╔██╗ ██║██║██║  ███╗██╔████╔██║███████║ ║", "cyan"),
        ("║     ██║  ██║██╔══╝  ██║╚██╗██║██║██║   ██║██║╚██╔╝██║██╔══██║ ║", "bright_cyan"),
        ("║     ██████╔╝███████╗██║ ╚████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║ ║", "cyan"),
        ("║     ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝ ║", "bright_cyan"),
        ("║                                                               ║", "bright_cyan"),
    ]
    
    # Print ASCII art lines
    for line, style in banner_lines:
        console.print(line, style=style)
    
    # Print text lines with proper centering (banner content width is 63 chars)
    banner_content_width = 63
    
    # Version line - centered with colored border
    version_str = "CRACKER v2.0"
    version_padding = (banner_content_width - len(version_str)) // 2
    version_line = f"[bright_cyan]║[/bright_cyan]{' ' * version_padding}[bold bright_cyan]{version_str}[/bold bright_cyan]{' ' * (banner_content_width - len(version_str) - version_padding)}[bright_cyan]║[/bright_cyan]"
    console.print(version_line)
    
    # Educational line - centered with colored border
    edu_str = "Educational Purpose Only - Use Responsibly"
    edu_padding = (banner_content_width - len(edu_str)) // 2
    edu_line = f"[bright_cyan]║[/bright_cyan]{' ' * edu_padding}[yellow]{edu_str}[/yellow]{' ' * (banner_content_width - len(edu_str) - edu_padding)}[bright_cyan]║[/bright_cyan]"
    console.print(edu_line)
    
    # GitHub line - centered with colored border
    github_str = "by @Iamdungx"
    github_padding = (banner_content_width - len(github_str)) // 2
    github_line = f"[bright_cyan]║[/bright_cyan]{' ' * github_padding}[dim]by [bold bright_blue]@Iamdungx[/bold bright_blue][/dim]{' ' * (banner_content_width - len(github_str) - github_padding)}[bright_cyan]║[/bright_cyan]"
    console.print(github_line)
    
    # Bottom border
    console.print("╚═══════════════════════════════════════════════════════════════╝", style="bright_cyan")
    
    # Parse chains
    chain_mapping = {
        "btc": Chain.BITCOIN,
        "bitcoin": Chain.BITCOIN,
        "eth": Chain.ETHEREUM,
        "ethereum": Chain.ETHEREUM,
        "bnb": Chain.BNB,
    }
    
    if chains:
        selected_chains = []
        for c in chains:
            if c.lower() in chain_mapping:
                selected_chains.append(chain_mapping[c.lower()])
            else:
                console.print(f"[yellow]Unknown chain: {c}[/yellow]")
        
        # Fallback to default chains if none were valid
        if not selected_chains:
            selected_chains = [Chain.BITCOIN, Chain.ETHEREUM]
    else:
        selected_chains = [Chain.BITCOIN, Chain.ETHEREUM]
    
    # Parse derivation path
    derivation_mapping = {
        "bip44": DerivationPath.BIP44,
        "bip49": DerivationPath.BIP49,
        "bip84": DerivationPath.BIP84,
    }
    selected_derivation = derivation_mapping.get(derivation.lower(), DerivationPath.BIP44)
    
    # Print configuration
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Workers: {workers}")
    console.print(f"  Chains: {', '.join(c.value for c in selected_chains)}")
    console.print(f"  Derivation: {derivation.upper()}")
    console.print(f"  Output: {config.output_dir}")
    console.print()
    
    # Disclaimer
    console.print(Panel(
        "[bold red]DISCLAIMER[/bold red]\n\n"
        "This tool is for EDUCATIONAL and RESEARCH purposes only.\n"
        "Using this tool to access wallets you don't own is ILLEGAL.\n"
        "The authors are not responsible for any misuse of this software.",
        title="Warning",
        border_style="red"
    ))
    console.print()
    
    # Confirm start
    if not typer.confirm("Do you understand and agree to use this responsibly?"):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)
    
    console.print("\n[green]Starting scanner...[/green]\n")
    
    # Run the async scanner
    asyncio.run(run_scanner(
        config=config,
        workers=workers,
        chains=selected_chains,
        derivations=[selected_derivation],
    ))


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold cyan]DEnigmaCracker[/bold cyan] version {__version__}")


@app.command()
def config(
    show: bool = typer.Option(
        False, "--show", "-s",
        help="Show current configuration"
    ),
    init: bool = typer.Option(
        False, "--init", "-i",
        help="Initialize configuration files"
    ),
):
    """Manage configuration."""
    if show:
        cfg = load_config()
        console.print("[bold]Current Configuration:[/bold]")
        console.print(f"  Ethereum API Key: {'*' * 8 if cfg.ethereum.api_key else 'Not set'}")
        console.print(f"  Bitcoin Enabled: {cfg.bitcoin.enabled}")
        console.print(f"  BNB Enabled: {cfg.bnb.enabled}")
        console.print(f"  Workers: {cfg.scanner.workers}")
        console.print(f"  Output Directory: {cfg.output_dir}")
    
    if init:
        console.print("[yellow]Creating default configuration...[/yellow]")
        console.print("Edit .env to add your API keys (see .env.example for template)")
        console.print("Optionally create assets/config.yaml for advanced configuration")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
