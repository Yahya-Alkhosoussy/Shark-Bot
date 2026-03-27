from os import getenv

from dotenv import load_dotenv
from googleapiclient.discovery import build

from utils.socials.youtubeCore.core import PlaylistItem

load_dotenv()

API_KEY = getenv("youtube_client_secret")

youtube = build("youtube", "v3", developerKey=API_KEY)


def get_channel(youtube_handle: str):

    channel_response = youtube.channels().list(part="contentDetails", forHandle=youtube_handle).execute()
    return channel_response


def get_uploads_id(youtube_handle: str) -> str:
    response = get_channel(youtube_handle)

    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_items(youtube_handle: str, limit: int = 10) -> list[PlaylistItem]:

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

    items = [PlaylistItem(**item) for item in raw_response["items"]]

    return items
