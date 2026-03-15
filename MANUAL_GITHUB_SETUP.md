# Manual GitHub Setup Steps

## ✅ Security Check Complete

All sensitive data has been removed from the repository. You're safe to push!

## Step-by-Step Instructions

### 1. Update Git Repository

```bash
# Stage all cleaned files
git add -A

# Create new commit with cleaned files
git commit -m "Remove sensitive data and setup scripts"

# Check what will be pushed (verify no credentials)
git log --oneline -5
```

### 2. Create GitHub Repository

1. Go to: **https://github.com/new**
2. Repository name: `youtube-shorts-automation`
3. Description: `Automated YouTube Shorts creator with AI-powered visuals`
4. **Visibility: PRIVATE** ✅ (Highly recommended!)
5. **DO NOT** check "Add a README file"
6. **DO NOT** check "Add .gitignore"
7. Click **"Create repository"**

### 3. Push to GitHub

```bash
# Add remote repository
git remote add origin https://github.com/mohit847/youtube-shorts-automation.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

### 4. Add GitHub Secrets

Go to: **https://github.com/mohit847/youtube-shorts-automation/settings/secrets/actions**

Click **"New repository secret"** for each of these:

#### Secret 1: GEMINI_API_KEY
- Name: `GEMINI_API_KEY`
- Value: Your Gemini API key from https://aistudio.google.com/app/apikey

#### Secret 2: CLOUDFLARE_ACCOUNT_ID
- Name: `CLOUDFLARE_ACCOUNT_ID`
- Value: Your Cloudflare account ID from dashboard

#### Secret 3: CLOUDFLARE_API_TOKEN
- Name: `CLOUDFLARE_API_TOKEN`
- Value: Your Cloudflare API token

#### Secret 4: DRIVE_FOLDER_ID
- Name: `DRIVE_FOLDER_ID`
- Value: Your Google Drive folder ID (where songs are stored)

#### Secret 5: DRIVE_PROCESSED_FOLDER_ID
- Name: `DRIVE_PROCESSED_FOLDER_ID`
- Value: Your Google Drive processed folder ID

#### Secret 6: YOUTUBE_CLIENT_SECRET
- Name: `YOUTUBE_CLIENT_SECRET`
- Value: **Entire contents** of `credentials/client_secret.json`
- How to get:
  ```bash
  # Windows
  type credentials\client_secret.json
  
  # Linux/Mac
  cat credentials/client_secret.json
  ```
- Copy everything including the curly braces `{ ... }`

#### Secret 7: YOUTUBE_TOKEN
- Name: `YOUTUBE_TOKEN`
- Value: **Entire contents** of `credentials/token.json`
- How to get:
  ```bash
  # Windows
  type credentials\token.json
  
  # Linux/Mac
  cat credentials/token.json
  ```
- Copy everything including the curly braces `{ ... }`

### 5. Verify Secrets

After adding all 7 secrets, you should see them listed at:
https://github.com/mohit847/youtube-shorts-automation/settings/secrets/actions

✅ Checklist:
- [ ] GEMINI_API_KEY
- [ ] CLOUDFLARE_ACCOUNT_ID
- [ ] CLOUDFLARE_API_TOKEN
- [ ] DRIVE_FOLDER_ID
- [ ] DRIVE_PROCESSED_FOLDER_ID
- [ ] YOUTUBE_CLIENT_SECRET
- [ ] YOUTUBE_TOKEN

### 6. Test the Workflow

1. Go to: **https://github.com/mohit847/youtube-shorts-automation/actions**
2. Click **"Auto Upload YouTube Shorts"** workflow
3. Click **"Run workflow"** button (top right)
4. Select branch: `main`
5. Click green **"Run workflow"** button
6. Wait 5-10 minutes for completion
7. Check for green checkmark ✅ or red X ❌

### 7. Check Workflow Logs

If the workflow fails:
1. Click on the failed run
2. Click on "upload-video" job
3. Expand each step to see error messages
4. Common issues:
   - Missing or incorrect secrets
   - Expired YouTube token
   - No songs in Drive folder
   - API quota exceeded

### 8. Verify Upload

After successful run:
- ✅ Check your YouTube channel for new video
- ✅ Check Google Drive - song should be in "Processed" folder
- ✅ Check video has correct metadata and visuals

## Schedule

Your automation will run automatically:
- **Morning**: 6:00 AM UTC (11:30 AM IST)
- **Evening**: 6:00 PM UTC (11:30 PM IST)

## Troubleshooting

### YouTube Token Expired

If you get authentication errors:

1. Run locally:
   ```bash
   python main.py --list
   ```

2. Browser will open for authentication

3. Sign in and grant permissions

4. New `credentials/token.json` will be created

5. Copy its contents to GitHub secret `YOUTUBE_TOKEN`

### No Songs Found

- Verify `DRIVE_FOLDER_ID` is correct
- Check songs are in the folder
- Ensure Drive API is enabled

### FFmpeg Errors

- Usually means invalid video settings
- Check GitHub Actions logs for details

### Rate Limiting

- Cloudflare AI: Wait or reduce image count
- YouTube API: Check daily quota
- Gemini API: Wait or use different key

## Security Best Practices

✅ **DO:**
- Keep repository PRIVATE
- Use GitHub Secrets for all credentials
- Rotate API keys periodically
- Monitor workflow runs

❌ **DON'T:**
- Commit `.env` file
- Commit `credentials/` folder
- Share secrets publicly
- Use personal tokens in code

## Need Help?

Check the workflow logs in GitHub Actions for detailed error messages.

## Summary

You're all set! Once you:
1. ✅ Push code to GitHub
2. ✅ Add 7 secrets
3. ✅ Test workflow

Your YouTube Shorts will be automatically created and uploaded twice daily! 🎉
