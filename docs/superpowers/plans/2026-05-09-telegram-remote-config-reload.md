# Telegram Remote Config Reload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Telegram command based remote control for `start` mode so an authorized chat can run `/reload`, inspect `/status`, and read `/help`.

**Architecture:** Keep `TelegramNotifier` send-only. Add `TelegramRemoteController` for Telegram command polling and `ReloadCoordinator` for serialized reload state. `run_app()` wires them together and updates logger/notifier/settings only after a new config validates.

**Tech Stack:** Python 3.11, Pydantic v2, Loguru, Typer, python-telegram-bot 22.6, pytest, ruff, mypy.

---

## Source Evidence

- Design spec: `docs/superpowers/specs/2026-05-09-telegram-remote-config-reload-design.md`
- Current config loader: `src/utils/config.py`
- Current daemon loop: `src/utils/app_runner.py`
- Current CLI runtime setup: `src/main.py`
- Current Telegram send-only notifier: `src/utils/telegram.py`

## File Structure

- Modify `src/utils/config.py`: add remote control config models and validation.
- Create `src/utils/reload.py`: define reload state/result and serialized reload execution.
- Create `src/utils/telegram_remote.py`: define Telegram command controller and command access checks.
- Modify `src/utils/app_runner.py`: wire coordinator/controller into `start` mode.
- Modify `src/main.py`: pass config source and log override options into `run_app()`.
- Modify `config/dev.yaml.example`: add disabled remote control defaults.
- Modify `config/prod.yaml.example`: add disabled remote control defaults.
- Modify `tests/test_utils/test_config.py`: cover remote control schema.
- Create `tests/test_utils/test_reload.py`: cover reload success/failure/status.
- Create `tests/test_utils/test_telegram_remote.py`: cover command authorization and replies.
- Modify `tests/test_utils/test_app_runner.py`: cover remote controller lifecycle in daemon mode.
- Modify `tests/test_main.py`: cover `run_app()` receives config dir/log options.

## Worktree Safety

The planning snapshot had a dirty worktree with existing modifications in several files this plan will touch. Before each task commit, run:

```bash
git status --short
git diff -- src/utils/config.py config/dev.yaml.example config/prod.yaml.example tests/test_utils/test_config.py
```

Use the `git diff -- ...` file list from the task being committed. Commit only the changes made for that task. If a listed file already contains unrelated changes, stop before committing and separate the commit scope; do not overwrite or revert those changes.

## Task 1: Config Schema

**Files:**
- Modify: `src/utils/config.py`
- Modify: `config/dev.yaml.example`
- Modify: `config/prod.yaml.example`
- Test: `tests/test_utils/test_config.py`

- [ ] **Step 1: Write failing config tests**

Append these tests to `tests/test_utils/test_config.py`:

```python
def test_remote_control_defaults_disabled() -> None:
    """Telegram remote control 기본값은 비활성화여야 한다."""
    settings = Settings()

    assert settings.telegram.remote_control.enabled is False
    assert settings.telegram.remote_control.allowed_chat_ids == []
    assert settings.telegram.remote_control.commands.reload is True
    assert settings.telegram.remote_control.commands.status is True
    assert settings.telegram.remote_control.commands.help is True


def test_load_config_with_remote_control_normalizes_chat_ids(tmp_path: Path) -> None:
    """허용 chat id는 문자열 리스트로 정규화되어야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "12345"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - 12345
      - "-100999"
    commands:
      reload: true
      status: false
      help: true
""",
        encoding="utf-8",
    )

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.telegram.remote_control.enabled is True
    assert config.telegram.remote_control.allowed_chat_ids == ["12345", "-100999"]
    assert config.telegram.remote_control.commands.reload is True
    assert config.telegram.remote_control.commands.status is False
    assert config.telegram.remote_control.commands.help is True


def test_remote_control_requires_allowed_chat_ids(tmp_path: Path) -> None:
    """원격제어가 켜져 있으면 allowed_chat_ids가 비어 있으면 안 된다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "12345"
  remote_control:
    enabled: true
    allowed_chat_ids: []
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="remote_control.allowed_chat_ids must not be empty when enabled",
    ):
        load_config(env="dev", config_dir=tmp_path)


def test_remote_control_requires_telegram_enabled(tmp_path: Path) -> None:
    """원격제어가 켜져 있으면 telegram.enabled도 켜져 있어야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: false
  bot_token: "token"
  chat_id: "12345"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "12345"
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="telegram.enabled must be true when remote_control.enabled is true",
    ):
        load_config(env="dev", config_dir=tmp_path)


def test_remote_control_requires_bot_token(tmp_path: Path) -> None:
    """원격제어가 켜져 있으면 bot_token이 비어 있으면 안 된다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: ""
  chat_id: "12345"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "12345"
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="telegram.bot_token must not be empty when remote_control.enabled is true",
    ):
        load_config(env="dev", config_dir=tmp_path)
```

