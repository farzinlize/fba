from rich.console import Console


class CustomConsole(Console):
    """Custom console"""

    def note(self, msg: str) -> None:
        """Print comment"""
        self.print(f'[bold white]•[/] [white]{msg}[/]')

    def info(self, msg: str) -> None:
        """Print information"""
        self.print(f'[bold cyan]•[/] {msg}')

    def tip(self, msg: str) -> None:
        """Print informational message"""
        self.print(f'[bold green]✓[/] [green]{msg}[/]')

    def warning(self, msg: str) -> None:
        """Print warning message"""
        self.print(f'[bold yellow]⚠[/] [yellow]{msg}[/]')

    def caution(self, msg: str) -> None:
        """Print danger message"""
        self.print(f'[bold red]✗[/] [red]{msg}[/]')


console = CustomConsole()
