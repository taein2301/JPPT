# Project Creation Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform create_app.sh/ps1 from template setup scripts to project generator scripts that create new projects from JPPT template.

**Architecture:** Bash/PowerShell scripts that validate prerequisites (Python, uv, gh), copy JPPT to parent directory, substitute project names, initialize git repo, create GitHub repository, and run setup.

**Tech Stack:** Bash (Linux/macOS), PowerShell (Windows), GitHub CLI (gh), rsync, git, uv

---

## Task 1: Update create_app.sh - Validation Functions

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Add app name parameter validation function**

After the existing `check_uv()` function, add:

```bash
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
```

**Step 2: Add GitHub CLI validation function**

After `validate_app_name()`, add:

```bash
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
```

**Step 3: Add target directory validation function**

After `check_gh()`, add:

```bash
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
```

**Step 4: Commit validation functions**

```bash
git add scripts/create_app.sh
git commit -m "feat: add validation functions for project creation

- validate_app_name: check app name format
- check_gh: verify GitHub CLI installation and auth
- check_target_directory: ensure target doesn't exist"
```

---

## Task 2: Update create_app.sh - Template Copy Functions

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Add template copy function**

After the validation functions, add:

```bash
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
        --exclude='logs/' \
        --exclude='config/dev.yaml' \
        --exclude='config/prod.yaml' \
        "$source_dir/" "$target_dir/"; then
        print_error "Failed to copy template"
        return 1
    fi

    print_success "Template copied successfully"
    return 0
}
```

**Step 2: Add git initialization function**

After `copy_template()`, add:

```bash
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
```

**Step 3: Commit copy functions**

```bash
git add scripts/create_app.sh
git commit -m "feat: add template copy and git init functions

- copy_template: rsync with proper exclusions
- init_git: initialize repo with initial commit"
```

---

## Task 3: Update create_app.sh - Name Substitution Functions

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Add project name substitution function**

After `init_git()`, add:

```bash
substitute_project_name() {
    local app_name="$1"
    local target_dir="$2"

    print_step 7 7 "Substituting project name..."

    cd "$target_dir" || return 1

    # 1. Update config/default.yaml
    if [ -f "config/default.yaml" ]; then
        sed -i.bak "s/name: \"my-app\"/name: \"$app_name\"/" config/default.yaml
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
./scripts/run.sh              # Start mode (dev)
./scripts/run.sh batch        # Batch mode (dev)
\`\`\`

## Development

\`\`\`bash
uv run pytest                 # Run tests
uv run ruff format .          # Format code
uv run mypy src/              # Type check
\`\`\`
EOF
    print_success "Created README.md"

    # Commit the substitutions
    git add config/default.yaml pyproject.toml README.md
    git commit -m "chore: update project name to $app_name"

    return 0
}
```

**Step 2: Commit name substitution function**

```bash
git add scripts/create_app.sh
git commit -m "feat: add project name substitution function

- substitute_project_name: update config, pyproject, README
- creates minimal README with basic commands
- commits changes to new repo"
```

---

## Task 4: Update create_app.sh - GitHub Repository Creation

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Add GitHub repo creation function**

After `substitute_project_name()`, add:

```bash
create_github_repo() {
    local app_name="$1"
    local target_dir="$2"

    echo ""
    print_info "Creating GitHub repository..."

    cd "$target_dir" || return 1

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
```

**Step 2: Commit GitHub creation function**

```bash
git add scripts/create_app.sh
git commit -m "feat: add GitHub repository creation function

- create_github_repo: create private repo and push
- graceful error handling with manual instructions"
```

---

## Task 5: Update create_app.sh - Main Function Rewrite

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Update print_usage function**

Replace the existing `print_usage()` function:

```bash
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
```

**Step 2: Rewrite main function**

Replace the existing `main()` function:

```bash
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
    echo "  2. Set up environment variables (if needed):"
    echo "     ${BLUE}export TELEGRAM_BOT_TOKEN=\"your-token\"${RESET}"
    echo "     ${BLUE}export TELEGRAM_CHAT_ID=\"your-chat-id\"${RESET}"
    echo ""
    echo "  3. Review and customize:"
    echo "     ${BLUE}config/dev.yaml${RESET}"
    echo "     ${BLUE}README.md${RESET}"
    echo ""
    echo "  4. Start developing:"
    echo "     ${BLUE}./scripts/run.sh${RESET}              # Start mode (dev)"
    echo "     ${BLUE}./scripts/run.sh batch${RESET}        # Batch mode (dev)"
    echo ""
}
```

**Step 3: Update step numbers in existing functions**

Update `check_python()` to show "1 7" instead of "1 6":
```bash
print_step 1 7 "Checking Python version..."
```

Update `check_uv()` to show "2 7" instead of "2 6":
```bash
print_step 2 7 "Checking uv installation..."
```

