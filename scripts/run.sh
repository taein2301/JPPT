#!/usr/bin/env bash
# JPPT (JKLEE Python Project Template) - Quick Run Script
# Simplified wrapper for running the application

set -e  # Exit on error

# ============================================================================
# Section 1: Colors and Helper Functions
# ============================================================================

# Colors using tput
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

print_error() {
    echo "${RED}✗${RESET} $1" >&2
}

print_info() {
    echo "${BLUE}ℹ${RESET} $1"
}

# ============================================================================
# Section 2: Validation Functions
# ============================================================================

check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed"
        echo ""
        echo "Install uv with:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
        echo "Or run the setup script first:"
        echo "  ./scripts/create_app.sh"
        exit 1
    fi
}

check_config() {
    local env=$1
    local config_file="config/${env}.yaml"

    if [ ! -f "$config_file" ]; then
        print_error "Configuration file not found: $config_file"
        echo ""
        echo "Create it with:"
        echo "  cp config/dev.yaml.example $config_file"
        echo ""
        echo "Or run the setup script:"
        echo "  ./scripts/create_app.sh"
        exit 1
    fi
}

setup_logs_dir() {
    if [ ! -d "logs" ]; then
        mkdir -p logs
    fi
}

# ============================================================================
# Section 3: Main Function
# ============================================================================

print_usage() {
    cat << EOF
Usage: ./scripts/run.sh [MODE] [ENV]

Quick wrapper for running JPPT application.

ARGUMENTS:
    MODE    Application mode (default: start)
            - start: Run in daemon/app mode
            - batch: Run in one-shot batch mode

    ENV     Environment (default: dev)
            - dev:  Development environment
            - prod: Production environment

OPTIONS:
    --help, -h    Show this help message

EXAMPLES:
    ./scripts/run.sh                # Start mode, dev environment
    ./scripts/run.sh batch          # Batch mode, dev environment
    ./scripts/run.sh start prod     # Start mode, prod environment
    ./scripts/run.sh batch prod     # Batch mode, prod environment

CONFIGURATION:
    Config files are loaded from: config/{ENV}.yaml
    Log files are written to: logs/jppt.log or logs/jppt_batch.log

FIRST TIME SETUP:
    If you haven't set up the project yet, run:
    ./scripts/create_app.sh

EOF
}

main() {
    # Parse arguments
    MODE="${1:-start}"
    ENV="${2:-dev}"

    # Check for help flag
    if [ "$MODE" = "--help" ] || [ "$MODE" = "-h" ]; then
        print_usage
        exit 0
    fi

    # Validate MODE
    if [ "$MODE" != "start" ] && [ "$MODE" != "batch" ]; then
        print_error "Invalid mode: $MODE"
        echo "Mode must be 'start' or 'batch'"
        echo ""
        print_usage
        exit 1
    fi

    # Validate ENV (just warn if not dev/prod, but allow it)
    if [ "$ENV" != "dev" ] && [ "$ENV" != "prod" ]; then
        print_info "Using custom environment: $ENV"
    fi

    # Check prerequisites
    check_uv
    check_config "$ENV"
    setup_logs_dir

    # Determine log file name
    if [ "$MODE" = "batch" ]; then
        LOG_FILE="logs/jppt_batch.log"
    else
        LOG_FILE="logs/jppt.log"
    fi

    # Print execution info
    echo "${BOLD}Starting jppt...${RESET}"
    echo "  ${BLUE}Mode:${RESET}        $MODE"
    echo "  ${BLUE}Environment:${RESET} $ENV"
    echo "  ${BLUE}Config:${RESET}      config/${ENV}.yaml"
    echo "  ${BLUE}Logs:${RESET}        $LOG_FILE"
    echo ""

    # Run the application
    # Note: We don't use 'set -e' for this command because we want to capture its exit code
    set +e
    uv run python -m src.main "$MODE" --env "$ENV"
    EXIT_CODE=$?
    set -e

    # Handle exit
    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        print_error "Application exited with error (code: $EXIT_CODE)"
        echo ""
        echo "Check the logs for details:"
        echo "  tail -f $LOG_FILE"
        exit $EXIT_CODE
    fi

    exit 0
}

# Run main function
main "$@"
