<#
.SYNOPSIS
  Grandfather-father-son style retention for backup files named guard_yyyyMMdd_HHmmss.dump[.gpg].
.DESCRIPTION
  Keeps the newest backup of each of the last -KeepDaily days and the newest backup of each of the last
  -KeepWeekly weeks. Everything else (and its .sha256 file) is deleted.
  Supports -WhatIf / -Confirm, so ALWAYS try it with -WhatIf first.
.EXAMPLE
  ./Invoke-BackupRotation.ps1 -Path ../backups -KeepDaily 7 -KeepWeekly 4 -WhatIf
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory)][string]$Path,
    [int]$KeepDaily  = 7,
    [int]$KeepWeekly = 4
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Path -PathType Container)) { throw "Backup directory not found: $Path" }

$pattern = '^guard_(\d{8})_(\d{6})\.dump(\.gpg)?$'
$backups = @(Get-ChildItem -LiteralPath $Path -File | Where-Object { $_.Name -match $pattern } | ForEach-Object {
    $null = $_.Name -match $pattern
    [pscustomobject]@{
        File = $_
        Time = [datetime]::ParseExact("$($Matches[1])$($Matches[2])", 'yyyyMMddHHmmss', [cultureinfo]::InvariantCulture)
    }
} | Sort-Object Time -Descending)

if (-not $backups) { Write-Warning "No backups matching the naming pattern in $Path"; return }

$keep = New-Object 'System.Collections.Generic.HashSet[string]'
$now = Get-Date
# newest backup per calendar day within the daily window
$backups | Where-Object { $_.Time -ge $now.Date.AddDays(-($KeepDaily - 1)) } |
    Group-Object { $_.Time.Date } | ForEach-Object { [void]$keep.Add($_.Group[0].File.FullName) }
# newest backup per week within the weekly window (week starts Monday)
$backups | Where-Object { $_.Time -ge $now.Date.AddDays(-7 * $KeepWeekly) } |
    Group-Object { $d = $_.Time.Date; $d.AddDays(-(([int]$d.DayOfWeek + 6) % 7)) } |
    ForEach-Object { [void]$keep.Add($_.Group[0].File.FullName) }
# never delete the very newest backup, whatever else happens
[void]$keep.Add($backups[0].File.FullName)

$removed = 0; $freed = 0
foreach ($b in $backups) {
    if ($keep.Contains($b.File.FullName)) { Write-Verbose "keep   $($b.File.Name)"; continue }
    if ($PSCmdlet.ShouldProcess($b.File.FullName, 'Delete old backup')) {
        $freed += $b.File.Length
        Remove-Item -LiteralPath $b.File.FullName -Force
        $sum = "$($b.File.FullName).sha256"
        if (Test-Path -LiteralPath $sum) { Remove-Item -LiteralPath $sum -Force }
        $removed++
    }
}
Write-Host ("Backups found: {0}, kept: {1}, removed: {2}, freed: {3:N1} MB" -f $backups.Count, $keep.Count, $removed, ($freed / 1MB))
