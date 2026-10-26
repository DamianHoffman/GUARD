<#
.SYNOPSIS
  Weekly campaign report for the sales department: reads reporting.campaign_summary, writes a CSV.
.DESCRIPTION
  Connects as the read-only analyst role (guard_analyst), which cannot see personal data.
  Password is read from $env:ANALYST_PASSWORD. UTF-8 with BOM + semicolon delimiter so that Polish
  Excel opens the file correctly by double-click.
.EXAMPLE
  $env:ANALYST_PASSWORD = '...'; ./Export-CampaignReport.ps1 -OutputDir ./reports -OnlyActive
#>
[CmdletBinding()]
param(
    [string]$DbHost = 'localhost',
    [int]$Port = 5432,
    [string]$Database = 'guard',
    [string]$OutputDir = (Join-Path (Join-Path $PSScriptRoot '..') 'reports'),
    [switch]$OnlyActive,
    [double]$OverBudgetPct = 100
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $env:ANALYST_PASSWORD) { throw 'Set $env:ANALYST_PASSWORD first.' }
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) { throw 'psql not found in PATH.' }

$where = if ($OnlyActive) { "WHERE status = 'active'" } else { '' }
$sql = "SELECT campaign_code, campaign_name, advertiser, status, start_date, end_date, budget_pln, spend_pln, " +
       "impressions, clicks, ctr_pct, cpc_pln, budget_used_pct, last_data_date FROM reporting.campaign_summary $where ORDER BY spend_pln DESC"

$env:PGPASSWORD = $env:ANALYST_PASSWORD
try {
    $rows = & psql -h $DbHost -p $Port -U guard_analyst -d $Database --csv -X -q -c $sql | ConvertFrom-Csv
    if ($LASTEXITCODE -ne 0) { throw "psql failed (exit $LASTEXITCODE)" }
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

$null = New-Item -ItemType Directory -Force -Path $OutputDir
$file = Join-Path $OutputDir ("campaign_report_{0:yyyy-MM-dd}.csv" -f (Get-Date))
$rows | Export-Csv -Path $file -NoTypeInformation -Delimiter ';' -Encoding UTF8

$over = @($rows | Where-Object { $_.budget_used_pct -and [double]$_.budget_used_pct -gt $OverBudgetPct })
Write-Host ("{0} campaigns exported to {1}" -f @($rows).Count, $file)
if ($over.Count -gt 0) {
    Write-Warning ("{0} campaign(s) above {1}% of budget:" -f $over.Count, $OverBudgetPct)
    ($over | Select-Object campaign_code, advertiser, budget_pln, spend_pln, budget_used_pct | Format-Table -AutoSize | Out-String -Width 200).TrimEnd() | Write-Host
}
