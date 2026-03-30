import asyncio
from os import getenv
from typing import Any

from dotenv import load_dotenv
from TikTokApi import TikTokApi

load_dotenv()


async def get_latest_videos() -> tuple[list[str], list[int], list, Any]:
    "grabs all of the links of the past 10 videos from a certain tiktok user"
    ms_token = getenv("msToken")
    async with TikTokApi() as api:
        if ms_token is not None:
            print(ms_token)
            await api.create_sessions(
                num_sessions=1,
                sleep_after=3,
                headless=False,
                ms_tokens=[ms_token],
                browser="chromium",
                override_browser_args=["--disable-blink-features=AutomationControlled"],
            )
        else:
            await api.create_sessions(
                num_sessions=1,
                sleep_after=3,
                headless=False,
                browser="chromium",
                override_browser_args=["--disable-blink-features=AutomationControlled"],
            )

        user = api.user("sharkocalypse")
        user_data = await user.info()  # You need to fetch the user info first

        profile_picture = (
            user_data.get("userInfo", {}).get("user", {}).get("avatarLarger")
            or user_data.get("userInfo", {}).get("user", {}).get("avatarMedium")
            or user_data.get("userInfo", {}).get("user", {}).get("avatarThumb")
        )
        video_links: list[str] = []
        videos = []
        async for video in user.videos(count=20):
            videos.append(video)

        videos.sort(key=lambda v: v.id, reverse=True)

        # take latest 5
        latest_5 = videos[:5]
        video_links: list[str] = []
        video_ids: list[int] = []
        video_thumbnails = []
        for video in latest_5:
            video_ids.append(video.id)
            video_links.append(f"https://www.tiktok.com/@sharkocalypse/video/{video.id}")
            video_data = video.as_dict
            thumbnail = (
                video_data.get("video", {}).get("cover")  # Standard cover
                or video_data.get("video", {}).get("originCover")  # Original/higher res
                or video_data.get("video", {}).get("dynamicCover")  # Animated cover (if exists)
            )
            video_thumbnails.append(thumbnail)

        return video_links, video_ids, video_thumbnails, profile_picture


# This file is to be ran to initialise the database
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # So it would always run from the most parent directory and avoid import errors
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from SQL.socialMedia.tiktok import add_link

    async def put_videos_in_SQL_initial():
        links, ids, thumbnails, profile_picture = await get_latest_videos()
        for link, id in zip(links, ids):
            add_link(link, id)
        print(thumbnails)
        print(profile_picture)

    asyncio.run(put_videos_in_SQL_initial())
