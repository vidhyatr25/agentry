import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import Publisher

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


@provider("publisher", "youtube")
class YouTubePublisher(Publisher):
    def _access_token(self):
        client_id = self.options.get("client_id") or self.ctx.secrets.get("YOUTUBE_CLIENT_ID")
        client_secret = self.options.get("client_secret") or self.ctx.secrets.get(
            "YOUTUBE_CLIENT_SECRET"
        )
        refresh_token = self.options.get("refresh_token") or self.ctx.secrets.get(
            "YOUTUBE_REFRESH_TOKEN"
        )
        resp = requests.post(
            TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=60,
        )
        if resp.status_code >= 400:
            raise ProviderError(f"youtube token refresh failed: {resp.status_code}")
        return resp.json()["access_token"]

    def publish(self, video_path, metadata):
        token = self._access_token()
        snippet = {
            "title": metadata["title"][:100],
            "description": metadata.get("description", "")[:4900],
            "tags": metadata.get("tags", [])[:30],
            "categoryId": str(self.options.get("category_id", 24)),
        }
        status = {
            "privacyStatus": self.options.get("privacy", "public"),
            "selfDeclaredMadeForKids": bool(self.options.get("made_for_kids", True)),
        }
        init = requests.post(
            UPLOAD_URL,
            params={"uploadType": "resumable", "part": "snippet,status"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Upload-Content-Type": "video/*",
            },
            json={"snippet": snippet, "status": status},
            timeout=120,
        )
        if init.status_code >= 400:
            raise ProviderError(f"youtube init failed: {init.status_code} {init.text[:300]}")
        upload_url = init.headers["Location"]
        with open(video_path, "rb") as handle:
            content = handle.read()
        upload = requests.put(
            upload_url,
            headers={"Content-Type": "video/*", "Content-Length": str(len(content))},
            data=content,
            timeout=self.options.get("upload_timeout", 1200),
        )
        if upload.status_code >= 400:
            raise ProviderError(
                f"youtube upload failed: {upload.status_code} {upload.text[:300]}"
            )
        video_id = upload.json()["id"]
        return {
            "platform": "youtube",
            "video_id": video_id,
            "url": f"https://youtu.be/{video_id}",
            "status": "published",
        }
