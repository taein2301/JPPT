# JPPT (JKLEE Python Project Template) - Initial Setup Script
# This script sets up a complete development environment in one command

$ErrorActionPreference = "Stop"

# Set console encoding to UTF-8 for proper character display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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
    Print-Step -Current 1 -Total 7 -Message "Checking Python version..."

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
    Print-Step -Current 2 -Total 7 -Message "Checking uv installation..."

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

function Validate-AppName {
    param([string]$AppName)

    if ([string]::IsNullOrWhiteSpace($AppName)) {
        Print-Error "App name is required"
        Write-Host ""
        Write-Host "Usage: .\scripts\create_app.ps1 <app-name> [OPTIONS]"
        Write-Host "Example: .\scripts\create_app.ps1 my-awesome-app"
        return $false
    }

    # Check valid characters (lowercase, numbers, hyphen, underscore)
    if ($AppName -notmatch '^[a-z0-9][a-z0-9_-]*$') {
        Print-Error "Invalid app name: '$AppName'"
        Write-Host ""
        Write-Host "App name must:"
        Write-Host "  - Start with lowercase letter or number"
        Write-Host "  - Contain only lowercase letters, numbers, hyphens, underscores"
        Write-Host ""
        Write-Host "Valid examples: my-app, my_app, myapp123"
        Write-Host "Invalid examples: MyApp, -myapp, my app"
        return $false
    }

    Print-Success "App name '$AppName' is valid"
    return $true
}

function Check-Gh {
    Print-Step -Current 3 -Total 7 -Message "Checking GitHub CLI installation..."

    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) {
        Print-Error "GitHub CLI (gh) is not installed"
        Write-Host ""
        Write-Host "Install GitHub CLI:"
        Write-Host "  Visit: https://cli.github.com/"
        Write-Host "  Or use: winget install GitHub.cli"
        return $false
    }

    $ghVersion = gh --version 2>&1 | Select-Object -First 1
    Print-Success "GitHub CLI found: $ghVersion"

    # Check authentication
    $authStatus = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Print-Error "GitHub CLI is not authenticated"
        Write-Host ""
        Write-Host "Please authenticate with:"
        Write-Host "  gh auth login"
        Write-Host ""
        return $false
    }

    Print-Success "GitHub CLI is authenticated"
    return $true
}

function Check-TargetDirectory {
    param([string]$TargetDir)

    Print-Step -Current 4 -Total 7 -Message "Checking target directory..."

    if (Test-Path $TargetDir) {
        Print-Error "Directory already exists: $TargetDir"
        Write-Host ""
        Write-Host "Please choose a different app name or remove the existing directory."
        return $false
    }

    Print-Success "Target directory is available: $TargetDir"
    return $true
}

function Copy-Template {
    param(
        [string]$SourceDir,
        [string]$TargetDir
    )

    Print-Step -Current 5 -Total 7 -Message "Copying template to $TargetDir..."

    try {
        # Create parent directory if needed
        $parentDir = Split-Path $TargetDir
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }

        # Copy directory with exclusions
        $excludeItems = @(
            '.git',
            '.venv',
            '__pycache__',
            '*.pyc',
            '.pytest_cache',
            '.mypy_cache',
            '.ruff_cache',
            'htmlcov',
            'logs',
            'config\dev.yaml',
            'config\prod.yaml',
            'docs'
        )

        # Use robocopy for efficient directory copying
        $robocopyArgs = @(
            $SourceDir,
            $TargetDir,
            '/E',  # Copy subdirectories including empty ones
            '/NP', # No progress
            '/NFL', # No file list
            '/NDL', # No directory list
            '/NJH', # No job header
            '/NJS'  # No job summary
        )

        # Add exclusions
        foreach ($exclude in $excludeItems) {
            $robocopyArgs += '/XD'
            $robocopyArgs += $exclude
            $robocopyArgs += '/XF'
            $robocopyArgs += $exclude
        }

        $result = & robocopy @robocopyArgs 2>&1

        # Robocopy exit codes: 0-7 are success, 8+ are errors
        if ($LASTEXITCODE -ge 8) {
            throw "Robocopy failed with exit code $LASTEXITCODE"
        }

        Print-Success "Template copied successfully"
        return $true
    }
    catch {
        Print-Error "Failed to copy template: $_"
        return $false
    }
}

