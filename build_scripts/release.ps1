# Build the installer and publish it as a GitHub release - the release the
# in-app "Check for updates" button (app/core/updater.py) offers to users.
#
# Usage (from anywhere; bump app/version.py, commit and push first):
#   powershell -ExecutionPolicy Bypass -File build_scripts\release.ps1 -Notes "What changed, for users"
#
# Needs: PyInstaller, Inno Setup 6, and the GitHub CLI signed in
# (winget install GitHub.cli; gh auth login). -Notes is shown to users in
# the "Update available" prompt. If build_scripts\output\USER_GUIDE.pdf
# exists, a zip of Setup.exe + the PDF is attached too (for manual installs).

param(
    [Parameter(Mandatory = $true)][string]$Notes
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# Native tools report failure by exit code. Windows PowerShell 5.1 can turn
# their stderr output into errors, so "Stop" is lifted while they run.
function Invoke-Native([string]$What, [scriptblock]$Command) {
    $ErrorActionPreference = "Continue"
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$What failed (exit code $LASTEXITCODE)" }
}

$match = Select-String -Path "app\version.py" -Pattern '__version__\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"'
if (-not $match) { throw "Couldn't read __version__ from app\version.py" }
$version = $match.Matches[0].Groups[1].Value
$tag = "v$version"
Write-Host "Releasing $tag"

# The release must match a pushed commit, so the tag points at real source.
if (git status --porcelain) { throw "Working tree has uncommitted changes - commit and push first." }
Invoke-Native "git fetch" { git fetch origin main --quiet }
$head = git rev-parse HEAD
if ($head -ne (git rev-parse origin/main)) { throw "HEAD isn't origin/main - push (or pull) first." }

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "GitHub CLI (gh) not found - winget install GitHub.cli, then gh auth login." }
$ErrorActionPreference = "Continue"
gh release view $tag *> $null
$exists = $LASTEXITCODE -eq 0
$ErrorActionPreference = "Stop"
if ($exists) { throw "Release $tag already exists - bump __version__ in app\version.py." }

$iscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) { throw "Inno Setup not found at $iscc" }

Invoke-Native "PyInstaller" { python -m PyInstaller --noconfirm build_scripts\automaticprocess.spec }
Invoke-Native "Inno Setup" { & $iscc "/DMyAppVersion=$version" build_scripts\installer.iss }

$setup = "build_scripts\output\AutomaticProcess-Setup.exe"
$assets = @($setup)
$guide = "build_scripts\output\USER_GUIDE.pdf"
if (Test-Path $guide) {
    $zip = "build_scripts\output\AutomaticProcess-$tag.zip"
    Compress-Archive -Path $setup, $guide -DestinationPath $zip -Force
    $assets += $zip
} else {
    Write-Warning "No $guide - publishing Setup.exe only (no zip)."
}

Invoke-Native "gh release create" { gh release create $tag @assets --target $head --title $tag --notes $Notes }
Write-Host "Published $tag"
