# Import Simplify Copilot application history from Chrome extension storage (LevelDB).
# Close Chrome first for best results (or uses .ldb snapshot copy).
#
# Usage:
#   .\scripts\import_simplify_history.ps1
#   .\scripts\import_simplify_history.ps1 -ChromeProfile "Profile 4"

param(
    [string]$ChromeProfile = "Profile 4",
    [string]$OutCsv = "$PSScriptRoot\..\tracking\simplify_import.csv"
)

$extId = "pbanhockgagggenencehbnadejlgchfc"
$ldbDir = "$env:LOCALAPPDATA\Google\Chrome\User Data\$ChromeProfile\Local Extension Settings\$extId"
$ldbFile = Get-ChildItem $ldbDir -Filter "*.ldb" -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 1

if (-not $ldbFile) {
    Write-Error "Simplify extension data not found. Install Simplify Copilot in Chrome or check profile name."
    exit 1
}

$tmp = Join-Path $env:TEMP "simplify-import.ldb"
Copy-Item $ldbFile.FullName $tmp -Force
$bytes = [System.IO.File]::ReadAllBytes($tmp)
$text = [System.Text.Encoding]::UTF8.GetString($bytes)

$companies = [regex]::Matches($text, '"companyName"\s*:\s*"([^"]{2,80})"') |
    ForEach-Object { $_.Groups[1].Value.Trim() } |
    Where-Object {
        $_ -match '^[A-Za-z0-9]' -and
        $_ -notmatch 'INPUT|Tag|ATSKey|i!' -and
        $_.Length -ge 3 -and $_.Length -le 70
    } |
    Select-Object -Unique |
    Sort-Object

$rows = foreach ($c in $companies) {
    [PSCustomObject]@{
        date       = ""
        company    = $c
        title      = ""
        source     = "Simplify"
        url        = ""
        status     = "imported_simplify"
        notes      = "Imported from extension LevelDB; title/date not in local blob - enrich from dashboard"
    }
}

$rows | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8
Write-Host "Exported $($rows.Count) companies to $OutCsv"
Write-Host "Tip: For full history (titles, dates, status), export CSV from https://simplify.jobs/dashboard"