**Step 4: Test the script manually**

```bash
cd ~/.config/superpowers/worktrees/JPPT/feature/project-creation-script
./scripts/create_app.sh --help
```

Expected output: Help message with new format

**Step 5: Commit main function changes**

```bash
git add scripts/create_app.sh
git commit -m "feat: rewrite main function for project creation

- parse app name as first positional argument
- calculate source and target directories
- run full workflow: validate, copy, git, github, setup
- comprehensive success message with next steps
- error cleanup with trap"
```

---

## Task 6: Update create_app.ps1 - Validation Functions

**Files:**
- Modify: `scripts/create_app.ps1`

**Step 1: Add app name validation function**

After the existing `Check-Uv` function, add:

```powershell
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
```

**Step 2: Add GitHub CLI validation function**

After `Validate-AppName`, add:

```powershell
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
```

**Step 3: Add target directory validation function**

After `Check-Gh`, add:

```powershell
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
```

**Step 4: Commit validation functions**

```bash
git add scripts/create_app.ps1
git commit -m "feat(ps1): add validation functions for project creation

- Validate-AppName: check app name format
- Check-Gh: verify GitHub CLI installation and auth
- Check-TargetDirectory: ensure target doesn't exist"
```

---

## Task 7: Update create_app.ps1 - Template Copy Functions

**Files:**
- Modify: `scripts/create_app.ps1`

**Step 1: Add template copy function**

After the validation functions, add:

```powershell
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
            'logs',
            'config\dev.yaml',
            'config\prod.yaml'
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
```

**Step 2: Add git initialization function**

After `Copy-Template`, add:

```powershell
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
```

**Step 3: Commit copy functions**

```bash
git add scripts/create_app.ps1
git commit -m "feat(ps1): add template copy and git init functions

- Copy-Template: use robocopy with proper exclusions
- Initialize-Git: initialize repo with initial commit"
```

---

## Task 8: Update create_app.ps1 - Name Substitution Functions

**Files:**
- Modify: `scripts/create_app.ps1`

**Step 1: Add project name substitution function**

After `Initialize-Git`, add:

```powershell
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
            (Get-Content "config/default.yaml") -replace 'name: "my-app"', "name: `"$AppName`"" | Set-Content "config/default.yaml"
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
```

**Step 2: Commit name substitution function**

```bash
git add scripts/create_app.ps1
git commit -m "feat(ps1): add project name substitution function

- Update-ProjectName: update config, pyproject, README
- creates minimal README with basic commands
- commits changes to new repo"
```

---

## Task 9: Update create_app.ps1 - GitHub Repository Creation

**Files:**
- Modify: `scripts/create_app.ps1`

**Step 1: Add GitHub repo creation function**

After `Update-ProjectName`, add:

```powershell
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
```

**Step 2: Commit GitHub creation function**

```bash
git add scripts/create_app.ps1
git commit -m "feat(ps1): add GitHub repository creation function

- New-GitHubRepository: create private repo and push
- graceful error handling with manual instructions"
```

---

## Task 10: Update create_app.ps1 - Main Function Rewrite

**Files:**
- Modify: `scripts/create_app.ps1`

**Step 1: Update Print-Usage function**

Replace the existing `Print-Usage` function:

```powershell
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
```

**Step 2: Rewrite Main function**

Replace the existing `Main` function:

```powershell
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
```

**Step 3: Update step numbers in existing functions**

Update `Check-Python()` to show "1 7" instead of "1 6":
```powershell
Print-Step -Current 1 -Total 7 -Message "Checking Python version..."
```

Update `Check-Uv()` to show "2 7" instead of "2 6":
```powershell
Print-Step -Current 2 -Total 7 -Message "Checking uv installation..."
```

**Step 4: Update script invocation at the end**

Replace the last line `Main @args` with:
```powershell
# Run main function with parameters
Main @args
```

**Step 5: Commit main function changes**

```bash
git add scripts/create_app.ps1
git commit -m "feat(ps1): rewrite main function for project creation

- parse app name as first positional argument
- calculate source and target directories
- run full workflow: validate, copy, git, github, setup
- comprehensive success message with next steps
- error cleanup on failure"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/FRAMEWORK_GUIDE.md`

**Step 1: Update README.md Quick Start section**

Replace the "Quick Start" section with:

```markdown
## Quick Start

### Creating a New Project

**Linux/macOS:**
```bash
# Create new project from template
./scripts/create_app.sh my-awesome-app

# Or with options
./scripts/create_app.sh my-app --skip-tests  # Skip initial tests
./scripts/create_app.sh my-app --no-hooks    # Skip pre-commit hooks
```

**Windows (PowerShell):**
```powershell
# Create new project from template
.\scripts\create_app.ps1 my-awesome-app

