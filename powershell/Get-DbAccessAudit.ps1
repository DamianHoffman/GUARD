<#
.SYNOPSIS
  Database account audit: who can log in, who is superuser, who can read personal data.
.DESCRIPTION
  Uses psql (no extra modules needed). Credentials come from the environment, never from parameters:
  PGPASSWORD (admin). Writes a CSV for the audit trail and prints findings. Exit code 1 if something
  looks wrong (extra superusers, roles that can read core.advertisers without being on the allow-list).
.EXAMPLE
  $env:PGPASSWORD = '...'; ./Get-DbAccessAudit.ps1 -DbHost localhost -User postgres
#>
[CmdletBinding()]
param(
    [string]$DbHost = 'localhost',
    [int]$Port = 5432,
    [string]$Database = 'guard',
    [string]$User = 'postgres',
    [string]$OutputDir = (Join-Path (Join-Path $PSScriptRoot '..') 'logs'),
    [string[]]$AllowedPiiReaders = @('postgres', 'guard_backup')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $env:PGPASSWORD) { throw 'Set $env:PGPASSWORD first (do not pass passwords as parameters).' }
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) { throw 'psql not found in PATH.' }

function Invoke-Psql([string]$Sql) {
    $out = & psql -h $DbHost -p $Port -U $User -d $Database --csv -X -q -c $Sql
    if ($LASTEXITCODE -ne 0) { throw "psql failed (exit $LASTEXITCODE)" }
    $out | ConvertFrom-Csv
}

$roles = Invoke-Psql @"
SELECT r.rolname AS role, r.rolcanlogin AS can_login, r.rolsuper AS superuser, r.rolcreaterole AS create_role,
       r.rolcreatedb AS create_db, r.rolconnlimit AS conn_limit, r.rolvaliduntil AS password_expires,
       has_table_privilege(r.rolname, 'core.advertisers', 'SELECT') AS can_read_pii,
       COALESCE((SELECT string_agg(g.rolname, ';') FROM pg_auth_members m JOIN pg_roles g ON g.oid = m.roleid
                 WHERE m.member = r.oid), '') AS member_of
FROM pg_roles r WHERE r.rolname !~ '^pg_' ORDER BY r.rolname
"@

$findings = @()
foreach ($r in $roles) {
    if ($r.superuser -eq 't' -and $r.role -ne $User)               { $findings += "Superuser that is not the admin account: $($r.role)" }
    if ($r.can_read_pii -eq 't' -and $r.role -notin $AllowedPiiReaders) { $findings += "Role can read personal data but is not on the allow-list: $($r.role)" }
    if ($r.can_login -eq 't' -and -not $r.password_expires)        { Write-Verbose "No password expiry set for login role $($r.role)" }
}

$null = New-Item -ItemType Directory -Force -Path $OutputDir
$file = Join-Path $OutputDir ("db_access_audit_{0:yyyyMMdd}.csv" -f (Get-Date))
$roles | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $file

($roles | Format-Table role, can_login, superuser, can_read_pii, member_of -AutoSize | Out-String -Width 200).TrimEnd() | Write-Host
if ($findings) { $findings | ForEach-Object { Write-Warning $_ }; Write-Host "Audit written to $file"; exit 1 }
Write-Host "No findings. Audit written to $file"