- [ ] **Step 2: Run the config tests and verify failure**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_config.py -q
```

Expected: FAIL because `TelegramConfig` has no `remote_control` field.

- [ ] **Step 3: Implement config models**

In `src/utils/config.py`, insert these classes after `LoggingConfig` and before `TelegramConfig`:

```python
class TelegramRemoteCommandsConfig(BaseModel):
    """Telegram 원격제어 명령 활성화 설정.

    Attributes:
        reload: 설정 reload 명령 활성화 여부
        status: 상태 조회 명령 활성화 여부
        help: 도움말 명령 활성화 여부
    """

    reload: bool = Field(default=True)
    status: bool = Field(default=True)
    help: bool = Field(default=True)


class TelegramRemoteControlConfig(BaseModel):
    """Telegram 원격제어 설정.

    Attributes:
        enabled: 원격제어 활성화 여부
        allowed_chat_ids: 명령 실행을 허용할 Telegram chat id 목록
        commands: 명령별 활성화 설정
    """

    enabled: bool = Field(default=False)
    allowed_chat_ids: list[str] = Field(default_factory=list)
    commands: TelegramRemoteCommandsConfig = Field(
        default_factory=TelegramRemoteCommandsConfig
    )

    @field_validator("allowed_chat_ids", mode="before")
    @classmethod
    def normalize_allowed_chat_ids(cls, value: object) -> list[str]:
        """Telegram chat id를 문자열 리스트로 정규화합니다."""
        if value is None:
            return []
        if isinstance(value, (str, int)):
            return [str(value)]
        if isinstance(value, list):
            return [str(item) for item in value]
        raise ValueError("allowed_chat_ids must be a list of chat ids")

    @model_validator(mode="after")
    def validate_enabled_config(self) -> "TelegramRemoteControlConfig":
        """원격제어 활성화 시 허용 chat id를 필수로 요구합니다."""
        if self.enabled and not self.allowed_chat_ids:
            raise ValueError("remote_control.allowed_chat_ids must not be empty when enabled")
        return self
```

Then update `TelegramConfig`:

```python
class TelegramConfig(BaseModel):
    """텔레그램 연동 설정.

    Attributes:
        enabled: 텔레그램 알림 활성화 여부
        bot_token: 텔레그램 봇 토큰
        chat_id: 텔레그램 채팅방 ID
    """

    enabled: bool = Field(default=False)
    bot_token: str = Field(default="")
    chat_id: str = Field(default="")
    silent_time: "TelegramSilentTimeConfig" = Field(
        default_factory=lambda: TelegramSilentTimeConfig()
    )
    remote_control: TelegramRemoteControlConfig = Field(
        default_factory=TelegramRemoteControlConfig
    )

    @model_validator(mode="after")
    def validate_remote_control(self) -> "TelegramConfig":
        """원격제어 활성화 시 Telegram 송신 설정도 유효해야 합니다."""
        if not self.remote_control.enabled:
            return self
        if not self.enabled:
            raise ValueError("telegram.enabled must be true when remote_control.enabled is true")
        if not self.bot_token:
            raise ValueError("telegram.bot_token must not be empty when remote_control.enabled is true")
        return self
```

- [ ] **Step 4: Update example configs**

Add this block under `telegram.silent_time` in both `config/dev.yaml.example` and `config/prod.yaml.example`:

```yaml
  remote_control:
    enabled: false
    allowed_chat_ids: []
    commands:
      reload: true
      status: true
      help: true
```

- [ ] **Step 5: Run focused config tests**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_config.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit config schema**

Run:

```bash
git add src/utils/config.py config/dev.yaml.example config/prod.yaml.example tests/test_utils/test_config.py
git commit -m "feat: add telegram remote control config"
```

## Task 2: Reload Coordinator

**Files:**
- Create: `src/utils/reload.py`
- Test: `tests/test_utils/test_reload.py`

- [ ] **Step 1: Write failing reload tests**

Create `tests/test_utils/test_reload.py`:

```python
from pathlib import Path

import pytest

from src.utils.config import Settings
from src.utils.reload import ReloadCoordinator