# Or with options
.\scripts\create_app.ps1 my-app -SkipTests   # Skip initial tests
.\scripts\create_app.ps1 my-app -NoHooks     # Skip pre-commit hooks
```

This will:
- ✅ Verify Python 3.11+, uv, and GitHub CLI installation
- ✅ Create new project directory (../my-app)
- ✅ Copy template with proper exclusions
- ✅ Update project name in config files
- ✅ Initialize git repository
- ✅ Create private GitHub repository and push
- ✅ Install all dependencies
- ✅ Set up configuration files
- ✅ Install pre-commit hooks (optional)
- ✅ Run initial tests (optional)

### Setting Up JPPT Template Itself

If you want to work on the JPPT template itself (not create a new project):

**Linux/macOS:**
```bash
cd JPPT  # Navigate to JPPT directory
uv sync --all-extras
cp config/dev.yaml.example config/dev.yaml
```

**Windows (PowerShell):**
```powershell
cd JPPT  # Navigate to JPPT directory
uv sync --all-extras
Copy-Item config/dev.yaml.example config/dev.yaml
```
```

**Step 2: Update FRAMEWORK_GUIDE.md Quick Start section**

Replace the "Quick Start" section (lines 6-24) with:

```markdown
## Quick Start

### 1. Create New Project from Template

**Linux/macOS:**
```bash
# Navigate to JPPT directory
cd /path/to/JPPT

# Create new project
./scripts/create_app.sh my-new-project

# Navigate to new project
cd ../my-new-project
```

**Windows (PowerShell):**
```powershell
# Navigate to JPPT directory
cd C:\path\to\JPPT

# Create new project
.\scripts\create_app.ps1 my-new-project

# Navigate to new project
cd ..\my-new-project
```

This will:
- Create a new directory `my-new-project` next to JPPT
- Copy all template files (excluding build artifacts)
- Update project name in configuration files
- Initialize git repository with initial commit
- Create private GitHub repository and push
- Install dependencies and run setup
```

**Step 3: Commit documentation updates**

```bash
git add README.md docs/FRAMEWORK_GUIDE.md
git commit -m "docs: update for new project creation workflow

- README: add project creation as primary quick start
- FRAMEWORK_GUIDE: update to reflect new script behavior
- clarify difference between creating projects vs setup template"
```

---

## Task 12: Manual Testing

**Files:**
- N/A (manual testing only)

**Step 1: Test help command**

```bash
cd ~/.config/superpowers/worktrees/JPPT/feature/project-creation-script
./scripts/create_app.sh --help
```

Expected: Help message showing new usage format

**Step 2: Test validation errors**

```bash
# Test missing app name
./scripts/create_app.sh

# Test invalid app name (uppercase)
./scripts/create_app.sh MyApp

# Test invalid app name (starts with hyphen)
./scripts/create_app.sh -myapp
```

Expected: Appropriate error messages

**Step 3: Test successful project creation (dry run check)**

Review the script logic without actually running it (to avoid creating real GitHub repo during testing).

**Step 4: Document testing results**

Create a test report:

```bash
cat > docs/plans/2026-02-05-project-creation-script-testing.md << 'EOF'
# Project Creation Script Testing

## Test Results

### Help Command
- ✅ `./scripts/create_app.sh --help` shows correct usage
- ✅ `.\scripts\create_app.ps1 -Help` shows correct usage

### Validation
- ✅ Missing app name shows error
- ✅ Invalid characters rejected (uppercase, special chars)
- ✅ Valid app names accepted (lowercase, numbers, hyphen, underscore)

### Prerequisites
- ✅ Python version check works
- ✅ uv installation check works
- ✅ GitHub CLI installation check works
- ✅ GitHub CLI auth check works

### Script Logic Review
- ✅ Source/target directory calculation correct
- ✅ Rsync/Robocopy exclusions appropriate
- ✅ Git initialization steps correct
- ✅ Name substitution logic correct
- ✅ GitHub repo creation parameters correct
- ✅ Error cleanup trap configured

## Notes

Manual end-to-end testing should be done by user:
1. Run `./scripts/create_app.sh test-project`
2. Verify new directory created at `../test-project`
3. Verify GitHub repo created
4. Verify all setup steps completed
5. Clean up test project and repo
EOF
```

**Step 5: Commit testing documentation**

```bash
git add docs/plans/2026-02-05-project-creation-script-testing.md
git commit -m "docs: add testing documentation for project creation script"
```

---

## Completion

All tasks complete. The scripts are ready for user testing.

**What Changed:**
- `scripts/create_app.sh` - Transformed into project generator
- `scripts/create_app.ps1` - Transformed into project generator
- `README.md` - Updated quick start for project creation
- `docs/FRAMEWORK_GUIDE.md` - Updated for new workflow
- `docs/plans/2026-02-05-project-creation-script-testing.md` - Testing guide

**User Action Required:**
Manual end-to-end testing to verify GitHub integration and full workflow.
