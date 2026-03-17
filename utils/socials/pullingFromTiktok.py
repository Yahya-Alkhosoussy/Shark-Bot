import asyncio

from TikTokApi import TikTokApi


async def get_latest_videos() -> list[str]:
    "grabs all of the links of the past 10 videos from a certain tiktok user"
    async with TikTokApi() as api:
        await api.create_sessions(num_sessions=1, sleep_after=3, headless=False)

        user = api.user("sharkocalypse")
        video_links: list[str] = []
        async for video in user.videos(count=5):
            video_links.append(f"https://www.tiktok.com/@sharkocalypse/video/{video.id}")

        return video_links


asyncio.run(get_latest_videos())
