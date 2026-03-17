import asyncio
from os import getenv

from dotenv import load_dotenv
from TikTokApi import TikTokApi

load_dotenv()


async def get_latest_videos() -> list[str]:
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
        video_links: list[str] = []
        async for video in user.videos(count=5):
            video_links.append(f"https://www.tiktok.com/@sharkocalypse/video/{video.id}")
        return video_links


# This file is to be ran to initialise the database
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # So it would always run from the most parent directory and avoid import errors
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from SQL.socialMedia.tiktok import add_link

    async def put_videos_in_SQL_initial():
        links = await get_latest_videos()
        for link in links:
            add_link(link)

    asyncio.run(put_videos_in_SQL_initial())
