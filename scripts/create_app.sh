#!/usr/bin/env bash
# JPPT (JKLEE Python Project Template) - Initial Setup Script
# This script sets up a complete development environment in one command

set -e  # Exit on error

# Clear any existing virtual environment from parent template
unset VIRTUAL_ENV

# ============================================================================
# Section 1: Colors and Helper Functions
# ============================================================================

# Colors using tput (portable across macOS/Linux)
if command -v tput &> /dev/null && [ -t 1 ]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    BOLD=""
    RESET=""
fi

# Helper functions
print_step() {
    echo "${BOLD}${BLUE}[$1/$2] $3${RESET}"
}

print_success() {
    echo "${GREEN}✓${RESET} $1"
}

print_error() {
    echo "${RED}✗${RESET} $1" >&2
}

print_warning() {
    echo "${YELLOW}⚠${RESET} $1"
}

print_info() {
    echo "${BLUE}ℹ${RESET} $1"
}

# ============================================================================
# Section 2: Validation Functions
# ============================================================================

check_python() {
    print_step 1 7 "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.11 or higher:"
        echo "  macOS: brew install python@3.11"
        echo "  Linux: sudo apt install python3.11"
        return 1
    fi

    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    local major=$(echo "$python_version" | cut -d. -f1)
    local minor=$(echo "$python_version" | cut -d. -f2)

    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
        print_error "Python 3.11+ required, but found Python $python_version"
        echo "Please upgrade Python:"
        echo "  macOS: brew install python@3.11"
        echo "  Linux: sudo apt install python3.11"
        return 1
    fi

    print_success "Python $python_version found"
    return 0
}

check_uv() {
    print_step 2 7 "Checking uv installation..."

    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed"
        echo ""
        echo "Install uv with:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
        echo "Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        return 1
    fi

    local uv_version=$(uv --version 2>&1)
    print_success "uv found: $uv_version"
    return 0
}

validate_app_name() {
    local app_name="$1"

    if [ -z "$app_name" ]; then
        print_error "App name is required"
        echo ""
        echo "Usage: ./scripts/create_app.sh <app-name> [OPTIONS]"
        echo "Example: ./scripts/create_app.sh my-awesome-app"
        return 1
    fi

    # Check valid characters (lowercase, numbers, hyphen, underscore)
    if ! echo "$app_name" | grep -qE '^[a-z0-9][a-z0-9_-]*$'; then
        print_error "Invalid app name: '$app_name'"
        echo ""
        echo "App name must:"
        echo "  - Start with lowercase letter or number"
        echo "  - Contain only lowercase letters, numbers, hyphens, underscores"
        echo ""
        echo "Valid examples: my-app, my_app, myapp123"
        echo "Invalid examples: MyApp, -myapp, my app"
        return 1
    fi

    print_success "App name '$app_name' is valid"
    return 0
}

check_gh() {
    print_step 3 7 "Checking GitHub CLI installation..."

    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        echo ""
        echo "Install GitHub CLI:"
        echo "  macOS: brew install gh"
        echo "  Linux: See https://cli.github.com/"
        echo ""
        return 1
    fi

    local gh_version=$(gh --version 2>&1 | head -n1)
    print_success "GitHub CLI found: $gh_version"

    # Check authentication
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI is not authenticated"
        echo ""
        echo "Please authenticate with:"
        echo "  gh auth login"
        echo ""
        return 1
    fi

    print_success "GitHub CLI is authenticated"
    return 0
}

check_target_directory() {
    local target_dir="$1"

    print_step 4 7 "Checking target directory..."

    if [ -d "$target_dir" ]; then
        print_warning "Directory already exists: $target_dir"
        echo ""
        read -p "Delete existing directory and continue? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing directory..."
            rm -rf "$target_dir"
            print_success "Existing directory removed"
        else
            print_error "Aborted by user"
            return 1
        fi
    fi

    print_success "Target directory is available: $target_dir"
    return 0
}

copy_template() {
    local source_dir="$1"
    local target_dir="$2"

    print_step 5 7 "Copying template to $target_dir..."

    # Create parent directory if needed
    mkdir -p "$(dirname "$target_dir")"

    # Copy with rsync, excluding build artifacts and local config
    if ! rsync -av \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='.mypy_cache' \
        --exclude='.ruff_cache' \
        --exclude='htmlcov/' \
        --exclude='logs/' \
        --exclude='config/dev.yaml' \
        --exclude='config/prod.yaml' \
        --exclude='docs/' \
        "$source_dir/" "$target_dir/"; then
        print_error "Failed to copy template"
        return 1
    fi

    print_success "Template copied successfully"
    return 0
}

init_git() {
    local target_dir="$1"

    print_step 6 7 "Initializing git repository..."

    cd "$target_dir" || return 1

    if ! git init; then
        print_error "Failed to initialize git repository"
        return 1
    fi

    if ! git add .; then
        print_error "Failed to stage files"
        return 1
    fi

    if ! git commit -m "Initial commit from JPPT template"; then
        print_error "Failed to create initial commit"
        return 1
    fi

    print_success "Git repository initialized"
    return 0
}

