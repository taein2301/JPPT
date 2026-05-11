"""Typer를 사용한 CLI 진입점.

이 모듈은 애플리케이션의 명령줄 인터페이스를 정의합니다.
start(앱 모드)와 batch(배치 모드) 두 가지 실행 모드를 제공합니다.
"""

import asyncio
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import typer
from loguru import logger

from src.utils.config import Settings, load_config
from src.utils.logger import setup_logger

CLI_NAME = "jppt"
DIST_NAME = "jppt"

# 프로젝트 루트 디렉토리 (src/의 부모 디렉토리)
app = typer.Typer(
    name=CLI_NAME,
    help="JKLEE Python Project Template",
    add_completion=False,
)

_SENSITIVE_CONFIG_KEYS = frozenset(
    {
        "access_key",
        "access_token",
        "account_no",
        "account_number",
        "account_product_code",
        "api_key",
        "api_secret",
        "app_key",
        "app_secret",
        "bot_token",
        "chat_id",
        "dsn",
        "product_code",
        "secret_key",
    }
)


def _mask_config_secrets(value: Any, *, key: str | None = None) -> Any:
    """로그에 남기기 전 config secret 값을 마스킹합니다."""
    if key in _SENSITIVE_CONFIG_KEYS:
        return "<redacted>"
    if isinstance(value, dict):
        return {
            item_key: _mask_config_secrets(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_mask_config_secrets(item) for item in value]
    return value


def _build_config_log_summary(
    *,
    mode: str,
    env: str,
    settings: Settings,
    effective_log_level: str,
    log_file: Path,
) -> dict[str, Any]:
    """실행 시작 로그에 남길 config 요약을 생성합니다."""
    config_values = _mask_config_secrets(settings.model_dump(mode="json"))
    return {
        "mode": mode,
        "env": env,
        "effective_log_level": effective_log_level,
        "log_file": str(log_file),
        **config_values,
    }


def _log_loaded_config(
    *,
    mode: str,
    env: str,
    settings: Settings,
    effective_log_level: str,
    log_file: Path,
) -> None:
    """실행 시작 시 핵심 설정 요약을 로깅합니다."""
    summary = _build_config_log_summary(
        mode=mode,
        env=env,
        settings=settings,
        effective_log_level=effective_log_level,
        log_file=log_file,
    )
    logger.info(
        "Loaded config summary:\n{}",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
    )


def _resolve_log_level(config_level: str, log_level: str | None, verbose: bool) -> str:
    if verbose:
        return "DEBUG"
    if log_level:
        return log_level.upper()
    return config_level


def _resolve_config_dir(config: str | None) -> Path | None:
    """CLI config 파일 옵션에서 설정 디렉토리를 추출합니다."""
    if config is None:
        return None
    return Path(config).parent


def _load_settings(env: str, config: str | None) -> Settings:
    """CLI 옵션에 따라 설정을 로드합니다."""
    config_dir = _resolve_config_dir(config)
    if config_dir is not None:
        return load_config(env=env, config_dir=config_dir)
    return load_config(env=env)


def _build_log_file(app_name: str, suffix: str = "") -> Path:
    """실행 모드별 로그 파일 경로를 생성합니다."""
    return Path.home() / "logs" / f"{app_name}{suffix}.log"


def _configure_runtime(
    *,
    mode: str,
    env: str,
    settings: Settings,
    log_level: str | None,
    verbose: bool,
    log_suffix: str = "",
) -> Settings:
    """로거를 초기화하고 핵심 설정 요약을 남깁니다."""
    effective_log_level = _resolve_log_level(settings.logging.level, log_level, verbose)
    log_file = _build_log_file(settings.app.name, log_suffix)
    setup_logger(
        level=effective_log_level,
        log_file=log_file,
        format_str=settings.logging.format,
        json_logs=settings.logging.json_logs,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )
    _log_loaded_config(
        mode=mode,
        env=env,
        settings=settings,
        effective_log_level=effective_log_level,
        log_file=log_file,
    )
    return settings


def _package_version() -> str:
    """설치된 패키지 버전을 반환합니다."""
    try:
        return version(DIST_NAME)
    except PackageNotFoundError:
        return "0.1.0"


def version_callback(value: bool) -> None:
    """버전 정보를 출력하고 종료합니다."""
    if value:
        typer.echo(f"{CLI_NAME} version {_package_version()}")
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
    log_level: str | None = typer.Option(None, "--log-level", "-l", help="Override log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Shortcut for --log-level DEBUG"),
) -> None:
    """앱 모드로 실행합니다 (데몬/장시간 실행).

    주기적인 작업을 수행하거나 신호를 받을 때까지 계속 실행되는 모드입니다.
    Ctrl+C 또는 SIGTERM 신호로 graceful shutdown이 가능합니다.
    """
    config_dir = _resolve_config_dir(config)
    settings = _load_settings(env, config)
    _configure_runtime(
        mode="start",
        env=env,
        settings=settings,
        log_level=log_level,
        verbose=verbose,
    )

    logger.info(f"Starting {settings.app.name} in app mode")
    logger.info(f"Environment: {env}")
    logger.info(f"Debug mode: {settings.app.debug}")

    # 앱 실행 (비동기)
    from src.utils.app_runner import run_app

    asyncio.run(
        run_app(
            settings,
            env,
            config_dir=config_dir,
            log_level=log_level,
            verbose=verbose,
        )
    )


@app.command()
def batch(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str | None = typer.Option(None, "--log-level", "-l", help="Override log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Shortcut for --log-level DEBUG"),
) -> None:
    """배치 모드로 실행합니다 (일회성 실행).

    작업을 한 번 실행하고 종료하는 모드입니다.
    cron이나 스케줄러에서 주기적으로 호출하기에 적합합니다.
    """
    settings = _load_settings(env, config)
    _configure_runtime(
        mode="batch",
        env=env,
        settings=settings,
        log_level=log_level,
        verbose=verbose,
        log_suffix="_batch",
    )

    logger.info(f"Starting {settings.app.name} in batch mode")
    logger.info(f"Environment: {env}")

    # 배치 실행 (비동기)
    from src.utils.batch_runner import run_batch

    asyncio.run(run_batch(settings, env))


if __name__ == "__main__":
    app()
