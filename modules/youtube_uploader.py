"""
YouTube Shorts Uploader
Uploads videos to YouTube as Shorts with full metadata using YouTube Data API v3.
"""

import time
import httplib2
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import UPLOAD_CATEGORY_ID, DEFAULT_PRIVACY


# Retry configuration for resumable uploads
MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


def upload_to_youtube(creds, video_path, title, description, tags,
                       thumbnail_path=None, privacy_status=None,
                       category_id=None):
    """
    Upload a video to YouTube as a Short.

    Args:
        creds: Google OAuth2 credentials (from drive_downloader.authenticate)
        video_path: Path to the video file
        title: Video title (max 100 chars)
        description: Video description
        tags: List of tags
        thumbnail_path: Optional path to custom thumbnail
        privacy_status: 'public', 'private', or 'unlisted'
        category_id: YouTube category ID (default: 10 for Music)

    Returns:
        dict with 'video_id', 'url', and 'status'
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    privacy_status = privacy_status or DEFAULT_PRIVACY
    category_id = category_id or UPLOAD_CATEGORY_ID

    # Ensure title has #Shorts for YouTube to recognize it
    if "#shorts" not in title.lower() and "#Shorts" not in title:
        if len(title) + 9 <= 100:
            title = f"{title} #Shorts"

    # Truncate title if too long
    if len(title) > 100:
        title = title[:97] + "..."

    # Ensure description includes #Shorts
    if "#shorts" not in description.lower() and "#Shorts" not in description:
        description += "\n\n#Shorts"

    print(f"  📤 Uploading to YouTube...")
    print(f"  📝 Title: {title}")
    print(f"  🔒 Privacy: {privacy_status}")

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:30],  # YouTube allows max 30 tags
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
        }
    }

    # Create upload request with resumable upload
    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5  # 5MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Execute upload with retry logic
    response = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  ⬆️  Upload progress: {pct}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                retry += 1
                if retry > MAX_RETRIES:
                    raise Exception(f"Upload failed after {MAX_RETRIES} retries: {e}")
                wait_time = 2 ** retry
                print(f"  ⚠️  HTTP {e.resp.status}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            retry += 1
            if retry > MAX_RETRIES:
                raise Exception(f"Upload failed after {MAX_RETRIES} retries: {e}")
            wait_time = 2 ** retry
            print(f"  ⚠️  Error: {e}, retrying in {wait_time}s...")
            time.sleep(wait_time)

    video_id = response["id"]
    video_url = f"https://youtube.com/shorts/{video_id}"

    # Set custom thumbnail if provided
    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            _set_thumbnail(youtube, video_id, thumbnail_path)
        except Exception as e:
            print(f"  ⚠️  Thumbnail upload failed (video still uploaded): {e}")

    print(f"  ✅ Upload complete!")
    print(f"  🔗 Video URL: {video_url}")

    return {
        "video_id": video_id,
        "url": video_url,
        "status": privacy_status,
        "title": title
    }


def _set_thumbnail(youtube, video_id, thumbnail_path):
    """Set a custom thumbnail for an uploaded video."""
    thumbnail_path = Path(thumbnail_path)
    media = MediaFileUpload(
        str(thumbnail_path),
        mimetype="image/jpeg",
        resumable=False
    )
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=media
    ).execute()
    print(f"  🖼️  Custom thumbnail set!")
