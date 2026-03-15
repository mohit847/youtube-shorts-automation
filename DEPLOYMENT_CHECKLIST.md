# Deployment Checklist ✅

Use this checklist to ensure everything is set up correctly.

## Pre-Deployment

- [ ] All code is working locally
- [ ] `.env` file configured with your credentials
- [ ] `credentials/client_secret.json` exists
- [ ] `credentials/token.json` generated (run `python main.py --list` once)
- [ ] Tested video generation locally
- [ ] Tested YouTube upload locally

## GitHub Repository Setup

- [ ] Created GitHub repository
- [ ] Repository is private (recommended for credentials safety)
- [ ] `.gitignore` is in place (prevents committing secrets)

## Push Code

- [ ] Run `git init` (if new repo)
- [ ] Run `git add .`
- [ ] Run `git commit -m "Initial commit"`
- [ ] Run `git remote add origin YOUR_REPO_URL`
- [ ] Run `git push -u origin main`

## GitHub Secrets Configuration

Go to: **Settings → Secrets and variables → Actions → New repository secret**

- [ ] Added `GEMINI_API_KEY`
- [ ] Added `CLOUDFLARE_ACCOUNT_ID`
- [ ] Added `CLOUDFLARE_API_TOKEN`
- [ ] Added `DRIVE_FOLDER_ID`
- [ ] Added `DRIVE_PROCESSED_FOLDER_ID`
- [ ] Added `YOUTUBE_CLIENT_SECRET` (entire JSON content)
- [ ] Added `YOUTUBE_TOKEN` (entire JSON content)

## Verify Secrets

Double-check each secret:
- [ ] No extra spaces or newlines
- [ ] JSON secrets are valid JSON format
- [ ] API keys are active and not expired
- [ ] Drive folder IDs are correct

## Test Workflow

- [ ] Go to **Actions** tab
- [ ] Click "Auto Upload YouTube Shorts"
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Wait for completion (5-10 minutes)
- [ ] Check if workflow succeeded (green checkmark)
- [ ] If failed, read error logs and fix issues

## Verify Upload

- [ ] Check your YouTube channel
- [ ] Verify video was uploaded
- [ ] Check video quality and metadata
- [ ] Verify song was moved to "Processed" folder in Drive

## Schedule Configuration

- [ ] Verified cron schedule in `.github/workflows/auto-upload.yml`
- [ ] Confirmed times are in UTC (convert from your timezone)
- [ ] Tested that schedule triggers correctly

## Monitoring Setup

- [ ] Enabled email notifications for workflow failures (GitHub Settings)
- [ ] Bookmarked Actions page for quick access
- [ ] Set up mobile notifications (optional)

## Maintenance Plan

- [ ] Know how to update secrets when tokens expire
- [ ] Know how to manually trigger workflow
- [ ] Know how to check logs for debugging
- [ ] Have backup of credentials locally

## Optional Enhancements

- [ ] Set up Slack/Discord notifications for uploads
- [ ] Create dashboard to track upload stats
- [ ] Add error alerting system
- [ ] Set up automatic token refresh

## Final Checks

- [ ] Workflow runs successfully
- [ ] Videos upload to YouTube
- [ ] Songs move to processed folder
- [ ] No errors in logs
- [ ] Schedule is working as expected

## Emergency Contacts

- GitHub Actions Status: https://www.githubstatus.com/
- YouTube API Status: https://developers.google.com/youtube/v3
- Cloudflare Status: https://www.cloudflarestatus.com/

---

## When Everything is ✅

🎉 **Congratulations!** Your automated YouTube Shorts system is live!

Your videos will now be automatically:
1. Downloaded from Google Drive
2. Analyzed with AI
3. Enhanced with visuals
4. Uploaded to YouTube
5. Moved to processed folder

**Twice daily** without any manual intervention!

---

## Quick Commands

```bash
# Check workflow status
gh run list --workflow=auto-upload.yml

# View latest run logs
gh run view --log

# Manually trigger workflow
gh workflow run auto-upload.yml

# List all secrets
gh secret list
```

(Requires GitHub CLI: https://cli.github.com/)
