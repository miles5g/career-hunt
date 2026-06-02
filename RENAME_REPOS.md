# Rename GitHub repositories (one-time)

Run after `gh auth login` in PowerShell:

```powershell
# Live stream project
gh repo rename tiktok-live-bridge --repo miles5g/live_roblox

# Game (currently zombietrain; train-hole URL redirects here — same repo)
gh repo rename rail-survivor --repo miles5g/zombietrain

# Isometric prototype
gh repo rename isometric-grid-prototype --repo miles5g/milky-world
```

Then update local remotes:

```powershell
cd "c:\Users\owner\Documents\Cursor Projects\live_roblox"
git remote set-url origin https://github.com/miles5g/tiktok-live-bridge.git

cd "c:\Users\owner\Documents\Cursor Projects\train-hole"
git remote set-url origin https://github.com/miles5g/rail-survivor.git

cd "c:\Users\owner\Documents\Cursor Projects\milky-world"
git remote set-url origin https://github.com/miles5g/isometric-grid-prototype.git
```

## Profile bio (run once)

```powershell
gh api user -X PATCH -f bio="Business ops & automation · Python, SQL, VBA, React, Supabase · Building internal tools and AI-assisted workflows. Santa Monica."
gh api user -X PATCH -f company="Gursey | Schneider LLP"
gh api user -X PATCH -f location="Santa Monica, CA"
gh api user -X PATCH -f blog="https://www.linkedin.com/in/milesjohnsondata"
```

## Profile README repo

```powershell
gh repo create miles5g --public --description "Profile" 2>$null
cd $env:TEMP
git clone https://github.com/miles5g/miles5g.git
copy "c:\Users\owner\Documents\Cursor Projects\Career\github-profile-README.md" miles5g\README.md
cd miles5g
git add README.md
git commit -m "Update profile README"
git push
```
