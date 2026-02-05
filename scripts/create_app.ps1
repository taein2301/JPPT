# JPPT (JKLEE Python Project Template) - Initial Setup Script
# This script sets up a complete development environment in one command

$ErrorActionPreference = "Stop"

# ============================================================================
# Section 1: Colors and Helper Functions
# ============================================================================

function Print-Step {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Message
    )
    Write-Host "[$Current/$Total] $Message" -ForegroundColor Blue
}

function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

# ============================================================================
# Section 2: Validation Functions
# ============================================================================

function Check-Python {
    Print-Step -Current 1 -Total 6 -Message "Checking Python version..."

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python3 -ErrorAction SilentlyContinue
    }

    if (-not $python) {
        Print-Error "Python 3 is not installed"
        Write-Host ""
        Write-Host "Please install Python 3.11 or higher:"
        Write-Host "  Visit: https://www.python.org/downloads/"
        Write-Host "  Or use: winget install Python.Python.3.11"
        return $false
    }

    $pythonCmd = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }
    $versionOutput = & $pythonCmd --version 2>&1
    $version = $versionOutput -replace "Python ", ""
    $versionParts = $version.Split(".")
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]

    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Print-Error "Python 3.11+ required, but found Python $version"
        Write-Host ""
        Write-Host "Please upgrade Python:"
        Write-Host "  Visit: https://www.python.org/downloads/"
        Write-Host "  Or use: winget install Python.Python.3.11"
        return $false
    }

    Print-Success "Python $version found"
    return $true
}

function Check-Uv {
    Print-Step -Current 2 -Total 6 -Message "Checking uv installation..."

    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Print-Error "uv is not installed"
        Write-Host ""
        Write-Host "Install uv with:"
        Write-Host "  PowerShell: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
        Write-Host ""
        Write-Host "Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        return $false
    }

    $uvVersion = uv --version 2>&1
    Print-Success "uv found: $uvVersion"
    return $true
}

# ============================================================================
# Section 3: Installation Functions
# ============================================================================

function Install-Dependencies {
    Print-Step -Current 3 -Total 6 -Message "Installing dependencies..."

    try {
        uv sync --all-extras
        Print-Success "Dependencies installed successfully"
        return $true
    }
    catch {
        Print-Error "Failed to install dependencies"
        Write-Host "Try running: uv sync --all-extras"
        return $false
    }
}

function Setup-Config {
    Print-Step -Current 4 -Total 6 -Message "Setting up configuration files..."

    $configExample = "config/dev.yaml.example"
    $configTarget = "config/dev.yaml"

    if (-not (Test-Path $configExample)) {
        Print-Warning "Example config not found: $configExample"
        return $true
    }

    if (Test-Path $configTarget) {
        Print-Info "Configuration file already exists: $configTarget (skipping)"
    }
    else {
        try {
            Copy-Item $configExample $configTarget
            Print-Success "Created $configTarget"
        }
        catch {
            Print-Error "Failed to create $configTarget"
            return $false
        }
    }

    return $true
}

function Setup-Directories {
    Print-Step -Current 5 -Total 6 -Message "Creating directories..."

    try {
        if (-not (Test-Path "logs")) {
            New-Item -ItemType Directory -Path "logs" -Force | Out-Null
        }
        Print-Success "Created logs/ directory"
        return $true
    }
    catch {
        Print-Warning "Failed to create logs/ directory (may already exist)"
        return $true
    }
}

function Install-Hooks {
    param([bool]$SkipHooks)

    if ($SkipHooks) {
        Print-Info "Skipping pre-commit hooks installation (--no-hooks)"
        return $true
    }

    Print-Step -Current 6 -Total 6 -Message "Installing pre-commit hooks..."

    if (-not (Test-Path ".pre-commit-config.yaml")) {
        Print-Warning "No .pre-commit-config.yaml found, skipping hooks installation"
        return $true
    }

    try {
        uv run pre-commit install 2>&1 | Out-Null
        Print-Success "Pre-commit hooks installed"
        return $true
    }
    catch {
        Print-Warning "Failed to install pre-commit hooks (non-critical, continuing...)"
        Print-Info "You can manually install later with: uv run pre-commit install"
        return $true
    }
}

function Run-TestsOptional {
    param([bool]$SkipTests)

    if ($SkipTests) {
        Print-Info "Skipping initial tests (--skip-tests)"
        return $true
    }

    Write-Host ""
    Write-Host "Running initial tests..." -ForegroundColor Blue

    try {
        uv run pytest -v
        Print-Success "All tests passed"
    }
    catch {
        Print-Warning "Some tests failed, but setup is complete"
        Print-Info "Review test output above and fix any issues"
    }

    return $true
}

# ============================================================================
# Section 4: Main Function
# ============================================================================

function Print-Usage {
    Write-Host @"
Usage: .\scripts\create_app.ps1 [OPTIONS]

Set up JPPT development environment in one command.

OPTIONS:
    -SkipTests      Skip running initial tests
    -NoHooks        Skip pre-commit hooks installation
    -Help           Show this help message

EXAMPLES:
    .\scripts\create_app.ps1              # Full setup
    .\scripts\create_app.ps1 -SkipTests   # Setup without tests
    .\scripts\create_app.ps1 -NoHooks     # Setup without hooks

"@
}

function Main {
    param(
        [switch]$SkipTests,
        [switch]$NoHooks,
        [switch]$Help
    )

    if ($Help) {
        Print-Usage
        exit 0
    }

    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║  JPPT - Development Environment Setup         ║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""

    # Run setup steps
    if (-not (Check-Python)) { exit 1 }
    if (-not (Check-Uv)) { exit 1 }
    if (-not (Install-Dependencies)) { exit 1 }
    if (-not (Setup-Config)) { exit 1 }
    if (-not (Setup-Directories)) { exit 1 }
    Install-Hooks -SkipHooks:$NoHooks

    # Optional tests
    Run-TestsOptional -SkipTests:$SkipTests

    # Success message
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  Setup Complete! 🎉                            ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Blue
    Write-Host ""
    Write-Host "  1. Set up environment variables (if needed):"
    Write-Host "     `$env:TELEGRAM_BOT_TOKEN=`"your-token`"" -ForegroundColor Cyan
    Write-Host "     `$env:TELEGRAM_CHAT_ID=`"your-chat-id`"" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Review and customize your configuration:"
    Write-Host "     config/dev.yaml" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Start the application:"
    Write-Host "     .\scripts\run.ps1              # Start mode (dev)" -ForegroundColor Cyan
    Write-Host "     .\scripts\run.ps1 batch        # Batch mode (dev)" -ForegroundColor Cyan
    Write-Host "     .\scripts\run.ps1 start prod   # Start mode (prod)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4. Run tests:"
    Write-Host "     uv run pytest" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor Blue
    Write-Host "  README.md - Project overview and usage"
    Write-Host "  docs/     - Additional documentation"
    Write-Host ""
}

# Run main function with parameters
Main @args