def _write_config(path: Path, *, app_name: str, log_level: str = "INFO") -> None:
    path.write_text(
        f"""
app:
  name: "{app_name}"
  version: "0.1.0"
  debug: false
logging:
  level: "{log_level}"
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
""",
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_reload_success_updates_current_settings(tmp_path: Path) -> None:
    config_file = tmp_path / "dev.yaml"
    _write_config(config_file, app_name="before")
    initial = Settings(app={"name": "before"})
    applied: list[Settings] = []

    async def apply_settings(settings: Settings) -> None:
        applied.append(settings)

    coordinator = ReloadCoordinator(
        settings=initial,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )
    _write_config(config_file, app_name="after", log_level="DEBUG")

    result = await coordinator.reload()

    assert result.succeeded is True
    assert result.error_type is None
    assert coordinator.current_settings.app.name == "after"
    assert coordinator.current_settings.logging.level == "DEBUG"
    assert coordinator.reload_count == 1
    assert coordinator.last_reload_status == "success"
    assert applied[0].app.name == "after"
    assert "reload success" in result.message


@pytest.mark.asyncio
async def test_reload_failure_keeps_existing_settings(tmp_path: Path) -> None:
    config_file = tmp_path / "dev.yaml"
    _write_config(config_file, app_name="before")
    initial = Settings(app={"name": "before"})
    applied: list[Settings] = []

    async def apply_settings(settings: Settings) -> None:
        applied.append(settings)

    coordinator = ReloadCoordinator(
        settings=initial,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )
    config_file.write_text("app: [broken", encoding="utf-8")

    result = await coordinator.reload()

    assert result.succeeded is False
    assert coordinator.current_settings.app.name == "before"
    assert coordinator.reload_count == 0
    assert coordinator.last_reload_status == "failed"
    assert result.error_type is not None
    assert "reload failed" in result.message
    assert applied == []


@pytest.mark.asyncio
async def test_reload_apply_failure_keeps_existing_settings(tmp_path: Path) -> None:
    config_file = tmp_path / "dev.yaml"
    _write_config(config_file, app_name="before")
    initial = Settings(app={"name": "before"})

    async def apply_settings(settings: Settings) -> None:
        raise RuntimeError(f"cannot apply {settings.app.name}")

    coordinator = ReloadCoordinator(
        settings=initial,
        env="dev",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )
    _write_config(config_file, app_name="after")

    result = await coordinator.reload()

    assert result.succeeded is False
    assert coordinator.current_settings.app.name == "before"
    assert coordinator.reload_count == 0
    assert coordinator.last_reload_status == "failed"
    assert result.error_type == "RuntimeError"


def test_status_message_contains_runtime_state_without_secrets(tmp_path: Path) -> None:
    settings = Settings(
        app={"name": "status-app"},
        telegram={"enabled": True, "bot_token": "secret-token", "chat_id": "12345"},
    )

    async def apply_settings(next_settings: Settings) -> None:
        return None

    coordinator = ReloadCoordinator(
        settings=settings,
        env="prod",
        config_dir=tmp_path,
        apply_settings=apply_settings,
    )

    message = coordinator.status_message()

    assert "[STATUS-APP] status" in message
    assert "Env : prod" in message
    assert "Reload count : 0" in message
    assert "secret-token" not in message
    assert "12345" not in message
```

- [ ] **Step 2: Run reload tests and verify failure**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_reload.py -q
```

Expected: FAIL because `src.utils.reload` does not exist.

- [ ] **Step 3: Implement `src/utils/reload.py`**

Create `src/utils/reload.py`:

```python
"""설정 reload 상태와 실행을 관리합니다."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.utils.config import Settings, load_config

ApplySettings = Callable[[Settings], Awaitable[None]]


@dataclass(slots=True)
class ReloadResult:
    """설정 reload 결과."""

    succeeded: bool
    message: str
    settings: Settings
    error_type: str | None = None
    error_message: str | None = None


class ReloadCoordinator:
    """설정 reload 요청을 직렬화하고 현재 설정 상태를 관리합니다."""

    def __init__(
        self,
        *,
        settings: Settings,
        env: str,
        config_dir: Path | None,
        apply_settings: ApplySettings,
    ) -> None:
        self.current_settings = settings
        self.env = env
        self.config_dir = config_dir
        self.reload_count = 0
        self.last_reload_status = "never"
        self.last_reload_at: datetime | None = None
        self.last_reload_error: str | None = None
        self._apply_settings = apply_settings
        self._started_at = datetime.now(UTC)
        self._lock = asyncio.Lock()

    async def reload(self) -> ReloadResult:
        """설정을 다시 로드하고 성공 시 런타임에 반영합니다."""
        async with self._lock:
            try:
                next_settings = load_config(env=self.env, config_dir=self.config_dir)
                await self._apply_settings(next_settings)
            except Exception as exc:
                self.last_reload_status = "failed"
                self.last_reload_at = datetime.now(UTC)
                self.last_reload_error = f"{type(exc).__name__}: {exc}"
                return ReloadResult(
                    succeeded=False,
                    message=self._format_reload_message("reload failed", self.last_reload_error),
                    settings=self.current_settings,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )

            self.current_settings = next_settings
            self.reload_count += 1
            self.last_reload_status = "success"
            self.last_reload_at = datetime.now(UTC)
            self.last_reload_error = None
            return ReloadResult(
                succeeded=True,
                message=self._format_reload_message("reload success", None),
                settings=self.current_settings,
            )

    def status_message(self) -> str:
        """현재 runtime 상태를 Telegram 응답 메시지로 반환합니다."""
        now = datetime.now(UTC)
        uptime_seconds = int((now - self._started_at).total_seconds())
        display_name = self.current_settings.app.name.strip().upper()
        lines = [
            f"[{display_name}] status",
            f"Env : {self.env}",
            f"Uptime seconds : {uptime_seconds}",
            f"Remote control : {self.current_settings.telegram.remote_control.enabled}",
            f"Reload count : {self.reload_count}",
            f"Last reload : {self.last_reload_status}",
        ]
        if self.last_reload_at is not None:
            lines.append(f"Last reload at : {self.last_reload_at.isoformat()}")
        if self.last_reload_error is not None:
            lines.append(f"Last reload error : {self.last_reload_error}")
        return "\n".join(lines)

    def _format_reload_message(self, status: str, error: str | None) -> str:
        display_name = self.current_settings.app.name.strip().upper()
        lines = [
            f"[{display_name}] {status}",
            f"Env : {self.env}",
        ]
        if error is not None:
            lines.append(f"Error : {error}")
        return "\n".join(lines)
```

- [ ] **Step 4: Run reload tests**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_reload.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit reload coordinator**

Run:

```bash
git add src/utils/reload.py tests/test_utils/test_reload.py
git commit -m "feat: add config reload coordinator"
```

## Task 3: Telegram Remote Controller

**Files:**
- Create: `src/utils/telegram_remote.py`
- Test: `tests/test_utils/test_telegram_remote.py`

- [ ] **Step 1: Write failing remote controller tests**

Create `tests/test_utils/test_telegram_remote.py`:

```python
from types import SimpleNamespace

import pytest

from src.utils.config import Settings, TelegramRemoteControlConfig
from src.utils.reload import ReloadResult
from src.utils.telegram_remote import TelegramRemoteController


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


def _fake_update(chat_id: int | str) -> SimpleNamespace:
    message = FakeMessage()
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id),
        effective_message=message,
        message=message,
    )


@pytest.mark.asyncio
async def test_reload_command_requires_allowed_chat_id() -> None:
    called = False

    async def reload_callback() -> ReloadResult:
        nonlocal called
        called = True
        raise AssertionError("unauthorized reload should not call callback")

    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=TelegramRemoteControlConfig(
            enabled=True,
            allowed_chat_ids=["12345"],
        ),
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )
    update = _fake_update("99999")

    await controller.handle_reload(update, SimpleNamespace())

    assert called is False
    assert update.effective_message.replies == []


@pytest.mark.asyncio
async def test_reload_command_replies_with_result_for_allowed_chat() -> None:
    async def reload_callback() -> ReloadResult:
        return ReloadResult(
            succeeded=True,
            message="[APP] reload success\nEnv : prod",
            settings=Settings(),
        )

    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=TelegramRemoteControlConfig(
            enabled=True,
            allowed_chat_ids=["12345"],
        ),
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )
    update = _fake_update(12345)

    await controller.handle_reload(update, SimpleNamespace())

    assert update.effective_message.replies == ["[APP] reload success\nEnv : prod"]


@pytest.mark.asyncio
async def test_disabled_reload_command_returns_command_disabled() -> None:
    async def reload_callback() -> ReloadResult:
        raise AssertionError("disabled command should not call callback")

    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=TelegramRemoteControlConfig(
            enabled=True,
            allowed_chat_ids=["12345"],
            commands={"reload": False},
        ),
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )
    update = _fake_update("12345")

    await controller.handle_reload(update, SimpleNamespace())

    assert update.effective_message.replies == ["reload command disabled"]


@pytest.mark.asyncio
async def test_status_command_replies_without_reload() -> None:
    async def reload_callback() -> ReloadResult:
        raise AssertionError("status should not call reload")

    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=TelegramRemoteControlConfig(
            enabled=True,
            allowed_chat_ids=["12345"],
        ),
        reload_callback=reload_callback,
        status_callback=lambda: "[APP] status",
    )
    update = _fake_update("12345")

    await controller.handle_status(update, SimpleNamespace())

    assert update.effective_message.replies == ["[APP] status"]


@pytest.mark.asyncio
async def test_help_command_lists_enabled_commands() -> None:
    async def reload_callback() -> ReloadResult:
        raise AssertionError("help should not call reload")

    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=TelegramRemoteControlConfig(
            enabled=True,
            allowed_chat_ids=["12345"],
            commands={"reload": True, "status": False, "help": True},
        ),
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )
    update = _fake_update("12345")

    await controller.handle_help(update, SimpleNamespace())

    assert update.effective_message.replies == ["Commands:\n/reload\n/help"]


def test_update_remote_control_replaces_allowed_chat_ids() -> None:
    async def reload_callback() -> ReloadResult:
        raise AssertionError("not used")

    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=TelegramRemoteControlConfig(
            enabled=True,
            allowed_chat_ids=["1"],
        ),
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )

    controller.update_remote_control(
        TelegramRemoteControlConfig(enabled=True, allowed_chat_ids=["2"])
    )

    assert controller.is_chat_allowed("1") is False
    assert controller.is_chat_allowed("2") is True
```

- [ ] **Step 2: Run remote controller tests and verify failure**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_telegram_remote.py -q
```

Expected: FAIL because `src.utils.telegram_remote` does not exist.

- [ ] **Step 3: Implement `src/utils/telegram_remote.py`**

Create `src/utils/telegram_remote.py`:

```python
"""Telegram command 기반 원격제어 컨트롤러."""

from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from src.utils.config import TelegramRemoteControlConfig
from src.utils.reload import ReloadResult

ReloadCallback = Callable[[], Awaitable[ReloadResult]]
StatusCallback = Callable[[], str]


class TelegramRemoteController:
    """Telegram command를 수신해 허용된 원격제어 요청만 실행합니다."""

    def __init__(
        self,
        *,
        bot_token: str,
        remote_control: TelegramRemoteControlConfig,
        reload_callback: ReloadCallback,
        status_callback: StatusCallback,
    ) -> None:
        self._bot_token = bot_token
        self._remote_control = remote_control
        self._reload_callback = reload_callback
        self._status_callback = status_callback
        self._application: Application[Any, Any, Any, Any, Any, Any] | None = None

    def update_remote_control(self, remote_control: TelegramRemoteControlConfig) -> None:
        """reload 후 원격제어 설정을 교체합니다."""
        self._remote_control = remote_control

    def is_chat_allowed(self, chat_id: str | int | None) -> bool:
        """chat id가 원격제어 허용 목록에 포함되는지 확인합니다."""
        if chat_id is None or not self._remote_control.enabled:
            return False
        return str(chat_id) in self._remote_control.allowed_chat_ids

    async def start(self) -> None:
        """Telegram polling을 시작합니다."""
        if not self._remote_control.enabled:
            logger.info("Telegram remote control disabled")
            return

        self._application = ApplicationBuilder().token(self._bot_token).build()
        self._application.add_handler(CommandHandler("reload", self.handle_reload))
        self._application.add_handler(CommandHandler("status", self.handle_status))
        self._application.add_handler(CommandHandler("help", self.handle_help))

        await self._application.initialize()
        await self._application.start()
        if self._application.updater is None:
            raise RuntimeError("Telegram updater is not available")
        await self._application.updater.start_polling()
        logger.info("Telegram remote control started")

    async def stop(self) -> None:
        """Telegram polling을 중지합니다."""
        if self._application is None:
            return
        if self._application.updater is not None:
            await self._application.updater.stop()
        await self._application.stop()
        await self._application.shutdown()
        self._application = None
        logger.info("Telegram remote control stopped")

    async def handle_reload(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """허용된 chat의 /reload 명령을 처리합니다."""
        del context
        if not self._is_authorized(update, "reload"):
            return
        if not self._remote_control.commands.reload:
            await self._reply(update, "reload command disabled")
            return
        result = await self._reload_callback()
        await self._reply(update, result.message)

    async def handle_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """허용된 chat의 /status 명령을 처리합니다."""
        del context
        if not self._is_authorized(update, "status"):
            return
        if not self._remote_control.commands.status:
            await self._reply(update, "status command disabled")
            return
        await self._reply(update, self._status_callback())

    async def handle_help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """허용된 chat의 /help 명령을 처리합니다."""
        del context
        if not self._is_authorized(update, "help"):
            return
        if not self._remote_control.commands.help:
            await self._reply(update, "help command disabled")
            return

        commands: list[str] = []
        if self._remote_control.commands.reload:
            commands.append("/reload")
        if self._remote_control.commands.status:
            commands.append("/status")
        if self._remote_control.commands.help:
            commands.append("/help")
        await self._reply(update, "Commands:\n" + "\n".join(commands))

    def _is_authorized(self, update: Update, command: str) -> bool:
        chat_id = self._chat_id(update)
        if self.is_chat_allowed(chat_id):
            return True
        logger.warning(
            "Unauthorized Telegram remote command ignored: command={} chat_id={}",
            command,
            chat_id,
        )
        return False

    @staticmethod
    def _chat_id(update: Update) -> str | None:
        if update.effective_chat is None:
            return None
        return str(update.effective_chat.id)

    @staticmethod
    async def _reply(update: Update, text: str) -> None:
        if update.effective_message is None:
            logger.warning("Telegram remote command has no effective message")
            return
        await update.effective_message.reply_text(text)
```

- [ ] **Step 4: Run remote controller tests**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_telegram_remote.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit remote controller**

Run:

```bash
git add src/utils/telegram_remote.py tests/test_utils/test_telegram_remote.py
git commit -m "feat: add telegram remote controller"
```

## Task 4: App Runner Integration

**Files:**
- Modify: `src/main.py`
- Modify: `src/utils/app_runner.py`
- Modify: `tests/test_main.py`
- Modify: `tests/test_utils/test_app_runner.py`

- [ ] **Step 1: Write failing CLI/app runner tests**

Add this test to `tests/test_main.py`:

```python
@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_start_passes_runtime_reload_options_to_run_app(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
    temp_config_dir: Path,
) -> None:
    """start는 reload에 필요한 config_dir/log override를 run_app에 전달해야 한다."""
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG", "json_logs": False},
        telegram={"enabled": False},
    )

    custom_config = temp_config_dir / "custom.yaml"
    result = runner.invoke(
        app,
        ["start", "--config", str(custom_config), "--log-level", "ERROR"],
    )

    assert result.exit_code == 0
    coroutine = mock_asyncio_run.call_args.args[0]
    assert coroutine.cr_frame is not None
    assert coroutine.cr_frame.f_locals["config_dir"] == temp_config_dir
    assert coroutine.cr_frame.f_locals["log_level"] == "ERROR"
    coroutine.close()
```

Replace `tests/test_utils/test_app_runner.py` with:

```python
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.app_runner import run_app
from src.utils.config import Settings


@pytest.mark.asyncio
async def test_run_app_shutdown() -> None:
    settings = Settings()

    with (
        patch("src.utils.app_runner.GracefulShutdown") as mock_shutdown_class,
        patch(
            "src.utils.app_runner.TelegramNotifier.send_message",
            new_callable=AsyncMock,
        ) as mock_send,
    ):
        mock_shutdown = AsyncMock()
        mock_shutdown.should_exit = True
        mock_shutdown.__aenter__.return_value = mock_shutdown
        mock_shutdown.__aexit__.return_value = None
        mock_shutdown_class.return_value = mock_shutdown

        await run_app(settings, "prod")

    assert mock_send.await_args_list[0].args[0] == "[JPPT] 🚀 start\nEnv : prod"
    assert mock_send.await_args_list[1].args[0] == "[JPPT] 🛑 stop\nReason : gracefully"


@pytest.mark.asyncio
async def test_run_app_starts_and_stops_remote_controller() -> None:
    settings = Settings(
        telegram={
            "enabled": True,
            "bot_token": "token",
            "chat_id": "12345",
            "remote_control": {
                "enabled": True,
                "allowed_chat_ids": ["12345"],
            },
        }
    )

    with (
        patch("src.utils.app_runner.GracefulShutdown") as mock_shutdown_class,
        patch("src.utils.app_runner.TelegramNotifier.send_message", new_callable=AsyncMock),
        patch("src.utils.app_runner.TelegramRemoteController") as mock_controller_class,
    ):
        mock_shutdown = AsyncMock()
        mock_shutdown.should_exit = True
        mock_shutdown.__aenter__.return_value = mock_shutdown
        mock_shutdown.__aexit__.return_value = None
        mock_shutdown_class.return_value = mock_shutdown
        mock_controller = AsyncMock()
        mock_controller_class.return_value = mock_controller

        await run_app(settings, "prod", config_dir=Path("/tmp/config"))

    mock_controller.start.assert_awaited_once()
    mock_shutdown.register_cleanup.assert_called_once_with(mock_controller.stop)


@pytest.mark.asyncio
async def test_run_app_does_not_start_remote_controller_when_disabled() -> None:
    settings = Settings(telegram={"enabled": False})

    with (
        patch("src.utils.app_runner.GracefulShutdown") as mock_shutdown_class,
        patch("src.utils.app_runner.TelegramNotifier.send_message", new_callable=AsyncMock),
        patch("src.utils.app_runner.TelegramRemoteController") as mock_controller_class,
    ):
        mock_shutdown = AsyncMock()
        mock_shutdown.should_exit = True
        mock_shutdown.__aenter__.return_value = mock_shutdown
        mock_shutdown.__aexit__.return_value = None
        mock_shutdown_class.return_value = mock_shutdown

        await run_app(settings, "prod")

    mock_controller_class.assert_not_called()
```

- [ ] **Step 2: Run integration tests and verify failure**

Run:

```bash
uv run pytest --no-cov tests/test_main.py tests/test_utils/test_app_runner.py -q
```

Expected: FAIL because `run_app()` does not accept reload runtime options and app runner does not import `TelegramRemoteController`.

- [ ] **Step 3: Update `src/main.py`**

Add a helper near `_load_settings`:

```python
def _resolve_config_dir(config: str | None) -> Path | None:
    """CLI config 옵션에서 config directory 계약을 계산합니다."""
    if config is None:
        return None
    return Path(config).parent
```

Replace `_load_settings` with:

```python
def _load_settings(env: str, config: str | None) -> Settings:
    """CLI 옵션에 따라 설정을 로드합니다."""
    config_dir = _resolve_config_dir(config)
    if config_dir is not None:
        return load_config(env=env, config_dir=config_dir)
    return load_config(env=env)
```

In `start()`, compute `config_dir` and pass runtime options:

```python
    config_dir = _resolve_config_dir(config)
    settings = _load_settings(env, config)
```

Replace the final `asyncio.run()` call in `start()`:

```python
    asyncio.run(
        run_app(
            settings,
            env,
            config_dir=config_dir,
            log_level=log_level,
            verbose=verbose,
        )
    )
```

Leave `batch()` unchanged except for `_load_settings()` using `_resolve_config_dir()` internally.

- [ ] **Step 4: Update `src/utils/app_runner.py`**

Replace `src/utils/app_runner.py` with this implementation:

```python
"""장시간 실행되는 데몬을 위한 앱 모드 실행기.

이 모듈은 시그널 처리와 graceful shutdown을 지원하는 앱 모드 실행을 담당합니다.
"""

import asyncio
from pathlib import Path

from loguru import logger

from src.utils.config import Settings
from src.utils.logger import setup_logger
from src.utils.reload import ReloadCoordinator
from src.utils.signals import GracefulShutdown, setup_signal_handlers
from src.utils.telegram import TelegramNotifier
from src.utils.telegram_remote import TelegramRemoteController


def _build_log_file(app_name: str) -> Path:
    """start 모드 로그 파일 경로를 생성합니다."""
    return Path.home() / "logs" / f"{app_name}.log"


def _resolve_log_level(config_level: str, log_level: str | None, verbose: bool) -> str:
    """CLI override와 config 값을 합쳐 실제 로그 레벨을 결정합니다."""
    if verbose:
        return "DEBUG"
    if log_level:
        return log_level.upper()
    return config_level


def _configure_logger(settings: Settings, log_level: str | None, verbose: bool) -> None:
    """현재 settings 기준으로 logger를 재설정합니다."""
    effective_log_level = _resolve_log_level(settings.logging.level, log_level, verbose)
    setup_logger(
        level=effective_log_level,
        log_file=_build_log_file(settings.app.name),
        format_str=settings.logging.format,
        json_logs=settings.logging.json_logs,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )


def _build_notifier(settings: Settings) -> TelegramNotifier:
    """현재 settings 기준으로 Telegram notifier를 생성합니다."""
    return TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
        enabled=settings.telegram.enabled,
        silent_time=settings.telegram.silent_time,
    )


