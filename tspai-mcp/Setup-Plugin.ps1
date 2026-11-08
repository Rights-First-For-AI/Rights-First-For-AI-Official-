[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Workspace,
    [ValidateSet('en','ja')][string]$Language = 'en',
    [ValidateRange(1,43200)][int]$SessionSeconds = 3600,
    [switch]$EnablePlus1
)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use a standard Windows account, not an elevated PowerShell.'
}
if (-not [IO.Path]::IsPathRooted($Workspace) -or
    -not (Test-Path -LiteralPath $Workspace -PathType Container)) {
    throw 'Workspace must be an existing absolute directory.'
}
$Workspace = (Resolve-Path -LiteralPath $Workspace).Path
$base = Join-Path $env:LOCALAPPDATA 'TSPAI-MCP-Plugin'
$data = Join-Path $base 'data'
$baseFull = [IO.Path]::GetFullPath($base).TrimEnd('\')
$workspaceFull = [IO.Path]::GetFullPath($Workspace).TrimEnd('\')
if ($workspaceFull.Equals($baseFull, [StringComparison]::OrdinalIgnoreCase) -or
    $workspaceFull.StartsWith($baseFull + '\', [StringComparison]::OrdinalIgnoreCase) -or
    $baseFull.StartsWith($workspaceFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Keep the workspace separate from the private plugin runtime and records.'
}
$lock = Join-Path $PSScriptRoot 'requirements-windows.lock.txt'
$lockHash = (Get-FileHash -LiteralPath $lock -Algorithm SHA256).Hash.ToLower()
$venv = Join-Path $base ('venvs\' + $lockHash)
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    & py -3.11 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 x64 with venv support is required.' }
}
& $python -I -c "import sys, struct; assert sys.version_info[:2] == (3, 11) and struct.calcsize('P') == 8"
if ($LASTEXITCODE -ne 0) { throw 'The environment must use Python 3.11 x64.' }
& $python -I -m pip install --no-index --find-links (Join-Path $PSScriptRoot 'vendor\wheels') --require-hashes --only-binary=:all: -r $lock
if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
& $python -I -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency verification failed.' }
& $python -I -u (Join-Path $PSScriptRoot 'plugin_entry.py') --check --language $Language
if ($LASTEXITCODE -ne 0) { throw 'Plugin import check failed.' }
New-Item -ItemType Directory -Path $base -Force | Out-Null
New-Item -ItemType Directory -Path $data -Force | Out-Null
$config = [ordered]@{
    schema_version = 1
    workspace = $Workspace
    data_dir = $data
    language = $Language
    session_seconds = $SessionSeconds
    enable_plus1 = [bool]$EnablePlus1
}
$config | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $base 'config.json') -Encoding UTF8
Write-Host 'Setup completed. Install the plugin in a compatible Windows desktop host.'
Write-Host 'Windows Hello approval is still required when the server starts.'
