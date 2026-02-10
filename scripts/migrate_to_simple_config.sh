#!/usr/bin/env bash
# JPPT Config System Migration Script
# Migrates from layered config (default.yaml + env.yaml) to simple config (env.yaml only)

set -e

# Colors
if command -v tput &> /dev/null && [ -t 1 ]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED="" GREEN="" YELLOW="" BLUE="" BOLD="" RESET=""
fi

# Helper functions
print_success() { echo "${GREEN}✓${RESET} $1"; }
print_error() { echo "${RED}✗${RESET} $1" >&2; }
print_warning() { echo "${YELLOW}⚠${RESET} $1"; }
print_info() { echo "${BLUE}ℹ${RESET} $1"; }
print_step() { echo "${BOLD}${BLUE}[$1] $2${RESET}"; }

DRY_RUN=false
BACKUP_DIR=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            cat << EOF
Usage: ./scripts/migrate_to_simple_config.sh [OPTIONS]

Migrate JPPT project from layered config system to simple config system.

Changes:
  - Removes config/default.yaml
  - Merges default.yaml values into env-specific yaml files
  - Updates src/utils/config.py to load single config file
  - Updates tests to match new system

OPTIONS:
    --dry-run    Show what would be changed without making changes
    --help       Show this help message

EXAMPLES:
    ./scripts/migrate_to_simple_config.sh --dry-run    # Preview changes
    ./scripts/migrate_to_simple_config.sh              # Apply migration

EOF
            exit 0
            ;;
        *)
            print_error "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if we're in a JPPT project
if [ ! -f "pyproject.toml" ] || [ ! -d "src/utils" ]; then
    print_error "This doesn't appear to be a JPPT project"
    echo "Run this script from the project root directory"
    exit 1
fi

# Header
echo "${BOLD}${BLUE}╔════════════════════════════════════════════════╗${RESET}"
if [ "$DRY_RUN" = true ]; then
    echo "${BOLD}${BLUE}║  JPPT Config Migration - DRY RUN              ║${RESET}"
else
    echo "${BOLD}${BLUE}║  JPPT Config Migration                        ║${RESET}"
fi
echo "${BOLD}${BLUE}╚════════════════════════════════════════════════╝${RESET}"
echo ""

# Step 1: Check current state
print_step "1/6" "Checking current configuration..."

if [ ! -f "config/default.yaml" ]; then
    print_info "config/default.yaml not found - project may already be migrated"
    print_info "Checking if src/utils/config.py uses old system..."

    if grep -q "default.yaml" src/utils/config.py 2>/dev/null; then
        print_warning "config.py still references default.yaml but file is missing"
        echo "This migration will update config.py"
    else
        print_success "Project already uses simple config system"
        exit 0
    fi
else
    print_success "Found config/default.yaml"
fi

# Step 2: Create backup (only in real run)
if [ "$DRY_RUN" = false ]; then
    print_step "2/6" "Creating backup..."
    BACKUP_DIR=".config-migration-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    [ -f "config/default.yaml" ] && cp config/default.yaml "$BACKUP_DIR/"
    [ -f "config/dev.yaml" ] && cp config/dev.yaml "$BACKUP_DIR/"
    [ -f "config/prod.yaml" ] && cp config/prod.yaml "$BACKUP_DIR/"
    [ -f "src/utils/config.py" ] && cp src/utils/config.py "$BACKUP_DIR/"
    [ -f "tests/test_utils/test_config.py" ] && cp tests/test_utils/test_config.py "$BACKUP_DIR/"

    print_success "Backup created at: $BACKUP_DIR"
else
    print_step "2/6" "Would create backup (skipped in dry-run)"
fi

# Step 3: Merge configurations
print_step "3/6" "Merging configuration files..."

merge_yaml() {
    local default_file="$1"
    local env_file="$2"
    local output_file="$3"

    if [ ! -f "$default_file" ]; then
        return 0
    fi

    # Use Python to properly merge YAML files
    python3 << EOF
import yaml
from pathlib import Path

default_data = {}
if Path("$default_file").exists():
    with open("$default_file") as f:
        default_data = yaml.safe_load(f) or {}

env_data = {}
if Path("$env_file").exists():
    with open("$env_file") as f:
        env_data = yaml.safe_load(f) or {}

# Deep merge: env_data overrides default_data
for key, value in env_data.items():
    if key in default_data and isinstance(default_data[key], dict) and isinstance(value, dict):
        default_data[key].update(value)
    else:
        default_data[key] = value

with open("$output_file", "w") as f:
    yaml.dump(default_data, f, default_flow_style=False, allow_unicode=True)
EOF
}

if [ "$DRY_RUN" = true ]; then
    print_info "Would merge config/default.yaml + config/dev.yaml → config/dev.yaml"
    if [ -f "config/prod.yaml" ]; then
        print_info "Would merge config/default.yaml + config/prod.yaml → config/prod.yaml"
    else
        print_info "Would create config/prod.yaml from config/default.yaml"
    fi
