"""Typer를 사용한 CLI 진입점.

이 모듈은 애플리케이션의 명령줄 인터페이스를 정의합니다.
start(앱 모드)와 batch(배치 모드) 두 가지 실행 모드를 제공합니다.
"""

import asyncio
from pathlib import Path

import typer
from loguru import logger

from src.utils.config import load_config
from src.utils.logger import setup_logger

# 프로젝트 루트 디렉토리 (src/의 부모 디렉토리)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = typer.Typer(
    name="jppt",
    help="JKLEE Python Project Template",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """버전 정보를 출력하고 종료합니다."""
    if value:
        # Load config to get app name and version dynamically
        settings = load_config(env="dev")
        typer.echo(f"{settings.app.name} version {settings.app.version}")
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
    """JKLEE Python Project Template - 모던 Python CLI 애플리케이션."""
    pass


@app.command()
def start(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """앱 모드로 실행합니다 (데몬/장시간 실행).

    주기적인 작업을 수행하거나 신호를 받을 때까지 계속 실행되는 모드입니다.
    Ctrl+C 또는 SIGTERM 신호로 graceful shutdown이 가능합니다.
    """
    # 설정 로드 (커스텀 경로 또는 기본 경로)
    if config:
        config_dir = Path(config).parent
        settings = load_config(env=env, config_dir=config_dir)
    else:
        settings = load_config(env=env)

    # 로깅 설정 (verbose 모드면 DEBUG 레벨로 변경)
    if verbose:
        log_level = "DEBUG"

    log_file = PROJECT_ROOT / "logs" / f"{settings.app.name}.log"
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

    # 앱 실행 (비동기)
    from src.utils.app_runner import run_app

    asyncio.run(run_app(settings))


@app.command()
def batch(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """배치 모드로 실행합니다 (일회성 실행).

    작업을 한 번 실행하고 종료하는 모드입니다.
    cron이나 스케줄러에서 주기적으로 호출하기에 적합합니다.
    """
    # 설정 로드 (커스텀 경로 또는 기본 경로)
    if config:
        config_dir = Path(config).parent
        settings = load_config(env=env, config_dir=config_dir)
    else:
        settings = load_config(env=env)

    # 로깅 설정 (verbose 모드면 DEBUG 레벨로 변경)
    if verbose:
        log_level = "DEBUG"

    log_file = PROJECT_ROOT / "logs" / f"{settings.app.name}_batch.log"
    setup_logger(
        level=log_level,
        log_file=log_file,
        format_str=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )

    logger.info(f"Starting {settings.app.name} in batch mode")
    logger.info(f"Environment: {env}")

    # 배치 실행 (비동기)
    from src.utils.batch_runner import run_batch

    asyncio.run(run_batch(settings))


if __name__ == "__main__":
    app()
