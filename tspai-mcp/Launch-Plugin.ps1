[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run the plugin as a standard Windows user.'
    }
    $base = Join-Path $env:LOCALAPPDATA 'TSPAI-MCP-Plugin'
    $configPath = Join-Path $base 'config.json'
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw 'Run Setup-Plugin.ps1 with an existing dedicated workspace first.'
    }
    $config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($config.schema_version -ne 1 -or
        $config.language -notin @('en','ja') -or
        $config.enable_plus1 -isnot [bool] -or
        $config.session_seconds -isnot [int] -or
        $config.session_seconds -lt 1 -or $config.session_seconds -gt 43200) {
        throw 'Invalid plugin configuration; rerun Setup-Plugin.ps1.'
    }
    if (-not [IO.Path]::IsPathRooted($config.workspace) -or
        -not (Test-Path -LiteralPath $config.workspace -PathType Container)) {
        throw 'The configured workspace is missing or is not absolute.'
    }
    $expectedData = Join-Path $base 'data'
    if ($config.data_dir -ne $expectedData) { throw 'Unexpected plugin data directory.' }
    $lockHash = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'requirements-windows.lock.txt') -Algorithm SHA256).Hash.ToLower()
    $python = Join-Path $base ('venvs\' + $lockHash + '\Scripts\python.exe')
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw 'Matching Python environment is missing; rerun Setup-Plugin.ps1.'
    }
    $serverArgs = @('-I','-u',(Join-Path $PSScriptRoot 'plugin_entry.py'),
        '--workspace',$config.workspace,'--data-dir',$config.data_dir,
        '--language',$config.language,'--session-seconds',[string]$config.session_seconds)
    if ($config.enable_plus1) { $serverArgs += '--enable-plus1' }
    # stdout is reserved for MCP. Do not add Write-Host/log output here.
    & $python @serverArgs
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
