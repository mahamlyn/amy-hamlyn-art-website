[CmdletBinding()]
param()

if ($MyInvocation.InvocationName -ne '.') {
    throw 'Dot-source this script to deactivate the environment in the current session: . .\scripts\deactivate-test-env.ps1'
}

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$venvPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot '.venv'))
$cachePath = Join-Path $projectRoot '__pycache__'
$activeVenvPath = $null

if ($env:VIRTUAL_ENV) {
    $activeVenvPath = [System.IO.Path]::GetFullPath($env:VIRTUAL_ENV)
    if (-not [string]::Equals($activeVenvPath, $venvPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Another virtual environment is active ($activeVenvPath). It was left untouched."
    }

    $deactivateCommand = Get-Command deactivate -CommandType Function -ErrorAction SilentlyContinue
    if (-not $deactivateCommand) {
        throw 'The project environment is active, but its deactivate function is unavailable. No folders were removed.'
    }

    deactivate
    if ($env:VIRTUAL_ENV) {
        throw 'The project environment did not deactivate successfully. No folders were removed.'
    }
}

$currentPath = [System.IO.Path]::GetFullPath((Get-Location).Path)
$venvPrefix = $venvPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
if ([string]::Equals($currentPath, $venvPath, [System.StringComparison]::OrdinalIgnoreCase) -or
    $currentPath.StartsWith($venvPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Change to a directory outside .venv before running cleanup. No folders were removed.'
}

if (Test-Path -LiteralPath $venvPath) {
    Remove-Item -LiteralPath $venvPath -Recurse -Force
    Write-Host "Removed project virtual environment: $venvPath"
} else {
    Write-Host 'Project virtual environment is already absent.'
}

if (Test-Path -LiteralPath $cachePath) {
    Remove-Item -LiteralPath $cachePath -Recurse -Force
    Write-Host "Removed project Python cache: $cachePath"
} else {
    Write-Host 'Project Python cache is already absent.'
}
