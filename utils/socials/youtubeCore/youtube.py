import json
from os import getenv

from dotenv import load_dotenv
from googleapiclient.discovery import build

if __name__ != "__main__":
    from utils.socials.youtubeCore.core import Channel, PlaylistItem
else:
    from core import Channel, PlaylistItem

load_dotenv()

API_KEY = getenv("youtube_client_secret")

youtube = build("youtube", "v3", developerKey=API_KEY)


def get_channel(youtube_handle: str):

    channel_response = youtube.channels().list(part="contentDetails", forHandle=youtube_handle).execute()
    return channel_response


def get_channel_id(youtube_handle: str):
    channel_response = youtube.channels().list(part="id", forHandle=youtube_handle).execute()
    return channel_response["items"][0]["id"]


def get_uploads_id(youtube_handle: str) -> str:
    response = get_channel(youtube_handle)

    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_video_items(youtube_handle: str, limit: int = 10) -> list[PlaylistItem]:

    uploads_playlist_id = get_uploads_id(youtube_handle)
    # Make your API call
    raw_response = (
        youtube.playlistItems()
        .list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=limit,
        )
        .execute()
    )
    with open("response.json", mode="w") as f:
        json.dump(raw_response, f)

    items = [PlaylistItem(**item) for item in raw_response["items"]]

    return items


def get_channel_item(youtube_handle: str) -> Channel:
    channel = get_channel_id(youtube_handle)
    raw_response = youtube.channels().list(part="snippet", id=channel).execute()
    with open("channel_response.json", mode="w") as f:
        json.dump(raw_response, f, indent=2)

    return Channel(**raw_response["items"][0])