substitute_project_name() {
    local app_name="$1"
    local target_dir="$2"

    print_step 7 7 "Substituting project name..."

    cd "$target_dir" || return 1

    # 1. Update config/default.yaml
    if [ -f "config/default.yaml" ]; then
        sed -i.bak "s/name: \".*\"/name: \"$app_name\"/" config/default.yaml
        rm -f config/default.yaml.bak
        print_success "Updated config/default.yaml"
    fi

    # 2. Update pyproject.toml
    if [ -f "pyproject.toml" ]; then
        sed -i.bak "s/name = \"jppt\"/name = \"$app_name\"/" pyproject.toml
        rm -f pyproject.toml.bak
        print_success "Updated pyproject.toml"
    fi

    # 3. Create minimal README.md
    cat > README.md << EOF
# $app_name

Created from [JPPT](https://github.com/taein2301/JPPT) template.

## Setup

\`\`\`bash
./scripts/create_app.sh
\`\`\`

## Run

\`\`\`bash
./run.sh              # Start mode (dev)
./run.sh batch        # Batch mode (dev)
\`\`\`

## Development

\`\`\`bash
uv run pytest                 # Run tests
uv run ruff format .          # Format code
uv run mypy src/              # Type check
\`\`\`
EOF
    print_success "Created README.md"

    # 4. Create docs directory and empty PRD.md
    mkdir -p docs
    touch docs/PRD.md
    print_success "Created docs/PRD.md"

    # Commit the substitutions
    git add config/default.yaml pyproject.toml README.md docs/PRD.md
    git commit -m "chore: update project name to $app_name"

    return 0
}

create_github_repo() {
    local app_name="$1"
    local target_dir="$2"

    echo ""
    print_info "Creating GitHub repository..."

    cd "$target_dir" || return 1

    # Check if repository already exists
    local github_user=$(gh api user -q .login 2>/dev/null)
    if gh repo view "$github_user/$app_name" &>/dev/null; then
        print_warning "GitHub repository already exists: $github_user/$app_name"
        echo ""
        read -p "Delete existing repository and continue? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deleting existing repository..."
            if gh repo delete "$github_user/$app_name" --yes; then
                print_success "Existing repository deleted"
            else
                print_error "Failed to delete existing repository"
                return 1
            fi
        else
            print_error "Aborted by user"
            return 1
        fi
    fi

    if ! gh repo create "$app_name" \
        --private \
        --source=. \
        --description="Created from JPPT template" \
        --push; then
        print_error "Failed to create GitHub repository"
        echo ""
        print_warning "Local project created successfully at: $target_dir"
        print_info "You can create the repository manually:"
        print_info "  cd $target_dir"
        print_info "  gh repo create $app_name --private --source=. --push"
        return 1
    fi

    local repo_url=$(gh repo view --json url -q .url)
    print_success "GitHub repository created: $repo_url"
    print_success "Initial commit pushed to main branch"

    return 0
}

# ============================================================================
# Section 3: Installation Functions
# ============================================================================

install_deps() {
    print_step 3 6 "Installing dependencies..."

    if ! uv sync --all-extras; then
        print_error "Failed to install dependencies"
        echo "Try running: uv sync --all-extras"
        return 1
    fi

    print_success "Dependencies installed successfully"
    return 0
}

setup_config() {
    print_step 4 6 "Setting up configuration files..."

    local config_example="config/dev.yaml.example"
    local config_target="config/dev.yaml"

    if [ ! -f "$config_example" ]; then
        print_warning "Example config not found: $config_example"
        return 0
    fi

    if [ -f "$config_target" ]; then
        print_info "Configuration file already exists: $config_target (skipping)"
    else
        if cp "$config_example" "$config_target"; then
            print_success "Created $config_target"
        else
            print_error "Failed to create $config_target"
            return 1
        fi
    fi

    return 0
}

setup_dirs() {
    print_step 5 6 "Creating directories..."

    if mkdir -p logs; then
        print_success "Created logs/ directory"
    else
        print_warning "Failed to create logs/ directory (may already exist)"
    fi

    return 0
}

install_hooks() {
    if [ "$SKIP_HOOKS" = true ]; then
        print_info "Skipping pre-commit hooks installation (--no-hooks)"
        return 0
    fi

    print_step 6 6 "Installing pre-commit hooks..."

    if [ ! -f ".pre-commit-config.yaml" ]; then
        print_warning "No .pre-commit-config.yaml found, skipping hooks installation"
        return 0
    fi

    if uv run pre-commit install 2>&1; then
        print_success "Pre-commit hooks installed"
    else
        print_warning "Failed to install pre-commit hooks (non-critical, continuing...)"
        print_info "You can manually install later with: uv run pre-commit install"
    fi

    return 0
}

run_tests_optional() {
    if [ "$SKIP_TESTS" = true ]; then
        print_info "Skipping initial tests (--skip-tests)"
        return 0
    fi

    echo ""
    echo "${BOLD}Running initial tests...${RESET}"

    if uv run pytest -v; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed, but setup is complete"
        print_info "Review test output above and fix any issues"
    fi

    return 0
}

# ============================================================================
# Section 4: Main Function
# ============================================================================

print_usage() {
    cat << EOF
Usage: ./scripts/create_app.sh <app-name> [OPTIONS]

Create a new project from JPPT template.

ARGUMENTS:
    <app-name>      Name of the new project (lowercase, numbers, -, _ only)

OPTIONS:
    --skip-tests    Skip running initial tests
    --no-hooks      Skip pre-commit hooks installation
    --help          Show this help message

EXAMPLES:
    ./scripts/create_app.sh my-awesome-app
    ./scripts/create_app.sh my-app --skip-tests
    ./scripts/create_app.sh my-app --no-hooks

REQUIREMENTS:
    - Python 3.11+
    - uv (https://docs.astral.sh/uv/)
    - GitHub CLI (https://cli.github.com/)

EOF
}

main() {
    # Parse app name (first positional argument)
    APP_NAME=""
    SKIP_TESTS=false
    SKIP_HOOKS=false

    # Get app name from first argument
    if [ -n "$1" ] && [[ ! "$1" =~ ^-- ]]; then
        APP_NAME="$1"
        shift
    fi

    # Parse options
    for arg in "$@"; do
        case $arg in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --no-hooks)
                SKIP_HOOKS=true
                shift
                ;;
            --help|-h)
                print_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $arg"
                print_usage
                exit 1
                ;;
        esac
    done

    # Show header
    echo "${BOLD}${BLUE}╔════════════════════════════════════════════════╗${RESET}"
    echo "${BOLD}${BLUE}║  JPPT - New Project Creation                  ║${RESET}"
    echo "${BOLD}${BLUE}╚════════════════════════════════════════════════╝${RESET}"
    echo ""

    # Get current directory (JPPT template location)
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    TARGET_DIR="$(dirname "$SOURCE_DIR")/$APP_NAME"

    # Run validation steps
    check_python || exit 1
    check_uv || exit 1
    check_gh || exit 1
    validate_app_name "$APP_NAME" || exit 1
    check_target_directory "$TARGET_DIR" || exit 1

    # Setup error cleanup
    cleanup_on_error() {
        if [ -d "$TARGET_DIR" ]; then
            print_warning "Cleaning up incomplete project..."
            rm -rf "$TARGET_DIR"
        fi
    }
    trap cleanup_on_error ERR

    # Copy and setup template
    copy_template "$SOURCE_DIR" "$TARGET_DIR" || exit 1
    init_git "$TARGET_DIR" || exit 1
    substitute_project_name "$APP_NAME" "$TARGET_DIR" || exit 1
    create_github_repo "$APP_NAME" "$TARGET_DIR" || exit 1

    # Install dependencies and setup (in target directory)
    cd "$TARGET_DIR" || exit 1
    install_deps || exit 1
    setup_config || exit 1
    setup_dirs || exit 1
    install_hooks

    # Optional tests
    run_tests_optional

    # Success message
    echo ""
    echo "${BOLD}${GREEN}╔════════════════════════════════════════════════╗${RESET}"
    echo "${BOLD}${GREEN}║  Project Created Successfully! 🎉              ║${RESET}"
    echo "${BOLD}${GREEN}╚════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo "${BOLD}Project:${RESET} $APP_NAME"
    echo "${BOLD}Location:${RESET} $TARGET_DIR"
    if [ -d "$TARGET_DIR/.git" ]; then
        local repo_url=$(cd "$TARGET_DIR" && gh repo view --json url -q .url 2>/dev/null || echo "")
        if [ -n "$repo_url" ]; then
            echo "${BOLD}GitHub:${RESET} $repo_url"
        fi
    fi
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo ""
    echo "  1. Navigate to your project:"
    echo "     ${BLUE}cd $TARGET_DIR${RESET}"
    echo ""
    echo "  2. Set up Telegram (optional):"
    echo "     ${BLUE}# BOT_TOKEN: Message @BotFather -> /newbot${RESET}"
    echo "     ${BLUE}# CHAT_ID: Message @userinfobot or https://api.telegram.org/bot<TOKEN>/getUpdates${RESET}"
    echo "     ${BLUE}export TELEGRAM_BOT_TOKEN=\"your-token\"${RESET}"
    echo "     ${BLUE}export TELEGRAM_CHAT_ID=\"your-chat-id\"${RESET}"
    echo ""
    echo "  3. Review and customize:"
    echo "     ${BLUE}config/dev.yaml${RESET}"
    echo "     ${BLUE}README.md${RESET}"
    echo ""
    echo "  4. Start developing:"
    echo "     ${BLUE}./run.sh${RESET}              # Start mode (dev)"
    echo "     ${BLUE}./run.sh batch${RESET}        # Batch mode (dev)"
    echo ""
    echo ""
    echo "${BOLD}${GREEN}Opening new shell in project directory...${RESET}"
    echo ""

    # Change to target directory and start new shell
    cd "$TARGET_DIR" || exit 1
    exec "${SHELL:-/bin/bash}"
}

# Run main function
main "$@"
