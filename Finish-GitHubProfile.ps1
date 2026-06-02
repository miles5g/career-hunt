# One-shot: finish GitHub CLI login + set profile bio (run after approving device in browser)
$gh = "C:\Program Files\GitHub CLI\gh.exe"
Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue

Write-Host "If not logged in yet, a browser window will open. Approve the device, then return here." -ForegroundColor Cyan
& $gh auth login -h github.com -p https -w -s user
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Setting profile fields..." -ForegroundColor Green
& $gh api user -X PATCH -f bio="Business ops & automation · Python, SQL, VBA, React, Supabase · Building internal tools and AI-assisted workflows. Santa Monica."
& $gh api user -X PATCH -f company="Gursey | Schneider LLP"
& $gh api user -X PATCH -f location="Santa Monica, CA"
& $gh api user -X PATCH -f blog="https://www.linkedin.com/in/milesjohnsondata"

Write-Host "Done. Check https://github.com/miles5g" -ForegroundColor Green
