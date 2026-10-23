[CmdletBinding()]
param(
    [switch]$InstallDependencies
)

if ($MyInvocation.InvocationName -ne '.') {
    throw 'Dot-source this script to activate the environment in the current session: . .\scripts\activate-test-env.ps1'
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'
$activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'

if (-not (Test-Path $venvPython)) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if ($pyLauncher) {
        & $pyLauncher.Source -3 -m venv $venvPath
    } elseif ($pythonCommand) {
        & $pythonCommand.Source -m venv $venvPath
    } else {
        throw 'Python was not found. Install Python 3 and ensure py or python is on PATH.'
    }

    if ($LASTEXITCODE -ne 0) {
        throw 'Virtual environment creation failed.'
    }
}

$pythonVersion = & $venvPython --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "The existing virtual environment cannot start Python ($pythonVersion). Remove the project's .venv folder and run this script again to recreate it."
}

if (-not (Test-Path $activateScript)) {
    throw "Virtual environment activation script not found: $activateScript"
}

. $activateScript

if ($InstallDependencies) {
    & $venvPython -m pip install -r (Join-Path $projectRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        throw 'Dependency installation failed.'
    }
}

Write-Host "Activated project environment: $venvPath"
if (-not $InstallDependencies) {
    Write-Host 'Use -InstallDependencies to install or update requirements.txt packages.'
}
