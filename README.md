# YouTube Shorts Automation

Automated YouTube Shorts creator that downloads songs from Google Drive, generates AI-powered visuals, and uploads to YouTube.

## Features

- 🎵 AI-powered song analysis (Gemini)
- 🎨 Dynamic image generation (Cloudflare AI)
- 🎬 Automated video creation with lyrics
- 📤 Auto-upload to YouTube
- ⏰ Scheduled uploads (morning & evening)

## Setup

### 1. Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in your credentials
cp .env.example .env
```

### 2. GitHub Actions Setup

#### Required Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

1. **GEMINI_API_KEY** - Your Google Gemini API key
2. **CLOUDFLARE_ACCOUNT_ID** - Cloudflare account ID
3. **CLOUDFLARE_API_TOKEN** - Cloudflare API token
4. **DRIVE_FOLDER_ID** - Google Drive folder ID (where songs are stored)
5. **DRIVE_PROCESSED_FOLDER_ID** - Google Drive folder ID (for processed songs)
6. **YOUTUBE_CLIENT_SECRET** - Contents of `credentials/client_secret.json` file
7. **YOUTUBE_TOKEN** - Contents of `credentials/token.json` file (after first OAuth)

#### Getting YouTube Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3 and Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `client_secret.json`
6. Run locally once: `python main.py` to generate `token.json`
7. Copy contents of both files to GitHub secrets

### 3. Schedule Configuration

The workflow runs automatically:
- **Morning**: 6:00 AM UTC (adjust in `.github/workflows/auto-upload.yml`)
- **Evening**: 6:00 PM UTC

To change schedule, edit the cron expressions:
```yaml
schedule:
  - cron: '0 6 * * *'   # Morning (UTC)
  - cron: '0 18 * * *'  # Evening (UTC)
```

### 4. Manual Trigger

You can manually trigger the workflow:
1. Go to Actions tab in GitHub
2. Select "Auto Upload YouTube Shorts"
3. Click "Run workflow"

## Configuration

Edit `.env` to customize:

```env
# Channel settings
WATERMARK_TEXT=Musiqstar
CHANNEL_NAME=Musiqstar

# Video settings
MAX_VIDEO_DURATION=59
INTRO_SKIP_SECONDS=10

# Image generation
SECONDS_PER_IMAGE=3
MIN_IMAGES=4
MAX_IMAGES=15

# Call-to-action
CTA_TEXT=Like & Subscribe ❤️
CTA_DURATION=5
```

## Usage

### Local
```bash
# Process one song
python main.py

# List available songs
python main.py --list

# Process specific song
python main.py --song "Song Name"

# Process all songs
python main.py --all

# Generate without uploading
python main.py --no-upload
```

### GitHub Actions
Runs automatically on schedule or manually via Actions tab.

## Troubleshooting

- **FFmpeg not found**: Install FFmpeg on your system
- **API quota exceeded**: Wait or use different API keys
- **Upload failed**: Check YouTube token is valid
- **No songs found**: Verify Drive folder ID and permissions

## License

MIT