function Initialize-Git {
    param([string]$TargetDir)

    Print-Step -Current 6 -Total 7 -Message "Initializing git repository..."

    try {
        Set-Location $TargetDir

        git init 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to initialize git repository"
        }

        git add . 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to stage files"
        }

        git commit -m "Initial commit from JPPT template" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create initial commit"
        }

        Print-Success "Git repository initialized"
        return $true
    }
    catch {
        Print-Error $_
        return $false
    }
}

function Update-ProjectName {
    param(
        [string]$AppName,
        [string]$TargetDir
    )

    Print-Step -Current 7 -Total 7 -Message "Substituting project name..."

    try {
        Set-Location $TargetDir

        # 1. Update config/default.yaml
        if (Test-Path "config/default.yaml") {
            (Get-Content "config/default.yaml") -replace 'name: ".*"', "name: `"$AppName`"" | Set-Content "config/default.yaml"
            Print-Success "Updated config/default.yaml"
        }

        # 2. Update pyproject.toml
        if (Test-Path "pyproject.toml") {
            (Get-Content "pyproject.toml") -replace 'name = "jppt"', "name = `"$AppName`"" | Set-Content "pyproject.toml"
            Print-Success "Updated pyproject.toml"
        }

        # 3. Create minimal README.md
        $readmeContent = @"
# $AppName

Created from [JPPT](https://github.com/taein2301/JPPT) template.

## Setup

``````bash
.\scripts\create_app.ps1
``````

## Run

``````bash
.\scripts\run.ps1              # Start mode (dev)
.\scripts\run.ps1 batch        # Batch mode (dev)
``````

## Development

``````bash
uv run pytest                 # Run tests
uv run ruff format .          # Format code
uv run mypy src/              # Type check
``````
"@
        Set-Content -Path "README.md" -Value $readmeContent
        Print-Success "Created README.md"

        # Commit the substitutions
        git add config/default.yaml pyproject.toml README.md 2>&1 | Out-Null
        git commit -m "chore: update project name to $AppName" 2>&1 | Out-Null

        return $true
    }
    catch {
        Print-Error "Failed to substitute project name: $_"
        return $false
    }
}

function New-GitHubRepository {
    param(
        [string]$AppName,
        [string]$TargetDir
    )

    Write-Host ""
    Print-Info "Creating GitHub repository..."

    try {
        Set-Location $TargetDir

        gh repo create $AppName `
            --private `
            --source=. `
            --description="Created from JPPT template" `
            --push 2>&1 | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "gh repo create failed"
        }

        $repoUrl = gh repo view --json url -q .url 2>&1
        Print-Success "GitHub repository created: $repoUrl"
        Print-Success "Initial commit pushed to main branch"

        return $true
    }
    catch {
        Print-Error "Failed to create GitHub repository"
        Write-Host ""
        Print-Warning "Local project created successfully at: $TargetDir"
        Print-Info "You can create the repository manually:"
        Print-Info "  cd $TargetDir"
        Print-Info "  gh repo create $AppName --private --source=. --push"
        return $false
    }
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
Usage: .\scripts\create_app.ps1 <app-name> [OPTIONS]

Create a new project from JPPT template.

ARGUMENTS:
    <app-name>      Name of the new project (lowercase, numbers, -, _ only)

OPTIONS:
    -SkipTests      Skip running initial tests
    -NoHooks        Skip pre-commit hooks installation
    -Help           Show this help message

EXAMPLES:
    .\scripts\create_app.ps1 my-awesome-app
    .\scripts\create_app.ps1 my-app -SkipTests
    .\scripts\create_app.ps1 my-app -NoHooks

REQUIREMENTS:
    - Python 3.11+
    - uv (https://docs.astral.sh/uv/)
    - GitHub CLI (https://cli.github.com/)

"@
}

function Main {
    param(
        [Parameter(Position=0)]
        [string]$AppName,
        [switch]$SkipTests,
        [switch]$NoHooks,
        [switch]$Help
    )

    if ($Help) {
        Print-Usage
        exit 0
    }

    # Show header
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║  JPPT - New Project Creation                  ║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""

    # Get current directory (JPPT template location)
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $sourceDir = Split-Path -Parent $scriptPath
    $sourceDir = Resolve-Path $sourceDir
    $targetDir = Join-Path (Split-Path -Parent $sourceDir) $AppName

    # Run validation steps
    if (-not (Check-Python)) { exit 1 }
    if (-not (Check-Uv)) { exit 1 }
    if (-not (Check-Gh)) { exit 1 }
    if (-not (Validate-AppName -AppName $AppName)) { exit 1 }
    if (-not (Check-TargetDirectory -TargetDir $targetDir)) { exit 1 }

    # Setup error cleanup
    $ErrorActionPreference = "Stop"
    try {
        # Copy and setup template
        if (-not (Copy-Template -SourceDir $sourceDir -TargetDir $targetDir)) { throw "Copy failed" }
        if (-not (Initialize-Git -TargetDir $targetDir)) { throw "Git init failed" }
        if (-not (Update-ProjectName -AppName $AppName -TargetDir $targetDir)) { throw "Name substitution failed" }
        if (-not (New-GitHubRepository -AppName $AppName -TargetDir $targetDir)) { throw "GitHub creation failed" }

        # Install dependencies and setup (in target directory)
        Set-Location $targetDir
        if (-not (Install-Dependencies)) { throw "Dependency installation failed" }
        if (-not (Setup-Config)) { throw "Config setup failed" }
        if (-not (Setup-Directories)) { throw "Directory setup failed" }
        Install-Hooks -SkipHooks:$NoHooks

        # Optional tests
        Run-TestsOptional -SkipTests:$SkipTests

        # Success message
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║  Project Created Successfully! 🎉              ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "Project: " -NoNewline
        Write-Host $AppName -ForegroundColor White
        Write-Host "Location: " -NoNewline
        Write-Host $targetDir -ForegroundColor White

        if (Test-Path "$targetDir\.git") {
            $repoUrl = gh repo view --json url -q .url 2>$null
            if ($repoUrl) {
                Write-Host "GitHub: " -NoNewline
                Write-Host $repoUrl -ForegroundColor White
            }
        }

        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Blue
        Write-Host ""
        Write-Host "  1. Navigate to your project:"
        Write-Host "     cd $targetDir" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  2. Set up environment variables (if needed):"
        Write-Host "     `$env:TELEGRAM_BOT_TOKEN=`"your-token`"" -ForegroundColor Cyan
        Write-Host "     `$env:TELEGRAM_CHAT_ID=`"your-chat-id`"" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  3. Review and customize:"
        Write-Host "     config\dev.yaml" -ForegroundColor Cyan
        Write-Host "     README.md" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  4. Start developing:"
        Write-Host "     .\scripts\run.ps1              # Start mode (dev)" -ForegroundColor Cyan
        Write-Host "     .\scripts\run.ps1 batch        # Batch mode (dev)" -ForegroundColor Cyan
        Write-Host ""
    }
    catch {
        # Cleanup on error
        if (Test-Path $targetDir) {
            Print-Warning "Cleaning up incomplete project..."
            Remove-Item -Recurse -Force $targetDir
        }
        Print-Error "Project creation failed: $_"
        exit 1
    }
}

# Run main function with parameters
Main @args
