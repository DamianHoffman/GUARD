<#
.SYNOPSIS
  Server health report for Windows or Linux (PowerShell 7+ or Windows PowerShell 5.1).
.DESCRIPTION
  Collects uptime, memory, disk usage and (optionally) the state of named services.
  Prints a table, writes a JSON report and returns exit code 0 (OK), 1 (WARN) or 2 (CRIT),
  so it can be scheduled (Task Scheduler / cron) and wired to alerting.
.EXAMPLE
  ./Get-ServerHealth.ps1 -OutputDir ./reports -Service postgresql,cron
#>
[CmdletBinding()]
param(
    [string]$OutputDir = (Join-Path (Join-Path $PSScriptRoot '..') 'logs'),
    [string[]]$Service = @(),
    [int]$DiskWarnPct = 80,
    [int]$DiskCritPct = 90,
    [int]$MemWarnPct  = 85
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# `pwsh -File script.ps1 -Service a,b` delivers one string "a,b": split it so cron / Task Scheduler calls work
$Service = @($Service | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

$isWin = ($PSVersionTable.PSEdition -eq 'Desktop') -or ($IsWindows -eq $true)
$findings = New-Object System.Collections.Generic.List[object]
function Add-Finding([string]$Level, [string]$Check, [string]$Message) {
    $script:findings.Add([pscustomobject]@{ Level = $Level; Check = $Check; Message = $Message })
}

# --- uptime + memory
if ($isWin) {
    $os     = Get-CimInstance Win32_OperatingSystem
    $uptime = (Get-Date) - $os.LastBootUpTime
    $memTotalMB = [math]::Round($os.TotalVisibleMemorySize / 1024)
    $memFreeMB  = [math]::Round($os.FreePhysicalMemory / 1024)
    $osName = $os.Caption
} else {
    $uptime = [TimeSpan]::FromSeconds([double](((Get-Content /proc/uptime) -split ' ')[0]))
    $mem = @{}
    Get-Content /proc/meminfo | ForEach-Object { if ($_ -match '^(\w+):\s+(\d+)') { $mem[$Matches[1]] = [double]$Matches[2] } }
    $memTotalMB = [math]::Round($mem['MemTotal'] / 1024)
    $memFreeMB  = [math]::Round($mem['MemAvailable'] / 1024)
    $osName = ((Get-Content /etc/os-release | Where-Object { $_ -like 'PRETTY_NAME=*' }) -replace 'PRETTY_NAME=|"', '')
}
$memUsedPct = [math]::Round(100 * ($memTotalMB - $memFreeMB) / $memTotalMB, 1)
Add-Finding ($(if ($memUsedPct -ge $MemWarnPct) { 'WARN' } else { 'OK' })) 'memory' "$memUsedPct% used ($memFreeMB MB free of $memTotalMB MB)"
Add-Finding 'OK' 'uptime' ("{0}d {1}h {2}m" -f $uptime.Days, $uptime.Hours, $uptime.Minutes)

# --- disks
if ($isWin) {
    $disks = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
        [pscustomobject]@{ Name = $_.DeviceID; UsedPct = [math]::Round(100 * ($_.Size - $_.FreeSpace) / $_.Size, 1); FreeGB = [math]::Round($_.FreeSpace / 1GB, 1) }
    }
} else {
    $disks = & df -P -BG -x tmpfs -x devtmpfs -x overlay | Select-Object -Skip 1 | ForEach-Object {
        $p = $_ -split '\s+'
        [pscustomobject]@{ Name = $p[5]; UsedPct = [double]($p[4].TrimEnd('%')); FreeGB = [double]($p[3].TrimEnd('G')) }
    }
}
foreach ($d in $disks) {
    $lvl = if ($d.UsedPct -ge $DiskCritPct) { 'CRIT' } elseif ($d.UsedPct -ge $DiskWarnPct) { 'WARN' } else { 'OK' }
    Add-Finding $lvl "disk $($d.Name)" "$($d.UsedPct)% used, $($d.FreeGB) GB free"
}

# --- services
foreach ($svc in $Service) {
    if ($isWin) {
        $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
        $state = if ($s) { $s.Status.ToString() } else { 'not found' }
        $ok = ($state -eq 'Running')
    } else {
        try { $state = (& systemctl is-active $svc 2>$null) | Select-Object -First 1 } catch { $state = $null }
        if (-not $state) { $state = 'unknown (systemctl not available?)' }
        $ok = ($state -eq 'active')
    }
    Add-Finding ($(if ($ok) { 'OK' } else { 'CRIT' })) "service $svc" $state
}

# --- output
$null = New-Item -ItemType Directory -Force -Path $OutputDir
$report = [pscustomobject]@{
    Host = [System.Net.Dns]::GetHostName(); OS = $osName; Time = (Get-Date).ToString('s'); Findings = $findings
}
$file = Join-Path $OutputDir ("health_{0}_{1:yyyyMMdd_HHmmss}.json" -f $report.Host, (Get-Date))
$report | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $file

# Format-Table output is lost in non-interactive hosts unless it is rendered to a string first
($findings | Format-Table -AutoSize | Out-String -Width 200).TrimEnd() | Write-Host
Write-Host "Report written to $file"
if ($findings.Level -contains 'CRIT') { exit 2 }
if ($findings.Level -contains 'WARN') { exit 1 }
exit 0