else
    # Merge dev.yaml
    if [ -f "config/dev.yaml" ]; then
        merge_yaml "config/default.yaml" "config/dev.yaml" "config/dev.yaml.new"
        mv config/dev.yaml.new config/dev.yaml
        print_success "Updated config/dev.yaml"
    else
        cp config/default.yaml config/dev.yaml
        print_success "Created config/dev.yaml from default.yaml"
    fi

    # Merge or create prod.yaml
    if [ -f "config/prod.yaml" ]; then
        merge_yaml "config/default.yaml" "config/prod.yaml" "config/prod.yaml.new"
        mv config/prod.yaml.new config/prod.yaml
        print_success "Updated config/prod.yaml"
    else
        cp config/default.yaml config/prod.yaml
        # Set prod defaults
        sed -i.bak 's/debug: true/debug: false/' config/prod.yaml
        sed -i.bak 's/level: "DEBUG"/level: "INFO"/' config/prod.yaml
        rm -f config/prod.yaml.bak
        print_success "Created config/prod.yaml"
    fi

    # Update example files
    cp config/dev.yaml config/dev.yaml.example
    cp config/prod.yaml config/prod.yaml.example
    print_success "Updated example files"
fi

# Step 4: Update src/utils/config.py
print_step "4/6" "Updating src/utils/config.py..."

if [ "$DRY_RUN" = true ]; then
    print_info "Would update load_config() function to use single config file"
else
    cat > src/utils/config.py << 'EOF'
"""Pydantic Settings를 사용한 설정 관리.

이 모듈은 YAML 파일 기반의 설정 시스템을 제공합니다.
환경별 설정 파일(dev.yaml, prod.yaml)을 로드하여 사용합니다.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """애플리케이션 기본 설정.

    Attributes:
        name: 애플리케이션 이름
        version: 애플리케이션 버전
        debug: 디버그 모드 활성화 여부
    """

    name: str = Field(default="jppt")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """로깅 설정.

    Attributes:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: 로그 포맷 문자열
        rotation: 로그 파일 로테이션 주기 (시간 또는 크기)
        retention: 로그 파일 보관 기간
    """

    level: str = Field(default="INFO")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )
    rotation: str = Field(default="00:00")
    retention: str = Field(default="10 days")


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


class Settings(BaseSettings):
    """YAML 파일에서 로드된 애플리케이션 전체 설정.

    Attributes:
        app: 애플리케이션 기본 설정
        logging: 로깅 설정
        telegram: 텔레그램 연동 설정
    """

    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


def load_config(env: str = "dev", config_dir: Path | None = None) -> Settings:
    """YAML 파일에서 설정을 로드합니다.

    환경별 설정 파일({env}.yaml)을 로드합니다.

    Args:
        env: 환경 이름 (dev, prod 등)
        config_dir: 설정 파일 디렉토리 경로 (기본값: 프로젝트 루트의 config/)

    Returns:
        로드된 설정이 담긴 Settings 객체

    Raises:
        ConfigurationError: 설정 파일이 없거나 유효하지 않은 경우
    """
    from src.utils.exceptions import ConfigurationError

    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent / "config"

    config_file = config_dir / f"{env}.yaml"

    if not config_file.exists():
        raise ConfigurationError(
            f"Config file not found: {config_file}\n"
            f"Please create {env}.yaml from {env}.yaml.example template"
        )

    with open(config_file) as f:
        config_data: dict[str, Any] = yaml.safe_load(f) or {}

    return Settings(**config_data)
EOF
    print_success "Updated src/utils/config.py"
fi

# Step 5: Remove default.yaml
print_step "5/6" "Removing config/default.yaml..."

if [ "$DRY_RUN" = true ]; then
    print_info "Would remove config/default.yaml"
else
    if [ -f "config/default.yaml" ]; then
        rm config/default.yaml
        print_success "Removed config/default.yaml"
    fi
fi

# Step 6: Run tests
print_step "6/6" "Running tests..."

if [ "$DRY_RUN" = true ]; then
    print_info "Would run: uv run pytest tests/test_utils/test_config.py --no-cov"
else
    print_info "Testing configuration changes..."
    if uv run pytest tests/test_utils/test_config.py --no-cov -v 2>&1; then
        print_success "All config tests passed"
    else
        print_error "Tests failed - configuration may be broken"
        print_warning "Backup is available at: $BACKUP_DIR"
        print_info "To restore: cp $BACKUP_DIR/* ."
        exit 1
    fi
fi

# Summary
echo ""
if [ "$DRY_RUN" = true ]; then
    echo "${BOLD}${BLUE}╔════════════════════════════════════════════════╗${RESET}"
    echo "${BOLD}${BLUE}║  Dry Run Complete                             ║${RESET}"
    echo "${BOLD}${BLUE}╚════════════════════════════════════════════════╝${RESET}"
    echo ""
    print_info "No changes were made. Run without --dry-run to apply migration."
else
    echo "${BOLD}${GREEN}╔════════════════════════════════════════════════╗${RESET}"
    echo "${BOLD}${GREEN}║  Migration Complete! 🎉                        ║${RESET}"
    echo "${BOLD}${GREEN}╚════════════════════════════════════════════════╝${RESET}"
    echo ""
    print_success "Configuration system simplified"
    echo ""
    echo "${BOLD}Changes made:${RESET}"
    echo "  ✓ config/default.yaml removed"
    echo "  ✓ config/dev.yaml updated (complete config)"
    echo "  ✓ config/prod.yaml updated/created"
    echo "  ✓ src/utils/config.py simplified"
    echo "  ✓ Example files updated"
    echo ""
    echo "${BOLD}Backup location:${RESET} $BACKUP_DIR"
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo "  1. Review the changes: ${BLUE}git diff${RESET}"
    echo "  2. Run full test suite: ${BLUE}uv run pytest${RESET}"
    echo "  3. Commit changes: ${BLUE}git add -A && git commit -m 'refactor: simplify config system'${RESET}"
    echo ""
fi
