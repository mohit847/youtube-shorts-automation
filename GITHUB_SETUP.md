# GitHub Actions Setup Guide

Follow these steps to set up automated YouTube Shorts uploads using GitHub Actions.

## Step 1: Push Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: YouTube Shorts automation"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

## Step 2: Get YouTube API Credentials

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it (e.g., "YouTube Shorts Automation")
4. Click "Create"

### 2.2 Enable APIs

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search and enable:
   - **YouTube Data API v3**
   - **Google Drive API**

### 2.3 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: Your channel name
   - User support email: Your email
   - Developer contact: Your email
   - Add scopes: `../auth/youtube.upload`, `../auth/drive`
   - Add test users: Your Google account email
4. Back to "Create OAuth client ID":
   - Application type: **Desktop app**
   - Name: "YouTube Automation"
   - Click "Create"
5. Download the JSON file → rename to `client_secret.json`
6. Place in `credentials/` folder

### 2.4 Generate Token (First Time)

```bash
# Run locally to authenticate
python main.py --list

# This will:
# 1. Open browser for Google OAuth
# 2. Ask you to sign in and grant permissions
# 3. Generate credentials/token.json
```

## Step 3: Add GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 7 secrets:

### 3.1 API Keys

**GEMINI_API_KEY**
```
your_gemini_api_key_here
```
(Get from: https://aistudio.google.com/app/apikey)

**CLOUDFLARE_ACCOUNT_ID**
```
your_cloudflare_account_id
```

**CLOUDFLARE_API_TOKEN**
```
your_cloudflare_api_token
```
(Get from: Cloudflare Dashboard → AI → Workers AI)

### 3.2 Google Drive Folders

**DRIVE_FOLDER_ID**
```
your_drive_folder_id_here
```
(From your Drive folder URL)

**DRIVE_PROCESSED_FOLDER_ID**
```
your_processed_folder_id_here
```

### 3.3 YouTube Credentials

**YOUTUBE_CLIENT_SECRET**
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```
(Copy entire contents of `credentials/client_secret.json`)

**YOUTUBE_TOKEN**
```json
{
  "token": "ya29.a0AfB_...",
  "refresh_token": "1//0gXXX...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "scopes": ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/drive"],
  "expiry": "2024-01-01T00:00:00.000000Z"
}
```
(Copy entire contents of `credentials/token.json` after running locally once)

## Step 4: Configure Schedule

Edit `.github/workflows/auto-upload.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'   # 6:00 AM UTC = 11:30 AM IST
  - cron: '0 18 * * *'  # 6:00 PM UTC = 11:30 PM IST
```

### Cron Format
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday=0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23, UTC)
└─────────── Minute (0-59)
```

### Common Schedules
- `0 6 * * *` - Every day at 6:00 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 9,21 * * *` - 9 AM and 9 PM UTC
- `0 0 * * 1` - Every Monday at midnight

## Step 5: Test the Workflow

### Manual Test
1. Go to your GitHub repo
2. Click **Actions** tab
3. Select "Auto Upload YouTube Shorts"
4. Click **Run workflow** → **Run workflow**
5. Watch the logs

### Check Logs
- Green checkmark = Success
- Red X = Failed (click to see error logs)

## Step 6: Monitor

### View Runs
- GitHub repo → **Actions** tab
- See all workflow runs and their status

### Debugging
If workflow fails:
1. Click on the failed run
2. Expand the failed step
3. Read error messages
4. Common issues:
   - Invalid API keys
   - Expired YouTube token (re-run local auth)
   - No songs in Drive folder
   - FFmpeg errors

## Step 7: Update Secrets (When Needed)

### Token Expired?
1. Run locally: `python main.py --list`
2. Re-authenticate in browser
3. Copy new `credentials/token.json` contents
4. Update **YOUTUBE_TOKEN** secret in GitHub

### Change API Keys?
Just update the corresponding secret in GitHub → Settings → Secrets

## Troubleshooting

### "No songs found"
- Check DRIVE_FOLDER_ID is correct
- Ensure songs are in the folder
- Verify Drive API is enabled

### "YouTube upload failed"
- Token might be expired → regenerate
- Check video meets YouTube requirements
- Verify YouTube API quota

### "FFmpeg error"
- Usually means invalid transition or filter
- Check GitHub Actions logs for details

### "Rate limited"
- Cloudflare AI: Wait or reduce image count
- YouTube: Check daily quota limits
- Gemini: Wait or use different API key

## Security Notes

⚠️ **NEVER commit these files:**
- `.env`
- `credentials/client_secret.json`
- `credentials/token.json`
- Any API keys

✅ **Always use GitHub Secrets** for sensitive data

## Need Help?

Check the logs in GitHub Actions for detailed error messages.
