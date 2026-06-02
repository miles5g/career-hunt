# Import Simplify_Tracked_Jobs CSV into Career tracking format.
param(
    [string]$InputCsv = "$env:USERPROFILE\Downloads\Simplify_Tracked_Jobs_2026-05-20.csv",
    [string]$ArchiveCopy = "$PSScriptRoot\..\tracking\simplify_export_2026-05-20.csv",
    [string]$OutApplications = "$PSScriptRoot\..\tracking\applications.csv",
    [string]$OutFull = "$PSScriptRoot\..\tracking\simplify_jobs_full.csv"
)

function Get-DirectJobUrl([string]$url) {
    if ([string]::IsNullOrWhiteSpace($url)) { return "" }
    if ($url -match 'linkedin\.com/jobs/search') { return $url }
    return $url
}

function Get-Lane([string]$title) {
    $t = $title.ToLower()
    if ($t -match 'implementation|onboarding|technical account|deployment strategist|solutions architect') { return 'A-implementation' }
    if ($t -match 'automation|process|systems|gtm engineer|data analyst|ai data|fp&a') { return 'B-automation' }
    if ($t -match 'revops|revenue ops|bizops|business operations|strategy') { return 'C-bizops-revops' }
    return 'other'
}

function Score-Job([string]$title, [string]$company, [string]$location) {
    $t = $title.ToLower()
    $c = $company.ToLower()
    $fit = 3
    if ($t -match 'product ops|bizops|business operations|implementation|revops analyst|strategy.and operations|automation engineer|process') { $fit = 4 }
    if ($t -match 'director|senior manager|principal') { $fit = 2 }
    if ($t -match 'consultant|fractional|contractor') { $fit = 3 }
    $boredom = 4
    if ($t -match 'automation|systems|engineer|architect|implementation|product ops|gtm engineer') { $boredom = 5 }
    if ($t -match 'data analyst|business development') { $boredom = 3 }
    $culture = 4
    if ($location -match 'remote|usa|united states') { $culture = 5 }
    if ($location -match 'mexico|ireland|uk|canada|dallas|atlanta|chicago|new york') { $culture = 3 }
    $comp = 3
    $win = 3
    if ($c -match 'openai|google|stripe|discord|airbnb|activision|riot') { $win = 2 }
    if ($t -match 'associate|analyst|specialist|implementation') { $win = 4 }
    $total = $fit + $boredom + $culture + $comp + $win
    return @{ fit=$fit; boredom=$boredom; culture=$culture; comp=$comp; win=$win; total=$total }
}

if (-not (Test-Path $InputCsv)) {
    Write-Error "File not found: $InputCsv"
    exit 1
}

Copy-Item $InputCsv $ArchiveCopy -Force
$rows = Import-Csv $InputCsv

$out = foreach ($r in $rows) {
    $scores = Score-Job $r.'Job Title' $r.'Company Name' $r.Location
    $status = switch ($r.Status) {
        'APPLIED' { 'applied' }
        'SAVED' { 'saved' }
        default { $r.Status.ToLower() }
    }
    $date = if ($r.'Applied Date' -and $r.'Applied Date' -ne 'N/A') { $r.'Applied Date' } else { $r.'Status Date' }
    [PSCustomObject]@{
        date            = $date
        company         = $r.'Company Name'
        title           = $r.'Job Title'
        source          = 'Simplify'
        url             = Get-DirectJobUrl $r.'Job URL'
        score_fit       = $scores.fit
        score_boredom   = $scores.boredom
        score_culture   = $scores.culture
        score_comp      = $scores.comp
        score_win       = $scores.win
        total           = $scores.total
        status          = $status
        notes           = "lane=$(Get-Lane $r.'Job Title'); loc=$($r.Location); type=$($r.job_type)"
        resume_version  = ''
        follow_up_date  = ''
    }
}

$out | Export-Csv $OutFull -NoTypeInformation -Encoding UTF8
$out | Export-Csv $OutApplications -NoTypeInformation -Encoding UTF8

Write-Host "Imported $($out.Count) jobs"
Write-Host "  Archive: $ArchiveCopy"
Write-Host "  Full:    $OutFull"
Write-Host "  Tracker: $OutApplications"

# Summary stats
$applied = ($out | Where-Object status -eq 'applied').Count
$saved = ($out | Where-Object status -eq 'saved').Count
$dupes = $out | Group-Object company, title | Where-Object Count -gt 1
Write-Host "  Applied: $applied | Saved: $saved | Duplicate title rows: $($dupes.Count)"
