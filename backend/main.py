from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

from backend.core.registrar import register_app
from backend.plugin.core import check_required_plugins, get_plugins
from backend.plugin.requirements import install_requirements
from backend.utils.console import console
from backend.utils.timezone import timezone


def _get_log_prefix() -> str:
    """Get startup log prefix"""
    return f'{timezone.to_str(timezone.now(), "%Y-%m-%d %H:%M:%S.%M0")} | {"INFO": <8} | - | '


def _prepare_plugins() -> None:
    """Check required plugins and install missing dependencies"""
    log_prefix = _get_log_prefix()

    console.print(Text(f'{log_prefix}Checking required plugins...', style='bold cyan'))

    check_required_plugins()

    console.print(Text(f'{log_prefix}Checking plugin dependencies...', style='bold cyan'))

    plugins = get_plugins()

    with Progress(
        SpinnerColumn(finished_text=f'[bold green]{log_prefix}Plugins ready[/]'),
        TextColumn('{task.description}'),
        TextColumn('{task.completed}/{task.total}', style='bold green'),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task('Installing plugin dependencies...', total=len(plugins))
        for plugin in plugins:
            progress.update(task, description=f'[bold magenta]Installing dependencies for plugin {plugin}...[/]')
            install_requirements(plugin)
            progress.advance(task)
        progress.update(task, description='[bold green]-[/]')

    console.print(Text(f'{log_prefix}Starting service...', style='bold magenta'))


_prepare_plugins()
app = register_app()
