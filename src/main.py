"""
DEnigmaCracker v2.0 - Main entry point.
A cryptocurrency wallet scanner for educational purposes.
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    shutdown_requested = True
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
    Run the main scanning loop.
    
    Args:
        config: Application configuration
        workers: Number of concurrent workers
        chains: Blockchain chains to scan
        derivations: Derivation paths to use
    """
    global shutdown_requested
    
    # Initialize components
    generator = WalletGenerator(words_num=12)
    output_manager = OutputManager(config)
    
    async with BalanceChecker(config) as checker:
        stats = {
            "scanned": 0,
            "found": 0,
            "errors": 0,
            "rate": 0.0,
            "elapsed": 0.0,
        }
        
        import time
        start_time = time.time()
        
        with Live(console=console, refresh_per_second=4) as live:
            while not shutdown_requested:
                try:
                    # Generate mnemonic
                    mnemonic = generator.generate_mnemonic()
                    
                    # Derive wallets for all enabled chains
                    wallets = generator.derive_all_wallets(
                        mnemonic=mnemonic,
                        chains=chains,
                        derivations=derivations,
                    )
                    
                    # Check balances
                    result = await checker.scan_seed(mnemonic, wallets)
                    
                    # Update statistics
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
                    
                    # Update live display
                    layout = Layout()
                    layout.split_column(
                        Layout(Panel(
                            Text("DEnigmaCracker v2.0", justify="center", style="bold cyan"),
                            title="Running",
                            border_style="cyan"
                        ), size=3),
                        Layout(create_status_table(stats)),
                    )
                    live.update(layout)
                    
                    # Save progress periodically
                    if stats["scanned"] % 100 == 0:
                        output_manager.save_progress(stats["scanned"], stats["found"])
                    
                except Exception as e:
                    logger.error(f"Error in scan loop: {e}")
                    stats["errors"] += 1
                    await asyncio.sleep(1)
        
        # Final summary
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
    
    # Print banner
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██████╗ ███████╗███╗   ██╗██╗ ██████╗ ███╗   ███╗ █████╗  ║
║     ██╔══██╗██╔════╝████╗  ██║██║██╔════╝ ████╗ ████║██╔══██╗ ║
║     ██║  ██║█████╗  ██╔██╗ ██║██║██║  ███╗██╔████╔██║███████║ ║
║     ██║  ██║██╔══╝  ██║╚██╗██║██║██║   ██║██║╚██╔╝██║██╔══██║ ║
║     ██████╔╝███████╗██║ ╚████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║ ║
║     ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝ ║
║                                                               ║
║                    CRACKER v2.0                               ║
║           Educational Purpose Only - Use Responsibly          ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="cyan")
    
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
        console.print("Edit assets/env/DEnigmaCracker.env to add your API keys")
        console.print("Optionally create assets/config.yaml for advanced configuration")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
