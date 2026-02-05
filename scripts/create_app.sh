#!/usr/bin/env bash
# JPPT (JKLEE Python Project Template) - Initial Setup Script
# This script sets up a complete development environment in one command

set -e  # Exit on error

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
    print_step 1 6 "Checking Python version..."

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
    print_step 2 6 "Checking uv installation..."

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
        print_error "Directory already exists: $target_dir"
        echo ""
        echo "Please choose a different app name or remove the existing directory."
        return 1
    fi

    print_success "Target directory is available: $target_dir"
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
Usage: ./scripts/create_app.sh [OPTIONS]

Set up JPPT development environment in one command.

OPTIONS:
    --skip-tests    Skip running initial tests
    --no-hooks      Skip pre-commit hooks installation
    --help          Show this help message

EXAMPLES:
    ./scripts/create_app.sh              # Full setup
    ./scripts/create_app.sh --skip-tests # Setup without tests
    ./scripts/create_app.sh --no-hooks   # Setup without hooks

EOF
}

main() {
    # Parse arguments
    SKIP_TESTS=false
    SKIP_HOOKS=false

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

    echo "${BOLD}${BLUE}╔════════════════════════════════════════════════╗${RESET}"
    echo "${BOLD}${BLUE}║  JPPT - Development Environment Setup         ║${RESET}"
    echo "${BOLD}${BLUE}╚════════════════════════════════════════════════╝${RESET}"
    echo ""

    # Run setup steps
    check_python || exit 1
    check_uv || exit 1
    install_deps || exit 1
    setup_config || exit 1
    setup_dirs || exit 1
    install_hooks

    # Optional tests
    run_tests_optional

    # Success message
    echo ""
    echo "${BOLD}${GREEN}╔════════════════════════════════════════════════╗${RESET}"
    echo "${BOLD}${GREEN}║  Setup Complete! 🎉                            ║${RESET}"
    echo "${BOLD}${GREEN}╚════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo ""
    echo "  1. Set up environment variables (if needed):"
    echo "     ${BLUE}export TELEGRAM_BOT_TOKEN=\"your-token\"${RESET}"
    echo "     ${BLUE}export TELEGRAM_CHAT_ID=\"your-chat-id\"${RESET}"
    echo ""
    echo "  2. Review and customize your configuration:"
    echo "     ${BLUE}config/dev.yaml${RESET}"
    echo ""
    echo "  3. Start the application:"
    echo "     ${BLUE}./scripts/run.sh${RESET}              # Start mode (dev)"
    echo "     ${BLUE}./scripts/run.sh batch${RESET}        # Batch mode (dev)"
    echo "     ${BLUE}./scripts/run.sh start prod${RESET}   # Start mode (prod)"
    echo ""
    echo "  4. Run tests:"
    echo "     ${BLUE}uv run pytest${RESET}"
    echo ""
    echo "${BOLD}Documentation:${RESET}"
    echo "  README.md - Project overview and usage"
    echo "  docs/     - Additional documentation"
    echo ""
}

# Run main function
main "$@"
