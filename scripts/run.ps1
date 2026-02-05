# JPPT (JKLEE Python Project Template) - Quick Run Script
# Simplified wrapper for running the application

$ErrorActionPreference = "Stop"

# ============================================================================
# Section 1: Colors and Helper Functions
# ============================================================================

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

# ============================================================================
# Section 2: Validation Functions
# ============================================================================

function Check-Uv {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Print-Error "uv is not installed"
        Write-Host ""
        Write-Host "Install uv with:"
        Write-Host "  powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
        Write-Host ""
        Write-Host "Or run the setup script first:"
        Write-Host "  .\scripts\create_app.ps1"
        exit 1
    }
}

function Check-Config {
    param([string]$Env)

    $configFile = "config/$Env.yaml"

    if (-not (Test-Path $configFile)) {
        Print-Error "Configuration file not found: $configFile"
        Write-Host ""
        Write-Host "Create it with:"
        Write-Host "  Copy-Item config/dev.yaml.example $configFile"
        Write-Host ""
        Write-Host "Or run the setup script:"
        Write-Host "  .\scripts\create_app.ps1"
        exit 1
    }
}

function Setup-LogsDirectory {
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    }
}

# ============================================================================
# Section 3: Main Function
# ============================================================================

function Print-Usage {
    Write-Host @"
Usage: .\scripts\run.ps1 [MODE] [ENV]

Quick wrapper for running JPPT application.

ARGUMENTS:
    MODE    Application mode (default: start)
            - start: Run in daemon/app mode
            - batch: Run in one-shot batch mode

    ENV     Environment (default: dev)
            - dev:  Development environment
            - prod: Production environment

OPTIONS:
    -Help, -h    Show this help message

EXAMPLES:
    .\scripts\run.ps1                # Start mode, dev environment
    .\scripts\run.ps1 batch          # Batch mode, dev environment
    .\scripts\run.ps1 start prod     # Start mode, prod environment
    .\scripts\run.ps1 batch prod     # Batch mode, prod environment

CONFIGURATION:
    Config files are loaded from: config/{ENV}.yaml
    Log files are written to: logs/jppt.log or logs/jppt_batch.log

FIRST TIME SETUP:
    If you haven't set up the project yet, run:
    .\scripts\create_app.ps1

"@
}

function Main {
    param(
        [string]$Mode = "start",
        [string]$Env = "dev"
    )

    # Check for help flag
    if ($Mode -eq "-Help" -or $Mode -eq "-h" -or $Mode -eq "--help") {
        Print-Usage
        exit 0
    }

    # Validate MODE
    if ($Mode -ne "start" -and $Mode -ne "batch") {
        Print-Error "Invalid mode: $Mode"
        Write-Host "Mode must be 'start' or 'batch'"
        Write-Host ""
        Print-Usage
        exit 1
    }

    # Validate ENV (just warn if not dev/prod, but allow it)
    if ($Env -ne "dev" -and $Env -ne "prod") {
        Print-Info "Using custom environment: $Env"
    }

    # Check prerequisites
    Check-Uv
    Check-Config -Env $Env
    Setup-LogsDirectory

    # Determine log file name
    $logFile = if ($Mode -eq "batch") {
        "logs/jppt_batch.log"
    } else {
        "logs/jppt.log"
    }

    # Print execution info
    Write-Host "Starting jppt..." -ForegroundColor Blue
    Write-Host "  Mode:        $Mode" -ForegroundColor Gray
    Write-Host "  Environment: $Env" -ForegroundColor Gray
    Write-Host "  Config:      config/$Env.yaml" -ForegroundColor Gray
    Write-Host "  Logs:        $logFile" -ForegroundColor Gray
    Write-Host ""

    # Run the application
    try {
        uv run python -m src.main $Mode --env $Env
        exit 0
    }
    catch {
        Write-Host ""
        Print-Error "Application exited with error"
        Write-Host ""
        Write-Host "Check the logs for details:"
        Write-Host "  Get-Content $logFile -Tail 50"
        exit 1
    }
}

# Parse arguments and run main function
if ($args.Count -eq 0) {
    Main
}
elseif ($args.Count -eq 1) {
    Main -Mode $args[0]
}
elseif ($args.Count -eq 2) {
    Main -Mode $args[0] -Env $args[1]
}
else {
    Print-Error "Too many arguments"
    Print-Usage
    exit 1
}
