from datetime import datetime, timedelta, timezone
from os import environ, getenv

import requests
from dotenv import load_dotenv, set_key

load_dotenv()


def refresh_token(user: str):
    token_r = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": getenv("mod_log_id"),
            "client_secret": getenv("mod_log_secret"),
            "grant_type": "refresh_token",
            "refresh_token": getenv(user.upper() + "_TWITCH_REFRESH_TOKEN"),
        },
    )
    data = token_r.json()

    # update in memory
    environ["TWITCH_ACCESS_TOKEN"] = data["access_token"]

    # update .env
    set_key(".env", f"{user.upper()}_TWITCH_ACCESS_TOKEN", data["access_token"])

    if "refresh_token" in data:
        environ[f"{user.upper()}_TWITCH_REFRESH_TOKEN"] = data["refresh_token"]
        set_key(".env", f"{user.upper()}_TWITCH_REFRESH_TOKEN", data["refresh_token"])

    return data["access_token"]


def twitch_request(url: str, params: dict, user: str):
    if user == "shark" or user == "spider":
        headers = {
            "Client-ID": getenv("mod_log_id"),
            "Authorization": f"Bearer {getenv(f'{user.upper()}_TWITCH_ACCESS_TOKEN')}",
        }
    else:
        token_r = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": getenv("twitch_client_id"),
                "client_secret": getenv("twitch_client_secret"),
                "grant_type": "client_credentials",
            },
        )
        access_token = token_r.json()["access_token"]
        headers = {"Client-ID": getenv("twitch_client_id"), "Authorization": f"Bearer {access_token}"}
    r = requests.get(url, params=params, headers=headers)
    if r.status_code == 401:
        new_token = refresh_token(user)
        headers["Authorization"] = f"Bearer {new_token}"
        r = requests.get(url, params=params, headers=headers)
    return r.json()


def get_user_id(twitch_user: str, user: str):
    user_r = twitch_request("https://api.twitch.tv/helix/users", params={"login": twitch_user}, user=user)
    return user_r["data"][0]["id"]


def get_clips(
    username: str = "sharkocalypse",
    days_ago: int = 0,
    hours_ago: int = 0,
    minutes_ago: int = 0,
    seconds_ago: int = 0,
    user: str = "shark",
) -> list[str]:
    broadcaster_id = get_user_id(username, user)
    # Get clips from the past 24 hours
    day_ago = (
        datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)
    ).isoformat()

    clips_r = twitch_request(
        "https://api.twitch.tv/helix/clips",
        params={"broadcaster_id": broadcaster_id, "started_at": day_ago, "first": 20},
        user=user,
    )
    clips = clips_r["data"]
    links: list[str] = []
    for clip in clips:
        links.append(clip["url"])

    return links


# mod stuff
def get_bans(user: str, twitch_user: str) -> tuple[list[str], list[str], list[str], list[timedelta | None]]:
    """
    Returns:
        list[str] -> banned usernames
        list[str] -> reasons banned
        list[str] -> mod that used the ban hammer
        list[timedelta | None] -> ban duration
    """
    r = twitch_request(
        "https://api.twitch.tv/helix/moderation/banned",
        params={"broadcaster_id": get_user_id(user=user, twitch_user=twitch_user)},
        user=user,
    )
    if r.get("status") == 401:
        raise
    data = r["data"]
    people_banned: list[str] = []
    reasons: list[str] = []
    mod_that_banned: list[str] = []
    created_at: list[str] = []
    expires_at: list[str] = []
    duration: list[timedelta | None] = []
    for log in data:
        # print(log.keys())
        people_banned.append(log["user_name"])
        reasons.append(log["reason"])
        mod_that_banned.append(log["moderator_name"])
        expires_at.append(log["expires_at"])
        created_at.append(log["created_at"])

    for ctime, etime in zip(created_at, expires_at):
        if etime:
            delta = datetime.fromisoformat(etime) - datetime.fromisoformat(ctime)
            duration.append(delta)
        else:
            duration.append(None)

    return people_banned, reasons, mod_that_banned, duration
