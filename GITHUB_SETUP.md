# GitHub profile — finish setup

## Done automatically

- **listsnap** — full codebase pushed to https://github.com/miles5g/listsnap (Luke Everly credit removed)
- **zombietrain / train-hole** — same repository (no duplicate to delete). Canonical URL: https://github.com/miles5g/zombietrain
- README display names updated: **TikTok Live Bridge**, **Rail Survivor**, **Isometric Grid Prototype**

## You run once (`gh auth login` first)

See **RENAME_REPOS.md** for:

1. Renaming repos to professional slugs (`tiktok-live-bridge`, `rail-survivor`, `isometric-grid-prototype`)
2. Setting profile **bio**, **company**, **location**, **blog**
3. Creating **miles5g/miles5g** profile README (if push failed below)

### Create profile repo manually (if needed)

1. https://github.com/new → owner **miles5g**, repository name **miles5g** (exactly your username)
2. Public, add a README
3. Replace its README with `Career/github-profile-README.md` and push

Or after `gh auth login`:

```powershell
gh repo create miles5g --public --description "GitHub profile"
cd "c:\Users\owner\Documents\Cursor Projects\Career\miles5g-profile"
git push -u origin main
```
