"""CLI entry point using Typer."""
import asyncio
from pathlib import Path

import typer
from loguru import logger

from jppt.utils.config import load_config
from jppt.utils.logger import setup_logger

app = typer.Typer(
    name="jppt",
    help="JKLEE Python Project Template",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo("jppt version 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """JKLEE Python Project Template - Modern Python CLI application."""
    pass


@app.command()
def start(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Start app mode (daemon)."""
    # Load configuration
    if config:
        config_dir = Path(config).parent
        settings = load_config(env=env, config_dir=config_dir)
    else:
        settings = load_config(env=env)

    # Setup logging
    if verbose:
        log_level = "DEBUG"

    log_file = Path("logs") / f"{settings.app.name}.log"
    setup_logger(
        level=log_level,
        log_file=log_file,
        format_str=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )

    logger.info(f"Starting {settings.app.name} in app mode")
    logger.info(f"Environment: {env}")
    logger.info(f"Debug mode: {settings.app.debug}")

    # Run app
    from jppt.utils.app_runner import run_app

    asyncio.run(run_app(settings))


@app.command()
def batch(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Run batch mode (one-shot)."""
    # Load configuration
    if config:
        config_dir = Path(config).parent
        settings = load_config(env=env, config_dir=config_dir)
    else:
        settings = load_config(env=env)

    # Setup logging
    if verbose:
        log_level = "DEBUG"

    log_file = Path("logs") / f"{settings.app.name}_batch.log"
    setup_logger(
        level=log_level,
        log_file=log_file,
        format_str=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )

    logger.info(f"Starting {settings.app.name} in batch mode")
    logger.info(f"Environment: {env}")

    # Run batch
    from jppt.utils.batch_runner import run_batch

    asyncio.run(run_batch(settings))


if __name__ == "__main__":
    app()
