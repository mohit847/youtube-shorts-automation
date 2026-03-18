# Complete Credentials Setup Guide

This guide will help you create ALL the credentials and API keys needed for the YouTube Shorts automation.

---

## 1. Gemini API Key (Google AI)

### What it's for:
- Analyzing songs and extracting lyrics
- Generating metadata (titles, descriptions, tags)

### How to get it:

1. Go to: **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select **"Create API key in new project"** (or use existing)
5. Copy the API key (starts with `AIzaSy...`)
6. Save it - you'll need it for GitHub Secrets

**Example format:** `AIzaSyAbCdEfGhIjKlMnQrStUvWxYz1234567`

---

## 2. Cloudflare Workers AI Credentials

### What it's for:
- Generating AI images for video backgrounds

### How to get it:

#### Step 1: Create Cloudflare Account
1. Go to: **https://dash.cloudflare.com/sign-up**
2. Sign up with email
3. Verify your email

#### Step 2: Get Account ID
1. Log in to Cloudflare Dashboard
2. Go to: **https://dash.cloudflare.com/**
3. Click on **"Workers & Pages"** in left sidebar
4. Click **"Overview"**
5. On the right side, you'll see **"Account ID"**
6. Copy it (32 characters, hex format)

**Example format:** `0f4ddf5fc01647156236960aab36`

#### Step 3: Create API Token
1. In Cloudflare Dashboard, click your profile (top right)
2. Click **"My Profile"**
3. Click **"API Tokens"** tab
4. Click **"Create Token"**
5. Click **"Use template"** next to **"Edit Cloudflare Workers"**
6. Or create custom token with these permissions:
   - Account → Workers AI → Read
   - Account → Workers Scripts → Edit
