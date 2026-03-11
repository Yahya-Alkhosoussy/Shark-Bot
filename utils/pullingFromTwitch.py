from datetime import datetime, timedelta, timezone
from os import getenv

import requests
from dotenv import load_dotenv

load_dotenv()
client_id = getenv("twitch_client_id")
client_secret = getenv("twitch_client_secret")

# Get access token:
token_r = requests.post(
    "https://id.twitch.tv/oauth2/token",
    params={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"},
)

access_token = token_r.json()["access_token"]

# Get broadcaster ID from username
headers = {"Client-ID": client_id, "Authorization": f"Bearer {access_token}"}


def get_user_id(username: str):
    user_r = requests.get("https://api.twitch.tv/helix/users", params={"login": username}, headers=headers)
    return user_r.json()["data"][0]["id"]


def get_clips(
    username: str = "sharkocalypse", days_ago: int = 0, hours_ago: int = 0, minutes_ago: int = 0, seconds_ago: int = 0
):
    broadcaster_id = get_user_id(username)
    # Get clips from the past 24 hours
    day_ago = (
        datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)
    ).isoformat()

    clips_r = requests.get(
        "https://api.twitch.tv/helix/clips",
        params={"broadcaster_id": broadcaster_id, "started_at": day_ago, "first": 20},
        headers=headers,
    )
    clips = clips_r.json()["data"]
    for clip in clips:
        print(clip["url"])


get_clips()
