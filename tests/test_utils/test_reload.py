"""설정 reload coordinator 테스트."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.utils.config import Settings
from src.utils.reload import ReloadCoordinator


def _write_config(
    config_dir: Path,
    *,
    app_name: str,
    remote_control_enabled: bool = False,
    bot_token: str = "",
    chat_id: str = "",
) -> None:
    """테스트용 dev.yaml 파일을 작성합니다."""
    config_dir.mkdir(exist_ok=True)
    allowed_chat_ids = f'\n    allowed_chat_ids:\n      - "{chat_id}"' if chat_id else ""
    config_dir.joinpath("dev.yaml").write_text(
        f"""
app:
  name: "{app_name}"
  version: "0.1.0"
  debug: false
telegram:
  enabled: {str(bool(bot_token)).lower()}
  bot_token: "{bot_token}"
  chat_id: "{chat_id}"
  remote_control:
    enabled: {str(remote_control_enabled).lower()}{allowed_chat_ids}
""",
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_reload_success_updates_state_and_calls_apply_settings(tmp_path: Path) -> None:
    """reload 성공 시 설정과 상태를 성공 기준으로 교체해야 한다."""
    current_settings = Settings(app={"name": "old-app"})
    _write_config(tmp_path, app_name="new-app")
    apply_settings = AsyncMock()
    coordinator = ReloadCoordinator(
        settings=current_settings,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )

    result = await coordinator.reload()

    assert result.succeeded is True
    assert result.settings.app.name == "new-app"
    assert result.error_type is None
    assert result.error_message is None
    assert coordinator.current_settings.app.name == "new-app"
    assert coordinator.reload_count == 1
    assert coordinator.last_reload_status == "success"
    assert coordinator.last_reload_error is None
    assert coordinator.last_reload_at is not None
    apply_settings.assert_awaited_once()
    assert apply_settings.await_args.args[0].app.name == "new-app"


@pytest.mark.asyncio
async def test_reload_load_failure_keeps_old_settings_and_does_not_apply(
    tmp_path: Path,
) -> None:
    """설정 로드 실패 시 기존 설정을 유지하고 apply_settings를 호출하지 않아야 한다."""
    current_settings = Settings(app={"name": "old-app"})
    tmp_path.joinpath("dev.yaml").write_text("- invalid\n- root\n", encoding="utf-8")
    apply_settings = AsyncMock()
    coordinator = ReloadCoordinator(
        settings=current_settings,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )

    result = await coordinator.reload()

    assert result.succeeded is False
    assert result.settings is current_settings
    assert result.error_type == "ConfigurationError"
    assert result.error_message == "config reload failed"
    assert coordinator.current_settings is current_settings
    assert coordinator.reload_count == 0
    assert coordinator.last_reload_status == "failed"
    assert coordinator.last_reload_error == "ConfigurationError: config reload failed"
    assert apply_settings.await_count == 0


@pytest.mark.asyncio
async def test_reload_apply_settings_failure_keeps_old_settings_and_reports_runtime_error(
    tmp_path: Path,
) -> None:
    """apply_settings 실패 시 기존 설정을 유지하고 RuntimeError를 보고해야 한다."""
    current_settings = Settings(app={"name": "old-app"})
    _write_config(tmp_path, app_name="new-app")
    apply_settings = AsyncMock(side_effect=RuntimeError("apply failed"))
    coordinator = ReloadCoordinator(
        settings=current_settings,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )

    result = await coordinator.reload()

    assert result.succeeded is False
    assert result.settings is current_settings
    assert result.error_type == "RuntimeError"
    assert result.error_message == "config reload failed"
    assert coordinator.current_settings is current_settings
    assert coordinator.reload_count == 0
    assert coordinator.last_reload_status == "failed"
    assert coordinator.last_reload_error == "RuntimeError: config reload failed"
    apply_settings.assert_awaited_once()
    assert apply_settings.await_args.args[0].app.name == "new-app"


@pytest.mark.asyncio
async def test_reload_validation_failure_does_not_expose_new_telegram_secrets(
    tmp_path: Path,
) -> None:
    """새 설정 검증 실패 메시지는 새 Telegram secret을 노출하지 않아야 한다."""
    current_settings = Settings(app={"name": "old-app"})
    tmp_path.joinpath("dev.yaml").write_text(
        """
app:
  name: "new-app"
telegram:
  enabled: true
  bot_token: "new-secret-token"
  chat_id: "99999"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "99999"
    commands:
      reload: true
      status: true
      help: true
      unknown_secret: "new-secret-token"
""",
        encoding="utf-8",
    )
    apply_settings = AsyncMock()
    coordinator = ReloadCoordinator(
        settings=current_settings,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )

    result = await coordinator.reload()
    message = coordinator.status_message()

    assert result.succeeded is False
    assert result.error_type == "ValidationError"
    assert result.settings is current_settings
    assert coordinator.current_settings is current_settings
    assert apply_settings.await_count == 0
    assert "new-secret-token" not in result.message
    assert "99999" not in result.message
    assert "new-secret-token" not in str(result.error_message)
    assert "99999" not in str(result.error_message)
    assert "new-secret-token" not in message
    assert "99999" not in message


def test_status_message_includes_reload_state_without_telegram_secrets() -> None:
    """상태 메시지는 reload 상태를 포함하고 Telegram secret을 노출하지 않아야 한다."""
    settings = Settings(
        app={"name": "secret-app"},
        telegram={
            "enabled": True,
            "bot_token": "123456:SECRET",
            "chat_id": "-100999",
            "remote_control": {
                "enabled": True,
                "allowed_chat_ids": ["-100999"],
            },
        },
    )
    coordinator = ReloadCoordinator(
        settings=settings,
        env="prod",
        config_dir=Path("config"),
        apply_settings=AsyncMock(),
    )
    coordinator.last_reload_status = "failed"
    coordinator.last_reload_at = datetime(2026, 5, 9, 12, 30, tzinfo=UTC)
    coordinator.last_reload_error = "RuntimeError: token=123456:SECRET chat=-100999"

    message = coordinator.status_message()

    assert "[SECRET-APP]" in message
    assert "Env : prod" in message
    assert "Uptime Seconds :" in message
    assert "Remote Control : enabled" in message
    assert "Reload Count : 0" in message
    assert "Last Reload Status : failed" in message
    assert "Last Reload At : 2026-05-09T12:30:00+00:00" in message
    assert "Last Reload Error : RuntimeError: token=[redacted] chat=[redacted]" in message
    assert "123456:SECRET" not in message
    assert "-100999" not in message


def test_status_message_redacts_overlapping_telegram_secrets_by_longest_first() -> None:
    """겹치는 Telegram secret은 긴 값부터 치환해서 부분 누출을 막아야 한다."""
    settings = Settings(
        app={"name": "secret-app"},
        telegram={
            "enabled": True,
            "bot_token": "123456:SECRET",
            "chat_id": "123456",
            "remote_control": {
                "enabled": True,
                "allowed_chat_ids": ["123456"],
            },
        },
    )
    coordinator = ReloadCoordinator(
        settings=settings,
        env="prod",
        config_dir=Path("config"),
        apply_settings=AsyncMock(),
    )
    coordinator.last_reload_status = "failed"
    coordinator.last_reload_error = "RuntimeError: token=123456:SECRET chat=123456"

    message = coordinator.status_message()

    assert "123456:SECRET" not in message
    assert "123456" not in message
    assert "[redacted]:SECRET" not in message
    assert "RuntimeError: token=[redacted] chat=[redacted]" in message