7. Click **"Continue to summary"**
8. Click **"Create Token"**
9. **COPY THE TOKEN NOW** (you can't see it again!)

**Example format:** `w4DzfKlIj88Co_ndFm_kNr-_7xxos2bAdgf-p`

---

## 3. Google Drive Folder IDs

### What it's for:
- Downloading songs to process
- Moving processed songs to archive folder

### How to get it:

#### Step 1: Create Folders in Google Drive

1. Go to: **https://drive.google.com/**
2. Create two folders:
   - **"YouTube Songs"** (for songs to process)
   - **"Processed Songs"** (for completed songs)

#### Step 2: Get Folder IDs

1. Open the **"YouTube Songs"** folder
2. Look at the URL in your browser:
   ```
   https://drive.google.com/drive/folders/1WzQs6dm3jKE8cK6-0iRCCDtJXOCZEdXi
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                          This is your DRIVE_FOLDER_ID
   ```
3. Copy the long string after `/folders/`
4. Repeat for **"Processed Songs"** folder

**Example format:** `1WzQs6dm3jKE8cK6-0iRCCDJXOCZEdXi`

#### Step 3: Upload Test Song
1. Upload an MP3 file to "YouTube Songs" folder
2. This will be used for testing

---

## 4. YouTube API Credentials (OAuth 2.0)

### What it's for:
- Uploading videos to your YouTube channel
- Accessing Google Drive

### How to get it:

#### Step 1: Create Google Cloud Project

1. Go to: **https://console.cloud.google.com/**
2. Click **"Select a project"** (top bar)
3. Click **"New Project"**
4. Project name: `YouTube Shorts Automation`
5. Click **"Create"**
6. Wait for project to be created
7. Select the new project from dropdown

#### Step 2: Enable Required APIs

1. In left sidebar, click **"APIs & Services"** → **"Library"**
2. Search for **"YouTube Data API v3"**
3. Click on it → Click **"Enable"**
4. Go back to Library
5. Search for **"Google Drive API"**
6. Click on it → Click **"Enable"**

#### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** → Click **"Create"**
3. Fill in:
   - App name: `YouTube Shorts Automation`
   - User support email: Your email
   - Developer contact: Your email
4. Click **"Save and Continue"**
5. Click **"Add or Remove Scopes"**
6. Search and add these scopes:
   - `../auth/youtube.upload`
   - `../auth/youtube.force-ssl`
   - `../auth/drive`
7. Click **"Update"** → **"Save and Continue"**
8. Click **"Add Users"** → Add your Google account email
9. Click **"Save and Continue"**
10. Click **"Back to Dashboard"**

#### Step 4: Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `YouTube Automation Desktop`
5. Click **"Create"**
6. Click **"Download JSON"** (download icon)
7. Save the file as `client_secret.json`
8. Move it to your project's `credentials/` folder

**File location:** `credentials/client_secret.json`

#### Step 5: Generate Token (First Time Authentication)

1. Open terminal in your project folder
2. Run:
   ```bash
   python main.py --list
   ```
3. A browser window will open
4. Sign in with your Google account
5. Click **"Continue"** when warned about unverified app
6. Grant all permissions
7. Browser will show "Authentication successful"
8. A file `credentials/token.json` is now created

**File location:** `credentials/token.json`

---

## 5. Summary of All Credentials

You should now have:

| Credential | Where to Get | Format |
|-----------|--------------|--------|
| **GEMINI_API_KEY** | https://aistudio.google.com/app/apikey | `AIzaSy...` (39 chars) |
| **CLOUDFLARE_ACCOUNT_ID** | Cloudflare Dashboard | `0f4ddf...` (32 chars) |
| **CLOUDFLARE_API_TOKEN** | Cloudflare API Tokens | `w4DzfK...` (40+ chars) |
| **DRIVE_FOLDER_ID** | Google Drive URL | `1WzQs6...` (33 chars) |
| **DRIVE_PROCESSED_FOLDER_ID** | Google Drive URL | `1BM8F0...` (33 chars) |
| **YOUTUBE_CLIENT_SECRET** | Google Cloud Console | JSON file content |
| **YOUTUBE_TOKEN** | Generated locally | JSON file content |

---

## 6. Local Setup (.env file)

Create a `.env` file in your project root:

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

Fill in:

```env
GEMINI_API_KEY=your_actual_gemini_key_here
CLOUDFLARE_ACCOUNT_ID=your_actual_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_actual_cloudflare_token
DRIVE_FOLDER_ID=your_actual_drive_folder_id
DRIVE_PROCESSED_FOLDER_ID=your_actual_processed_folder_id
YOUTUBE_CLIENT_SECRET_PATH=credentials/client_secret.json
DEFAULT_PRIVACY=public
UPLOAD_CATEGORY_ID=10
MAX_VIDEO_DURATION=59
INTRO_SKIP_SECONDS=10
WATERMARK_TEXT=Musiqstar
CHANNEL_NAME=Musiqstar
SECONDS_PER_IMAGE=3
MIN_IMAGES=4
MAX_IMAGES=15
CTA_TEXT=Like & Subscribe ❤️
CTA_DURATION=5
```

---

## 7. Test Locally

Before pushing to GitHub, test everything works:

```bash
# Test Drive connection
python main.py --list

# Test full pipeline (without upload)
python main.py --no-upload

# Test with upload
python main.py
```

If everything works, you're ready for GitHub!

---

## 8. Add to GitHub Secrets

Once your code is pushed to GitHub:

1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`
2. Click **"New repository secret"** for each:

### Secret 1: GEMINI_API_KEY
```
Name: GEMINI_API_KEY
Value: [Paste your Gemini API key]
```

### Secret 2: CLOUDFLARE_ACCOUNT_ID
```
Name: CLOUDFLARE_ACCOUNT_ID
Value: [Paste your Cloudflare account ID]
```

### Secret 3: CLOUDFLARE_API_TOKEN
```
Name: CLOUDFLARE_API_TOKEN
Value: [Paste your Cloudflare API token]
```

### Secret 4: DRIVE_FOLDER_ID
```
Name: DRIVE_FOLDER_ID
Value: [Paste your Drive folder ID]
```

### Secret 5: DRIVE_PROCESSED_FOLDER_ID
```
Name: DRIVE_PROCESSED_FOLDER_ID
Value: [Paste your processed folder ID]
```

### Secret 6: YOUTUBE_CLIENT_SECRET
```
Name: YOUTUBE_CLIENT_SECRET
Value: [Paste ENTIRE contents of credentials/client_secret.json]
```

To get the content:
```bash
# Windows
type credentials\client_secret.json

# Linux/Mac
cat credentials/client_secret.json
```

Copy everything including `{` and `}`

### Secret 7: YOUTUBE_TOKEN
```
Name: YOUTUBE_TOKEN
Value: [Paste ENTIRE contents of credentials/token.json]
```

To get the content:
```bash
# Windows
type credentials\token.json

# Linux/Mac
cat credentials/token.json
```

Copy everything including `{` and `}`

---

## 9. Troubleshooting

### Gemini API Key Issues
- **Error: API key not valid**
  - Regenerate key at https://aistudio.google.com/app/apikey
  - Make sure no extra spaces when copying

### Cloudflare Issues
- **Error: Authentication failed**
  - Verify Account ID is correct (32 hex characters)
  - Regenerate API token with correct permissions
  
### Drive Issues
- **Error: Folder not found**
  - Make sure folder is not in Trash
  - Check folder ID from URL is correct
  - Ensure Drive API is enabled

### YouTube Issues
- **Error: Invalid credentials**
  - Re-run `python main.py --list` to regenerate token
  - Make sure OAuth consent screen has your email as test user
  - Check both APIs are enabled (YouTube + Drive)

---

## 10. Security Reminders

✅ **DO:**
- Keep `.env` file local (never commit)
- Keep `credentials/` folder local (never commit)
- Use GitHub Secrets for automation
- Rotate API keys periodically

❌ **DON'T:**
- Share API keys publicly
- Commit credentials to git
- Use same keys across multiple projects
- Share OAuth tokens

---

## Need Help?

If you get stuck:
1. Check error messages carefully
2. Verify each credential is correct
3. Test locally before GitHub
4. Check API quotas and limits

---

**You're all set!** Once you have all 7 credentials, you can run the automation locally and on GitHub Actions.
