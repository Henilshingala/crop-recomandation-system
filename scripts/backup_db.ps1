# Daily SQLite backup with 7-day retention.
# Run via Task Scheduler or: .\scripts\backup_db.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DbPath = Join-Path $ProjectRoot "Backend\app\db.sqlite3"
$BackupDir = Join-Path $ProjectRoot "Backups"
$RetentionDays = 7

if (-not (Test-Path $DbPath)) {
    Write-Error "DB not found: $DbPath"
    exit 1
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$Date = Get-Date -Format "yyyyMMdd"
$BackupFile = Join-Path $BackupDir "db_$Date.sqlite3"

Copy-Item $DbPath $BackupFile -Force
Write-Host "Backed up to $BackupFile"

$Cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupDir -Filter "db_*.sqlite3" | Where-Object { $_.LastWriteTime -lt $Cutoff } | Remove-Item -Force
Write-Host "Retention: kept last $RetentionDays days"
