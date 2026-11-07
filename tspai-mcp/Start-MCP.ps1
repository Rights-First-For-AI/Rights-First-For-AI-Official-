[CmdletBinding()]
param(
    [string]$Workspace,
    [string]$Python = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
    [ValidateRange(1,43200)][int]$SessionSeconds = 3600,
    [ValidateSet('en','ja')][string]$Language = 'en',
    [switch]$EnableWrite,
    [switch]$EnableCreate,
    [switch]$EnableEdit,
    [switch]$EnableDelete,
    [switch]$EnablePowerShell,
    [switch]$EnablePlus1,
    [switch]$Check
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Python missing; create the candidate venv first' }
$manifestPath = Join-Path $PSScriptRoot 'SHA256SUMS.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($entry in $manifest.PSObject.Properties) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $entry.Name) -Algorithm SHA256).Hash
    if ($actual -ne $entry.Value) { throw "Candidate checksum mismatch: $($entry.Name)" }
}
$server = Join-Path $PSScriptRoot 'server.py'
if ($Check) {
    & $Python -I -u $server --check --language $Language
    if ($LASTEXITCODE -ne 0) { throw 'Import check failed' }
    return
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run the candidate as a normal user, not an administrator'
}
if (-not $Workspace -or -not [IO.Path]::IsPathRooted($Workspace) -or
    -not (Test-Path -LiteralPath $Workspace -PathType Container)) { throw 'Existing absolute workspace required' }
$serverArgs = @('-I','-u',$server,'--workspace',$Workspace,'--session-seconds',"$SessionSeconds")
if ($Language -eq 'ja') { $serverArgs += @('--language','ja') }
if ($EnableWrite) { $serverArgs += '--enable-write' }
if ($EnableCreate) { $serverArgs += '--enable-create' }
if ($EnableEdit) { $serverArgs += '--enable-edit' }
if ($EnableDelete) { $serverArgs += '--enable-delete' }
if ($EnablePowerShell) { $serverArgs += '--enable-powershell' }
if ($EnablePlus1) { $serverArgs += '--enable-plus1' }
& $Python @serverArgs
if ($LASTEXITCODE -ne 0) { throw 'Candidate server stopped with an error' }
