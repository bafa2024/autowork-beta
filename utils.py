from datetime import datetime
from rich.console import Console

console = Console()

def log_info(message: str):
    """Log info message"""
    console.print(f"[blue][{datetime.now().strftime('%H:%M:%S')}][/blue] {message}")

def log_success(message: str):
    """Log success message"""
    console.print(f"[green][{datetime.now().strftime('%H:%M:%S')}][/green] {message}")

def log_error(message: str):
    """Log error message"""
    console.print(f"[red][{datetime.now().strftime('%H:%M:%S')}][/red] {message}")

def log_warning(message: str):
    """Log warning message"""
    console.print(f"[yellow][{datetime.now().strftime('%H:%M:%S')}][/yellow] {message}")