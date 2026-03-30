import json

from pydantic import BaseModel


class ResourceId(BaseModel):
    kind: str
    videoId: str


class ThumbnailInfo(BaseModel):
    url: str
    width: int | None = None
    height: int | None = None


class Thumbnails(BaseModel):
    default: ThumbnailInfo
    medium: ThumbnailInfo | None = None
    high: ThumbnailInfo | None = None


class PlaylistItemSnippet(BaseModel):
    title: str
    description: str
    publishedAt: str
    resourceId: ResourceId
    thumbnails: Thumbnails

    @property
    def url(self) -> str:
        return f"https://youtu.be/{self.resourceId.videoId}"

    @property
    def thumbnail_url(self) -> str:
        "Returns the URL for the thumbnail. It's high res if available"
        for name in ("high", "medium", "default"):
            thumb: ThumbnailInfo | None = getattr(self.thumbnails, name, None)
            if thumb and thumb.url:
                return thumb.url

        raise ValueError("No Thumbnails found")


class PlaylistItem(BaseModel):
    snippet: PlaylistItemSnippet


class ChannelSnippet(BaseModel):
    title: str  # name
    description: str  # bio
    publishedAt: str
    thumbnails: Thumbnails

    @property
    def profile_url(self) -> str:
        """Return the highest‑resolution profile picture that exists."""
        for name in ("high", "medium", "default"):
            thumb = getattr(self.thumbnails, name, None)
            if thumb and thumb.url:
                return thumb.url
        raise ValueError("No profile picture found")


class Channel(BaseModel):
    id: str
    snippet: ChannelSnippet


if __name__ == "__main__":
    with open("response.json", "r") as f:
        raw = json.load(f)

    items = [PlaylistItem(**item) for item in raw["items"]]

    for item in items:
        title = item.snippet.title
        video_id = item.snippet.resourceId.videoId
        url = item.snippet.url
        description = item.snippet.description
        published = item.snippet.publishedAt
        thumbnail = item.snippet.thumbnail_url

        print(title, url, description, thumbnail)
