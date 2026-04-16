import asyncio
import re
import time
from datetime import datetime, timedelta, timezone
from os import environ, getenv

import aiohttp
from dotenv import load_dotenv, set_key

from exceptions.exceptions import FormatError

load_dotenv()

_token_lock = asyncio.Lock()

async def refresh_token(user: str):
    async with _token_lock:
        async with aiohttp.ClientSession() as sesh:
            token_r = await sesh.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": getenv("mod_log_id"),
                    "client_secret": getenv("mod_log_secret"),
                    "grant_type": "refresh_token",
                    "refresh_token": getenv(user.upper() + "_TWITCH_REFRESH_TOKEN"),
                },
            )
        data = await token_r.json()

        # update in memory
        environ["TWITCH_ACCESS_TOKEN"] = data["access_token"]

        # update .env
        set_key(".env", f"{user.upper()}_TWITCH_ACCESS_TOKEN", data["access_token"])

        if "refresh_token" in data:
            environ[f"{user.upper()}_TWITCH_REFRESH_TOKEN"] = data["refresh_token"]
            set_key(".env", f"{user.upper()}_TWITCH_REFRESH_TOKEN", data["refresh_token"])

    return data["access_token"]


async def twitch_request(url: str, params: dict, user: str | None):
    if user == "shark" or user == "spider":
        headers = {
            "Client-ID": getenv("mod_log_id"),
            "Authorization": f"Bearer {getenv(f'{user.upper()}_TWITCH_ACCESS_TOKEN')}",
        }
        async with aiohttp.ClientSession() as sess:
            r = await sess.get(url, params=params, headers=headers)
            if r.status == 401 and user is not None:
                new_token = await refresh_token(user)
                headers["Authorization"] = f"Bearer {new_token}"
                r = await sess.get(url, params=params, headers=headers)
            return await r.json()
    else:
        async with aiohttp.ClientSession() as sesh:
            token_r = await sesh.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": getenv("twitch_client_id"),
                    "client_secret": getenv("twitch_client_secret"),
                    "grant_type": "client_credentials",
                },
            )

            token_json: dict = await token_r.json()
            access_token = token_json["access_token"]
            headers = {"Client-ID": getenv("twitch_client_id"), "Authorization": f"Bearer {access_token}"}
            r = await sesh.get(url, params=params, headers=headers)
            if r.status == 401 and user is not None:
                new_token = await refresh_token(user)
                headers["Authorization"] = f"Bearer {new_token}"
                r = await sesh.get(url, params=params, headers=headers)
            return await r.json()


async def get_user_id(twitch_user: str, user: str | None):
    user_r = await twitch_request("https://api.twitch.tv/helix/users", params={"login": twitch_user}, user=user)
    return user_r["data"][0]["id"]


def parse_twitch_duration(duration: str) -> timedelta:
    # Twitch gives duration in this format "6h26m14s", so use regular expressions to format it
    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    result = re.fullmatch(pattern=pattern, string=duration)
    if result is None:
        raise FormatError("duration is in the wrong format", 1011)
    hours = int(result.group(1) or 0)
    minutes = int(result.group(2) or 0)
    seconds = int(result.group(3) or 0)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


async def internal_handle_stream_end(username: str, user: str):
    broadcaster_id = await get_user_id(username, user)

    # Small buffer for twitch
    time.sleep(30)

    # grab most recent vod
    vod_r = await twitch_request(
        "https://api.twitch.tv/helix/videos", params={"user_id": broadcaster_id, "type": "archive", "first": 1}, user=user
    )
    vod = vod_r["data"][0]
    duration = parse_twitch_duration(vod["duration"])
    hours = int(duration.total_seconds() // 3600)
    minutes = int(duration.total_seconds() % 3600) // 60  # modulus is to strip the full hours from the equation
    seconds = int(duration.total_seconds() % 60)  # strips the full minutes

    clips = get_clips(username=username, user=user, hours_ago=hours, minutes_ago=minutes, seconds_ago=seconds)

    return await clips


async def is_live(username: str, user: str | None = None) -> bool:
    broadcaster_id = await get_user_id(user=user, twitch_user=username)

    response = await twitch_request(
        "https://api.twitch.tv/helix/streams",
        params={"user_id": broadcaster_id},
        user=user,
    )

    return bool(len(response["data"]) > 0)


async def user_exists(username: str, user: str | None = None) -> bool:
    user_r = await twitch_request("https://api.twitch.tv/helix/users", params={"login": username}, user=user)

    return bool(len(user_r["data"]) > 0)


async def get_clips(
    username: str = "sharkocalypse",
    days_ago: int = 0,
    hours_ago: int = 0,
    minutes_ago: int = 0,
    seconds_ago: int = 0,
    user: str = "shark",
) -> list[str]:
    broadcaster_id = await get_user_id(username, user)
    # Get clips from the past 24 hours
    day_ago = (
        datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)
    ).isoformat()

    clips_r = await twitch_request(
        "https://api.twitch.tv/helix/clips",
        params={"broadcaster_id": broadcaster_id, "started_at": day_ago, "first": 20},
        user=user,
    )
    clips = clips_r["data"]
    links: list[str] = []
    for clip in clips:
        links.append(clip["url"])

    return links


# live stream stuff
async def get_stream_details(username: str, user: str | None = None):
    "Returns the title, game name and viewer count of a stream!"
    broadcaster_id = await get_user_id(twitch_user=username, user=user)
    # get title
    stream_r = await twitch_request("https://api.twitch.tv/helix/streams", params={"user_id": broadcaster_id}, user=user)

    data = stream_r["data"]

    if data:
        title = data[0]["title"]
        game_name = data[0]["game_name"]
        thumbnail = data[0]["thumbnail_url"]
        return title, game_name, thumbnail
    return None


async def get_profile_picture(username: str, user: str | None = None):
    "returns a profile picture of a twitch user"
    broadcaster_id = await get_user_id(username, user)

    user_r = await twitch_request("https://api.twitch.tv/helix/users", params={"id": broadcaster_id}, user=user)

    user_data = user_r["data"][0]

    return user_data["profile_image_url"]


# mod stuff
async def get_bans(
    user: str, twitch_user: str
) -> tuple[list[str], list[str | None], list[str], list[timedelta | None], list[str]]:
    """
    Returns:
        list[str] -> banned usernames
        list[str] -> reasons banned
        list[str] -> mod that used the ban hammer
        list[timedelta | None] -> ban duration
    """
    r = await twitch_request(
        "https://api.twitch.tv/helix/moderation/banned",
        params={"broadcaster_id": await get_user_id(user=user, twitch_user=twitch_user)},
        user=user,
    )
    if r.get("status") == 401:
        print("ERROR: ", r)
        raise
    data = r["data"]
    people_banned: list[str] = []
    reasons: list[str | None] = []
    mod_that_banned: list[str] = []
    created_at: list[str] = []
    expires_at: list[str] = []
    duration: list[timedelta | None] = []
    for log in data:
        # print(log.keys())
        people_banned.append(log["user_name"])
        reasons.append(log["reason"]) if log["reason"] else reasons.append(None)
        mod_that_banned.append(log["moderator_name"])
        expires_at.append(log["expires_at"])
        created_at.append(log["created_at"])

    for ctime, etime in zip(created_at, expires_at):
        if etime:
            delta = datetime.fromisoformat(etime) - datetime.fromisoformat(ctime)
            duration.append(delta)
        else:
            duration.append(None)

    return people_banned, reasons, mod_that_banned, duration, created_at