async def run_app(
    settings: Settings,
    env: str,
    *,
    config_dir: Path | None = None,
    log_level: str | None = None,
    verbose: bool = False,
) -> None:
    """앱 모드를 실행합니다 (graceful shutdown 지원 데몬).

    Args:
        settings: 애플리케이션 설정
        env: 실행 환경 이름
        config_dir: reload 시 다시 읽을 config directory
        log_level: CLI 로그 레벨 override
        verbose: DEBUG 로그 강제 여부
    """
    logger.info("App mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    current_settings = settings
    notifier = _build_notifier(current_settings)
    controller: TelegramRemoteController | None = None

    async def apply_settings(next_settings: Settings) -> None:
        nonlocal current_settings, notifier, controller
        _configure_logger(next_settings, log_level, verbose)
        current_settings = next_settings
        notifier = _build_notifier(next_settings)
        if controller is not None:
            controller.update_remote_control(next_settings.telegram.remote_control)

    coordinator = ReloadCoordinator(
        settings=current_settings,
        env=env,
        config_dir=config_dir,
        apply_settings=apply_settings,
    )

    if current_settings.telegram.remote_control.enabled:
        controller = TelegramRemoteController(
            bot_token=current_settings.telegram.bot_token,
            remote_control=current_settings.telegram.remote_control,
            reload_callback=coordinator.reload,
            status_callback=coordinator.status_message,
        )
        await controller.start()

    await notifier.send_message(
        TelegramNotifier.format_status_message(
            current_settings.app.name,
            "start",
            env=env,
        )
    )

    shutdown = GracefulShutdown()
    setup_signal_handlers(shutdown)
    if controller is not None:
        shutdown.register_cleanup(controller.stop)

    try:
        async with shutdown:
            logger.info("App running (Press Ctrl+C to stop)")

            iteration = 0
            while not shutdown.should_exit:
                iteration += 1
                logger.debug(f"App iteration {iteration}")
                await asyncio.sleep(5)

        logger.info("App mode stopped")
        await notifier.send_message(
            TelegramNotifier.format_status_message(
                current_settings.app.name,
                "stop",
                reason="gracefully",
            )
        )
    except Exception as e:
        logger.error(f"App crashed: {e}")
        raise
```

- [ ] **Step 5: Run focused app tests**

Run:

```bash
uv run pytest --no-cov tests/test_main.py tests/test_utils/test_app_runner.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit app runner integration**

Run:

```bash
git add src/main.py src/utils/app_runner.py tests/test_main.py tests/test_utils/test_app_runner.py
git commit -m "feat: wire telegram remote reload into app runner"
```

## Task 5: Documentation and Full Verification

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `docs/FRAMEWORK_GUIDE.md`

- [ ] **Step 1: Update operator documentation**

Add this section to `README.md` immediately after the existing `### Telegram Setup` section:

````markdown
### Telegram Remote Control

`start` mode can optionally accept Telegram commands from allowlisted chat IDs.
Remote control is disabled by default.

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "YOUR_CHAT_ID"
    commands:
      reload: true
      status: true
      help: true
```

Available commands:

- `/reload`: reload `config/{env}.yaml`; keep the previous settings if validation fails.
- `/status`: show app name, env, uptime, remote control state, and last reload state.
- `/help`: show enabled commands.

Unauthorized chat IDs are ignored and cannot execute commands.
````

Add this section to `README.ko.md` immediately after the existing `### 텔레그램 설정` section:

````markdown
### Telegram 원격제어

`start` 모드는 허용된 Telegram chat id에서 온 명령만 선택적으로 처리할 수 있습니다.
원격제어 기본값은 비활성화입니다.

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "YOUR_CHAT_ID"
    commands:
      reload: true
      status: true
      help: true
```

명령:

- `/reload`: `config/{env}.yaml`을 다시 읽습니다. 검증 실패 시 기존 설정을 유지합니다.
- `/status`: 앱 이름, env, uptime, 원격제어 상태, 마지막 reload 상태를 보여줍니다.
- `/help`: 활성화된 명령만 보여줍니다.

허용되지 않은 chat id의 명령은 실행하지 않습니다.
````

Add this section to `docs/FRAMEWORK_GUIDE.md` immediately after the existing `### Telegram Notifications` section:

````markdown
### Telegram 원격제어

`start` 모드는 허용된 Telegram chat id에서 온 명령만 선택적으로 처리할 수 있습니다.
원격제어 기본값은 비활성화입니다.

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "YOUR_CHAT_ID"
    commands:
      reload: true
      status: true
      help: true
```

명령:

- `/reload`: `config/{env}.yaml`을 다시 읽습니다. 검증 실패 시 기존 설정을 유지합니다.
- `/status`: 앱 이름, env, uptime, 원격제어 상태, 마지막 reload 상태를 보여줍니다.
- `/help`: 활성화된 명령만 보여줍니다.

허용되지 않은 chat id의 명령은 실행하지 않습니다.
````

- [ ] **Step 2: Run focused tests**

Run:

```bash
uv run pytest --no-cov tests/test_utils/test_config.py tests/test_utils/test_reload.py tests/test_utils/test_telegram_remote.py tests/test_utils/test_app_runner.py tests/test_main.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
uv run pytest --no-cov
```

Expected: PASS.

- [ ] **Step 4: Run lint**

Run:

```bash
uv run ruff check src tests
```

Expected: PASS.

- [ ] **Step 5: Run type check**

Run:

```bash
uv run mypy src --exclude src/logs
```

Expected: PASS.

- [ ] **Step 6: Commit documentation and verification fixes**

Run:

```bash
git add README.md README.ko.md docs/FRAMEWORK_GUIDE.md
git commit -m "docs: document telegram remote control"
```

## Self-Review Checklist

- Spec coverage: config model, `/reload`, `/status`, `/help`, allowed chat id access control, reload failure preserving old settings, logging/notifier refresh, and batch exclusion are all assigned to tasks.
- Red-flag scan: no unresolved implementation gaps are present in this plan.
- Type consistency: `TelegramRemoteControlConfig`, `ReloadCoordinator`, `ReloadResult`, and `TelegramRemoteController` names are defined before later tasks use them.
- Scope check: Telegram webhook, local signal reload, `run.sh reload`, shell execution, and domain trading commands remain excluded.
