import json

from pydantic import BaseModel


class ResourceId(BaseModel):
    kind: str
    videoId: str


class PlaylistItemSnippet(BaseModel):
    title: str
    description: str
    publishedAt: str
    resourceId: ResourceId

    @property
    def url(self) -> str:
        return f"https://youtu.be/{self.resourceId.videoId}"


class PlaylistItem(BaseModel):
    snippet: PlaylistItemSnippet


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

        print(title, url, description)
