# Quick Start Guide

## Option 1: Automated Setup (Recommended)

### Windows
```bash
setup_github.bat
```

### Linux/Mac
```bash
chmod +x setup_github.sh
./setup_github.sh
```

Then follow the prompts!

## Option 2: Manual Setup

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Add GitHub Secrets

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these 7 secrets:

| Secret Name | Where to Get It |
|------------|-----------------|
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → AI |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → AI |
| `DRIVE_FOLDER_ID` | From your Drive folder URL |
| `DRIVE_PROCESSED_FOLDER_ID` | From your Drive folder URL |
| `YOUTUBE_CLIENT_SECRET` | Copy contents of `credentials/client_secret.json` |
| `YOUTUBE_TOKEN` | Copy contents of `credentials/token.json` |

### 3. Get YouTube Credentials

**First time only:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable YouTube Data API v3 & Drive API
3. Create OAuth credentials (Desktop app)
4. Download as `credentials/client_secret.json`
5. Run locally: `python main.py --list`
6. Authenticate in browser
7. This creates `credentials/token.json`
8. Copy both JSON files to GitHub secrets

### 4. Done!

Your automation will now run:
- **Morning**: 6:00 AM UTC
- **Evening**: 6:00 PM UTC

Or trigger manually: **Actions tab → Run workflow**

## Customization

Edit `.github/workflows/auto-upload.yml` to change schedule:

```yaml
schedule:
  - cron: '0 6 * * *'   # Change time here
  - cron: '0 18 * * *'  # Change time here
```

## Troubleshooting

**Workflow fails?**
1. Check Actions tab for error logs
2. Verify all 7 secrets are added correctly
3. Ensure YouTube token is valid (re-run local auth if expired)

**Need detailed help?**
See `GITHUB_SETUP.md` for complete instructions.
