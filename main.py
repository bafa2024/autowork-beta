import asyncio
import sys
from rich.console import Console
from rich.prompt import Prompt

from autowork import AutoWork
from monitor import RealtimeMonitor
from utils import log_info, log_success, log_error

console = Console()

async def run_batch_fetch():
    """Run batch project fetch"""
    async with AutoWork() as autowork:
        await autowork.process_batch_fetch()

async def run_batch_bid():
    """Run batch bidding"""
    async with AutoWork() as autowork:
        await autowork.process_batch_bid(max_bids=5)

async def run_monitor():
    """Run realtime monitor"""
    monitor = RealtimeMonitor()
    await monitor.run()

async def show_status():
    """Show system status"""
    async with AutoWork() as autowork:
        await autowork.show_summary()

def main():
    """Main menu"""
    console.print("[bold blue]AutoWork System[/bold blue]")
    console.print("1. Fetch Projects (Batch)")
    console.print("2. Place Bids (Batch)")
    console.print("3. Realtime Monitor")
    console.print("4. Show Status")
    console.print("5. Start Web Dashboard")
    console.print("6. Exit")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"])
    
    if choice == "1":
        asyncio.run(run_batch_fetch())
    elif choice == "2":
        asyncio.run(run_batch_bid())
    elif choice == "3":
        asyncio.run(run_monitor())
    elif choice == "4":
        asyncio.run(show_status())
    elif choice == "5":
        import subprocess
        subprocess.run([sys.executable, "web_dashboard.py"])
    elif choice == "6":
        console.print("Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            console.print("\n[red]Interrupted by user[/red]")
            sys.exit(0)
        except Exception as e:
            log_error(f"Error: {e}")
        
        console.print("\n")